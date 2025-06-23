# celery.py
"""
Celery configuration for AfriMail Pro
"""
import os
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afrimail.settings')

app = Celery('afrimail')

# Configure Celery using settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'backend.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Every hour
    },
    'update-engagement-scores': {
        'task': 'backend.tasks.update_engagement_scores',
        'schedule': 86400.0,  # Daily
    },
    'process-scheduled-campaigns': {
        'task': 'backend.tasks.process_scheduled_campaigns',
        'schedule': 300.0,  # Every 5 minutes
    },
    'generate-analytics-snapshots': {
        'task': 'backend.tasks.generate_analytics_snapshots',
        'schedule': 86400.0,  # Daily
    },
    'send-weekly-reports': {
        'task': 'backend.tasks.send_weekly_reports',
        'schedule': 604800.0,  # Weekly
    },
    'check-subscription-expirations': {
        'task': 'backend.tasks.check_subscription_expirations',
        'schedule': 86400.0,  # Daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')