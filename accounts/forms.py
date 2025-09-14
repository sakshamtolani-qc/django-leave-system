# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

User = get_user_model()


class AddUserForm(UserCreationForm):
    """Form for HR/Admin to create new employee accounts"""

    email = forms.EmailField(required=True, help_text="Employee's work email address")
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+1-555-0123"}),
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., IT, HR, Finance"}),
    )
    employee_id = forms.CharField(
        max_length=20,
        required=False,
        help_text="Unique employee identifier (leave blank for auto-generation)",
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial="employee",
        help_text="Select the appropriate role for this employee",
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=["manager", "hr", "admin"]),
        required=False,
        empty_label="Select reporting manager (optional)",
    )
    profile_picture = forms.ImageField(
        required=False, help_text="Optional profile picture for the employee"
    )
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Uncheck to create inactive account (user cannot login)",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "department",
            "role",
            "manager",
            "profile_picture",
            "is_active",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        # Special handling for certain fields
        self.fields["is_active"].widget.attrs["class"] = "form-check-input"
        self.fields["role"].widget.attrs["class"] = "form-select"
        self.fields["manager"].widget.attrs["class"] = "form-select"

        # Customize help text
        self.fields["username"].help_text = (
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        )
        self.fields["password1"].help_text = (
            "Your password must contain at least 8 characters."
        )
        self.fields["password2"].help_text = (
            "Enter the same password as before, for verification."
        )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data["employee_id"]
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("A user with this employee ID already exists.")
        return employee_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data["phone"]
        user.department = self.cleaned_data["department"]
        user.employee_id = self.cleaned_data["employee_id"]
        user.role = self.cleaned_data["role"]
        user.manager = self.cleaned_data["manager"]
        user.is_active = self.cleaned_data["is_active"]

        if commit:
            # Handle potential IntegrityError for employee_id
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    user.save()
                    # Create leave balance for new user
                    from .models import LeaveBalance

                    LeaveBalance.objects.create(user=user)
                    break
                except IntegrityError as e:
                    if "employee_id" in str(e) and attempt < max_attempts - 1:
                        # Clear the employee_id to force regeneration
                        user.employee_id = None
                        continue
                    else:
                        raise forms.ValidationError(
                            "Unable to create unique employee ID. Please try again."
                        )

        return user


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    department = forms.CharField(max_length=100, required=False)
    employee_id = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "department",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("username", css_class="form-group col-md-6 mb-0"),
                Column("email", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("employee_id", css_class="form-group col-md-6 mb-0"),
                Column("phone", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            "department",
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            Submit("submit", "Register", css_class="btn btn-primary"),
        )


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Enter your username",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        )

        # Remove help text
        for field in self.fields.values():
            field.help_text = None


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "department",
            "profile_picture",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("email", css_class="form-group col-md-6 mb-0"),
                Column("phone", css_class="form-group col-md-6 mb-0"),
                css_class="form-row",
            ),
            "department",
            "profile_picture",
            Submit("submit", "Update Profile", css_class="btn btn-success"),
        )
