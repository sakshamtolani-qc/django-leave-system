# employees/views.py - COMPLETE FIXED VERSION

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import ExtendedProfileUpdateForm,ExtendedProfileForm

User = get_user_model()

@login_required
def employee_directory(request):
    """Employee directory with search functionality"""
    query = request.GET.get('q', '')
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    
    # Base queryset - only active employees
    employees = User.objects.filter(
        is_active=True
    ).select_related('leave_balance')
    
    # Apply search query
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(department__icontains=query)
        )
    
    # Apply filters
    if department_filter:
        employees = employees.filter(department=department_filter)
    
    if role_filter:
        employees = employees.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(employees.order_by('first_name', 'last_name'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = User.objects.exclude(department='').exclude(
        department__isnull=True
    ).values_list('department', flat=True).distinct().order_by('department')
    
    roles = User.ROLE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj,
        'query': query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'departments': departments,
        'roles': roles,
        'total_employees': employees.count(),
    }
    
    return render(request, 'employees/directory.html', context)
@login_required
def extended_profile_view(request, user_id=None):
    """Extended profile information update (EmployeeProfile model fields)"""
    # Allow users to edit their own profile, or HR/Admin to edit others
    if user_id and (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user
    
    # Check permissions
    if target_user != request.user and not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "You can only edit your own extended profile.")
        return redirect('accounts:basic_profile')
    
    # Get or create employee profile
    try:
        from .models import EmployeeProfile
        profile, created = EmployeeProfile.objects.get_or_create(user=target_user)
    except Exception as e:
        messages.error(request, "Error accessing employee profile.")
        return redirect('accounts:basic_profile')
    
    if request.method == 'POST':
        form = ExtendedProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Extended profile updated successfully!')
            return redirect('employees:extended_profile')
    else:
        form = ExtendedProfileUpdateForm(instance=profile)

    context = {
        'form': form,
        'target_user': target_user,
        'is_own_profile': target_user == request.user,
    }
    
    return render(request, 'employees/extended_profile.html', context)

# Update the employee_profile view with privacy controls
@login_required
def employee_profile(request, employee_id):
    """View employee profile with privacy controls"""
    from .models import EmployeeProfile
    
    employee = get_object_or_404(User, id=employee_id, is_active=True)
    profile = EmployeeProfile.objects.filter(user=employee).first()

    # Determine who can see private info
    is_own_profile = (request.user == employee)
    is_hr_admin = request.user.role in ['hr', 'admin'] or request.user.is_superuser
    show_private_info = is_own_profile or is_hr_admin

    skills_list = []
    if profile and profile.skills:
        skills_list = [skill.strip() for skill in profile.skills.split(',') if skill.strip()]

    context = {
        'employee': employee,
        'profile': profile,
        'skills_list': skills_list,
        'show_private_info': show_private_info,
        'is_own_profile': is_own_profile,
        'user': request.user,  # for template access
    }
    return render(request, 'employees/profile.html', context)