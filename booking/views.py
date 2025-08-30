from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from datetime import date, timedelta

from .forms import BookingForm, PlayerForm
from .models import Player, Booking, StudentUser, AdminUser
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


# -------------------- HOME --------------------
def home(request):
    return render(request, 'booking/home.html')


# -------------------- STUDENT AUTH --------------------
def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            student = StudentUser.objects.get(email=email)
            if student.password == password:  # plain text for now
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


# -------------------- ADMIN AUTH --------------------
def custom_admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            admin = AdminUser.objects.get(username=username)
            if admin.password == password:  # plain text
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

    context = {
        'all_bookings': Booking.objects.all().order_by('-created_at'),
        'pending_bookings': Booking.objects.filter(status='Pending').order_by('-created_at'),
        'approved_bookings': Booking.objects.filter(status='Approved').order_by('-created_at'),
    }
    return render(request, 'booking/admin_dashboard.html', context)


def approve_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_number=roll_no)
    booking.status = 'Approved'
    booking.save()
    return redirect('custom_admin_dashboard')


def reject_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_number=roll_no)
    booking.status = 'Rejected'
    booking.save()
    return redirect('custom_admin_dashboard')


def create_sample_data(request):
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')

    if Booking.objects.count() == 0:
        # Sample bookings
        Booking.objects.bulk_create([
            Booking(student_name="John Smith", roll_number="CS2021001", ground="Ground A",
                    date=date.today() + timedelta(days=1), time_slot="9.00 - 11.00",
                    purpose="Football practice", number_of_players=8, status="Pending"),
            Booking(student_name="Sarah Johnson", roll_number="EE2021045", ground="Ground B",
                    date=date.today() + timedelta(days=2), time_slot="15.00 - 17.00",
                    purpose="Basketball preparation", number_of_players=10, status="Approved"),
            Booking(student_name="Mike Wilson", roll_number="ME2021078", ground="Ground A",
                    date=date.today() + timedelta(days=3), time_slot="13.00 - 15.00",
                    purpose="Cricket practice", number_of_players=11, status="Pending")
        ])
        # Sample players
        Player.objects.bulk_create([
            Player(name="John Smith", branch="CSE", year="TE", division="A"),
            Player(name="Sarah Johnson", branch="EE", year="SE", division="B"),
            Player(name="Mike Wilson", branch="ME", year="BE", division="C")
        ])

    return redirect('custom_admin_dashboard')


# -------------------- STUDENT BOOKING --------------------
def student_booking(request):
    number_options = range(1, 6)  # adjust max players
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            # Save the booking
            booking_form.save()
            # Redirect to success page
            return redirect('booking_success')
    else:
        booking_form = BookingForm()

    return render(request, 'booking/booking_success.html', {
        'booking_form': booking_form,
        'number_options': number_options
    })


def booking_success(request):
    """
    Display booking success modal.
    The "Book Another Ground" button links back to 'student_booking'.
    """
    return render(request, 'booking/booking_success.html')


def booking_success(request):
    return render(request, 'booking/booking_success.html')


# -------------------- STUDENT DASHBOARD --------------------
def student_dashboard(request):
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')

    bookings = Booking.objects.filter(student_email=student_email).order_by('-date')
    return render(request, 'booking/student_dashboard.html', {
        'student_name': request.session.get('student_name', 'Student'),
        'student_email': student_email,
        'bookings': bookings,
    })


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
        booked_slots = Booking.objects.filter(
            ground=ground, date=date_selected, status__in=["Pending", "Approved"]
        ).values_list('time_slot', flat=True)
        for slot in time_slots:
            availability.append({"time": slot, "status": "booked" if slot in booked_slots else "available"})
    else:
        for slot in time_slots:
            availability.append({"time": slot, "status": "freeze"})

    return JsonResponse({'availability': availability})


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
        slots.append({"time": slot, "status": "booked" if booked else "available"})

    return JsonResponse({"slots": slots})
