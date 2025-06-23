# backend/management/__init__.py
# Empty file

# backend/management/commands/__init__.py
# Empty file

# backend/management/commands/create_default_users.py
"""
Management command to create default users for AfriMail Pro
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.authentication import AuthenticationService


class Command(BaseCommand):
    help = 'Create default super admin and test users for AfriMail Pro'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Skip creation if users already exist',
        )
        parser.add_argument(
            '--admin-only',
            action='store_true',
            help='Create only admin users, not test clients',
        )
    
    def handle(self, *args, **options):
        auth_service = AuthenticationService()
        
        self.stdout.write(self.style.SUCCESS('Creating default users...'))
        
        try:
            with transaction.atomic():
                result = auth_service.create_default_users()
                
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully created {result['created_count']} users"
                        )
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            "Default passwords:\n"
                            "- Admin users: AfriMail2024!@#\n"
                            "- Test clients: TestUser123!\n"
                            "Please change these passwords immediately!"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to create users: {result['error']}")
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating users: {str(e)}")
            )
