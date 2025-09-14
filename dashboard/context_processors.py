# dashboard/context_processors.py - New file
from leaves.models import LeaveApplication

def navigation_context(request):
    """
    Context processor to provide navigation data for all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        if request.user.role == 'hr':
            # HR pending count
            context['hr_pending_count'] = LeaveApplication.objects.filter(
                status='pending'
            ).count()
            
        elif request.user.role == 'admin' or request.user.is_superuser:
            # Admin pending count
            context['admin_pending_count'] = LeaveApplication.objects.filter(
                status='hr_approved'
            ).count()
            
        # Employee's own stats
        if request.user.role == 'employee':
            my_leaves = LeaveApplication.objects.filter(employee=request.user)
            context['my_pending_count'] = my_leaves.filter(
                status__in=['pending', 'hr_approved']
            ).count()
    
    return context

