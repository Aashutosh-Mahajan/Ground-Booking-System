from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta, datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .forms import BookingForm, PlayerForm, StudentSignupForm, OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm
from .models import Player, Booking, AllotedGroundBooking
from .models import StudentUser, AdminUser, OTPVerification
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone


# -------------------- HELPER FUNCTIONS --------------------
def mask_email(email):
    """Mask email address for privacy (e.g., ma***@gmail.com)"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:2] + '***'
    
    return f"{masked_local}@{domain}"


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
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            context = {'error': 'Please enter both email and password.'}
            return render(request, "booking/student_login.html", context)
        else:
            try:
                student = StudentUser.objects.get(email=email)
                if student.password == password:
                    request.session['student_email'] = student.email
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                    context = {'error': 'Invalid password'}
                    return render(request, "booking/student_login.html", context)
            except StudentUser.DoesNotExist:
                context = {'error': 'No student found with this email address'}
                return render(request, "booking/student_login.html", context)

    return render(request, "booking/student_login.html")


# -------------------- STUDENT SIGNUP --------------------
def student_signup(request):
    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            # Generate OTP
            otp = OTPVerification.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            # Delete any existing OTP for this email
            OTPVerification.objects.filter(email=form.cleaned_data['email']).delete()
            
            # Create OTP record with signup data
            otp_record = OTPVerification.objects.create(
                email=form.cleaned_data['email'],
                otp=otp,
                expires_at=expires_at,
                full_name=form.cleaned_data['full_name'],
                roll_number=form.cleaned_data['roll_number'],
                branch=form.cleaned_data['branch'],
                year=form.cleaned_data['year'],
                division=form.cleaned_data['division'],
                password=form.cleaned_data['password']
            )
            
            # Send OTP email
            try:
                subject = 'Email Verification - SportsDeck Ground Booking'
                
                # Render HTML email template
                html_content = render_to_string('booking/emails/signup_otp.html', {
                    'full_name': form.cleaned_data['full_name'],
                    'otp': otp,
                })
                
                # Plain text fallback
                text_content = f'''
Hello {form.cleaned_data['full_name']},

Thank you for signing up for SportsDeck Ground Booking System!

Your One-Time Password (OTP) for email verification is: {otp}

This OTP will expire in 10 minutes.

If you did not request this registration, please ignore this email.

Best regards,
SportsDeck Admin Team
                '''
                
                # Create email with both HTML and plain text
                email = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                
                # Store email in session for verification page
                request.session['signup_email'] = form.cleaned_data['email']
                messages.success(request, '📧 OTP sent to your email! Please check your inbox.')
                return redirect('verify_otp')
                
            except Exception as e:
                messages.error(request, f'Error sending OTP email: {str(e)}')
                otp_record.delete()
    else:
        form = StudentSignupForm()
    
    return render(request, 'booking/student_signup.html', {'form': form})


# -------------------- VERIFY OTP --------------------
def verify_otp(request):
    email = request.session.get('signup_email')
    if not email:
        messages.error(request, 'Invalid session. Please signup again.')
        return redirect('student_signup')
    
    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            try:
                otp_record = OTPVerification.objects.filter(
                    email=email,
                    is_verified=False
                ).latest('created_at')
                
                if otp_record.is_expired():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                elif otp_record.otp == entered_otp:
                    # OTP is valid, create the student account
                    StudentUser.objects.create(
                        full_name=otp_record.full_name,
                        email=otp_record.email,
                        roll_number=otp_record.roll_number,
                        branch=otp_record.branch,
                        year=otp_record.year,
                        division=otp_record.division,
                        password=otp_record.password
                    )
                    
                    # Mark OTP as verified
                    otp_record.is_verified = True
                    otp_record.save()
                    
                    # Clear session
                    del request.session['signup_email']
                    
                    messages.success(request, '🎉 Account created successfully! Please login to continue.')
                    return redirect('student_login')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    
            except OTPVerification.DoesNotExist:
                messages.error(request, 'No OTP found. Please signup again.')
                return redirect('student_signup')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'booking/verify_otp.html', {
        'form': form,
        'email': mask_email(email)
    })


# -------------------- RESEND OTP --------------------
def resend_otp(request):
    email = request.session.get('signup_email')
    if not email:
        messages.error(request, 'Invalid session. Please signup again.')
        return redirect('student_signup')
    
    try:
        # Get the latest OTP record for this email
        otp_record = OTPVerification.objects.filter(
            email=email,
            is_verified=False
        ).latest('created_at')
        
        # Generate new OTP
        new_otp = OTPVerification.generate_otp()
        otp_record.otp = new_otp
        otp_record.expires_at = timezone.now() + timedelta(minutes=10)
        otp_record.created_at = timezone.now()
        otp_record.save()
        
        # Send new OTP email
        try:
            subject = 'New OTP - SportsDeck Ground Booking'
            
            # Render HTML email template
            html_content = render_to_string('booking/emails/signup_otp.html', {
                'full_name': otp_record.full_name,
                'otp': new_otp,
            })
            
            # Plain text fallback
            text_content = f'''
Hello {otp_record.full_name},

Your new One-Time Password (OTP) for email verification is: {new_otp}

This OTP will expire in 10 minutes.

Best regards,
SportsDeck Admin Team
            '''
            
            # Create email with both HTML and plain text
            email_msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
            
            messages.success(request, 'New OTP sent to your email.')
            
        except Exception as e:
            messages.error(request, f'Error sending OTP email: {str(e)}')
            
    except OTPVerification.DoesNotExist:
        messages.error(request, 'No pending signup found. Please signup again.')
        return redirect('student_signup')
    
    return redirect('verify_otp')

def student_logout(request):
    request.session.flush()
    return redirect('student_login')


# -------------------- FORGOT PASSWORD --------------------
def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            student = StudentUser.objects.get(email=email)
            
            # Generate OTP
            otp = OTPVerification.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            # Delete any existing password reset OTP for this email
            OTPVerification.objects.filter(email=email, is_verified=False).delete()
            
            # Create OTP record for password reset
            otp_record = OTPVerification.objects.create(
                email=email,
                otp=otp,
                expires_at=expires_at,
                full_name=student.full_name or '',
                roll_number=student.roll_number or '',
                branch=student.branch or '',
                year=student.year or '',
                division=student.division or '',
                password=''  # Will be set during reset
            )
            
            # Send OTP email
            try:
                subject = 'Password Reset OTP - SportsDeck Ground Booking'
                
                # Render HTML email template
                html_content = render_to_string('booking/emails/reset_password_otp.html', {
                    'full_name': student.full_name or 'Student',
                    'otp': otp,
                })
                
                # Plain text fallback
                text_content = f'''
Hello {student.full_name},

You have requested to reset your password for SportsDeck Ground Booking System.

Your One-Time Password (OTP) for password reset is: {otp}

This OTP will expire in 10 minutes.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
SportsDeck Admin Team
                '''
                
                # Create email with both HTML and plain text
                email_msg = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                )
                email_msg.attach_alternative(html_content, "text/html")
                email_msg.send(fail_silently=False)
                
                # Store email in session for reset page
                request.session['reset_email'] = email
                messages.success(request, '📧 Password reset OTP sent! Please check your email.')
                return redirect('reset_password')
                
            except Exception as e:
                messages.error(request, f'Error sending OTP email: {str(e)}')
                otp_record.delete()
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'booking/forgot_password.html', {'form': form})


# -------------------- RESET PASSWORD --------------------
def reset_password(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Invalid session. Please start password reset again.')
        return redirect('forgot_password')
    
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            new_password = form.cleaned_data['new_password']
            
            try:
                otp_record = OTPVerification.objects.filter(
                    email=email,
                    is_verified=False
                ).latest('created_at')
                
                if otp_record.is_expired():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                elif otp_record.otp == entered_otp:
                    # OTP is valid, update the password
                    student = StudentUser.objects.get(email=email)
                    student.password = new_password
                    student.save()
                    
                    # Mark OTP as verified
                    otp_record.is_verified = True
                    otp_record.save()
                    
                    # Clear session
                    del request.session['reset_email']
                    
                    messages.success(request, '🔒 Password reset successfully! You can now login with your new password.')
                    return redirect('student_login')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    
            except OTPVerification.DoesNotExist:
                messages.error(request, 'No OTP found. Please start password reset again.')
                return redirect('forgot_password')
            except StudentUser.DoesNotExist:
                messages.error(request, 'Student account not found.')
                return redirect('forgot_password')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'booking/reset_password.html', {
        'form': form,
        'email': mask_email(email)
    })


# -------------------- RESEND RESET PASSWORD OTP --------------------
def resend_reset_otp(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Invalid session. Please start password reset again.')
        return redirect('forgot_password')
    
    try:
        student = StudentUser.objects.get(email=email)
        
        # Get the latest OTP record or create new one
        try:
            otp_record = OTPVerification.objects.filter(
                email=email,
                is_verified=False
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            # Create new OTP record
            otp = OTPVerification.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            otp_record = OTPVerification.objects.create(
                email=email,
                otp=otp,
                expires_at=expires_at,
                full_name=student.full_name or '',
                roll_number=student.roll_number or '',
                branch=student.branch or '',
                year=student.year or '',
                division=student.division or '',
                password=''
            )
        
        # Generate new OTP
        new_otp = OTPVerification.generate_otp()
        otp_record.otp = new_otp
        otp_record.expires_at = timezone.now() + timedelta(minutes=10)
        otp_record.created_at = timezone.now()
        otp_record.save()
        
        # Send new OTP email
        try:
            subject = 'New Password Reset OTP - SportsDeck Ground Booking'
            
            # Render HTML email template
            html_content = render_to_string('booking/emails/reset_password_otp.html', {
                'full_name': student.full_name or 'Student',
                'otp': new_otp,
            })
            
            # Plain text fallback
            text_content = f'''
Hello {student.full_name},

Your new One-Time Password (OTP) for password reset is: {new_otp}

This OTP will expire in 10 minutes.

Best regards,
SportsDeck Admin Team
            '''
            
            # Create email with both HTML and plain text
            email_msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
            
            messages.success(request, 'New OTP sent to your email.')
            
        except Exception as e:
            messages.error(request, f'Error sending OTP email: {str(e)}')
            
    except StudentUser.DoesNotExist:
        messages.error(request, 'Student account not found.')
        return redirect('forgot_password')
    
    return redirect('reset_password')

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
        messages.success(request, f'✅ Booking approved! Confirmation email sent successfully.')
    except Exception as e:
        # Email failed - log error and show warning but booking is still approved
        print(f"ERROR: Failed to send approval email to {to_approve.student_email}: {e}")
        messages.warning(request, f'⚠️ Booking approved, but email notification failed. Please inform the student manually.')
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
        messages.success(request, f'❌ Booking rejected. Notification email sent successfully.')
    except Exception as e:
        # Email failed - log error and show warning but booking is still rejected
        print(f"ERROR: Failed to send rejection email to {booking.student_email}: {e}")
        messages.warning(request, f'⚠️ Booking rejected, but email notification failed. Please inform the student manually.')
        pass
    
    return redirect('custom_admin_dashboard')
def student_booking(request):
    number_options = range(1, 12)

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            # Get booking details
            # Prefer posted email, else fall back to logged-in session email
            student_email = request.POST.get("student_email") or request.session.get('student_email')
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
            booking.student_email = student_email
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
        # Pre-fill email (and optionally name) for logged-in students
        initial = {}
        sess_email = request.session.get('student_email')
        if sess_email:
            initial['student_email'] = sess_email
            try:
                su = StudentUser.objects.get(email=sess_email)
                if su.full_name:
                    initial['student_name'] = su.full_name
            except StudentUser.DoesNotExist:
                pass

        booking_form = BookingForm(initial=initial)

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
