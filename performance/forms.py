# performance/forms.py
from django import forms
from .models import PerformanceReview
from datetime import date, timedelta

class PerformanceReviewForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = [
            'review_type', 'review_period_start', 'review_period_end',
            'technical_skills', 'communication', 'teamwork', 'leadership', 'productivity',
            'achievements', 'areas_for_improvement', 'goals_for_next_period', 'reviewer_comments'
        ]
        widgets = {
            'review_period_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'review_period_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'areas_for_improvement': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'goals_for_next_period': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'reviewer_comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form-control class to all select fields
        for field_name in ['review_type', 'technical_skills', 'communication', 'teamwork', 'leadership', 'productivity']:
            self.fields[field_name].widget.attrs['class'] = 'form-select'
        
        # Set default date range (last quarter)
        if not self.instance.pk:
            today = date.today()
            self.fields['review_period_end'].initial = today
            self.fields['review_period_start'].initial = today - timedelta(days=90)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('review_period_start')
        end_date = cleaned_data.get('review_period_end')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("Review period end date must be after start date.")
            
            if end_date > date.today():
                raise forms.ValidationError("Review period end date cannot be in the future.")
        
        return cleaned_data

class EmployeeCommentForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ['employee_comments']
        widgets = {
            'employee_comments': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control',
                'placeholder': 'Add your comments about this review...'
            })
        }