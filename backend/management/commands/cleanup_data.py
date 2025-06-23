# backend/management/commands/cleanup_data.py
"""
Management command to clean up old data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from backend.models import UserActivity, EmailLog, ContactImport


class Command(BaseCommand):
    help = 'Clean up old data to save storage space'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete data older than this many days'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f'Cleaning up data older than {days} days ({cutoff_date})')
        
        # User activities
        activities = UserActivity.objects.filter(created_at__lt=cutoff_date)
        activity_count = activities.count()
        
        # Email logs
        email_logs = EmailLog.objects.filter(queued_at__lt=cutoff_date)
        email_log_count = email_logs.count()
        
        # Old contact imports
        imports = ContactImport.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['COMPLETED', 'FAILED']
        )
        import_count = imports.count()
        
        if dry_run:
            self.stdout.write(f'Would delete:')
            self.stdout.write(f'  - {activity_count} user activities')
            self.stdout.write(f'  - {email_log_count} email logs')
            self.stdout.write(f'  - {import_count} contact imports')
        else:
            activities.delete()
            email_logs.delete()
            imports.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {activity_count + email_log_count + import_count} records'
                )
            )
