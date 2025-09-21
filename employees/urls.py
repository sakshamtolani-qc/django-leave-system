# employees/urls.py - Updated with extended profile URLs
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('directory/', views.employee_directory, name='directory'),
    path('profile/<int:employee_id>/', views.employee_profile, name='profile'),
    
    # Extended profile URLs
    path('profile/extended/', views.extended_profile_view, name='extended_profile'),
    path('profile/extended/<int:user_id>/', views.extended_profile_view, name='extended_profile_admin'),
]