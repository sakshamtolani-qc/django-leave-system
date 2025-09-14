# dashboard/views.py - Complete views for HR → Admin workflow
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from datetime import datetime, timedelta
from leaves.models import LeaveApplication, LeaveType
import json

User = get_user_model()

@login_required
def dashboard_home(request):
    """
    Main dashboard view with role-specific content
    """
    user = request.user
    today = timezone.now().date()
    
    context = {
        'user_role': user.role if hasattr(user, 'role') else 'admin' if user.is_superuser else 'employee',
        'today': today
    }
    
    if user.role == 'employee':
        # Employee dashboard statistics
        my_leaves = LeaveApplication.objects.filter(employee=user)
        
        context.update({
            'pending_leaves': my_leaves.filter(status='pending').count(),
            'hr_approved_leaves': my_leaves.filter(status='hr_approved').count(),
            'approved_leaves': my_leaves.filter(status='approved').count(),
            'rejected_leaves': my_leaves.filter(status='rejected').count(),
            'total_applications': my_leaves.count(),
            'recent_applications': my_leaves.select_related('leave_type').order_by('-created_at')[:5],
            'leave_balance': getattr(user, 'leave_balance', None),
        })
        
        # Upcoming leaves
        upcoming_leaves = my_leaves.filter(
            status='approved', 
            start_date__gt=today
        ).order_by('start_date')[:3]
        context['upcoming_leaves'] = upcoming_leaves
        
    elif user.role == 'hr':
        # HR dashboard statistics
        hr_pending = LeaveApplication.objects.filter(status='pending')
        all_applications = LeaveApplication.objects.all()
        
        context.update({
            'leaves_to_approve': hr_pending.count(),
            'total_applications': all_applications.count(),
            'approved_by_hr': LeaveApplication.objects.filter(hr_approved=True).count(),
            'pending_admin': LeaveApplication.objects.filter(status='hr_approved').count(),
            'recent_applications': hr_pending.select_related('employee', 'leave_type').order_by('-created_at')[:10],
        })
        
        # Department-wise pending applications
        dept_pending = hr_pending.values('employee__department').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        context['department_pending'] = dept_pending
        
        # HR monthly statistics
        monthly_stats = []
        for i in range(6):  # Last 6 months
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = LeaveApplication.objects.filter(
                created_at__date__range=[month_start, month_end],
                status__in=['pending', 'hr_approved', 'approved']
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%b'),
                'count': count
            })
        
        monthly_stats.reverse()
        context['monthly_stats'] = json.dumps(monthly_stats)
        
        # Leave type distribution
        leave_type_stats = LeaveType.objects.annotate(
            total_applications=Count('leaveapplication'),
            pending_count=Count('leaveapplication', filter=Q(leaveapplication__status='pending'))
        ).order_by('-total_applications')[:5]
        context['leave_type_stats'] = leave_type_stats
        
    elif user.role == 'admin' or user.is_superuser:
        # Admin dashboard statistics
        admin_pending = LeaveApplication.objects.filter(status='hr_approved')
        all_applications = LeaveApplication.objects.all()
        
        context.update({
            'leaves_to_approve': admin_pending.count(),
            'total_applications': all_applications.count(),
            'fully_approved': LeaveApplication.objects.filter(status='approved').count(),
            'total_rejected': LeaveApplication.objects.filter(status='rejected').count(),
            'recent_applications': admin_pending.select_related('employee', 'leave_type', 'hr_approved_by').order_by('-created_at')[:10],
        })
        
        # System-wide statistics
        context.update({
            'total_employees': User.objects.filter(role='employee', is_active=True).count(),
            'total_hr_staff': User.objects.filter(role='hr', is_active=True).count(),
            'pending_hr_review': LeaveApplication.objects.filter(status='pending').count(),
        })
        
        # Approval efficiency metrics
        avg_approval_time = LeaveApplication.objects.filter(
            status='approved',
            admin_approved_at__isnull=False,
            created_at__isnull=False
        ).extra(
            select={'approval_days': 'DATEDIFF(admin_approved_at, created_at)'}
        ).aggregate(avg_days=Avg('approval_days'))
        context['avg_approval_days'] = avg_approval_time['avg_days'] or 0
        
        # Monthly approval trends
        monthly_stats = []
        for i in range(12):  # Last 12 months
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            approved_count = LeaveApplication.objects.filter(
                admin_approved_at__date__range=[month_start, month_end]
            ).count()
            
            rejected_count = LeaveApplication.objects.filter(
                status='rejected',
                updated_at__date__range=[month_start, month_end]
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%b %Y'),
                'approved': approved_count,
                'rejected': rejected_count
            })
        
        monthly_stats.reverse()
        context['monthly_stats'] = json.dumps(monthly_stats)
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def reports(request):
    """
    Generate comprehensive reports - HR and Admin only
    """
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        raise PermissionDenied("Only HR and Admin users can view reports.")
    
    today = timezone.now().date()
    
    # Date filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department = request.GET.get('department')
    status = request.GET.get('status')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=30)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    # Base queryset
    applications = LeaveApplication.objects.select_related(
        'employee', 'leave_type', 'hr_approved_by', 'admin_approved_by'
    ).filter(created_at__date__range=[start_date, end_date])
    
    # Apply filters
    if department:
        applications = applications.filter(employee__department=department)
    if status:
        applications = applications.filter(status=status)
    
    # Summary statistics
    total_applications = applications.count()
    status_breakdown = applications.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Department statistics
    department_stats = applications.values(
        'employee__department'
    ).annotate(
        total_applications=Count('id'),
        approved_applications=Count('id', filter=Q(status='approved')),
        pending_applications=Count('id', filter=Q(status__in=['pending', 'hr_approved'])),
        rejected_applications=Count('id', filter=Q(status='rejected')),
        total_days=Count('days_requested'),
        avg_processing_days=Avg('days_requested')
    ).order_by('-total_applications')
    
    # Leave type statistics
    leave_type_stats = applications.values(
        'leave_type__name'
    ).annotate(
        total_count=Count('id'),
        approved_count=Count('id', filter=Q(status='approved')),
        avg_days=Avg('days_requested')
    ).order_by('-total_count')
    
    # Employee statistics (top applicants)
    employee_stats = applications.values(
        'employee__first_name', 'employee__last_name', 'employee__employee_id', 'employee__department'
    ).annotate(
        total_applications=Count('id'),
        approved_count=Count('id', filter=Q(status='approved')),
        total_days_requested=Count('days_requested')
    ).order_by('-total_applications')[:20]
    
    # Monthly trends
    monthly_trends = []
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        month_applications = applications.filter(
            created_at__date__range=[current_month, next_month - timedelta(days=1)]
        )
        
        monthly_trends.append({
            'month': current_month.strftime('%b %Y'),
            'total': month_applications.count(),
            'approved': month_applications.filter(status='approved').count(),
            'rejected': month_applications.filter(status='rejected').count(),
            'pending': month_applications.filter(status__in=['pending', 'hr_approved']).count()
        })
        
        current_month = next_month
    
    # Get available departments for filter
    departments = User.objects.values_list('department', flat=True).exclude(
        department__isnull=True
    ).exclude(department='').distinct().order_by('department')
    
    context = {
        'applications': applications.order_by('-created_at'),
        'total_applications': total_applications,
        'status_breakdown': status_breakdown,
        'department_stats': department_stats,
        'leave_type_stats': leave_type_stats,
        'employee_stats': employee_stats,
        'monthly_trends': monthly_trends,
        'departments': departments,
        'start_date': start_date,
        'end_date': end_date,
        'selected_department': department,
        'selected_status': status,
        'status_choices': LeaveApplication.STATUS_CHOICES,
    }
    
    return render(request, 'dashboard/reports.html', context)

