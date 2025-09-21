# documents/forms.py
from django import forms
from .models import OfferLetter
from datetime import date, timedelta

class OfferLetterForm(forms.ModelForm):
    class Meta:
        model = OfferLetter
        fields = ['position', 'department', 'salary', 'joining_date']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum joining date to tomorrow
        if not self.instance.pk:
            tomorrow = date.today() + timedelta(days=1)
            self.fields['joining_date'].initial = tomorrow
            self.fields['joining_date'].widget.attrs['min'] = tomorrow.strftime('%Y-%m-%d')
    
    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary and salary <= 0:
            raise forms.ValidationError("Salary must be a positive amount.")
        return salary
    
    def clean_joining_date(self):
        joining_date = self.cleaned_data.get('joining_date')
        if joining_date and joining_date <= date.today():
            raise forms.ValidationError("Joining date must be in the future.")
        return joining_date

class IDCardGenerationForm(forms.Form):
    """Simple form for ID card generation confirmation"""
    confirm = forms.BooleanField(
        required=True,
        label="I confirm that I want to generate/regenerate the ID card for this employee",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        if employee:
            self.fields['confirm'].label = f"Generate ID card for {employee.get_full_name()}"

# Global search form
class GlobalSearchForm(forms.Form):
    SEARCH_TYPE_CHOICES = [
        ('employees', 'Employees'),
        ('announcements', 'Announcements'),
        ('tickets', 'IT Tickets'),
        ('documents', 'Documents'),
        ('all', 'All'),
    ]
    
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search across the portal...'
        })
    )
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )