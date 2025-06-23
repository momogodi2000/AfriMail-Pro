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
