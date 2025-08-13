from django.shortcuts import render, redirect,get_object_or_404
from .forms import BookingForm, PlayerForm, PlayerFormSet
from .models import Player,Booking
from django.forms import formset_factory
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login

def home(request):
    return render(request, 'booking/home.html')

def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email == 'student@college.edu' and password == 'student123':
            return redirect('student-booking')
        else:
            return render(request, 'booking/student_login.html', {'error': 'Invalid credentials'})
    return render(request, 'booking/student_login.html')


# Hardcoded credentials
HARDCODED_ADMIN = {
    'username': 'admin',
    'password': 'admin123'
}


def custom_admin_login(request):
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


def custom_admin_dashboard(request):
    if not request.session.get('is_admin_logged_in'):
        return redirect('admin_login')
    print("✅ Admin session set successfully")

    return render(request, 'booking/admin_dashboard.html')

def student_booking(request):
    PlayerFormSet = formset_factory(PlayerForm, extra=0)

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        formset = PlayerFormSet(request.POST)

        if booking_form.is_valid() and formset.is_valid():
            booking = booking_form.save()
            for form in formset:
                player = form.save(commit=False)
                player.booking = booking
                player.save()
            return redirect('success-page')
    else:
        booking_form = BookingForm()
        formset = PlayerFormSet()

    return render(request, 'booking/student_booking.html', {
        'booking_form': booking_form,
        'formset': formset,
    })
def load_formset(request):
    num = int(request.GET.get('num', 0))
    PlayerFormSet = formset_factory(PlayerForm, extra=num)
    formset = PlayerFormSet()
    html = render_to_string('booking/player_formset.html', {'formset': formset})
    return HttpResponse(html)
def booking_view(request):
    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        number = int(request.POST.get('number_of_players', 1))
        player_formset = PlayerFormSet(request.POST, prefix='players', initial=[{}]*number)

        if booking_form.is_valid() and player_formset.is_valid():
            # Process data here
            return render(request, 'success.html')
    else:
        booking_form = BookingForm()
        player_formset = PlayerFormSet(prefix='players')

    return render(request, 'booking_form.html', {
        'booking_form': booking_form,
        'player_formset': player_formset
    })
def admin_dashboard(request):
    pending = Booking.objects.filter(status='Pending')
    approved = Booking.objects.filter(status='Approved')
    return render(request, 'booking/admin_dashboard.html', {'pending': pending, 'approved': approved})

def approve_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_no=roll_no)
    booking.status = 'Approved'
    booking.save()
    return redirect('admin_dashboard')

def reject_booking(request, roll_no):
    booking = get_object_or_404(Booking, roll_no=roll_no)
    booking.status = 'Rejected'
    booking.save()
    return redirect('admin_dashboard')


def booking_success(request):
    return render(request, 'booking/booking_success.html')
