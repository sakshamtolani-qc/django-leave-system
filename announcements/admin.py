# announcements/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Announcement, AnnouncementRead

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'priority_badge', 'is_active', 'is_pinned', 'expires_at', 'read_count', 'created_at')
    list_filter = ('category', 'priority', 'is_active', 'is_pinned', 'created_at', 'expires_at')
    search_fields = ('title', 'content', 'author__first_name', 'author__last_name')
    raw_id_fields = ('author',)
    filter_horizontal = ('target_departments',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Announcement Content', {
            'fields': ('title', 'content', 'attachment')
        }),
        ('Categorization', {
            'fields': ('category', 'priority', 'author')
        }),
        ('Targeting', {
            'fields': ('target_departments', 'target_roles'),
            'description': 'Leave empty for company-wide announcements'
        }),
        ('Settings', {
            'fields': ('is_active', 'is_pinned', 'expires_at')
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'low': '#6c757d',
            'medium': '#0d6efd', 
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{obj.get_priority_display()}</span>'
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def read_count(self, obj):
        count = obj.reads.count()
        return format_html(f'<span class="badge">{count} reads</span>')
    read_count.short_description = 'Reads'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').prefetch_related('reads')

@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'read_at')
    list_filter = ('read_at', 'announcement__category')
    search_fields = ('announcement__title', 'user__first_name', 'user__last_name')
    raw_id_fields = ('announcement', 'user')
    date_hierarchy = 'read_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('announcement', 'user')
