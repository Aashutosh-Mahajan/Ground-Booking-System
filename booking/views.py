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
# -------------------- HOME --------------------
def home(request):
    return render(request, 'booking/home.html')


# -------------------- STUDENT LOGIN --------------------

def student_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # ✅ Only require email/password for access — no DB fetch
        if email and password:
            # Save email in session to track login state
            request.session['student_email'] = email

            # Redirect to dashboard
            return redirect('student_dashboard')
        else:
            messages.error(request, "Please enter both email and password.")

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

    bookings = Booking.objects.all().order_by('-created_at')
    allotments = AllotedGroundBooking.objects.all().order_by('-date')

    context = {
        'bookings': bookings,
        'allotments': allotments,
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

# Reject Booking
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'Rejected'
    booking.save()
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
            booking.student_branch = request.POST.get("student_branch")
            booking.student_year = request.POST.get("student_year")
            booking.student_division = request.POST.get("student_division")
            booking.roll_number = request.POST.get("roll_number")

            # Booking info
            booking.ground = request.POST.get("ground")
            booking.date = request.POST.get("date")
            booking.time_slot = request.POST.get("time_slot")
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

    # No data fetched from DB — all info is manually entered
    return render(request, 'booking/student_dashboard.html', {
        'student_email': student_email,  # optional for welcome message
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
        "07:00 - 08:00", "08:00 - 09:00", "09:00 - 10:00",
        "10:00 - 11:00", "11:00 - 12:00", "12:00 - 13:00",
        "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
        "16:00 - 17:00", "17:00 - 18:00"
    ]

    slots = []

    # ❌ If ground or date is missing → freeze slots
    if not ground or not date_selected:
        for slot in time_slots:
            slots.append({"time": slot, "status": "freeze"})
        return JsonResponse({"slots": slots}, status=200)

    # ✅ Check bookings for each time slot
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

    return JsonResponse({"slots": slots}, status=200)
