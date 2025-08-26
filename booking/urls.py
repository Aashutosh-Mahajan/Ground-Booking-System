from django.urls import path
from .import views
from .views import custom_admin_login
urlpatterns = [
    path('', views.home, name='home'),
    path('student/login/', views.student_login, name='student_login'),         # ✅ changed from student-login/
    path('custom-admin/login/', custom_admin_login, name='admin_login'),  # override login               # ✅ changed from admin-login/
    path('custom-admin/logout/', views.admin_logout, name='admin_logout'),   # ✅ added logout
    path('custom-admin/sample-data/', views.create_sample_data, name='create_sample_data'),   # ✅ added sample data
    path('student/booking/', views.student_booking, name='student-booking'),    # ✅ changed from student-booking/
    path('custom-admin/dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),   # ✅ changed from admin-dashboard/
    path('booking/success/', views.booking_success, name='booking_success'),
    path('approve-booking/<str:roll_no>/', views.approve_booking, name='approve_booking'),
    path('reject-booking/<str:roll_no>/', views.reject_booking, name='reject_booking'),
    path('load-formset/', views.load_formset, name='load-formset'),
]