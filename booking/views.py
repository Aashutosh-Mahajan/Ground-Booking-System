from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta, datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .forms import BookingForm, PlayerForm
from .models import Player, Booking, AllotedGroundBooking
from .models import StudentUser, AdminUser
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from booking.models import StudentUser
from booking.utils.crypto import decrypt_data


# -------------------- HOME --------------------
def home(request):
    return render(request, 'booking/home.html')

# -------------------- STUDENT BOOKING HISTORY --------------------
def student_history(request):
    """Show the logged-in student's booking history with status."""
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')

    status_filter = (request.GET.get('status') or '').strip()

    bookings = (
        Booking.objects
        .filter(student_email=student_email)
        .prefetch_related('players')
        .order_by('-date', '-created_at')
    )
    if status_filter in {"Pending", "Approved", "Rejected"}:
        bookings = bookings.filter(status=status_filter)

    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'booking/student_history.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'student_email': student_email,
    })

# -------------------- STUDENT LOGIN --------------------
def student_login(request):
    if request.method == "POST":
        email_input = request.POST.get("email")
        password = request.POST.get("password")

        # Step 1: Validation (same as before)
        if not email_input or not password:
            return render(request, "booking/student_login.html", {
                "error": "Please enter both email and password."
            })
        
        students = StudentUser.objects.all()

        for student in students:
            try:
                decrypted_email = decrypt_data(student.email)

                if decrypted_email == email_input:
                    if student.password == password:
                        request.session["student_email"] = decrypted_email
                        request.session["student_id"] = student.id
                        return redirect("student_dashboard")
                    else:
                        return render(request, "booking/student_login.html", {
                            "error": "Invalid password"
                        })
            except Exception:
                # In case of corrupted or old plaintext data
                continue

        # Step 3: No match found
        return render(request, "booking/student_login.html", {
            "error": "No student found with this email address"
        })

    return render(request, "booking/student_login.html")


def student_logout(request):
    request.session.flush()
    return redirect('student_login')

# -------------------- ADMIN LOGIN --------------------
def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            admin = AdminUser.objects.get(username=username)
            if admin.password == password:
                request.session['is_admin_logged_in'] = True
                request.session['admin_username'] = admin.username
                return redirect('custom_admin_dashboard')
            else:
                messages.error(request, "Invalid password")
        except AdminUser.DoesNotExist:
            messages.error(request, "No admin found with this username")

    return render(request, 'booking/admin_login.html')

def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

# -------------------- ADMIN DASHBOARD --------------------
def custom_admin_dashboard(request):
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')

    date_str = (request.GET.get('date') or '').strip()
    ground   = (request.GET.get('ground') or '').strip()

    # FCFS: show oldest pending first
    bookings_qs = Booking.objects.filter(status='Pending').order_by('created_at')
    allot_qs    = AllotedGroundBooking.objects.select_related('booking').all().order_by('-date')

    if date_str:
        bookings_qs = bookings_qs.filter(date=date_str)
        allot_qs    = allot_qs.filter(date=date_str)

    if ground:
        bookings_qs = bookings_qs.filter(ground__iexact=ground)
        allot_qs    = allot_qs.filter(ground__iexact=ground)

    # Implement pagination for allotments (10 entries per page)
    allotments_paginator = Paginator(allot_qs, 10)
    page_number = request.GET.get('page', 1)
    allotments_page = allotments_paginator.get_page(page_number)

    grounds = (Booking.objects.values_list('ground', flat=True)
               .distinct().order_by('ground'))

    context = {
        'bookings': bookings_qs,
        'allotments': allotments_page,
        'allotments_paginator': allotments_paginator,
        'grounds': grounds,
        'selected_date': date_str,
        'selected_ground': ground,
    }
    return render(request, 'booking/admin_dashboard.html', context)

