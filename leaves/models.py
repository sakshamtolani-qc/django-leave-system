from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    max_days_per_request = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending HR Review"),
        ("hr_approved", "HR Approved - Pending Admin"),
        ("approved", "Fully Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    employee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="leave_applications"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )

    # HR approval fields
    hr_approved = models.BooleanField(default=False)
    hr_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_approved_leaves",
    )
    hr_approved_at = models.DateTimeField(null=True, blank=True)
    hr_comments = models.TextField(blank=True)

    # Admin approval fields
    admin_approved = models.BooleanField(default=False)
    admin_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_approved_leaves",
    )
    admin_approved_at = models.DateTimeField(null=True, blank=True)
    admin_comments = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # File attachments
    attachment = models.FileField(upload_to="leave_attachments/", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    def calculate_days(self):
        return (self.end_date - self.start_date).days + 1

    def save(self, *args, **kwargs):
        if not self.days_requested:
            self.days_requested = self.calculate_days()
        super().save(*args, **kwargs)

    def can_be_cancelled(self):
        return (
            self.status in ["pending", "hr_approved"]
            and self.start_date > timezone.now().date()
        )

    def get_current_approval_stage(self):
        if self.status == "pending":
            return "hr"
        elif self.status == "hr_approved":
            return "admin"
        return None

    def can_be_approved_by(self, user):
        if user.role == "hr" and self.status == "pending":
            return True
        elif user.role == "admin" and self.status == "hr_approved":
            return True
        elif user.is_superuser and self.status == "hr_approved":
            return True
        return False

class LeaveComment(models.Model):
    leave_application = models.ForeignKey(
        LeaveApplication, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.leave_application}"