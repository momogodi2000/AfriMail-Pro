# backend/context_processors.py
"""
Context processors for AfriMail Pro
Global context data available in all templates
"""
from django.conf import settings
from django.utils import timezone
from .models import CustomUser, Campaign, Contact
from datetime import timedelta


def global_context(request):
    """Add global context data to all templates"""
    context = {
        'platform_name': settings.PLATFORM_NAME,
        'platform_email': settings.PLATFORM_EMAIL,
        'current_year': timezone.now().year,
        'supported_countries': settings.AFRIMAIL_SETTINGS.get('SUPPORTED_COUNTRIES', []),
        'supported_languages': settings.AFRIMAIL_SETTINGS.get('SUPPORTED_LANGUAGES', []),
        'pricing': settings.AFRIMAIL_SETTINGS.get('PRICING', {}),
    }
    
    # Add user-specific context if authenticated
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_permissions': get_user_permissions(user),
            'user_stats': get_user_stats(user),
            'user_limits': user.get_plan_limits(),
            'trial_info': get_trial_info(user),
            'subscription_info': get_subscription_info(user),
        })
    
    return context


def get_user_permissions(user):
    """Get user permissions for template usage"""
    from .authentication import SecurityService
    return SecurityService.get_user_permissions(user)


def get_user_stats(user):
    """Get user statistics for dashboard"""
    try:
        # Get recent campaigns
        recent_campaigns = Campaign.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        # Get contact statistics
        total_contacts = Contact.objects.filter(user=user, is_subscribed=True).count()
        new_contacts_this_month = Contact.objects.filter(
            user=user,
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        
        # Get campaign statistics
        total_campaigns = Campaign.objects.filter(user=user).count()
        campaigns_this_month = Campaign.objects.filter(
            user=user,
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        
        return {
            'total_contacts': total_contacts,
            'new_contacts_this_month': new_contacts_this_month,
            'total_campaigns': total_campaigns,
            'campaigns_this_month': campaigns_this_month,
            'recent_campaigns': recent_campaigns,
            'monthly_email_usage': user.get_monthly_email_usage(),
        }
    except Exception:
        return {
            'total_contacts': 0,
            'new_contacts_this_month': 0,
            'total_campaigns': 0,
            'campaigns_this_month': 0,
            'recent_campaigns': [],
            'monthly_email_usage': 0,
        }


def get_trial_info(user):
    """Get trial information"""
    if user.is_trial_user:
        return {
            'is_trial': True,
            'days_remaining': user.trial_days_remaining,
            'is_active': user.is_trial_active,
            'trial_ends': user.trial_ends,
        }
    return {'is_trial': False}


def get_subscription_info(user):
    """Get subscription information"""
    return {
        'plan': user.subscription_plan,
        'plan_display': user.get_subscription_plan_display(),
        'is_active': user.subscription_active,
        'ends': user.subscription_ends,
        'auto_renew': user.auto_renew,
        'days_remaining': user.subscription_days_remaining,
    }


# backend/middleware.py
"""
Custom middleware for AfriMail Pro
"""
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from .models import UserActivity
from .authentication import SecurityService, SessionManager
import logging

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(MiddlewareMixin):
    """Middleware to check subscription status"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip for certain paths
        skip_paths = [
            '/admin/', '/login/', '/register/', '/logout/', '/verify-email/',
            '/reset-password/', '/forgot-password/', '/api/', '/health/',
            '/static/', '/media/', '/conditions/', '/policy/'
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Check authenticated users
        if request.user.is_authenticated and not request.user.is_super_admin:
            user = request.user
            
            # Check if user needs to complete onboarding
            if not user.onboarding_completed and not request.path.startswith('/onboarding/'):
                return HttpResponseRedirect(reverse('onboarding'))
            
            # Check trial status
            if user.is_trial_user and not user.is_trial_active:
                messages.warning(
                    request,
                    'Your trial has expired. Please upgrade your subscription to continue using AfriMail Pro.'
                )
                if not request.path.startswith('/billing/'):
                    return HttpResponseRedirect(reverse('billing_settings'))
            
            # Check subscription status
            if not user.subscription_active and not user.is_trial_active:
                messages.error(
                    request,
                    'Your subscription is not active. Please contact support or update your billing information.'
                )
                if not request.path.startswith('/billing/'):
                    return HttpResponseRedirect(reverse('billing_settings'))
        
        return None


class ActivityTrackingMiddleware(MiddlewareMixin):
    """Middleware to track user activity"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Track page views for authenticated users
        if request.user.is_authenticated and request.method == 'GET':
            # Skip certain paths
            skip_paths = [
                '/static/', '/media/', '/api/', '/health/', '/favicon.ico'
            ]
            
            if not any(request.path.startswith(path) for path in skip_paths):
                try:
                    UserActivity.log_activity(
                        user=request.user,
                        activity_type='FEATURE_USED',
                        description=f'Accessed {request.path}',
                        request=request,
                        metadata={
                            'path': request.path,
                            'method': request.method,
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error tracking activity: {str(e)}")
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """Custom security middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Validate session for authenticated users
        if request.user.is_authenticated:
            if not SecurityService.validate_session(request):
                logger.warning(f"Invalid session detected for user {request.user.email}")
                SessionManager.destroy_session(request)
                messages.warning(request, 'Your session has expired. Please log in again.')
                return HttpResponseRedirect(reverse('login'))
            
            # Check for suspicious activity
            if SecurityService.check_suspicious_activity(request.user, request):
                logger.warning(f"Suspicious activity detected for user {request.user.email}")
                # You might want to add additional security measures here
        
        return None
    
    def process_response(self, request, response):
        # Add security headers
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class TimezoneMiddleware(MiddlewareMixin):
    """Middleware to set user timezone"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            user_timezone = getattr(request.user, 'timezone', 'Africa/Douala')
            timezone.activate(user_timezone)
        else:
            timezone.deactivate()


class CORSMiddleware(MiddlewareMixin):
    """Simple CORS middleware for API endpoints"""
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response


# backend/signals.py
"""
Signal handlers for AfriMail Pro
"""
from django.db.models.signals import post_save, pre_delete, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from .models import (
    CustomUser, UserProfile, Contact, Campaign, EmailLog,
    ContactList, UserActivity
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Profile created for user: {instance.email}")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.email}: {str(e)}")


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Exception as e:
        logger.error(f"Error saving profile for user {instance.email}: {str(e)}")


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login"""
    try:
        # Update user last login info
        user.last_login = timezone.now()
        if request:
            user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # Set session login time
        if request and hasattr(request, 'session'):
            request.session['login_time'] = timezone.now().isoformat()
        
        logger.info(f"User logged in: {user.email}")
        
    except Exception as e:
        logger.error(f"Error in login handler for {user.email}: {str(e)}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Handle user logout"""
    try:
        if user:
            # Log logout activity
            UserActivity.log_activity(
                user=user,
                activity_type='LOGOUT',
                description='User logged out',
                request=request
            )
            
            logger.info(f"User logged out: {user.email}")
        
    except Exception as e:
        logger.error(f"Error in logout handler: {str(e)}")


@receiver(post_save, sender=Contact)
def update_contact_list_counts(sender, instance, created, **kwargs):
    """Update contact list counts when contact is added/modified"""
    try:
        # Update counts for all lists this contact belongs to
        for contact_list in instance.contact_lists.all():
            contact_list.update_contact_count()
        
        # Update user's total contact count
        user = instance.user
        user.total_contacts = Contact.objects.filter(
            user=user, 
            is_subscribed=True
        ).count()
        user.save(update_fields=['total_contacts'])
        
        if created:
            logger.info(f"Contact created: {instance.email} for user {user.email}")
        
    except Exception as e:
        logger.error(f"Error updating contact list counts: {str(e)}")


@receiver(post_delete, sender=Contact)
def update_contact_list_counts_on_delete(sender, instance, **kwargs):
    """Update contact list counts when contact is deleted"""
    try:
        # Update counts for all lists this contact belonged to
        for contact_list in instance.contact_lists.all():
            contact_list.update_contact_count()
        
        # Update user's total contact count
        user = instance.user
        user.total_contacts = Contact.objects.filter(
            user=user, 
            is_subscribed=True
        ).count()
        user.save(update_fields=['total_contacts'])
        
        logger.info(f"Contact deleted: {instance.email}")
        
    except Exception as e:
        logger.error(f"Error updating contact list counts on delete: {str(e)}")


@receiver(post_save, sender=Campaign)
def update_user_campaign_count(sender, instance, created, **kwargs):
    """Update user's campaign count when campaign is created"""
    try:
        if created:
            user = instance.user
            user.total_campaigns = Campaign.objects.filter(user=user).count()
            user.save(update_fields=['total_campaigns'])
            
            logger.info(f"Campaign created: {instance.name} for user {user.email}")
        
    except Exception as e:
        logger.error(f"Error updating user campaign count: {str(e)}")


@receiver(post_save, sender=EmailLog)
def update_email_statistics(sender, instance, created, **kwargs):
    """Update email statistics when email log is created/updated"""
    try:
        if instance.status == 'SENT' and instance.user:
            # Update user's total emails sent
            user = instance.user
            user.total_emails_sent += 1
            user.save(update_fields=['total_emails_sent'])
            
            # Update campaign statistics if applicable
            if instance.campaign:
                campaign = instance.campaign
                campaign.sent_count += 1
                campaign.save(update_fields=['sent_count'])
        
        # Update contact engagement if applicable
        if instance.contact and instance.status in ['OPENED', 'CLICKED']:
            contact = instance.contact
            if instance.status == 'OPENED':
                contact.total_opens += 1
            elif instance.status == 'CLICKED':
                contact.total_clicks += 1
            
            contact.last_engagement = timezone.now()
            contact.save(update_fields=['total_opens', 'total_clicks', 'last_engagement'])
        
    except Exception as e:
        logger.error(f"Error updating email statistics: {str(e)}")


@receiver(post_save, sender=ContactList)
def invalidate_list_cache(sender, instance, **kwargs):
    """Invalidate cache when contact list is updated"""
    try:
        cache_key = f"contact_list_{instance.id}_contacts"
        cache.delete(cache_key)
        
        # Also invalidate user's lists cache
        user_cache_key = f"user_{instance.user.id}_contact_lists"
        cache.delete(user_cache_key)
        
    except Exception as e:
        logger.error(f"Error invalidating list cache: {str(e)}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


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