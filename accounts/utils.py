from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

def send_email_notification(subject, template_name, context, recipient_email, from_email=None):
    """
    Send an email notification using HTML templates
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Add common context variables
        context.update({
            'company_name': getattr(settings, 'COMPANY_NAME', 'Quorium Consulting'),
            'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'base_url': getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000'),
        })
        
        # Render HTML email
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_leave_status_notification(leave_application, approver):
    """
    Send notification when leave status changes
    """
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
    
    context = {
        'leave': leave_application,
        'approver': approver,
        'approver_role': approver.get_role_display(),
        'comments': leave_application.hr_comments if approver.role == 'hr' else leave_application.admin_comments,
        'reviewer_name': approver.get_full_name() or approver.username,
        'review_date': leave_application.updated_at,
        'return_date': leave_application.end_date + timedelta(days=1),
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