@login_required
def user_list(request):
    """
    User management page - HR and Admin only
    """
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        raise PermissionDenied("Only HR and Admin users can manage users.")
    
    # Get all users with related data
    users = User.objects.select_related('leave_balance').prefetch_related(
        'leave_applications'
    ).order_by('first_name', 'last_name')
    
    # Filter options
    role_filter = request.GET.get('role')
    department_filter = request.GET.get('department')
    status_filter = request.GET.get('status')
    
    if role_filter:
        users = users.filter(role=role_filter)
    if department_filter:
        users = users.filter(department=department_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Get filter options
    departments = User.objects.values_list('department', flat=True).exclude(
        department__isnull=True
    ).exclude(department='').distinct().order_by('department')
    
    context = {
        'users': users,
        'departments': departments,
        'role_choices': User.ROLE_CHOICES,
        'selected_role': role_filter,
        'selected_department': department_filter,
        'selected_status': status_filter,
        "active_users_count": users.filter(is_active=True).count(),
        "inactive_users_count": users.filter(is_active=False).count(),
        "hr_admin_count" : users.filter(role__in=['hr', 'admin']).count()
        
    }
    
    return render(request, 'dashboard/user_list.html', context)

@login_required
def toggle_user_status(request, pk):
    """
    Ajax endpoint to activate/deactivate users
    """
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, pk=pk)
    
    # Prevent users from deactivating themselves
    if user == request.user:
        return JsonResponse({'error': 'You cannot deactivate your own account'}, status=400)
    
    # Prevent non-superusers from deactivating superusers
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({'error': 'You cannot modify superuser accounts'}, status=403)
    
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'User {user.get_full_name() or user.username} has been {"activated" if user.is_active else "deactivated"}'
    })

