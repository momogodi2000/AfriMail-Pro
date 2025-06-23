# backend/api_urls.py
"""
API URL patterns for AfriMail Pro
Simple API endpoints for AJAX requests from templates
"""
from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    # Authentication API
    path('auth/check-email/', views.check_email_availability, name='check_email'),
    path('auth/validate-password/', views.validate_password_strength, name='validate_password'),
    
    # User API
    path('user/profile/', views.user_profile_api, name='user_profile'),
    path('user/sessions/', views.get_active_sessions, name='active_sessions'),
    path('user/sessions/invalidate/', views.invalidate_all_sessions, name='invalidate_sessions'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]

# backend/utils.py
"""
Utility functions for AfriMail Pro
"""
import re
import hashlib
import secrets
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def is_valid_email(email):
        """Check if email format is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_disposable_email(email):
        """Check if email is from a disposable email service"""
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'tempmail.org',
            'mailinator.com', 'yopmail.com', 'throwaway.email',
            'temp-mail.org', 'getnada.com', 'maildrop.cc'
        ]
        
        domain = email.split('@')[1].lower()
        return domain in disposable_domains
    
    @staticmethod
    def extract_domain(email):
        """Extract domain from email"""
        try:
            return email.split('@')[1].lower()
        except IndexError:
            return None


class PasswordUtils:
    """Password utility functions"""
    
    @staticmethod
    def generate_random_password(length=12):
        """Generate a random password"""
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength and return score"""
        score = 0
        feedback = []
        
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("At least 8 characters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("At least one uppercase letter")
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("At least one lowercase letter")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("At least one number")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("At least one special character")
        
        strength_levels = {
            0: 'Very Weak',
            1: 'Weak',
            2: 'Fair',
            3: 'Good',
            4: 'Strong',
            5: 'Very Strong'
        }
        
        return {
            'score': score,
            'strength': strength_levels[score],
            'feedback': feedback,
            'is_strong': score >= 4
        }


class FileUtils:
    """File handling utilities"""
    
    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def secure_filename(filename):
        """Create a secure filename"""
        # Remove unsafe characters
        filename = re.sub(r'[^\w\s-]', '', filename.strip())
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename
    
    @staticmethod
    def get_file_size_mb(file_path):
        """Get file size in MB"""
        try:
            import os
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except OSError:
            return 0


class DateUtils:
    """Date and time utilities"""
    
    @staticmethod
    def format_relative_time(dt):
        """Format datetime as relative time"""
        if not dt:
            return ""
        
        now = timezone.now()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    @staticmethod
    def get_user_timezone_now(user):
        """Get current time in user's timezone"""
        from django.utils import timezone
        import pytz
        
        if hasattr(user, 'timezone') and user.timezone:
            try:
                user_tz = pytz.timezone(user.timezone)
                return timezone.now().astimezone(user_tz)
            except:
                pass
        
        return timezone.now()
    
    @staticmethod
    def format_duration(seconds):
        """Format seconds as human readable duration"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class NumberUtils:
    """Number formatting utilities"""
    
    @staticmethod
    def format_number(number):
        """Format number with commas"""
        try:
            return f"{int(number):,}"
        except (TypeError, ValueError):
            return str(number)
    
    @staticmethod
    def format_percentage(value, total, decimal_places=1):
        """Calculate and format percentage"""
        try:
            if total == 0:
                return "0%"
            percentage = (value / total) * 100
            return f"{percentage:.{decimal_places}f}%"
        except (TypeError, ZeroDivisionError):
            return "0%"
    
    @staticmethod
    def format_currency(amount, currency='FCFA'):
        """Format currency amount"""
        try:
            formatted = f"{int(amount):,}"
            if currency == 'FCFA':
                return f"{formatted} FCFA"
            else:
                return f"{currency} {formatted}"
        except (TypeError, ValueError):
            return f"{currency} 0"


class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def truncate_text(text, max_length=100, suffix="..."):
        """Truncate text to max length"""
        if not text or len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def slug_from_text(text):
        """Create URL-friendly slug from text"""
        text = re.sub(r'[^\w\s-]', '', text.strip().lower())
        return re.sub(r'[-\s]+', '-', text)
    
    @staticmethod
    def extract_first_name(full_name):
        """Extract first name from full name"""
        if not full_name:
            return ""
        return full_name.split()[0]
    
    @staticmethod
    def mask_email(email):
        """Mask email for privacy"""
        try:
            username, domain = email.split('@')
            if len(username) <= 2:
                masked_username = username
            else:
                masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
            return f"{masked_username}@{domain}"
        except ValueError:
            return email


class CacheUtils:
    """Cache utilities"""
    
    @staticmethod
    def generate_cache_key(prefix, *args):
        """Generate cache key from prefix and arguments"""
        key_parts = [str(prefix)]
        for arg in args:
            if hasattr(arg, 'id'):
                key_parts.append(str(arg.id))
            else:
                key_parts.append(str(arg))
        return '_'.join(key_parts)
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate cache keys matching pattern"""
        from django.core.cache import cache
        try:
            # This requires a cache backend that supports pattern deletion
            cache.delete_pattern(pattern)
        except AttributeError:
            # Fallback for cache backends that don't support patterns
            pass


class ValidationUtils:
    """General validation utilities"""
    
    @staticmethod
    def is_valid_phone(phone):
        """Validate phone number format"""
        # Basic validation for international phone numbers
        pattern = r'^\+?[1-9]\d{1,14}$'
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        return re.match(pattern, cleaned_phone) is not None
    
    @staticmethod
    def is_valid_url(url):
        """Validate URL format"""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def sanitize_input(text):
        """Sanitize user input"""
        if not text:
            return text
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        return text.strip()


class NotificationUtils:
    """Notification utilities"""
    
    @staticmethod
    def send_admin_notification(subject, message, level='info'):
        """Send notification to administrators"""
        try:
            admin_emails = [
                'momo@afrimailpro.com',
                'admin@afrimailpro.com'
            ]
            
            send_mail(
                subject=f"[AfriMail Pro Admin] {subject}",
                message=message,
                from_email=settings.PLATFORM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
    
    @staticmethod
    def log_security_event(event_type, user, details, request=None):
        """Log security events"""
        from .models import UserActivity
        
        try:
            UserActivity.log_activity(
                user=user,
                activity_type='SECURITY_EVENT',
                description=f"Security event: {event_type}",
                request=request,
                metadata={
                    'event_type': event_type,
                    'details': details,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Send notification for critical events
            if event_type in ['SUSPICIOUS_LOGIN', 'MULTIPLE_FAILED_LOGINS', 'ACCOUNT_LOCKOUT']:
                NotificationUtils.send_admin_notification(
                    f"Security Alert: {event_type}",
                    f"User: {user.email}\nDetails: {details}\nTime: {timezone.now()}"
                )
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")


class BulkOperationUtils:
    """Utilities for bulk operations"""
    
    @staticmethod
    def chunk_queryset(queryset, chunk_size=1000):
        """Split queryset into chunks for bulk processing"""
        count = queryset.count()
        for i in range(0, count, chunk_size):
            yield queryset[i:i + chunk_size]
    
    @staticmethod
    def bulk_update_with_progress(queryset, update_func, chunk_size=1000):
        """Bulk update with progress tracking"""
        total = queryset.count()
        processed = 0
        
        for chunk in BulkOperationUtils.chunk_queryset(queryset, chunk_size):
            for obj in chunk:
                update_func(obj)
                processed += 1
                
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{total} objects")
        
        return processed


class ExportUtils:
    """Data export utilities"""
    
    @staticmethod
    def queryset_to_csv(queryset, fields, filename=None):
        """Export queryset to CSV"""
        import csv
        from django.http import HttpResponse
        
        if filename is None:
            filename = f"export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header
        header = [field.replace('_', ' ').title() for field in fields]
        writer.writerow(header)
        
        # Write data
        for obj in queryset:
            row = []
            for field in fields:
                value = getattr(obj, field, '')
                if callable(value):
                    value = value()
                row.append(str(value))
            writer.writerow(row)
        
        return response


# backend/decorators.py
"""
Custom decorators for AfriMail Pro
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers


def subscription_required(view_func):
    """Decorator to check if user has active subscription"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user
        if user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        can_access, message = user.can_send_emails()
        if not can_access:
            messages.error(request, f"Subscription required: {message}")
            return redirect('billing_settings')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_required(view_func):
    """Decorator to check if user is admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_super_admin:
            raise PermissionDenied("Admin access required")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def ajax_required(view_func):
    """Decorator to ensure request is AJAX"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    
    return wrapper


def feature_required(feature_name):
    """Decorator to check if user has access to specific feature"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user = request.user
            if user.is_super_admin:
                return view_func(request, *args, **kwargs)
            
            limits = user.get_plan_limits()
            features = limits.get('features', [])
            
            if feature_name not in features:
                messages.error(
                    request, 
                    f"This feature requires a higher subscription plan. Please upgrade to access {feature_name}."
                )
                return redirect('billing_settings')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(max_requests=10, period=60):
    """Simple rate limiting decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            import time
            
            # Get client IP
            ip = request.META.get('REMOTE_ADDR', '')
            cache_key = f"rate_limit_{view_func.__name__}_{ip}"
            
            # Get current request count
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= max_requests:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                else:
                    messages.error(request, "Rate limit exceeded. Please try again later.")
                    return redirect('homepage')
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, period)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Add to backend/__init__.py to ensure signals are loaded
default_app_config = 'backend.apps.BackendConfig'