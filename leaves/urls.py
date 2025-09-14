from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    path('', views.LeaveApplicationListView.as_view(), name='my_leaves'),
    path('apply/', views.LeaveApplicationCreateView.as_view(), name='apply_leave'),
    path('<int:pk>/', views.LeaveApplicationDetailView.as_view(), name='leave_detail'),
    path('<int:pk>/approve/', views.approve_leave, name='approve_leave'),
    path('<int:pk>/cancel/', views.cancel_leave, name='cancel_leave'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # Separate views for HR and Admin
    path('hr/pending/', views.HRPendingLeavesView.as_view(), name='hr_pending'),
    path('admin/pending/', views.AdminPendingLeavesView.as_view(), name='admin_pending'),
    
    # Backward compatibility
    path('pending/', views.PendingLeavesView.as_view(), name='pending_leaves'),
]