def get_players(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    players = Player.objects.filter(booking=booking).values(
        "name", "branch", "year", "division",
    )
    return JsonResponse({
        "booking": booking.student_name,
        "players": list(players)
    }, status=200)

def get_equipment_for_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return JsonResponse({
        "equipment": booking.equipment or ""
    }, status=200)

# -------------------- Approve / Reject Booking --------------------
def approve_booking(request, booking_id):
    """Approve booking with graceful email error handling"""
    booking = get_object_or_404(Booking, id=booking_id)

    # Enforce FCFS and auto-reject conflicting pending requests atomically
    with transaction.atomic():
        # Lock the queue for this slot
        same_slot = (
            Booking.objects
            .select_for_update()
            .filter(
                date=booking.date,
                sport__iexact=(booking.sport or ''),
                time_slot=booking.time_slot,
            )
        )

        # Oldest pending wins for FCFS
        oldest_pending = same_slot.filter(status='Pending').order_by('created_at').first()
        to_approve = oldest_pending or booking

        # Set approved
        to_approve.status = 'Approved'
        to_approve.save()

        # Auto-reject all other pending for this exact slot (same date/sport/time)
        conflicts_qs = same_slot.filter(status='Pending').exclude(id=to_approve.id)
        conflicts = list(conflicts_qs)
        for c in conflicts:
            c.status = 'Rejected'
        if conflicts:
            Booking.objects.bulk_update(conflicts, ['status'])

        # Reflect in AllotedGroundBooking
        players_count = to_approve.players.count()
        AllotedGroundBooking.objects.update_or_create(
            booking=to_approve,
            date=to_approve.date,
            ground=to_approve.ground,
            time_slot=to_approve.time_slot,
            defaults={
                'allotted_to': to_approve.student_name,
                'roll_number': to_approve.roll_number,
                'purpose': to_approve.purpose,
                'players': players_count,
            }
        )

    # Email approved - mandatory email sending
    try:
        html = render_to_string(
            'booking/emails/booking_status_email.html',
            {
                'site_name': 'SportDeck',
                'status': 'Approved',
                'booking': to_approve,
                'players': list(to_approve.players.all().values('name', 'branch', 'year', 'division')),
            }
        )
        plain = strip_tags(html)
        send_mail(
            subject=f'Booking Approved — {to_approve.ground} on {to_approve.date}',
            message=plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_approve.student_email],
            html_message=html,
            fail_silently=False,
        )
        messages.success(request, f'Booking approved and confirmation email sent to {to_approve.student_email}')
    except Exception as e:
        # Email failed - log error and show warning but booking is still approved
        print(f"ERROR: Failed to send approval email to {to_approve.student_email}: {e}")
        messages.warning(request, f'Booking approved, but email notification failed. Please inform student manually.')
        pass

    # Email auto-rejected
    for rej in conflicts:
        try:
            r_html = render_to_string(
                'booking/emails/booking_status_email.html',
                {
                    'site_name': 'SportDeck',
                    'status': 'Rejected',
                    'booking': rej,
                    'players': list(rej.players.all().values('name', 'branch', 'year', 'division')),
                }
            )
            r_plain = strip_tags(r_html)
            send_mail(
                subject=f'Booking Rejected — {rej.ground} on {rej.date}',
                message=r_plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[rej.student_email],
                html_message=r_html,
                fail_silently=True,
            )
        except Exception:
            pass

    return redirect('custom_admin_dashboard')

def reject_booking(request, booking_id):
    """Reject booking with graceful email error handling"""
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'Rejected'
    booking.save()

    # Build HTML email and send - mandatory email sending
    try:
        html = render_to_string(
            'booking/emails/booking_status_email.html',
            {
                'site_name': 'SportDeck',
                'status': 'Rejected',
                'booking': booking,
                'players': list(booking.players.all().values('name', 'branch', 'year', 'division')),
            }
        )
        plain = strip_tags(html)
        send_mail(
            subject=f'Booking Rejected — {booking.ground} on {booking.date}',
            message=plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.student_email],
            html_message=html,
            fail_silently=False,
        )
        messages.success(request, f'Booking rejected and notification email sent to {booking.student_email}')
    except Exception as e:
        # Email failed - log error and show warning but booking is still rejected
        print(f"ERROR: Failed to send rejection email to {booking.student_email}: {e}")
        messages.warning(request, f'Booking rejected, but email notification failed. Please inform student manually.')
        pass
    
    return redirect('custom_admin_dashboard')
