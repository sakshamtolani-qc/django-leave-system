# announcements/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Announcement, AnnouncementRead
from .forms import AnnouncementForm
from django.db.models import Q

@login_required
def edit_announcement(request, pk):
    """Edit announcement - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to edit announcements.")
        return redirect('announcements:list')
    
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated successfully!')
            return redirect('announcements:detail', pk=announcement.pk)
    else:
        form = AnnouncementForm(instance=announcement)
    
    context = {
        'form': form,
        'announcement': announcement,
    }
    
    return render(request, 'announcements/edit.html', context)

@login_required
def delete_announcement(request, pk):
    """Delete announcement - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to delete announcements.")
        return redirect('announcements:list')
    
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
        return redirect('announcements:list')
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'announcements/delete.html', context)

@login_required
def announcement_list(request):
    """List all active announcements"""
    # Get announcements visible to current user
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    # Filter by department if specified
    if request.user.department:
        announcements = announcements.filter(
            Q(target_departments__isnull=True) |
            Q(target_departments__name=request.user.department)
        )
    
    # Filter by role if specified
    announcements = announcements.filter(
        Q(target_roles='') | Q(target_roles__icontains=request.user.role)
    )
    
    # Get read status for current user
    read_announcement_ids = AnnouncementRead.objects.filter(
        user=request.user
    ).values_list('announcement_id', flat=True)
    
    # Mark announcements as read/unread
    for announcement in announcements:
        announcement.is_read = announcement.id in read_announcement_ids
    
    context = {
        'announcements': announcements,
        'unread_count': announcements.exclude(id__in=read_announcement_ids).count(),
    }
    
    return render(request, 'announcements/list.html', context)

@login_required
def announcement_detail(request, pk):
    """View announcement details and mark as read"""
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    
    # Mark as read
    AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=request.user
    )
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'announcements/detail.html', context)

@login_required
def create_announcement(request):
    """Create new announcement - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "You don't have permission to create announcements.")
        return redirect('announcements:list')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Announcement created successfully!')
            return redirect('announcements:detail', pk=announcement.pk)
    else:
        form = AnnouncementForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'announcements/create.html', context)