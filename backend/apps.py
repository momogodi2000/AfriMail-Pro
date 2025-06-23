# backend/apps.py
"""
App configuration for backend
"""
from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'
    verbose_name = 'AfriMail Pro Backend'
    
    def ready(self):
        # Import signal handlers
        import backend.signals
        
        # Import any other startup code
        try:
            from . import tasks  # Import Celery tasks
        except ImportError:
            pass  # Celery might not be configured