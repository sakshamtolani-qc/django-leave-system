# performance/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from .models import PerformanceReview
from .forms import PerformanceReviewForm

User = get_user_model()

@login_required
def my_reviews(request):
    """Employee's complete review history"""
    reviews = PerformanceReview.objects.filter(
        employee=request.user
    ).select_related('reviewer').order_by('-review_period_end')
    
    context = {
        'reviews': reviews,
    }
    
    return render(request, 'performance/my_reviews.html', context)

@login_required
def add_employee_comment(request, pk):
    """Allow employee to add comments to their review"""
    review = get_object_or_404(PerformanceReview, pk=pk, employee=request.user)
    
    if request.method == 'POST':
        comment = request.POST.get('employee_comments', '')
        if comment:
            review.employee_comments = comment
            review.save()
            messages.success(request, 'Your comments have been added to the review.')
        return redirect('performance:review_detail', pk=pk)
    
    context = {
        'review': review,
    }
    
    return render(request, 'performance/add_comment.html', context)

@login_required
def performance_dashboard(request):
    """Performance dashboard for employees"""
    user = request.user
    
    # Get user's performance reviews
    reviews = PerformanceReview.objects.filter(employee=user).order_by('-review_period_end')
    
    # Calculate stats
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
    latest_review = reviews.first()
    
    # For managers/HR - get team reviews
    team_reviews = []
    if user.role in ['manager', 'hr', 'admin']:
        team_reviews = PerformanceReview.objects.filter(
            reviewer=user
        ).order_by('-created_at')[:10]
    
    context = {
        'reviews': reviews[:5],  # Latest 5 reviews
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'latest_review': latest_review,
        'team_reviews': team_reviews,
    }
    
    return render(request, 'performance/dashboard.html', context)

@login_required
def create_performance_review(request, employee_id):
    """Create a performance review - HR/Manager only"""
    if not (request.user.role in ['hr', 'admin', 'manager'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to create performance reviews.")
        return redirect('performance:dashboard')
    
    employee = get_object_or_404(User, id=employee_id)
    
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.employee = employee
            review.reviewer = request.user
            review.save()
            
            messages.success(request, f'Performance review created for {employee.get_full_name()}')
            return redirect('performance:review_detail', pk=review.pk)
    else:
        form = PerformanceReviewForm()
    
    context = {
        'form': form,
        'employee': employee,
    }
    
    return render(request, 'performance/create_review.html', context)

@login_required
def review_detail(request, pk):
    """View performance review details"""
    review = get_object_or_404(PerformanceReview, pk=pk)
    
    # Check permissions
    can_view = (
        request.user == review.employee or 
        request.user == review.reviewer or
        request.user.role in ['hr', 'admin'] or
        request.user.is_superuser
    )
    
    if not can_view:
        messages.error(request, "You don't have permission to view this review.")
        return redirect('performance:dashboard')
    
    context = {
        'review': review,
        'can_edit': request.user == review.reviewer and not review.is_finalized,
    }
    
    return render(request, 'performance/review_detail.html', context)

@login_required
def edit_review(request, pk):
    """Edit performance review - Reviewer only"""
    review = get_object_or_404(PerformanceReview, pk=pk)
    
    # Check permissions
    if not (request.user == review.reviewer and not review.is_finalized):
        messages.error(request, "You can only edit your own reviews that aren't finalized.")
        return redirect('performance:review_detail', pk=pk)
    
    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Performance review updated successfully!')
            return redirect('performance:review_detail', pk=review.pk)
    else:
        form = PerformanceReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'employee': review.employee,
    }
    
    return render(request, 'performance/edit_review.html', context)

@login_required
def bulk_review_creation(request):
    """Bulk review creation for multiple employees"""
    if not (request.user.role in ['hr', 'admin', 'manager'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to create bulk reviews.")
        return redirect('performance:dashboard')
    
    employees = User.objects.filter(role='employee', is_active=True)
    
    if request.method == 'POST':
        selected_employees = request.POST.getlist('employees')
        review_type = request.POST.get('review_type')
        review_period_start = request.POST.get('review_period_start')
        review_period_end = request.POST.get('review_period_end')
        
        created_count = 0
        for emp_id in selected_employees:
            try:
                employee = User.objects.get(id=emp_id)
                # Create basic review structure - to be filled later
                PerformanceReview.objects.create(
                    employee=employee,
                    reviewer=request.user,
                    review_type=review_type,
                    review_period_start=review_period_start,
                    review_period_end=review_period_end,
                    technical_skills=3,  # Default values
                    communication=3,
                    teamwork=3,
                    leadership=3,
                    productivity=3,
                    achievements="To be completed",
                    areas_for_improvement="To be completed",
                    goals_for_next_period="To be completed",
                )
                created_count += 1
            except User.DoesNotExist:
                continue
        
        messages.success(request, f'Created {created_count} performance review templates.')
        return redirect('performance:dashboard')
    
    context = {
        'employees': employees,
    }
    
    return render(request, 'performance/bulk_create.html', context)