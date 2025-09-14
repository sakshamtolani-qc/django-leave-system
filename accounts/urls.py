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
    path('profile/', views.profile_view, name='profile'),
    path('add-user/', views.add_user_view, name='add_user'),
]