# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User, LeaveBalance

@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'date_joined')
    list_filter = ('role', 'department', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Additional Info', {
            'fields': ('role', 'employee_id', 'phone', 'department', 'manager', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Additional Info', {
            'fields': ('role', 'employee_id', 'phone', 'department', 'manager')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'annual_leave', 'sick_leave', 'casual_leave', 'maternity_leave', 'paternity_leave')
    list_filter = ('user__department', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')