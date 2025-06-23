 backend/management/commands/create_superuser_if_none.py
"""
Management command to create a superuser if none exists
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if none exists'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')
    
    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Superuser already exists')
            )
            return
        
        email = options.get('email') or 'admin@afrimailpro.com'
        password = options.get('password') or 'AfriMail2024!@#'
        
        user = User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            company='AfriMail Pro',
            role='SUPER_ADMIN',
            is_verified=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superuser created: {email}')
        )
        self.stdout.write(
            self.style.WARNING(f'Password: {password}')
        )
        self.stdout.write(
            self.style.WARNING('Please change this password immediately!')
        )
