from django.urls import path
from .import views
from .views import custom_admin_login
urlpatterns = [
    path('', views.home, name='home'),
    path('student/login/', views.student_login, name='student_login'),         # ✅ changed from student-login/
    path('custom-admin/login/', custom_admin_login, name='admin_login'),  # override login               # ✅ changed from admin-login/
    path('student/booking/', views.student_booking, name='student-booking'),    # ✅ changed from student-booking/
    path('custom-admin/dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),   # ✅ changed from admin-dashboard/
    path('booking/success/', views.booking_success, name='booking_success'),
    path('approve-booking', views.approve_booking, name='approve_booking'),
    path('reject-booking', views.reject_booking, name='reject_booking'),
    path('load-formset/', views.load_formset, name='load-formset'),

]