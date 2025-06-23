
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


