# leaves/forms.py
from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import LeaveApplication, LeaveComment

class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'priority', 'attachment']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('leave_type', css_class='form-group col-md-6 mb-0'),
                Column('priority', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'reason',
            'attachment',
            Submit('submit', 'Submit Leave Application', css_class='btn btn-primary')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date < timezone.now().date():
                raise forms.ValidationError("Start date cannot be in the past.")
            if start_date > end_date:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data

class LeaveApprovalForm(forms.ModelForm):
    action = forms.ChoiceField(choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], widget=forms.RadioSelect)
    comments = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    class Meta:
        model = LeaveApplication
        fields = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'action',
            'comments',
            Submit('submit', 'Submit Decision', css_class='btn btn-primary')
        )

class LeaveCommentForm(forms.ModelForm):
    class Meta:
        model = LeaveComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'comment',
            Submit('submit', 'Add Comment', css_class='btn btn-sm btn-outline-primary')
        )