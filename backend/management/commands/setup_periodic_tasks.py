

# backend/management/commands/setup_periodic_tasks.py
"""
Management command to set up periodic tasks for AfriMail Pro
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for AfriMail Pro'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up periodic tasks...')
        
        # Create schedules
        daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,  # 2 AM
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        hourly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        weekly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=3,  # 3 AM
            day_of_week=1,  # Monday
            day_of_month='*',
            month_of_year='*',
        )
        
        # Define periodic tasks
        tasks = [
            {
                'name': 'Clean up expired sessions',
                'task': 'backend.tasks.cleanup_expired_sessions',
                'schedule': daily_schedule,
                'enabled': True,
            },
            {
                'name': 'Update engagement scores',
                'task': 'backend.tasks.update_engagement_scores',
                'schedule': daily_schedule,
                'enabled': True,
            },
            {
                'name': 'Process scheduled campaigns',
                'task': 'backend.tasks.process_scheduled_campaigns',
                'schedule': hourly_schedule,
                'enabled': True,
            },
            {
                'name': 'Generate analytics snapshots',
                'task': 'backend.tasks.generate_analytics_snapshots',
                'schedule': daily_schedule,
                'enabled': True,
            },
            {
                'name': 'Send weekly reports',
                'task': 'backend.tasks.send_weekly_reports',
                'schedule': weekly_schedule,
                'enabled': True,
            },
            {
                'name': 'Check subscription expirations',
                'task': 'backend.tasks.check_subscription_expirations',
                'schedule': daily_schedule,
                'enabled': True,
            },
        ]
        
        created_count = 0
        
        for task_data in tasks:
            task, created = PeriodicTask.objects.get_or_create(
                name=task_data['name'],
                defaults={
                    'task': task_data['task'],
                    'crontab': task_data['schedule'],
                    'enabled': task_data['enabled'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created task: {task.name}')
            else:
                self.stdout.write(f'Task already exists: {task.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up {created_count} periodic tasks'
            )
        )