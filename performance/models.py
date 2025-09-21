# performance/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()

class PerformanceReview(models.Model):
    REVIEW_TYPE_CHOICES = [
        ('annual', 'Annual Review'),
        ('quarterly', 'Quarterly Review'),
        ('probation', 'Probation Review'),
        ('mid_year', 'Mid-Year Review'),
    ]
    
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Above Average'),
        (5, 'Excellent'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_reviews')
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    
    # Performance metrics
    technical_skills = models.IntegerField(choices=RATING_CHOICES)
    communication = models.IntegerField(choices=RATING_CHOICES)
    teamwork = models.IntegerField(choices=RATING_CHOICES)
    leadership = models.IntegerField(choices=RATING_CHOICES)
    productivity = models.IntegerField(choices=RATING_CHOICES)
    
    # Comments
    achievements = models.TextField(help_text="Key achievements during review period")
    areas_for_improvement = models.TextField(help_text="Areas needing improvement")
    goals_for_next_period = models.TextField(help_text="Goals for next review period")
    reviewer_comments = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    
    # Overall rating (calculated)
    overall_rating = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_finalized = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Calculate overall rating
        ratings = [self.technical_skills, self.communication, self.teamwork, self.leadership, self.productivity]
        self.overall_rating = sum(ratings) / len(ratings)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_review_type_display()} - {self.review_period_end}"

