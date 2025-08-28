from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookingForm, PlayerForm, PlayerFormSet
from .models import Player, Booking
from django.forms import formset_factory
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login
from datetime import date, timedelta


def home(request):
    return render(request, 'booking/home.html')

def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Dummy credentials for now (you can later integrate Django authentication)
        if email == 'student@college.edu' and password == 'student123':
            # Store session data for student
            request.session['student_email'] = email
            request.session['student_name'] = 'John Doe'  # Replace with dynamic name if available

            # Redirect to dashboard instead of booking page
            return redirect('student_dashboard')
        else:
            return render(request, 'booking/student_login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'booking/student_login.html')


# Hardcoded credentials
HARDCODED_ADMIN = {
    'username': 'admin',
    'password': 'admin123'
}


def custom_admin_login(request):
    # Clear any existing session
    if 'is_admin_logged_in' in request.session:
        del request.session['is_admin_logged_in']

    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')

        if username == HARDCODED_ADMIN['username'] and password == HARDCODED_ADMIN['password']:
            # Simulate "logged-in" session
            request.session['is_admin_logged_in'] = True
            return redirect('custom_admin_dashboard')
        else:
            return render(request, 'booking/admin_login.html', {'error': 'Invalid credentials'})

    return render(request, 'booking/admin_login.html')


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')



def create_sample_data(request):
    """Create sample booking data for testing purposes"""
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')

    # Create sample bookings if none exist
    if Booking.objects.count() == 0:
        Booking.objects.create(
            student_name="John Smith",
            roll_number="CS2021001",
            ground="Ground A",
            date=date.today() + timedelta(days=1),
            time_slot="9.00 - 11.00",
            purpose="Football practice session for college team",
            number_of_players=8,
            status="Pending"
        )
        Booking.objects.create(
            student_name="Sarah Johnson",
            roll_number="EE2021045",
            ground="Ground B",
            date=date.today() + timedelta(days=2),
            time_slot="15.00 - 17.00",
            purpose="Basketball tournament preparation",
            number_of_players=10,
            status="Approved"
        )
        Booking.objects.create(
            student_name="Mike Wilson",
            roll_number="ME2021078",
            ground="Ground A",
            date=date.today() + timedelta(days=3),
            time_slot="13.00 - 15.00",
            purpose="Cricket match preparation and practice",
            number_of_players=11,
            status="Pending"
        )

        # Sample players (not linked due to no relation in model)
        Player.objects.create(name="John Smith", branch="CSE", year="TE", division="A")
        Player.objects.create(name="Sarah Johnson", branch="EE", year="SE", division="B")
        Player.objects.create(name="Mike Wilson", branch="ME", year="BE", division="C")

    return redirect('custom_admin_dashboard')


def custom_admin_dashboard(request):
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')

    all_bookings = Booking.objects.all().order_by('-created_at')
    pending_bookings = Booking.objects.filter(status='Pending').order_by('-created_at')
    approved_bookings = Booking.objects.filter(status='Approved').order_by('-created_at')

    context = {
        'all_bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
    }

    return render(request, 'booking/admin_dashboard.html', context)

def student_booking(request):
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)

        if booking_form.is_valid():
            booking = booking_form.save()

            # Handle dynamic player entries
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


def load_formset(request):
    num = int(request.GET.get('num', 0))
    PlayerFormSetLocal = formset_factory(PlayerForm, extra=num)
    formset = PlayerFormSetLocal()
    html = render_to_string('booking/player_formset.html', {'formset': formset})
    return HttpResponse(html)


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


def booking_success(request):
    return render(request, 'booking/booking_success.html')


def student_dashboard(request):
    # Check if session exists
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student_login')  # Redirect if not logged in

    student_name = request.session.get('student_name', 'Student')

    # Use the session email instead of request.user.email
    bookings = Booking.objects.filter(student_email=student_email).order_by('-date')

    return render(request, 'booking/student_dashboard.html', {
        'student_name': student_name,
        'student_email': student_email,
        'bookings': bookings,
    })

def student_logout(request):
    request.session.flush()  # This clears all session data
    return redirect('home')

def rules_regulations(request):
    return render(request, 'booking/rules_regulations.html')

def student_history(request):
    student_email = request.session.get('student_email')
    if not student_email:
        return redirect('student-login')

    # Filter bookings by the logged-in student
    history = Booking.objects.filter(student_email=student_email).order_by('-date')
    return render(request, 'booking/student_history.html', {'history': history})


