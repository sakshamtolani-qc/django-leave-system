# employees/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, Department
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from crispy_forms.helper import FormHelper

User = get_user_model()

class ExtendedProfileUpdateForm(forms.ModelForm):
    """Form for updating extended employee profile information"""
    class Meta:
        model = EmployeeProfile
        fields = [
            'date_of_birth', 'address', 'emergency_contact_name', 
            'emergency_contact_phone', 'bio', 'skills'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter skills separated by commas (e.g., Python, Project Management, Communication)'}),
        }
        help_texts = {
            'skills': 'Enter skills separated by commas',
            'emergency_contact_phone': 'This information is kept private',
            'address': 'This information is kept private'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'date_of_birth',
            'address',
            Row(
                Column('emergency_contact_name', css_class='form-group col-md-6 mb-0'),
                Column('emergency_contact_phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'bio',
            'skills',
            Submit('submit', 'Update Extended Profile', css_class='btn btn-success')
        )

class ExtendedProfileForm(forms.ModelForm):
    """Form for updating extended employee profile information"""
    class Meta:
        model = EmployeeProfile
        fields = [
            'date_of_birth', 'address', 'emergency_contact_name', 
            'emergency_contact_phone', 'bio', 'skills'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter skills separated by commas (e.g., Python, Project Management, Data Analysis)'}),
        }
        help_texts = {
            'date_of_birth': 'This information is kept confidential',
            'emergency_contact_name': 'Person to contact in case of emergency',
            'emergency_contact_phone': 'Emergency contact phone number',
            'bio': 'Brief description about yourself (visible to colleagues)',
            'skills': 'Your professional skills and expertise',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                Column('emergency_contact_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('emergency_contact_phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'address',
            'bio',
            'skills',
            Submit('submit', 'Update Extended Profile', css_class='btn btn-success')
        )

class EmployeeSearchForm(forms.Form):
    q = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, email, or employee ID...',
            'class': 'form-control'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + User.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate department choices
        departments = User.objects.exclude(department='').exclude(
            department__isnull=True
        ).values_list('department', flat=True).distinct().order_by('department')
        
        dept_choices = [('', 'All Departments')] + [(dept, dept) for dept in departments]
        self.fields['department'].widget = forms.Select(choices=dept_choices, attrs={'class': 'form-select'})

class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = [
            'date_of_birth', 'address', 'emergency_contact_name', 
            'emergency_contact_phone', 'bio', 'skills'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter skills separated by commas'}),
        }