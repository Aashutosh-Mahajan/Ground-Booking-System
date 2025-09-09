from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta, datetime
from django.views.decorators.csrf import csrf_exempt
from .forms import BookingForm, PlayerForm
from .models import Player, Booking,AllotedGroundBooking
from .models import StudentUser, AdminUser
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings

# -------------------- HOME --------------------
def home(request):
    return render(request, 'booking/home.html')


# -------------------- STUDENT LOGIN --------------------

def student_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
        else:
            # Look up student in DB and verify password
            try:
                student = StudentUser.objects.get(email=email)
                # Plain-text check from DB as requested
                if student.password == password:
                    request.session['student_email'] = student.email
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Invalid password")
            except StudentUser.DoesNotExist:
                messages.error(request, "No student found with this email")

    return render(request, "booking/student_login.html")

def student_logout(request):
    # Clear all student-related session data
    request.session.flush()
    return redirect('student_login')

# -------------------- ADMIN LOGIN --------------------


def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            admin = AdminUser.objects.get(username=username)
            # Plain-text check from DB as requested
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
# --------------------------
# Admin Dashboard
# --------------------------
def custom_admin_dashboard(request):
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')

    date_str = (request.GET.get('date') or '').strip()
    ground   = (request.GET.get('ground') or '').strip()

    # Show only pending booking requests in the Booking Requests table
    bookings_qs = Booking.objects.filter(status='Pending').order_by('-created_at')
    allot_qs    = AllotedGroundBooking.objects.all().order_by('-date')

    if date_str:
        bookings_qs = bookings_qs.filter(date=date_str)
        allot_qs    = allot_qs.filter(date=date_str)      # remove this line if you don't want to filter allotments

    if ground:
        bookings_qs = bookings_qs.filter(ground__iexact=ground)
        allot_qs    = allot_qs.filter(ground__iexact=ground)  # same note as above

    grounds = (Booking.objects.values_list('ground', flat=True)
               .distinct().order_by('ground'))

    context = {
        'bookings': bookings_qs,
        'allotments': allot_qs,
        'grounds': grounds,
        'selected_date': date_str,
        'selected_ground': ground,
    }
    return render(request, 'booking/admin_dashboard.html', context)

def get_players(request, booking_id):
    # Fetch booking
    booking = get_object_or_404(Booking, id=booking_id)

    # Get players linked to this booking
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
# --------------------------
# Approve Booking → Move to AllotedGroundBooking
# --------------------------
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'Approved'
    booking.save()

    AllotedGroundBooking.objects.get_or_create(
        booking=booking,   # 🔥 link booking here
        date=booking.date,
        ground=booking.ground,
        time_slot=booking.time_slot,
        allotted_to=booking.student_name,
        roll_number=booking.roll_number,
        purpose=booking.purpose,
        players=booking.number_of_players,
    )
    send_mail(
        subject=f'Ground Booking Approved for {booking.ground}',
        message=f'Hello {booking.student_name},\n\n'
                f'Your booking for the ground "{booking.ground}" on {booking.date} '
                f'during "{booking.time_slot}" has been approved.\n\n'
                f'Thank you!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.student_email],
        fail_silently=False,
    )
    return redirect('custom_admin_dashboard')

def get_allotment_players(request, allot_id):
    allotment = get_object_or_404(AllotedGroundBooking, id=allot_id)
    players = allotment.booking.players.all()  # 👈 works now!
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


def get_equipment_for_allotment(request, allot_id):
    allotment = get_object_or_404(AllotedGroundBooking, id=allot_id)
    equipment = allotment.booking.equipment if allotment.booking else ""
    return JsonResponse({"equipment": equipment}, status=200)

# Reject Booking
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'Rejected'
    booking.save()

    send_mail(
        subject=f'Ground Booking Rejected for {booking.ground}',
        message=f'Hello {booking.student_name},\n\n'
                f'Your booking for the ground "{booking.ground}" on {booking.date} '
                f'during "{booking.time_slot}" has been rejected.\n\n'
                f'Please contact admin for details.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.student_email],
        fail_silently=False,
    )
    return redirect('custom_admin_dashboard')

# -------------------- STUDENT BOOKING --------------------
def student_booking(request):
    number_options = range(1, 12)

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            booking = booking_form.save(commit=False)

            # Assign student info from form
            booking.student_name = request.POST.get("student_name")
            booking.student_email = request.POST.get("student_email")
            booking.student_branch = request.POST.get("student_branch")
            booking.student_year = request.POST.get("student_year")
            booking.student_division = request.POST.get("student_division")
            booking.roll_number = request.POST.get("roll_number")

            # Booking info
            booking.ground = request.POST.get("ground")
            booking.date = request.POST.get("date")
            booking.time_slot = request.POST.get("time_slot")
            # equipment may come from student_booking form as 'equipment_selected' or from the quick flow as 'equipment'
            booking.equipment = request.POST.get("equipment_selected") or request.POST.get('equipment') or ''
            booking.purpose = request.POST.get("purpose")
            booking.number_of_players = int(request.POST.get("number_of_players", 1))

            booking.save()

            # Save players dynamically
            num_players = booking.number_of_players
            for i in range(1, num_players + 1):
                Player.objects.create(
                    booking=booking,
                    name=request.POST.get(f'player{i}_name'),
                    branch=request.POST.get(f'player{i}_branch'),
                    year=request.POST.get(f'player{i}_year'),
                    division=request.POST.get(f'player{i}_division')
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
    # Check if student is "logged in"
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')
    
    first_name = student_email.split("@")[0].split(".")[0].capitalize()

    # No data fetched from DB — all info is manually entered
    return render(request, 'booking/student_dashboard.html', {
        'student_email': student_email,  # optional for welcome message
        'first_name': first_name,
    })


# -------------------- STUDENT HISTORY --------------------

# -------------------- RULES --------------------
def rules_regulations(request):
    return render(request, 'booking/rules_regulations.html')


# -------------------- AJAX AVAILABILITY --------------------

@csrf_exempt
def check_availability(request):
    ground = request.GET.get("ground")
    date_selected = request.GET.get("date")

    # ✅ Standardized time slots
    time_slots = [
        "07:00 AM - 09:00 AM", "04:00 PM - 06:00 PM ",
    ]

    slots = []

    # ❌ If ground or date is missing → freeze slots
    if not ground or not date_selected:
        for slot in time_slots:
            slots.append({"time": slot, "status": "freeze"})
        return JsonResponse({"slots": slots}, status=200)

    # ✅ Check bookings for each time slot. Book a slot if any Approved
    # booking overlaps with the slot. We parse a variety of time formats so
    # strings like "7:00 AM - 9:00 AM" and "07:00 - 09:00" both work.

    def parse_time_to_minutes(tstr):
        tstr = tstr.strip()
        # try several formats
        fmts = ["%I:%M %p", "%I:%M%p", "%H:%M", "%I %p"]
        for fmt in fmts:
            try:
                dt = datetime.strptime(tstr, fmt)
                return dt.hour * 60 + dt.minute
            except Exception:
                continue
        # try simple numeric like '7:00'
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

    # prepare approved booking ranges for this ground/date
    approved_bookings = Booking.objects.filter(
        ground=ground,
        date=date_selected,
        status__iexact='Approved'
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
                # overlap if start < be and bs < slot_e
                if bs < slot_e and slot_s < be:
                    booked = True
                    break

        slots.append({
            "time": slot,
            "status": "booked" if booked else "available"
        })

    return JsonResponse({"slots": slots}, status=200)
