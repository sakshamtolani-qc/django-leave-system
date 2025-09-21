# helpdesk/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import ITTicket, TicketComment
from .forms import ITTicketForm, TicketCommentForm
from django.utils import timezone

User = get_user_model()

def update_ticket_status(request, pk):
    """Update ticket status - IT staff only"""
    if not (request.user.role in ['admin', 'it'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to update ticket status.")
        return redirect('helpdesk:ticket_detail', pk=pk)
    
    ticket = get_object_or_404(ITTicket, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        assigned_to_id = request.POST.get('assigned_to')
        
        if status:
            ticket.status = status
            if status == 'resolved':
                ticket.resolved_at = timezone.now()
        
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id)
                ticket.assigned_to = assigned_user
            except User.DoesNotExist:
                pass
        
        ticket.save()
        messages.success(request, 'Ticket updated successfully!')
    
    return redirect('helpdesk:ticket_detail', pk=pk)

@login_required 
def manage_tickets(request):
    """IT ticket management dashboard - IT staff only"""
    if not (request.user.role in ['admin', 'it'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to access IT management.")
        return redirect('helpdesk:ticket_list')
    
    # Get all tickets for management
    tickets = ITTicket.objects.select_related('requester', 'assigned_to').order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_filter = request.GET.get('assigned', '')
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if assigned_filter:
        tickets = tickets.filter(assigned_to_id=assigned_filter)
    
    # Get IT staff for assignment
    it_staff = User.objects.filter(role__in=['admin', 'it'], is_active=True)
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_filter': assigned_filter,
        'status_choices': ITTicket.STATUS_CHOICES,
        'priority_choices': ITTicket.PRIORITY_CHOICES,
        'it_staff': it_staff,
    }
    
    return render(request, 'helpdesk/manage_tickets.html', context)

@login_required
def assign_ticket(request, pk):
    """Assign ticket to IT staff - IT staff only"""
    if not (request.user.role in ['admin', 'it'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to assign tickets.")
        return redirect('helpdesk:ticket_detail', pk=pk)
    
    ticket = get_object_or_404(ITTicket, pk=pk)
    
    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to')
        try:
            if assigned_to_id:
                assigned_user = User.objects.get(id=assigned_to_id, role__in=['admin', 'it'])
                ticket.assigned_to = assigned_user
                ticket.status = 'in_progress'
            else:
                ticket.assigned_to = None
                ticket.status = 'open'
            
            ticket.save()
            
            # Add comment about assignment
            TicketComment.objects.create(
                ticket=ticket,
                user=request.user,
                comment=f"Ticket {'assigned to ' + assigned_user.get_full_name() if assigned_user else 'unassigned'}",
                is_internal=True
            )
            
            messages.success(request, 'Ticket assignment updated successfully!')
        except User.DoesNotExist:
            messages.error(request, 'Invalid user selected for assignment.')
    
    return redirect('helpdesk:ticket_detail', pk=pk)


@login_required
def ticket_list(request):
    """List user's IT tickets"""
    tickets = ITTicket.objects.filter(requester=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'status_choices': ITTicket.STATUS_CHOICES,
    }
    
    return render(request, 'helpdesk/ticket_list.html', context)

@login_required
def create_ticket(request):
    """Create new IT ticket"""
    if request.method == 'POST':
        form = ITTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.requester = request.user
            ticket.save()
            
            messages.success(request, f'Ticket {ticket.ticket_id} created successfully!')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        form = ITTicketForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'helpdesk/create_ticket.html', context)

@login_required
def ticket_detail(request, pk):
    """View ticket details and comments"""
    ticket = get_object_or_404(ITTicket, pk=pk)
    
    # Check permissions
    can_view = (
        request.user == ticket.requester or
        request.user == ticket.assigned_to or
        request.user.role in ['admin', 'it'] or
        request.user.is_superuser
    )
    
    if not can_view:
        messages.error(request, "You don't have permission to view this ticket.")
        return redirect('helpdesk:ticket_list')
    
    # Handle comment submission
    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        comment_form = TicketCommentForm(user=request.user)
    
    # Get comments (filter internal ones for non-IT users)
    comments = ticket.comments.all()
    if not (request.user.role in ['admin', 'it'] or request.user.is_superuser):
        comments = comments.filter(is_internal=False)
    
    # Get IT staff for assignment dropdown
    it_staff = User.objects.filter(role__in=['admin', 'it'], is_active=True)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'can_manage': request.user.role in ['admin', 'it'] or request.user.is_superuser,
        'it_staff': it_staff,
    }
    
    return render(request, 'helpdesk/ticket_detail.html', context)
