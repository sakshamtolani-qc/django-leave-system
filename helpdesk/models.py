# helpdesk/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()

class ITTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending User Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    CATEGORY_CHOICES = [
        ('hardware', 'Hardware Issue'),
        ('software', 'Software Issue'),
        ('network', 'Network/Connectivity'),
        ('email', 'Email Issues'),
        ('access', 'Access/Permissions'),
        ('phone', 'Phone/Communication'),
        ('printer', 'Printer Issues'),
        ('other', 'Other'),
    ]
    
    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='it_tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    
    # File attachments
    attachment = models.FileField(upload_to='it_tickets/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Generate ticket ID like IT-2024-0001
            from datetime import datetime
            year = datetime.now().year
            count = ITTicket.objects.filter(created_at__year=year).count() + 1
            self.ticket_id = f"IT-{year}-{count:04d}"
        
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_id} - {self.title}"

class TicketComment(models.Model):
    ticket = models.ForeignKey(ITTicket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal comments only visible to IT staff")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_id} by {self.user.username}"
