from django.core.management.base import BaseCommand
from accounts.utils import send_email_notification

class Command(BaseCommand):
    help = 'Test SendGrid email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        email = options['email']
        
        success = send_email_notification(
            subject='Test Email from Leave Management System (SendGrid)',
            template_name='emails/registration_welcome.html',  # Use an existing template
            context={
                'user': {'username': 'Test User', 'first_name': 'Test'},
                'message': '<p>This is a test email using SendGrid. If you receive this, your email configuration is working!</p>'
            },
            recipient_email=email
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Test email sent successfully via SendGrid to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send test email to {email}'))