def student_booking(request):
    number_options = range(1, 12)

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            # Get booking details
            student_email = request.POST.get("student_email")
            booking_date = request.POST.get("date")
            
            # Check 1-day restriction for main student
            one_day_ago = datetime.now().date() - timedelta(days=1)
            recent_bookings = Booking.objects.filter(
                student_email=student_email,
                date__gte=one_day_ago,
                status='Approved'
            )
            
            if recent_bookings.exists():
                messages.error(request, f"You have already booked a ground within the last 24 hours. Please wait until {recent_bookings.first().date + timedelta(days=1)} to make another booking.")
                return render(request, 'booking/student_booking.html', {
                    'booking_form': booking_form,
                    'number_options': number_options
                })
            
            # Check 1-day restriction for selected players
            num_players = int(request.POST.get("number_of_players", 1))
            restricted_players = []
            
            for i in range(1, num_players + 1):
                player_email = request.POST.get(f'player{i}_name')
                if player_email:
                    # Check if this player has booked within 1 day
                    player_recent_bookings = Booking.objects.filter(
                        student_email=player_email,
                        date__gte=one_day_ago,
                        status='Approved'
                    )
                    if player_recent_bookings.exists():
                        try:
                            player = StudentUser.objects.get(email=player_email)
                            restricted_players.append(player.full_name)
                        except StudentUser.DoesNotExist:
                            restricted_players.append(player_email)
            
            if restricted_players:
                players_list = ", ".join(restricted_players)
                messages.error(request, f"The following players have already booked a ground within the last 24 hours and cannot be added: {players_list}")
                return render(request, 'booking/student_booking.html', {
                    'booking_form': booking_form,
                    'number_options': number_options
                })

            booking = booking_form.save(commit=False)

            # Organizer info
            booking.student_name = request.POST.get("student_name")
            booking.student_email = request.POST.get("student_email")
            booking.roll_number = ''  # optional, can fetch if needed

            # Booking info
            booking.ground = request.POST.get("ground")
            booking.sport = request.POST.get("sport") or ''
            booking.date = request.POST.get("date")
            booking.time_slot = request.POST.get("time_slot")
            booking.equipment = request.POST.get("equipment_selected") or request.POST.get('equipment') or ''
            booking.purpose = request.POST.get("purpose")
            booking.number_of_players = num_players

            booking.save()

            # Save players dynamically (auto-fetch branch/year/division)
            num_players = booking.number_of_players
            for i in range(1, num_players + 1):
                player_name_or_email = request.POST.get(f'player{i}_name')
                if not player_name_or_email:
                    continue

                # Fetch student from DB
                try:
                    student = StudentUser.objects.get(email=player_name_or_email)
                    Player.objects.create(
                        booking=booking,
                        name=student.full_name,
                        branch=student.branch,
                        year=student.year,
                        division=student.division
                    )
                except StudentUser.DoesNotExist:
                    # If not found, create with only name
                    Player.objects.create(
                        booking=booking,
                        name=player_name_or_email,
                        branch='',
                        year='',
                        division=''
                    )

            # Ensure at least one player exists (include organizer if none selected)
            if booking.players.count() == 0:
                try:
                    organizer = StudentUser.objects.get(email=booking.student_email)
                    Player.objects.create(
                        booking=booking,
                        name=organizer.full_name or booking.student_name,
                        branch=organizer.branch or '',
                        year=organizer.year or '',
                        division=organizer.division or ''
                    )
                except StudentUser.DoesNotExist:
                    Player.objects.create(
                        booking=booking,
                        name=booking.student_name or (booking.student_email or 'Organizer'),
                        branch='',
                        year='',
                        division=''
                    )

            return redirect('booking_success')
    else:
        booking_form = BookingForm()

    return render(request, 'booking/student_booking.html', {
        'booking_form': booking_form,
        'number_options': number_options
    })

def booking_success(request):
    return render(request, 'booking/booking_success.html')

