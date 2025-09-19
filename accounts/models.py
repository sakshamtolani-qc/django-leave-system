from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = CloudinaryField(
        'profile_pictures',
        null=True, 
        blank=True,
        transformation={
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'gravity': 'face',
            'quality': 'auto',
            'format': 'auto'
        }
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Only generate employee_id if it's empty and this is a new user
        if not self.employee_id and not self.pk:
            with transaction.atomic():
                # Get the last user with a QCE- employee_id
                last_user = User.objects.filter(
                    employee_id__startswith="QCE-"
                ).exclude(
                    employee_id__isnull=True
                ).exclude(
                    employee_id=""
                ).order_by("employee_id").last()
                
                if last_user and last_user.employee_id:
                    try:
                        # Extract number from QCE-0001 format
                        last_number = int(last_user.employee_id.split("-")[-1])
                    except (ValueError, IndexError):
                        last_number = 0
                else:
                    last_number = 0
                
                # Keep trying to find a unique ID
                max_attempts = 100
                for attempt in range(max_attempts):
                    new_number = last_number + 1 + attempt
                    new_employee_id = f"QCE-{new_number:04d}"
                    
                    # Check if this ID already exists
                    if not User.objects.filter(employee_id=new_employee_id).exists():
                        self.employee_id = new_employee_id
                        break
                else:
                    # If we can't find a unique ID after 100 attempts, use timestamp
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    self.employee_id = f"QCE-{timestamp}"
        
        super().save(*args, **kwargs)
    
    def get_profile_picture_url(self):
        """Get optimized profile picture URL"""
        if self.profile_picture:
            return self.profile_picture.build_url(
                width=150, 
                height=150, 
                crop='fill', 
                gravity='face',
                quality='auto',
                fetch_format='auto'
            )
        return None
    
    def get_profile_picture_large_url(self):
        """Get large profile picture URL for profile page"""
        if self.profile_picture:
            return self.profile_picture.build_url(
                width=300, 
                height=300, 
                crop='fill', 
                gravity='face',
                quality='auto',
                fetch_format='auto'
            )
        return None
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

# Rest of your models remain the same
class LeaveBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leave_balance')
    annual_leave = models.IntegerField(default=21)
    sick_leave = models.IntegerField(default=10)
    casual_leave = models.IntegerField(default=7)
    maternity_leave = models.IntegerField(default=90)
    paternity_leave = models.IntegerField(default=15)
    
    def __str__(self):
        return f"Leave Balance - {self.user.username}"