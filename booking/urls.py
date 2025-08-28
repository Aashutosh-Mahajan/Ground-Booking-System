from django.urls import path
from . import views
from .views import custom_admin_login

urlpatterns = [
    path('', views.home, name='home'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/booking/', views.student_booking, name='student_booking'),
    path('student/history/', views.student_history, name='student_history'),
    path('student/rules/', views.rules_regulations, name='rules_regulations'),

    path('custom-admin/login/', custom_admin_login, name='admin_login'),
    path('custom-admin/logout/', views.admin_logout, name='admin_logout'),
    path('custom-admin/dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('custom-admin/sample-data/', views.create_sample_data, name='create_sample_data'),
      path("get-slots/", views.get_slots, name="get_slots"),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('approve-booking/<str:roll_no>/', views.approve_booking, name='approve_booking'),
    path('reject-booking/<str:roll_no>/', views.reject_booking, name='reject_booking'),
    path('check-availability/', views.check_availability, name='check_availability'),
]
