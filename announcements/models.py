# announcements/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()

class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('policy', 'Policy Update'),
        ('event', 'Event'),
        ('system', 'System Update'),
        ('hr', 'HR Update'),
        ('finance', 'Finance'),
        ('it', 'IT Update'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    target_departments = models.ManyToManyField('employees.Department', blank=True, help_text="Leave empty for company-wide")
    target_roles = models.CharField(max_length=200, blank=True, help_text="Comma-separated roles (e.g., hr,admin)")
    
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File attachments
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    class Meta:
        ordering = ['-is_pinned', '-priority', '-created_at']
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"

class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('announcement', 'user')
