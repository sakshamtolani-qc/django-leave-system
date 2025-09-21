# employees/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Department, EmployeeProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head', 'employee_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    raw_id_fields = ('head',)
    
    def employee_count(self, obj):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        count = User.objects.filter(department=obj.name).count()
        return format_html(f'<span class="badge">{count}</span>')
    employee_count.short_description = 'Employee Count'

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'employment_status', 'joining_date', 'salary')
    list_filter = ('employment_status', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('employee_id',)
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'employee_id', 'employment_status', 'joining_date')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'address', 'bio', 'skills')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Employment Details', {
            'fields': ('salary',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')