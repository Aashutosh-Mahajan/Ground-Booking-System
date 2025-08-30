from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta, datetime

from .forms import BookingForm, PlayerForm
from .models import Player, Booking,AllotedGroundBooking
from .models import StudentUser, AdminUser
from django.contrib import messages

# -------------------- HOME --------------------
def home(request):
    return render(request, 'booking/home.html')


# -------------------- STUDENT LOGIN --------------------
def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            student = StudentUser.objects.get(email=email)
            if student.password == password:   # 👉 plain text compare (you can later use hashing)
                # ✅ store required details in session
                request.session['student_email'] = student.email
                request.session['student_name'] = getattr(student, 'name', 'Student')
                request.session['student_id'] = student.id

                return redirect('student_dashboard')
            else:
                messages.error(request, "Invalid password")
        except StudentUser.DoesNotExist:
            messages.error(request, "Student not found")
    
    return render(request, 'booking/student_login.html')
def student_logout(request):
    request.session.flush()
    return redirect('home')


# -------------------- ADMIN LOGIN --------------------


def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            admin = AdminUser.objects.get(username=username)

            # For now assume plain text password (same style as student)
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

    # Fetch from DB
    all_bookings = Booking.objects.all().order_by('-created_at')
    pending_bookings = Booking.objects.filter(status='Pending').order_by('-created_at')
    approved_bookings = Booking.objects.filter(status='Approved').order_by('-created_at')
    allotments = AllotedGroundBooking.objects.all().order_by('-date')

    context = {
        'all_bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'allotments': allotments,
    }
    return render(request, 'booking/admin_dashboard.html', context)

def get_booking_players(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    players = Player.objects.filter(booking=booking)
    return render(request, 'booking/admin_dashboard.html', {'booking': booking, 'players': players})
# --------------------------
# Approve Booking → Move to AllotedGroundBooking
# --------------------------
def approve_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_number=roll_no)
    booking.status = 'Approved'
    booking.save()

    # Create entry in AllotedGroundBooking if not already there
    AllotedGroundBooking.objects.get_or_create(
        ground=booking.ground,
        date=booking.date,
        time_slot=booking.time_slot,
        allotted_to=booking.student_name,
        purpose=booking.purpose,
        players=booking.number_of_players,
    )

    return redirect('custom_admin_dashboard')


# --------------------------
# Reject Booking
# --------------------------
def reject_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_number=roll_no)
    booking.status = 'Rejected'
    booking.save()
    return redirect('custom_admin_dashboard')


# -------------------- STUDENT BOOKING --------------------
def student_booking(request):
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)

        if booking_form.is_valid():
            ground = booking_form.cleaned_data['ground']
            date_selected = booking_form.cleaned_data['date']
            time_slot = booking_form.cleaned_data['time_slot']

            # Check for double booking
            clash = Booking.objects.filter(
                ground=ground,
                date=date_selected,
                time_slot=time_slot,
                status__in=["Pending", "Approved"]
            ).exists()

            if clash:
                return render(request, 'booking/student_booking.html', {
                    'booking_form': booking_form,
                    'error': f"❌ Slot already booked for {ground} on {date_selected} at {time_slot}"
                })

            booking = booking_form.save(commit=False)
            booking.student_email = request.session.get('student_email')
            booking.save()

            # Save players
            num_players = int(request.POST.get('number_of_players', 1))
            for i in range(1, num_players + 1):
                player_name = request.POST.get(f'player{i}_name')
                player_branch = request.POST.get(f'player{i}_branch')
                player_year = request.POST.get(f'player{i}_year')
                player_division = request.POST.get(f'player{i}_division')
                if player_name and player_branch and player_year and player_division:
                    Player.objects.create(
                        name=player_name,
                        branch=player_branch,
                        year=player_year,
                        division=player_division
                    )

            return redirect('booking_success')
    else:
        booking_form = BookingForm()

    return render(request, 'booking/student_booking.html', {
        'booking_form': booking_form,
    })


def booking_success(request):
    return render(request, 'booking/booking_success.html')


# -------------------- STUDENT DASHBOARD --------------------
def student_dashboard(request):
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')

    student_name = request.session.get('student_name', 'Student')

    # Fetch student's past bookings
    bookings = Booking.objects.filter(student_email=student_email).order_by('-date')

    return render(request, 'booking/student_dashboard.html', {
        'student_name': student_name,
        'student_email': student_email,
        'bookings': bookings,
    })


# -------------------- STUDENT HISTORY --------------------
def student_history(request):
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')

    history = Booking.objects.filter(student_email=student_email).order_by('-date')
    return render(request, 'booking/student_history.html', {'history': history})


# -------------------- RULES --------------------
def rules_regulations(request):
    return render(request, 'booking/rules_regulations.html')


# -------------------- AJAX AVAILABILITY --------------------
def check_availability(request):
    ground = request.GET.get('ground')
    date_selected = request.GET.get('date')

    time_slots = ["9.00 - 11.00", "11.00 - 13.00", "13.00 - 15.00", "15.00 - 17.00", "17.00 - 19.00"]
    availability = []

    if ground and date_selected:
        bookings = Booking.objects.filter(
            ground=ground, date=date_selected, status__in=["Pending", "Approved"]
        ).values_list('time_slot', flat=True)

        for slot in time_slots:
            if slot in bookings:
                availability.append({"time": slot, "status": "booked"})
            else:
                availability.append({"time": slot, "status": "available"})
    else:
        for slot in time_slots:
            availability.append({"time": slot, "status": "freeze"})

    return JsonResponse({'availability': availability})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def get_slots(request):
    date_selected = request.GET.get("date")
    ground = request.GET.get("ground")

    time_slots = ["6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM"]
    slots = []

    for slot in time_slots:
        booked = Booking.objects.filter(
            ground=ground,
            date=date_selected,
            time_slot=slot,
            status__in=["Pending", "Approved"]
        ).exists()
        slots.append({
            "time": slot,
            "status": "booked" if booked else "available"
        })

    return JsonResponse({"slots": slots})
