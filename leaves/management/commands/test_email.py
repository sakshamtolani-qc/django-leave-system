from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email configuration'
    
    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email address to send test email to')
    
    def handle(self, *args, **options):
        to_email = options.get('to') or 'test@example.com'
        
        try:
            send_mail(
                subject='Test Email from Leave Management System',
                message='This is a test email to verify your email configuration is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent successfully to {to_email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {str(e)}')
            )