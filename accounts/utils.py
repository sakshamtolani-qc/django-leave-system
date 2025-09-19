from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content
import json

logger = logging.getLogger(__name__)

def send_email_notification(subject, template_name, context, recipient_email, from_email=None):
    """
    Send an email notification using SendGrid API and HTML templates
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Add common context variables
        context.update({
            'company_name': getattr(settings, 'COMPANY_NAME', 'Quorium Consulting'),
            'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'base_url': getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000').rstrip('/'),
        })
        
        # Render HTML email
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        # Create SendGrid message
        message = Mail(
            from_email=from_email,
            to_emails=recipient_email,
            subject=subject,
            plain_text_content=text_content,
            html_content=html_content
        )
        
        # Send email using SendGrid
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Log response details
        logger.info(f"SendGrid Response - Status: {response.status_code}")
        logger.info(f"SendGrid Headers: {response.headers}")
        logger.info(f"Email sent successfully to {recipient_email}: {subject}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_new_employee_credentials_email(user, generated_password):
    """
    Send login credentials to newly created employee
    """
    subject = f"Your Account Credentials - {getattr(settings, 'COMPANY_NAME', 'Quorium Consulting')}"
    template = 'emails/new_employee_credentials.html'
    context = {
        'user': user,
        'generated_password': generated_password,
        'login_url': f"{getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000').rstrip('/')}/accounts/login/",
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=user.email
    )

def send_password_change_required_email(user):
    """
    Send email requiring password change
    """
    subject = f"Password Change Required - {getattr(settings, 'COMPANY_NAME', 'Quorium Consulting')}"
    template = 'emails/password_change_required.html'
    context = {
        'user': user,
        'change_password_url': f"{getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000').rstrip('/')}/accounts/change-password/",
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=user.email
    )

# Keep all your existing email functions
def send_leave_status_notification(leave_application, approver):
    """
    Send notification when leave status changes
    """
    from datetime import timedelta
    
    if leave_application.status == 'approved':
        subject = f"Leave Application Approved - #{leave_application.id}"
        template = 'emails/leave_approved.html'
    elif leave_application.status == 'hr_approved':
        subject = f"Leave Application - HR Approved - #{leave_application.id}"
        template = 'emails/leave_approved.html'
    elif leave_application.status == 'rejected':
        subject = f"Leave Application Update - #{leave_application.id}"
        template = 'emails/leave_rejected.html'
    else:
        subject = f"Leave Application Status Update - #{leave_application.id}"
        template = 'emails/leave_status_notification.html'
    
    # Calculate return date
    return_date = leave_application.end_date + timedelta(days=1)
    
    context = {
        'leave': leave_application,
        'approver': approver,
        'approver_role': approver.get_role_display(),
        'comments': leave_application.hr_comments if approver.role == 'hr' else leave_application.admin_comments,
        'reviewer_name': approver.get_full_name() or approver.username,
        'review_date': leave_application.updated_at,
        'return_date': return_date,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=leave_application.employee.email
    )

def send_approval_request_notification(leave_application, approver):
    """
    Send notification to approvers when new leave needs approval
    """
    subject = f"Leave Application Requires Your Approval - #{leave_application.id}"
    template = 'emails/approval_notification.html'
    
    if leave_application.status == 'pending':
        approval_type = "HR Review"
    else:
        approval_type = "Admin Final Approval"
    
    context = {
        'leave': leave_application,
        'approver': approver,
        'approval_type': approval_type,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=approver.email
    )

def send_registration_welcome_email(user):
    """
    Send welcome email to newly registered user
    """
    subject = f"Welcome to {getattr(settings, 'COMPANY_NAME', 'Quorium Consulting')}!"
    template = 'emails/registration_welcome.html'
    context = {
        'user': user,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=user.email
    )

def send_leave_submitted_email(leave_application):
    """
    Send confirmation email when leave is submitted
    """
    subject = f"Leave Application Submitted - #{leave_application.id}"
    template = 'emails/leave_submitted.html'
    context = {
        'leave': leave_application,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=leave_application.employee.email
    )
