# announcements/forms.py
from django import forms
from .models import Announcement
from employees.models import Department

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'category', 'priority',
            'target_departments', 'target_roles', 'expires_at',
            'is_pinned', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'target_departments': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
            'target_roles': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter roles separated by commas (e.g., hr,admin,employee)'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'target_departments': 'Leave empty for company-wide announcement',
            'target_roles': 'Leave empty for all roles',
            'expires_at': 'Leave empty if announcement should not expire',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate departments - you might want to use the Department model instead
        try:
            self.fields['target_departments'].queryset = Department.objects.all()
        except:
            # If Department model doesn't exist, hide this field
            self.fields['target_departments'].widget = forms.HiddenInput()