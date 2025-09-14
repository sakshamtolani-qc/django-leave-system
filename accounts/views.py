# accounts/views.py - Updated with email integration
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import UserRegistrationForm, ProfileUpdateForm, AddUserForm
from .models import LeaveBalance
from .utils import send_registration_welcome_email

class RegisterView(SuccessMessageMixin, CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    success_message = "Registration successful! You can now login."

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create leave balance for new user
        LeaveBalance.objects.create(user=self.object)
        
        # Send welcome email
        try:
            send_registration_welcome_email(self.object)
            messages.success(self.request, f'Registration successful! Welcome email sent to {self.object.email}')
        except Exception as e:
            messages.warning(self.request, f'Account created successfully, but email notification failed: {str(e)}')
        
        return response

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def add_user_view(request):
    """View for HR/Admin to create new employee accounts"""

    # Check permissions - only HR and Admin can create users
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        raise PermissionDenied("Only HR and Admin users can create new accounts.")

    if request.method == 'POST':
        form = AddUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            try:
                send_registration_welcome_email(user)
                messages.success(
                    request, 
                    f'Employee account created for {user.get_full_name()}! '
                    f'Welcome email sent to {user.email}. Username: {user.username}'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Employee account created for {user.get_full_name()} '
                    f'(Username: {user.username}) but email failed: {str(e)}'
                )
            
            return redirect('dashboard:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddUserForm()

    return render(request, 'accounts/add_user.html', {'form': form})