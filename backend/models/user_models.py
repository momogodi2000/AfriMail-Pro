"""
User Models for AfriMail Pro
Simplified 2-Actor System: Super Administrator and Marketing Manager
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets
import base64

class CustomUser(AbstractUser):
    """Enhanced User Model for AfriMail Pro with Simplified Actor System"""
    
    USER_ROLES = [
        ('SUPER_ADMIN', 'Super Administrator'),
        ('MARKETING_MANAGER', 'Marketing Manager'),
    ]
    
    SUBSCRIPTION_PLANS = [
        ('STARTER', 'Starter Plan'),
        ('PROFESSIONAL', 'Professional Plan'),
        ('ENTERPRISE', 'Enterprise Plan'),
    ]
    
    COUNTRIES = [
        ('CM', 'Cameroon'),
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),
        ('CI', 'Côte d\'Ivoire'),
        ('SN', 'Senegal'),
        ('GA', 'Gabon'),
        ('TD', 'Chad'),
        ('CF', 'Central African Republic'),
        ('ML', 'Mali'),
        ('BF', 'Burkina Faso'),
        ('TG', 'Togo'),
        ('BJ', 'Benin'),
        ('NE', 'Niger'),
        ('GN', 'Guinea'),
        ('MG', 'Madagascar'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Company Information
    company = models.CharField(max_length=100)
    company_website = models.URLField(blank=True, null=True)
    company_size = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-5', '1-5 employees'),
        ('6-20', '6-20 employees'),
        ('21-50', '21-50 employees'),
        ('51-200', '51-200 employees'),
        ('200+', '200+ employees'),
    ])
    industry = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('RETAIL', 'Retail & E-commerce'),
        ('RESTAURANT', 'Restaurant & Food'),
        ('HEALTHCARE', 'Healthcare'),
        ('EDUCATION', 'Education'),
        ('TECHNOLOGY', 'Technology'),
        ('FINANCE', 'Finance & Banking'),
        ('REAL_ESTATE', 'Real Estate'),
        ('AGRICULTURE', 'Agriculture'),
        ('TOURISM', 'Tourism & Travel'),
        ('MANUFACTURING', 'Manufacturing'),
        ('SERVICES', 'Professional Services'),
        ('OTHER', 'Other'),
    ])
    
    # Location
    country = models.CharField(max_length=2, choices=COUNTRIES, default='CM')
    city = models.CharField(max_length=50, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Africa/Douala')
    
    # User Role and Permissions (Simplified to 2 roles)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='MARKETING_MANAGER')
    
    # Subscription Information
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='STARTER')
    subscription_active = models.BooleanField(default=True)
    trial_started = models.DateTimeField(null=True, blank=True)
    trial_ends = models.DateTimeField(null=True, blank=True)
    subscription_started = models.DateTimeField(null=True, blank=True)
    subscription_ends = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    # Account Status
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_trial_user = models.BooleanField(default=True)
    
    # Onboarding
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.IntegerField(default=1)
    onboarding_data = models.JSONField(default=dict, blank=True)
    
    # Usage Statistics
    total_emails_sent = models.IntegerField(default=0)
    total_campaigns = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)
    last_campaign_sent = models.DateTimeField(null=True, blank=True)
    
    # Billing Information
    billing_name = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=5, default='en', choices=[
        ('en', 'English'),
        ('fr', 'Français'),
    ])
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_notifications = models.BooleanField(default=True)
    
    # Dashboard Preferences
    dashboard_theme = models.CharField(max_length=10, default='light', choices=[
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'Auto (System)'),
    ])
    dashboard_layout = models.CharField(max_length=20, default='default', choices=[
        ('default', 'Default Layout'),
        ('compact', 'Compact Layout'),
        ('expanded', 'Expanded Layout'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'company']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['country']),
            models.Index(fields=['is_active', 'subscription_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.company})"
    
    def get_absolute_url(self):
        return reverse('dashboard')
    
    @property
    def is_super_admin(self):
        """Check if user is Super Administrator"""
        return self.role == 'SUPER_ADMIN'
    
    @property
    def is_marketing_manager(self):
        """Check if user is Marketing Manager"""
        return self.role == 'MARKETING_MANAGER'
    
    @property
    def is_trial_active(self):
        """Check if trial period is still active"""
        if self.trial_ends:
            return timezone.now() < self.trial_ends
        return False
    
    @property
    def trial_days_remaining(self):
        """Get remaining trial days"""
        if self.trial_ends and self.is_trial_active:
            return (self.trial_ends - timezone.now()).days
        return 0
    
    @property
    def subscription_days_remaining(self):
        """Get remaining subscription days"""
        if self.subscription_ends and self.subscription_active:
            return (self.subscription_ends - timezone.now()).days
        return 0
    
    @property
    def display_name(self):
        """Get display name for UI"""
        full_name = self.get_full_name()
        return full_name if full_name.strip() else self.email
    
    def start_trial(self, trial_days=14):
        """Start user trial period"""
        self.trial_started = timezone.now()
        self.trial_ends = timezone.now() + timedelta(days=trial_days)
        self.is_trial_user = True
        self.subscription_active = True
        self.save()
    
    def activate_subscription(self, plan, duration_months=1):
        """Activate paid subscription"""
        self.subscription_plan = plan
        self.subscription_started = timezone.now()
        self.subscription_ends = timezone.now() + timedelta(days=duration_months * 30)
        self.subscription_active = True
        self.is_trial_user = False
        self.save()
    
    def get_plan_limits(self):
        """Get user plan limitations"""
        from django.conf import settings
        limits = settings.AFRIMAIL_SETTINGS
        
        return {
            'max_contacts': limits['MAX_CONTACTS_PER_USER'].get(self.subscription_plan, 2500),
            'max_emails_per_month': limits['MAX_EMAILS_PER_MONTH'].get(self.subscription_plan, 25000),
            'features': limits['FEATURES'].get(self.subscription_plan, []),
        }
    
    def can_send_emails(self):
        """Check if user can send emails"""
        if not self.subscription_active:
            return False, "Subscription not active"
        
        if self.is_trial_user and not self.is_trial_active:
            return False, "Trial period expired"
            
        # Check monthly email limit
        usage = self.get_monthly_email_usage()
        limits = self.get_plan_limits()
        
        if usage >= limits['max_emails_per_month']:
            return False, "Monthly email limit reached"
            
        return True, "Can send emails"
    
    def get_monthly_email_usage(self):
        """Get current month email usage"""
        from datetime import datetime
        from .campaign_models import Campaign
        
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage = Campaign.objects.filter(
            user=self,
            sent_at__gte=current_month_start,
            status='COMPLETED'
        ).aggregate(
            total_sent=models.Sum('sent_count')
        )
        
        return usage['total_sent'] or 0
    
    def generate_verification_token(self):
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        self.save()
        return self.verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if self.verification_token == token:
            self.is_verified = True
            self.verification_token = None
            self.save()
            return True
        return False


class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Avatar and Branding
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Additional Company Info
    company_description = models.TextField(blank=True, null=True)
    company_address = models.TextField(blank=True, null=True)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    company_founded_year = models.IntegerField(blank=True, null=True)
    company_employees_count = models.IntegerField(blank=True, null=True)
    
    # Contact Information
    secondary_email = models.EmailField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    facebook_page = models.URLField(blank=True, null=True)
    twitter_handle = models.CharField(max_length=50, blank=True, null=True)
    
    # Business Information
    business_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('B2B', 'Business to Business'),
        ('B2C', 'Business to Consumer'),
        ('B2B2C', 'Business to Business to Consumer'),
        ('MARKETPLACE', 'Marketplace'),
        ('NON_PROFIT', 'Non-Profit'),
        ('GOVERNMENT', 'Government'),
    ])
    annual_revenue = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('0-50K', '0 - 50,000 FCFA'),
        ('50K-500K', '50,000 - 500,000 FCFA'),
        ('500K-5M', '500,000 - 5,000,000 FCFA'),
        ('5M-50M', '5,000,000 - 50,000,000 FCFA'),
        ('50M+', '50,000,000+ FCFA'),
    ])
    target_audience = models.TextField(blank=True, null=True)
    marketing_goals = models.JSONField(default=list, blank=True)
    
    # Marketing Preferences
    default_sender_name = models.CharField(max_length=100, blank=True, null=True)
    default_sender_email = models.EmailField(blank=True, null=True)
    default_reply_to = models.EmailField(blank=True, null=True)
    email_signature = models.TextField(blank=True, null=True)
    
    # Tracking and Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True, null=True)
    
    # API Settings
    api_key = models.CharField(max_length=100, blank=True, null=True, unique=True)
    api_active = models.BooleanField(default=False)
    api_requests_count = models.IntegerField(default=0)
    api_last_used = models.DateTimeField(null=True, blank=True)
    
    # Notification Preferences
    daily_summary = models.BooleanField(default=True)
    weekly_report = models.BooleanField(default=True)
    campaign_alerts = models.BooleanField(default=True)
    system_updates = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"
    
    def generate_api_key(self):
        """Generate new API key"""
        self.api_key = f"afrimail_{secrets.token_urlsafe(32)}"
        self.api_active = True
        self.save()
        return self.api_key
    
    def get_avatar_url(self):
        """Get avatar URL or default"""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'
    
    def get_company_logo_url(self):
        """Get company logo URL or default"""
        if self.company_logo:
            return self.company_logo.url
        return '/static/images/default-company-logo.png'


class UserActivity(models.Model):
    """Track user activities for analytics and security"""
    
    ACTIVITY_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('PROFILE_UPDATE', 'Profile Updated'),
        ('CAMPAIGN_CREATED', 'Campaign Created'),
        ('CAMPAIGN_SENT', 'Campaign Sent'),
        ('CONTACT_IMPORTED', 'Contacts Imported'),
        ('TEMPLATE_CREATED', 'Template Created'),
        ('SETTINGS_UPDATED', 'Settings Updated'),
        ('API_ACCESS', 'API Access'),
        ('SUBSCRIPTION_CHANGED', 'Subscription Changed'),
        ('PAYMENT_MADE', 'Payment Made'),
        ('FEATURE_USED', 'Feature Used'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Geographic information
    country = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    
    # Session information
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description=None, request=None, metadata=None):
        """Log user activity"""
        activity_data = {
            'user': user,
            'activity_type': activity_type,
            'description': description,
            'metadata': metadata or {}
        }
        
        if request:
            activity_data.update({
                'ip_address': cls.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_key': request.session.session_key,
            })
        
        return cls.objects.create(**activity_data)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserSubscription(models.Model):
    """Track user subscription history and payments"""
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CASH', 'Cash Payment'),
        ('FREE_TRIAL', 'Free Trial'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=CustomUser.SUBSCRIPTION_PLANS)
    
    # Subscription period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    
    # Payment information
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')  # FCFA
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Mobile Money details
    mobile_money_provider = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('MTN', 'MTN Mobile Money'),
        ('ORANGE', 'Orange Money'),
        ('AIRTEL', 'Airtel Money'),
        ('MOOV', 'Moov Money'),
    ])
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Invoice information
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    invoice_generated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['plan']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.start_date.date()} to {self.end_date.date()})"
    
    @property
    def is_expired(self):
        """Check if subscription is expired"""
        return timezone.now() > self.end_date
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.invoice_number = f"AFP-{timestamp}-{self.user.id.hex[:8].upper()}"
        self.save()
        return self.invoice_number