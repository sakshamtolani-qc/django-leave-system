# accounts/urls.py - Updated with new profile URLs
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from .forms import CustomLoginForm

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(
        template_name='accounts/login.html',
        form_class=CustomLoginForm
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Profile URLs - Updated system
    path('profile/', views.basic_profile_view, name='profile'),  # Redirect compatibility
    path('profile/basic/', views.basic_profile_view, name='basic_profile'),
    
    path('add-user/', views.add_user_view, name='add_user'),
    path('change-password/', views.change_password_view, name='change_password'),
]