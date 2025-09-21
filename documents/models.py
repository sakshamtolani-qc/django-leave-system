# documents/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()

class IDCard(models.Model):
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='id_card')
    card_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_cards')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.card_number:
            # Generate card number like QC-ID-2024-0001
            from datetime import datetime
            year = datetime.now().year
            count = IDCard.objects.filter(issue_date__year=year).count() + 1
            self.card_number = f"QC-ID-{year}-{count:04d}"
        
        if not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = self.issue_date + timedelta(days=365*2)  # 2 years validity
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"ID Card - {self.employee.get_full_name()} - {self.card_number}"

class OfferLetter(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offer_letters')
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    joining_date = models.DateField()
    
    # Letter content
    letter_content = models.TextField(help_text="Auto-generated, can be customized")
    
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_offers')
    generated_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Offer Letter - {self.employee.get_full_name()} - {self.position}"
