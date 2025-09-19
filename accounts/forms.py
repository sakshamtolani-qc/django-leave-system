from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.db import IntegrityError
import secrets
import string

User = get_user_model()

class AddUserForm(UserCreationForm):
    """Form for HR/Admin to create new employee accounts"""
    email = forms.EmailField(required=True, help_text="Employee's work email address")
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(
        max_length=15, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+1-555-0123'})
    )
    department = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., IT, HR, Finance'})
    )
    employee_id = forms.CharField(
        max_length=20, 
        required=False,
        help_text="Unique employee identifier (leave blank for auto-generation)"
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial='employee',
        help_text="Select the appropriate role for this employee"
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['manager', 'hr', 'admin']),
        required=False,
        empty_label="Select reporting manager (optional)"
    )
    profile_picture = forms.ImageField(
        required=False,
        help_text="Optional profile picture for the employee"
    )
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Uncheck to create inactive account (user cannot login)"
    )
    
    # New fields for password management
    generate_password = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Generate a secure password automatically and send via email"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 
                 'department', 'role', 'manager', 'profile_picture',
                 'is_active', 'generate_password', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name != 'generate_password':
                field.widget.attrs['class'] = 'form-control'
            
        # Special handling for certain fields
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'
        self.fields['generate_password'].widget.attrs['class'] = 'form-check-input'
        self.fields['role'].widget.attrs['class'] = 'form-select'
        self.fields['manager'].widget.attrs['class'] = 'form-select'
        
        # Make password fields not required initially
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        
        # Customize help text
        self.fields['username'].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        self.fields['password1'].help_text = "Leave blank if generating password automatically"
        self.fields['password2'].help_text = "Leave blank if generating password automatically"
    
    def generate_secure_password(self):
        """Generate a secure random password"""
        length = 12
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        generate_password = cleaned_data.get('generate_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if generate_password:
            # If generating password, clear any manually entered passwords
            cleaned_data['password1'] = None
            cleaned_data['password2'] = None
        else:
            # If not generating, passwords are required
            if not password1:
                self.add_error('password1', 'Password is required when not auto-generating.')
            if not password2:
                self.add_error('password2', 'Password confirmation is required when not auto-generating.')
            if password1 and password2 and password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("A user with this employee ID already exists.")
        return employee_id
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.department = self.cleaned_data['department']
        user.employee_id = self.cleaned_data['employee_id']
        user.role = self.cleaned_data['role']
        user.manager = self.cleaned_data['manager']
        user.is_active = self.cleaned_data['is_active']
        
        # Handle password generation
        generated_password = None
        if self.cleaned_data['generate_password']:
            generated_password = self.generate_secure_password()
            user.set_password(generated_password)
        
        if commit:
            # Handle potential IntegrityError for employee_id
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    user.save()
                    # Create leave balance for new user
                    from .models import LeaveBalance
                    LeaveBalance.objects.create(user=user)
                    
                    # Store generated password for email sending
                    if generated_password:
                        user._generated_password = generated_password
                    
                    break
                except IntegrityError as e:
                    if 'employee_id' in str(e) and attempt < max_attempts - 1:
                        # Clear the employee_id to force regeneration
                        user.employee_id = None
                        continue
                    else:
                        raise forms.ValidationError("Unable to create unique employee ID. Please try again.")
            
        return user

# Add password change form
class CustomPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password",
        help_text="Your password must contain at least 8 characters."
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password",
        help_text="Enter the same password as above, for verification."
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("The new passwords do not match.")
            
            # Add password validation
            if len(new_password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user

# Keep your existing forms
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    department = forms.CharField(max_length=100, required=False)
    employee_id = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 
                 'department', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('employee_id', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'department',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Register', css_class='btn btn-primary')
        )

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autocomplete': 'username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
        
        # Remove help text
        for field in self.fields.values():
            field.help_text = None

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'profile_picture']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Validate file size (max 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            # Validate file type
            if not picture.content_type.startswith('image/'):
                raise forms.ValidationError("Please upload a valid image file.")
        return picture
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'department',
            'profile_picture',
            Submit('submit', 'Update Profile', css_class='btn btn-success')
        )