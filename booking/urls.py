from django.urls import path
from . import views
from .views import custom_admin_login

urlpatterns = [
    path('', views.home, name='home'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/signup/', views.student_signup, name='student_signup'),
    path('student/verify-otp/', views.verify_otp, name='verify_otp'),
    path('student/resend-otp/', views.resend_otp, name='resend_otp'),
    path('student/forgot-password/', views.forgot_password, name='forgot_password'),
    path('student/reset-password/', views.reset_password, name='reset_password'),
    path('student/resend-reset-otp/', views.resend_reset_otp, name='resend_reset_otp'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/history/', views.student_history, name='student_history'),
    path('student/booking/', views.student_booking, name='student_booking'),
    path('student/rules/', views.rules_regulations, name='rules_regulations'),

    path('custom-admin/login/', custom_admin_login, name='admin_login'),
    path('custom-admin/logout/', views.admin_logout, name='admin_logout'),
    path('custom-admin/dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
   
    path('booking/success/', views.booking_success, name='booking_success'),
   path('approve-booking/<int:booking_id>/', views.approve_booking, name='approve_booking'),
path('reject-booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('check-availability/', views.check_availability, name='check_availability'),
    path('get-players/<int:booking_id>/', views.get_players, name='get_players'),
       path('get-allotment-players/<int:allot_id>/', views.get_allotment_players, name='get_allotment_players'),
    path('get-equipment/<int:booking_id>/', views.get_equipment_for_booking, name='get_equipment_for_booking'),
    path('get-allotment-equipment/<int:allot_id>/', views.get_equipment_for_allotment, name='get_allotment_equipment'),
    path('fetch-student-data/', views.fetch_student_data, name='fetch_student_data'),
]
