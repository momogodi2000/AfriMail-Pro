


# backend/management/commands/send_test_email.py
"""
Management command to send test emails
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.services.email_service import EmailService

User = get_user_model()


class Command(BaseCommand):
    help = 'Send test email to verify email configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email address of the user to send from',
        )
        parser.add_argument(
            '--to-email',
            type=str,
            required=True,
            help='Email address to send test email to',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='AfriMail Pro Test Email',
            help='Subject line for test email',
        )
    
    def handle(self, *args, **options):
        try:
            user = User.objects.get(email=options['user_email'])
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with email {options['user_email']} not found")
            )
            return
        
        email_service = EmailService(user)
        
        html_content = '''
        <html>
        <body>
            <h2>AfriMail Pro Test Email</h2>
            <p>Hello!</p>
            <p>This is a test email sent from AfriMail Pro to verify your email configuration.</p>
            <p>If you received this email, your email setup is working correctly!</p>
            <hr>
            <p><small>Sent from AfriMail Pro - Professional Email Marketing Platform</small></p>
        </body>
        </html>
        '''
        
        text_content = '''
        AfriMail Pro Test Email
        
        Hello!
        
        This is a test email sent from AfriMail Pro to verify your email configuration.
        
        If you received this email, your email setup is working correctly!
        
        ---
        Sent from AfriMail Pro - Professional Email Marketing Platform
        '''
        
        self.stdout.write('Sending test email...')
        
        result = email_service.send_test_email(
            test_email=options['to_email'],
            subject=options['subject'],
            html_content=html_content,
            text_content=text_content
        )
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test email sent successfully to {options['to_email']}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to send test email: {result['error']}"
                )
            )