# -------------------- STUDENT DASHBOARD --------------------
def student_dashboard(request):
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')

    first_name = student_email.split("@")[0].split(".")[0].capitalize()

    return render(request, 'booking/student_dashboard.html', {
        'student_email': student_email,
        'first_name': first_name,
    })

# -------------------- RULES --------------------
def rules_regulations(request):
    return render(request, 'booking/rules_regulations.html')

# -------------------- AJAX AVAILABILITY --------------------
@csrf_exempt
def check_availability(request):
    ground = request.GET.get("ground")
    date_selected = request.GET.get("date")
    sport = (request.GET.get("sport") or '').strip()

    time_slots = [
        "07:00 AM - 09:00 AM", "04:00 PM - 06:00 PM",
    ]

    slots = []

    if not ground or not date_selected or not sport:
        for slot in time_slots:
            slots.append({"time": slot, "status": "freeze"})
        return JsonResponse({"slots": slots}, status=200)

    def parse_time_to_minutes(tstr):
        tstr = tstr.strip()
        fmts = ["%I:%M %p", "%I:%M%p", "%H:%M", "%I %p"]
        for fmt in fmts:
            try:
                dt = datetime.strptime(tstr, fmt)
                return dt.hour * 60 + dt.minute
            except Exception:
                continue
        try:
            parts = tstr.split(':')
            if len(parts) == 2:
                h = int(parts[0])
                m = int(''.join(ch for ch in parts[1] if ch.isdigit()))
                return h * 60 + m
        except Exception:
            pass
        return None

    def parse_range(rng):
        if not rng or '-' not in rng:
            return (None, None)
        a, b = rng.split('-', 1)
        start = parse_time_to_minutes(a)
        end = parse_time_to_minutes(b)
        return (start, end)

    approved_bookings = Booking.objects.filter(
        date=date_selected,
        status__iexact='Approved',
        sport__iexact=sport,
    )
    approved_ranges = []
    for b in approved_bookings:
        s, e = parse_range(b.time_slot or '')
        if s is not None and e is not None:
            approved_ranges.append((s, e))

    for slot in time_slots:
        slot_s, slot_e = parse_range(slot)
        booked = False
        if slot_s is not None and slot_e is not None:
            for (bs, be) in approved_ranges:
                if bs < slot_e and slot_s < be:
                    booked = True
                    break

        slots.append({
            "time": slot,
            "status": "booked" if booked else "available"
        })

    return JsonResponse({"slots": slots}, status=200)

# -------------------- AJAX: Fetch Student Data --------------------
def fetch_student_data(request):
    """
    AJAX endpoint to fetch student info by first name
    """
    q = request.GET.get("q", "")
    print(f"[fetch_student_data] Received query: '{q}'")
    
    if not q:
        print("[fetch_student_data] Empty query, returning empty list")
        return JsonResponse([], safe=False)

    # Search by first name (split full_name and check first part)
    students = StudentUser.objects.filter(full_name__icontains=q)[:10]
    print(f"[fetch_student_data] Found {students.count()} students")
    
    data = []
    for s in students:
        if s.full_name:  # Only include students with names
            data.append({
                "full_name": s.full_name,
                "email": s.email,
                "roll_number": s.roll_number,
                "branch": s.branch,
                "year": s.year,
                "division": s.division
            })
    
    print(f"[fetch_student_data] Returning {len(data)} student records")
    return JsonResponse(data, safe=False)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import AllotedGroundBooking

def get_allotment_players(request, allot_id):
    allotment = get_object_or_404(AllotedGroundBooking, id=allot_id)
    # Some legacy/allotment entries may not be linked to a Booking
    if not allotment.booking:
        return JsonResponse({"players": []})
    players = allotment.booking.players.all()  # get all players linked to this booking
    data = [
        {
            "name": p.name,
            "branch": p.branch,
            "year": p.year,
            "division": p.division,
        }
        for p in players
    ]
    return JsonResponse({"players": data})

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import AllotedGroundBooking

def get_equipment_for_allotment(request, allot_id):
    allotment = get_object_or_404(AllotedGroundBooking, id=allot_id)
    equipment = allotment.booking.equipment if allotment.booking else ""
    return JsonResponse({"equipment": equipment})
