
# backend/management/commands/setup_afrimail.py
"""
Management command to set up AfriMail Pro with initial data
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Set up AfriMail Pro with initial data and configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--no-users',
            action='store_true',
            help='Skip creating default users',
        )
        parser.add_argument(
            '--no-templates',
            action='store_true',
            help='Skip creating default email templates',
        )
        parser.add_argument(
            '--production',
            action='store_true',
            help='Set up for production environment',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up AfriMail Pro...')
        )
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=0)
        
        # Collect static files in production
        if options['production']:
            self.stdout.write('Collecting static files...')
            call_command('collectstatic', '--noinput', verbosity=0)
        
        # Create default users
        if not options['no_users']:
            self.stdout.write('Creating default users...')
            call_command('create_default_users')
        
        # Create default email templates
        if not options['no_templates']:
            self.stdout.write('Creating default email templates...')
            call_command('create_default_templates')
        
        # Create necessary directories
        self.create_directories()
        
        # Set up periodic tasks
        self.stdout.write('Setting up periodic tasks...')
        call_command('setup_periodic_tasks')
        
        self.stdout.write(
            self.style.SUCCESS('AfriMail Pro setup completed successfully!')
        )
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'media/avatars',
            'media/company_logos',
            'media/template_thumbnails',
            'media/contact_imports',
            'static/uploads',
            'logs',
        ]
        
        for directory in directories:
            full_path = os.path.join(settings.BASE_DIR, directory)
            os.makedirs(full_path, exist_ok=True)
            self.stdout.write(f'Created directory: {directory}')