@login_required
def user_detail(request, pk):
    """
    Detailed view of a user's profile and leave history
    """
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser or request.user.pk == pk):
        raise PermissionDenied("You can only view your own profile or you need HR/Admin privileges.")
    
    user = get_object_or_404(User, pk=pk)
    
    # Get user's leave history
    leave_applications = LeaveApplication.objects.filter(
        employee=user
    ).select_related('leave_type', 'hr_approved_by', 'admin_approved_by').order_by('-created_at')
    
    # Calculate statistics
    total_applications = leave_applications.count()
    approved_applications = leave_applications.filter(status='approved').count()
    pending_applications = leave_applications.filter(status__in=['pending', 'hr_approved']).count()
    rejected_applications = leave_applications.filter(status='rejected').count()
    
    # This year's leave usage
    current_year = timezone.now().year
    current_year_leaves = leave_applications.filter(
        start_date__year=current_year,
        status='approved'
    )
    
    total_days_taken = sum(leave.days_requested for leave in current_year_leaves)
    
    context = {
        'profile_user': user,
        'leave_applications': leave_applications[:20],  # Latest 20 applications
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'rejected_applications': rejected_applications,
        'total_days_taken': total_days_taken,
        'leave_balance': getattr(user, 'leave_balance', None),
        'can_edit': request.user == user or request.user.role in ['hr', 'admin'] or request.user.is_superuser,
    }
    
    return render(request, 'dashboard/user_detail.html', context)

@login_required
def analytics_dashboard(request):
    """
    Advanced analytics dashboard - Admin only
    """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        raise PermissionDenied("Only Admin users can view analytics.")
    
    today = timezone.now().date()
    current_year = today.year
    
    # Year-over-year comparison
    current_year_applications = LeaveApplication.objects.filter(
        created_at__year=current_year
    )
    previous_year_applications = LeaveApplication.objects.filter(
        created_at__year=current_year - 1
    )
    
    # Approval rate analysis
    total_processed = LeaveApplication.objects.filter(
        status__in=['approved', 'rejected']
    )
    approval_rate = 0
    if total_processed.count() > 0:
        approved_count = total_processed.filter(status='approved').count()
        approval_rate = (approved_count / total_processed.count()) * 100
    
    # Peak seasons analysis
    monthly_volumes = []
    for month in range(1, 13):
        volume = LeaveApplication.objects.filter(
            start_date__month=month
        ).count()
        monthly_volumes.append({
            'month': datetime(2024, month, 1).strftime('%B'),
            'volume': volume
        })
    
    # Department efficiency
    dept_efficiency = []
    departments = User.objects.values_list('department', flat=True).exclude(
        department__isnull=True
    ).exclude(department='').distinct()
    
    for dept in departments:
        dept_applications = LeaveApplication.objects.filter(
            employee__department=dept,
            status__in=['approved', 'rejected'],
            admin_approved_at__isnull=False
        )
        
        if dept_applications.exists():
            # Calculate average processing time
            avg_processing_time = 0
            for app in dept_applications:
                if app.admin_approved_at and app.created_at:
                    processing_days = (app.admin_approved_at.date() - app.created_at.date()).days
                    avg_processing_time += processing_days
            
            if dept_applications.count() > 0:
                avg_processing_time = avg_processing_time / dept_applications.count()
            
            dept_efficiency.append({
                'department': dept,
                'total_applications': LeaveApplication.objects.filter(employee__department=dept).count(),
                'approval_rate': (dept_applications.filter(status='approved').count() / dept_applications.count()) * 100 if dept_applications.count() > 0 else 0,
                'avg_processing_days': round(avg_processing_time, 1)
            })
    
    context = {
        'current_year_total': current_year_applications.count(),
        'previous_year_total': previous_year_applications.count(),
        'overall_approval_rate': round(approval_rate, 1),
        'monthly_volumes': monthly_volumes,
        'department_efficiency': dept_efficiency,
        'total_employees': User.objects.filter(is_active=True).count(),
        'total_departments': len(departments),
    }
    
    return render(request, 'dashboard/analytics.html', context)

@login_required
def export_report(request):
    """
    Export reports to CSV format
    """
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        raise PermissionDenied("Only HR and Admin users can export reports.")
    
    # Get filter parameters
    start_date = request.GET.get('start_date', (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().date().strftime('%Y-%m-%d'))
    
    # Query data
    applications = LeaveApplication.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).select_related('employee', 'leave_type')
    
    # Create CSV response
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leave_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Employee Name', 'Employee ID', 'Department', 'Leave Type',
        'Start Date', 'End Date', 'Days Requested', 'Status',
        'Application Date', 'HR Approved By', 'HR Approved Date',
        'Admin Approved By', 'Admin Approved Date', 'Reason'
    ])
    
    for app in applications:
        writer.writerow([
            app.employee.get_full_name() or app.employee.username,
            app.employee.employee_id or '',
            app.employee.department or '',
            app.leave_type.name,
            app.start_date,
            app.end_date,
            app.days_requested,
            app.get_status_display(),
            app.created_at.strftime('%Y-%m-%d'),
            app.hr_approved_by.get_full_name() if app.hr_approved_by else '',
            app.hr_approved_at.strftime('%Y-%m-%d') if app.hr_approved_at else '',
            app.admin_approved_by.get_full_name() if app.admin_approved_by else '',
            app.admin_approved_at.strftime('%Y-%m-%d') if app.admin_approved_at else '',
            app.reason[:100] + '...' if len(app.reason) > 100 else app.reason
        ])
    
    return response