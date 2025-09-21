# helpdesk/urls.py
from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:pk>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    # For IT staff
    path('manage/', views.manage_tickets, name='manage_tickets'),
    path('assign/<int:pk>/', views.assign_ticket, name='assign_ticket'),
]