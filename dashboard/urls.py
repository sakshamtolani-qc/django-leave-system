from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('reports/', views.reports, name='reports'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user_status'),
]