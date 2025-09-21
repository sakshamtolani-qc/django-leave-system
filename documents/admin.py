# documents/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import IDCard, OfferLetter

@admin.register(IDCard)
class IDCardAdmin(admin.ModelAdmin):
    list_display = ('employee', 'card_number', 'issue_date', 'expiry_date', 'is_active', 'generated_by', 'generated_at')
    list_filter = ('is_active', 'issue_date', 'expiry_date', 'generated_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'card_number', 'employee__employee_id')
    raw_id_fields = ('employee', 'generated_by')
    readonly_fields = ('card_number', 'generated_at')
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Card Information', {
            'fields': ('employee', 'card_number', 'is_active')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date')
        }),
        ('Generation Info', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'generated_by')

@admin.register(OfferLetter)
class OfferLetterAdmin(admin.ModelAdmin):
    list_display = ('employee', 'position', 'department', 'salary_display', 'joining_date', 'is_sent', 'generated_by', 'generated_at')
    list_filter = ('is_sent', 'joining_date', 'generated_at', 'department')
    search_fields = ('employee__first_name', 'employee__last_name', 'position', 'department')
    raw_id_fields = ('employee', 'generated_by')
    readonly_fields = ('generated_at', 'sent_at')
    date_hierarchy = 'joining_date'
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'position', 'department')
        }),
        ('Offer Details', {
            'fields': ('salary', 'joining_date')
        }),
        ('Letter Content', {
            'fields': ('letter_content',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at')
        }),
        ('Generation Info', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def salary_display(self, obj):
        return format_html(f'<strong>${obj.salary:,.2f}</strong>')
    salary_display.short_description = 'Salary'
    salary_display.admin_order_field = 'salary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'generated_by')