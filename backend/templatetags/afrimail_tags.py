# backend/templatetags/__init__.py
# Empty file

# backend/templatetags/afrimail_tags.py
"""
Custom template tags and filters for AfriMail Pro
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json

register = template.Library()


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total == 0:
            return 0
        return round((value / total) * 100, 2)
    except (TypeError, ZeroDivisionError):
        return 0


@register.filter
def format_number(value):
    """Format number with commas"""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


@register.filter
def format_currency(value, currency='FCFA'):
    """Format currency"""
    try:
        formatted_value = f"{int(value):,}"
        if currency == 'FCFA':
            return f"{formatted_value} FCFA"
        else:
            return f"{currency} {formatted_value}"
    except (TypeError, ValueError):
        return value


@register.filter
def time_since_short(value):
    """Short time since format"""
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    if diff.days > 365:
        return f"{diff.days // 365}y"
    elif diff.days > 30:
        return f"{diff.days // 30}mo"
    elif diff.days > 0:
        return f"{diff.days}d"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m"
    else:
        return "now"


@register.filter
def user_can(user, permission):
    """Check if user has specific permission"""
    from backend.authentication import SecurityService
    permissions = SecurityService.get_user_permissions(user)
    return permissions.get(permission, False)


@register.filter
def engagement_level_class(score):
    """Get CSS class for engagement level"""
    try:
        score = float(score)
        if score >= 70:
            return "text-success"
        elif score >= 40:
            return "text-warning"
        elif score >= 10:
            return "text-info"
        else:
            return "text-danger"
    except (TypeError, ValueError):
        return "text-muted"


@register.filter
def engagement_level_text(score):
    """Get text for engagement level"""
    try:
        score = float(score)
        if score >= 70:
            return "High"
        elif score >= 40:
            return "Medium"
        elif score >= 10:
            return "Low"
        else:
            return "Inactive"
    except (TypeError, ValueError):
        return "Unknown"


@register.filter
def campaign_status_class(status):
    """Get CSS class for campaign status"""
    status_classes = {
        'DRAFT': 'text-secondary',
        'SCHEDULED': 'text-info',
        'SENDING': 'text-primary',
        'SENT': 'text-success',
        'COMPLETED': 'text-success',
        'PAUSED': 'text-warning',
        'CANCELLED': 'text-danger',
        'FAILED': 'text-danger',
    }
    return status_classes.get(status, 'text-muted')


@register.filter
def subscription_status_class(user):
    """Get CSS class for subscription status"""
    if user.is_super_admin:
        return "text-primary"
    elif user.is_trial_user:
        if user.is_trial_active:
            return "text-warning"
        else:
            return "text-danger"
    elif user.subscription_active:
        return "text-success"
    else:
        return "text-danger"


@register.simple_tag
def progress_bar(value, total, css_class="primary"):
    """Render a progress bar"""
    try:
        if total == 0:
            percentage = 0
        else:
            percentage = min((value / total) * 100, 100)
        
        return format_html(
            '<div class="progress"><div class="progress-bar bg-{}" role="progressbar" '
            'style="width: {}%" aria-valuenow="{}" aria-valuemin="0" aria-valuemax="100">'
            '</div></div>',
            css_class, percentage, value
        )
    except (TypeError, ZeroDivisionError):
        return format_html('<div class="progress"><div class="progress-bar" style="width: 0%"></div></div>')


@register.simple_tag
def metric_card(title, value, subtitle="", icon="", color="primary"):
    """Render a metric card"""
    icon_html = f'<i class="{icon}"></i>' if icon else ''
    
    return format_html(
        '<div class="card border-{}">'
        '<div class="card-body">'
        '<div class="d-flex align-items-center">'
        '<div class="flex-grow-1">'
        '<h6 class="card-title text-muted mb-1">{}</h6>'
        '<h3 class="mb-0">{}</h3>'
        '{}'
        '</div>'
        '<div class="text-{}">{}</div>'
        '</div>'
        '</div>'
        '</div>',
        color, title, value, 
        f'<small class="text-muted">{subtitle}</small>' if subtitle else '',
        color, icon_html
    )


@register.simple_tag
def status_badge(status, type="campaign"):
    """Render a status badge"""
    if type == "campaign":
        status_config = {
            'DRAFT': ('secondary', 'Draft'),
            'SCHEDULED': ('info', 'Scheduled'),
            'SENDING': ('primary', 'Sending'),
            'SENT': ('success', 'Sent'),
            'COMPLETED': ('success', 'Completed'),
            'PAUSED': ('warning', 'Paused'),
            'CANCELLED': ('danger', 'Cancelled'),
            'FAILED': ('danger', 'Failed'),
        }
    elif type == "subscription":
        status_config = {
            'SUBSCRIBED': ('success', 'Subscribed'),
            'UNSUBSCRIBED': ('danger', 'Unsubscribed'),
            'BOUNCED': ('warning', 'Bounced'),
            'COMPLAINED': ('danger', 'Complained'),
            'PENDING': ('info', 'Pending'),
            'BLACKLISTED': ('dark', 'Blacklisted'),
        }
    else:
        status_config = {}
    
    css_class, display_text = status_config.get(status, ('secondary', status))
    
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        css_class, display_text
    )


@register.simple_tag
def trial_countdown(user):
    """Show trial countdown"""
    if not user.is_trial_user or not user.is_trial_active:
        return ""
    
    days_remaining = user.trial_days_remaining
    
    if days_remaining <= 3:
        css_class = "danger"
    elif days_remaining <= 7:
        css_class = "warning"
    else:
        css_class = "info"
    
    return format_html(
        '<div class="alert alert-{} alert-dismissible fade show" role="alert">'
        '<strong>Trial expires in {} days!</strong> '
        '<a href="{}" class="alert-link">Upgrade now</a> to continue using all features.'
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
        '</div>',
        css_class, days_remaining, reverse('billing_settings')
    )


@register.simple_tag
def feature_check(user, feature_name):
    """Check if user has access to a feature"""
    try:
        limits = user.get_plan_limits()
        features = limits.get('features', [])
        return feature_name in features
    except:
        return False


@register.simple_tag
def usage_meter(current, limit, label=""):
    """Show usage meter"""
    try:
        if limit == 0:
            percentage = 0
        else:
            percentage = min((current / limit) * 100, 100)
        
        if percentage >= 90:
            css_class = "danger"
        elif percentage >= 75:
            css_class = "warning"
        else:
            css_class = "success"
        
        return format_html(
            '<div class="mb-2">'
            '<div class="d-flex justify-content-between">'
            '<small>{}</small>'
            '<small>{} / {}</small>'
            '</div>'
            '<div class="progress" style="height: 6px;">'
            '<div class="progress-bar bg-{}" style="width: {}%"></div>'
            '</div>'
            '</div>',
            label, format_number(current), format_number(limit), css_class, percentage
        )
    except (TypeError, ZeroDivisionError):
        return ""


@register.inclusion_tag('components/breadcrumb.html')
def breadcrumb(items):
    """Render breadcrumb navigation"""
    return {'items': items}


@register.inclusion_tag('components/pagination.html')
def pagination(page_obj):
    """Render pagination"""
    return {'page_obj': page_obj}


@register.simple_tag
def json_script(data, element_id):
    """Output data as JSON in a script tag"""
    try:
        json_data = json.dumps(data)
        return format_html(
            '<script id="{}" type="application/json">{}</script>',
            element_id, json_data
        )
    except (TypeError, ValueError):
        return ""


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary in template"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None


@register.simple_tag
def settings_value(name):
    """Get settings value"""
    return getattr(settings, name, None)


# backend/tasks.py
"""
Celery tasks for AfriMail Pro
Background processing tasks
"""
from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import timedelta
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """Clean up expired sessions"""
    try:
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        
        logger.info(f"Cleaned up {count} expired sessions")
        return f"Cleaned up {count} expired sessions"
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def update_engagement_scores():
    """Update contact engagement scores"""
    try:
        from backend.models import Contact
        
        contacts = Contact.objects.filter(is_subscribed=True)
        updated_count = 0
        
        for contact in contacts:
            contact.calculate_engagement_score()
            updated_count += 1
        
        logger.info(f"Updated engagement scores for {updated_count} contacts")
        return f"Updated {updated_count} contact engagement scores"
    except Exception as e:
        logger.error(f"Error updating engagement scores: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def process_scheduled_campaigns():
    """Process scheduled campaigns that are ready to send"""
    try:
        from backend.models import Campaign
        from backend.services.campaign_service import CampaignService
        
        # Get campaigns scheduled for now or earlier
        scheduled_campaigns = Campaign.objects.filter(
            status='SCHEDULED',
            scheduled_at__lte=timezone.now()
        )
        
        processed_count = 0
        
        for campaign in scheduled_campaigns:
            try:
                campaign_service = CampaignService(campaign.user)
                campaign_service.send_campaign(campaign.id)
                processed_count += 1
                logger.info(f"Processed scheduled campaign: {campaign.name}")
            except Exception as e:
                logger.error(f"Error processing campaign {campaign.name}: {str(e)}")
                campaign.status = 'FAILED'
                campaign.save()
        
        return f"Processed {processed_count} scheduled campaigns"
    except Exception as e:
        logger.error(f"Error processing scheduled campaigns: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_analytics_snapshots():
    """Generate daily analytics snapshots"""
    try:
        from backend.models import AnalyticsSnapshot, PlatformAnalytics
        from backend.services.analytics_service import PlatformAnalyticsService
        
        date = timezone.now().date()
        
        # Generate platform analytics
        platform_service = PlatformAnalyticsService()
        platform_analytics = platform_service.generate_daily_snapshot(date)
        
        # Generate user analytics snapshots
        users = User.objects.filter(is_active=True)
        snapshot_count = 0
        
        for user in users:
            try:
                # Create daily snapshot for user
                AnalyticsSnapshot.objects.get_or_create(
                    user=user,
                    snapshot_type='DAILY',
                    snapshot_date=date,
                    defaults={
                        'campaigns_sent': user.campaigns.filter(
                            sent_at__date=date
                        ).count(),
                        'emails_sent': user.campaigns.filter(
                            sent_at__date=date
                        ).aggregate(total=models.Sum('sent_count'))['total'] or 0,
                        'total_contacts': user.contacts.filter(is_subscribed=True).count(),
                        'new_contacts': user.contacts.filter(
                            created_at__date=date
                        ).count(),
                    }
                )
                snapshot_count += 1
            except Exception as e:
                logger.error(f"Error creating snapshot for user {user.email}: {str(e)}")
        
        logger.info(f"Generated {snapshot_count} analytics snapshots")
        return f"Generated {snapshot_count} analytics snapshots"
    except Exception as e:
        logger.error(f"Error generating analytics snapshots: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_weekly_reports():
    """Send weekly reports to users"""
    try:
        from backend.services.report_service import ReportService
        
        users = User.objects.filter(
            is_active=True,
            email_notifications=True,
            profile__weekly_report=True
        )
        
        sent_count = 0
        
        for user in users:
            try:
                report_service = ReportService(user)
                report_service.send_weekly_report()
                sent_count += 1
                logger.info(f"Sent weekly report to {user.email}")
            except Exception as e:
                logger.error(f"Error sending weekly report to {user.email}: {str(e)}")
        
        return f"Sent weekly reports to {sent_count} users"
    except Exception as e:
        logger.error(f"Error sending weekly reports: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def check_subscription_expirations():
    """Check for upcoming subscription expirations and send notifications"""
    try:
        # Get subscriptions expiring in 3 days
        warning_date = timezone.now().date() + timedelta(days=3)
        expiring_soon = User.objects.filter(
            subscription_active=True,
            subscription_ends__date=warning_date
        )
        
        # Get expired subscriptions
        expired_subscriptions = User.objects.filter(
            subscription_active=True,
            subscription_ends__lt=timezone.now()
        )
        
        notification_count = 0
        
        # Send warning notifications
        for user in expiring_soon:
            try:
                from backend.services.notification_service import NotificationService
                notification_service = NotificationService()
                notification_service.send_subscription_expiry_warning(user)
                notification_count += 1
            except Exception as e:
                logger.error(f"Error sending expiry warning to {user.email}: {str(e)}")
        
        # Deactivate expired subscriptions
        expired_count = expired_subscriptions.count()
        expired_subscriptions.update(subscription_active=False)
        
        logger.info(f"Sent {notification_count} expiry warnings, deactivated {expired_count} expired subscriptions")
        return f"Processed {notification_count + expired_count} subscription updates"
    except Exception as e:
        logger.error(f"Error checking subscription expirations: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_logs():
    """Clean up old log entries"""
    try:
        from backend.models import UserActivity, EmailLog
        
        # Delete user activities older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        old_activities = UserActivity.objects.filter(created_at__lt=cutoff_date)
        activity_count = old_activities.count()
        old_activities.delete()
        
        # Delete email logs older than 180 days
        cutoff_date = timezone.now() - timedelta(days=180)
        old_email_logs = EmailLog.objects.filter(queued_at__lt=cutoff_date)
        email_log_count = old_email_logs.count()
        old_email_logs.delete()
        
        logger.info(f"Cleaned up {activity_count} old activities and {email_log_count} old email logs")
        return f"Cleaned up {activity_count + email_log_count} old log entries"
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def backup_database():
    """Create database backup"""
    try:
        # This would integrate with your backup solution
        # For now, just call Django's dumpdata command
        call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                    '--exclude=contenttypes', '--exclude=auth.permission',
                    output=f'backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        logger.info("Database backup completed")
        return "Database backup completed"
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def process_contact_imports():
    """Process pending contact imports"""
    try:
        from backend.models import ContactImport
        from backend.services.import_service import ContactImportService
        
        pending_imports = ContactImport.objects.filter(status='PENDING')
        processed_count = 0
        
        for import_obj in pending_imports:
            try:
                import_service = ContactImportService(import_obj.user)
                import_service.process_import(import_obj.id)
                processed_count += 1
                logger.info(f"Processed contact import: {import_obj.file_name}")
            except Exception as e:
                logger.error(f"Error processing import {import_obj.file_name}: {str(e)}")
                import_obj.status = 'FAILED'
                import_obj.error_message = str(e)
                import_obj.save()
        
        return f"Processed {processed_count} contact imports"
    except Exception as e:
        logger.error(f"Error processing contact imports: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_campaign_email(campaign_id, contact_id):
    """Send individual campaign email (for queue processing)"""
    try:
        from backend.models import Campaign, Contact
        from backend.services.email_service import EmailService
        
        campaign = Campaign.objects.get(id=campaign_id)
        contact = Contact.objects.get(id=contact_id)
        
        email_service = EmailService(campaign.user)
        
        # Personalize content
        personalized_content = email_service.personalize_content(
            campaign.html_content, contact
        )
        personalized_subject = email_service.personalize_content(
            campaign.subject, contact
        )
        
        # Send email
        result = email_service.send_single_email(
            recipient_email=contact.email,
            subject=personalized_subject,
            html_content=personalized_content,
            text_content=campaign.text_content,
            domain_config=campaign.domain_config,
            contact=contact,
            campaign=campaign
        )
        
        if result['success']:
            logger.info(f"Campaign email sent to {contact.email}")
            return f"Email sent to {contact.email}"
        else:
            logger.error(f"Failed to send campaign email to {contact.email}: {result['error']}")
            return f"Failed to send to {contact.email}: {result['error']}"
            
    except Exception as e:
        logger.error(f"Error sending campaign email: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def calculate_campaign_metrics(campaign_id):
    """Calculate campaign performance metrics"""
    try:
        from backend.models import Campaign
        
        campaign = Campaign.objects.get(id=campaign_id)
        campaign.calculate_metrics()
        
        logger.info(f"Calculated metrics for campaign: {campaign.name}")
        return f"Calculated metrics for campaign: {campaign.name}"
    except Exception as e:
        logger.error(f"Error calculating campaign metrics: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_test_email_task(user_id, test_email, subject, html_content, text_content=None):
    """Send test email asynchronously"""
    try:
        from backend.services.email_service import EmailService
        
        user = User.objects.get(id=user_id)
        email_service = EmailService(user)
        
        result = email_service.send_test_email(
            test_email=test_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if result['success']:
            logger.info(f"Test email sent to {test_email}")
            return f"Test email sent to {test_email}"
        else:
            logger.error(f"Failed to send test email: {result['error']}")
            return f"Failed to send test email: {result['error']}"
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return f"Error: {str(e)}"