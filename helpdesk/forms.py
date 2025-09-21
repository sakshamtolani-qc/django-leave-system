# helpdesk/forms.py
from django import forms
from .models import ITTicket, TicketComment

class ITTicketForm(forms.ModelForm):
    class Meta:
        model = ITTicket
        fields = ['title', 'description', 'category', 'priority', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the issue'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Detailed description of the issue including steps to reproduce, error messages, etc.'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'attachment': 'Optional: screenshots, error logs, etc.'
        }

class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Add a comment or update...'
            }),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        help_texts = {
            'is_internal': 'Check if this comment should only be visible to IT staff'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show internal checkbox to IT staff
        if not (user and (user.role in ['admin', 'it'] or user.is_superuser)):
            self.fields['is_internal'].widget = forms.HiddenInput()
            self.fields['is_internal'].initial = False

class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = ITTicket
        fields = ['status', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show IT staff in assigned_to
        from django.contrib.auth import get_user_model
        User = get_user_model()
        it_staff = User.objects.filter(
            role__in=['admin', 'it'],
            is_active=True
        ).order_by('first_name', 'last_name')
        
        self.fields['assigned_to'].queryset = it_staff
        self.fields['assigned_to'].empty_label = "Unassigned"