# employees/models.py - CORRECTED VERSION
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='department_head')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class EmployeeProfile(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    # Remove the duplicate employee_id field since User already has one
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    joining_date = models.DateField(default=timezone.now)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bio = models.TextField(blank=True, help_text="Brief description about the employee")
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Profile"
    
    @property
    def employee_id(self):
        """Get employee_id from the related User model"""
        return self.user.employee_id