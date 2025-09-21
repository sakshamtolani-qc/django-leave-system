# performance/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PerformanceReview

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_type', 'overall_rating_display', 'review_period_end', 'is_finalized', 'created_at')
    list_filter = ('review_type', 'is_finalized', 'created_at', 'review_period_end')
    search_fields = ('employee__first_name', 'employee__last_name', 'reviewer__first_name', 'reviewer__last_name')
    raw_id_fields = ('employee', 'reviewer')
    readonly_fields = ('overall_rating', 'created_at', 'updated_at')
    date_hierarchy = 'review_period_end'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('employee', 'reviewer', 'review_type', 'review_period_start', 'review_period_end', 'is_finalized')
        }),
        ('Performance Ratings', {
            'fields': ('technical_skills', 'communication', 'teamwork', 'leadership', 'productivity', 'overall_rating')
        }),
        ('Review Content', {
            'fields': ('achievements', 'areas_for_improvement', 'goals_for_next_period')
        }),
        ('Comments', {
            'fields': ('reviewer_comments', 'employee_comments'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def overall_rating_display(self, obj):
        if obj.overall_rating:
            stars = int(obj.overall_rating)
            star_html = '★' * stars + '☆' * (5 - stars)
            color = 'green' if obj.overall_rating >= 4 else 'orange' if obj.overall_rating >= 3 else 'red'
            return format_html(f'<span style="color: {color}; font-size: 16px;">{star_html}</span> ({obj.overall_rating:.1f})')
        return '-'
    overall_rating_display.short_description = 'Overall Rating'
    overall_rating_display.admin_order_field = 'overall_rating'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'reviewer')
