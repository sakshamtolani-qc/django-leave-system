# helpdesk/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ITTicket, TicketComment

@admin.register(ITTicket)
class ITTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'title', 'requester', 'status_badge', 'priority_badge', 'assigned_to', 'created_at', 'resolved_at')
    list_filter = ('status', 'priority', 'category', 'created_at', 'resolved_at')
    search_fields = ('ticket_id', 'title', 'description', 'requester__first_name', 'requester__last_name')
    raw_id_fields = ('requester', 'assigned_to')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at', 'resolved_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'title', 'description', 'attachment')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('requester', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'open': '#ffc107',
            'in_progress': '#0dcaf0',
            'pending': '#fd7e14',
            'resolved': '#198754',
            'closed': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{obj.get_status_display()}</span>'
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#6c757d',
            'medium': '#0d6efd',
            'high': '#fd7e14', 
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{obj.get_priority_display()}</span>'
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requester', 'assigned_to')

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'comment_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('ticket__ticket_id', 'ticket__title', 'user__first_name', 'user__last_name', 'comment')
    raw_id_fields = ('ticket', 'user')
    date_hierarchy = 'created_at'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'user')
