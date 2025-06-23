

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

