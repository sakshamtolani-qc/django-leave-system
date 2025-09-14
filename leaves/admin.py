from django.contrib import admin
from django.utils.html import format_html
from .models import LeaveType, LeaveApplication, LeaveComment

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_request', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('max_days_per_request', 'is_active')

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('get_employee_name', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status_badge', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'leave_type', 'created_at', 'employee__department')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name', 'reason')
    date_hierarchy = 'created_at'
    readonly_fields = ('days_requested', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'leave_type', 'priority')
        }),
        ('Leave Details', {
            'fields': ('start_date', 'end_date', 'days_requested', 'reason', 'attachment')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('HR Approval', {
            'fields': ('hr_approved', 'hr_approved_by', 'hr_approved_at', 'hr_comments'),
            'classes': ('collapse',)
        }),
        ('Admin Approval', {
            'fields': ('admin_approved', 'admin_approved_by', 'admin_approved_at', 'admin_comments'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    get_employee_name.short_description = 'Employee'
    get_employee_name.admin_order_field = 'employee__first_name'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'hr_approved': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'leave_type')

@admin.register(LeaveComment)
class LeaveCommentAdmin(admin.ModelAdmin):
    list_display = ('get_employee_name', 'get_commenter_name', 'comment_preview', 'created_at')
    list_filter = ('created_at', 'leave_application__status')
    search_fields = ('comment', 'user__username', 'leave_application__employee__username')
    date_hierarchy = 'created_at'
    
    def get_employee_name(self, obj):
        return obj.leave_application.employee.get_full_name() or obj.leave_application.employee.username
    get_employee_name.short_description = 'Employee'
    
    def get_commenter_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_commenter_name.short_description = 'Commenter'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'leave_application__employee')