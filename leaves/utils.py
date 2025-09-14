# leaves/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
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
            'company_name': getattr(settings, 'COMPANY_NAME', 'Leave Management System'),
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

def send_leave_approved_email(leave_application, approver_role, comments=''):
    """
    Send email when leave is approved (HR or Admin)
    """
    if leave_application.status == 'approved':
        subject = f"🎉 Leave Application Fully Approved - #{leave_application.id}"
    else:
        subject = f"Leave Application Approved by {approver_role} - #{leave_application.id}"
    
    template = 'emails/leave_approved.html'
    context = {
        'leave': leave_application,
        'approver_role': approver_role,
        'comments': comments,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=leave_application.employee.email
    )

def send_leave_rejected_email(leave_application, reviewer_name, comments=''):
    """
    Send email when leave is rejected
    """
    subject = f"Leave Application Status Update - #{leave_application.id}"
    template = 'emails/leave_rejected.html'
    context = {
        'leave': leave_application,
        'reviewer_name': reviewer_name,
        'review_date': leave_application.updated_at,
        'comments': comments,
    }
    
    return send_email_notification(
        subject=subject,
        template_name=template,
        context=context,
        recipient_email=leave_application.employee.email
    )

def send_approval_notification_to_approvers(leave_application):
    """
    Send notification to HR/Admin when a new leave needs approval
    """
    if leave_application.status == 'pending':
        # Notify HR users
        hr_users = User.objects.filter(role='hr', is_active=True)
        subject = f"New Leave Application for Review - #{leave_application.id}"
        template = 'emails/approval_notification.html'
        
        for hr_user in hr_users:
            context = {
                'leave': leave_application,
                'approver': hr_user,
                'approval_type': 'HR Review'
            }
            send_email_notification(
                subject=subject,
                template_name=template,
                context=context,
                recipient_email=hr_user.email
            )
    
    elif leave_application.status == 'hr_approved':
        # Notify Admin users
        admin_users = User.objects.filter(is_superuser=True, is_active=True)
        subject = f"Leave Application Ready for Final Approval - #{leave_application.id}"
        template = 'emails/approval_notification.html'
        
        for admin_user in admin_users:
            context = {
                'leave': leave_application,
                'approver': admin_user,
                'approval_type': 'Final Admin Approval'
            }
            send_email_notification(
                subject=subject,
                template_name=template,
                context=context,
                recipient_email=admin_user.email
            )