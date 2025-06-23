"""
Contact Models for AfriMail Pro
Comprehensive contact management system with advanced segmentation
"""
from django.db import models
from django.core.validators import validate_email
from django.utils import timezone
from taggit.managers import TaggableManager
from .user_models import CustomUser
import uuid
import re
import json

class ContactList(models.Model):
    """Contact lists/segments for organizing contacts"""
    
    LIST_TYPES = [
        ('MANUAL', 'Manual List'),
        ('DYNAMIC', 'Dynamic Segment'),
        ('IMPORTED', 'Imported List'),
        ('BEHAVIORAL', 'Behavioral Segment'),
        ('GEOGRAPHIC', 'Geographic Segment'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contact_lists')
    
    # List Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='MANUAL')
    
    # Dynamic Segment Conditions
    conditions = models.JSONField(default=dict, blank=True, help_text="Conditions for dynamic segments")
    
    # Statistics
    contact_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    last_calculated = models.DateTimeField(null=True, blank=True)
    
    # List Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Engagement metrics
    avg_engagement_score = models.FloatField(default=0.0)
    last_campaign_sent = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_lists'
        verbose_name = 'Contact List'
        verbose_name_plural = 'Contact Lists'
        unique_together = ['user', 'name']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['list_type']),
            models.Index(fields=['contact_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.contact_count} contacts)"
    
    def update_contact_count(self):
        """Update contact count for this list"""
        if self.list_type == 'DYNAMIC':
            # Calculate dynamic segment count
            self.contact_count = self.calculate_dynamic_count()
        else:
            # Count manual contacts
            self.contact_count = self.contacts.filter(is_subscribed=True).count()
        
        self.last_calculated = timezone.now()
        self.save(update_fields=['contact_count', 'last_calculated', 'updated_at'])
    
    def calculate_dynamic_count(self):
        """Calculate contact count for dynamic segments"""
        from .services.segmentation_service import SegmentationService
        service = SegmentationService(self.user)
        return service.calculate_segment_size(self.conditions)
    
    def get_contacts(self):
        """Get contacts in this list"""
        if self.list_type == 'DYNAMIC':
            from .services.segmentation_service import SegmentationService
            service = SegmentationService(self.user)
            return service.get_segment_contacts(self.conditions)
        else:
            return self.contacts.filter(is_subscribed=True)
    
    def get_engagement_stats(self):
        """Get engagement statistics for this list"""
        contacts = self.get_contacts()
        if not contacts.exists():
            return {'avg_score': 0, 'high_engaged': 0, 'low_engaged': 0}
        
        high_engaged = contacts.filter(engagement_score__gte=70).count()
        low_engaged = contacts.filter(engagement_score__lt=30).count()
        avg_score = contacts.aggregate(avg=models.Avg('engagement_score'))['avg'] or 0
        
        return {
            'avg_score': round(avg_score, 2),
            'high_engaged': high_engaged,
            'low_engaged': low_engaged,
            'total': contacts.count()
        }


class Contact(models.Model):
    """Individual contact/subscriber with comprehensive information"""
    
    SUBSCRIPTION_STATUS = [
        ('SUBSCRIBED', 'Subscribed'),
        ('UNSUBSCRIBED', 'Unsubscribed'),
        ('BOUNCED', 'Bounced'),
        ('COMPLAINED', 'Complained'),
        ('PENDING', 'Pending Confirmation'),
        ('BLACKLISTED', 'Blacklisted'),
    ]
    
    SUBSCRIPTION_SOURCES = [
        ('MANUAL', 'Manual Entry'),
        ('IMPORT', 'File Import'),
        ('FORM', 'Signup Form'),
        ('API', 'API'),
        ('CAMPAIGN', 'Campaign Signup'),
        ('REFERRAL', 'Referral'),
        ('WEBSITE', 'Website'),
        ('SOCIAL_MEDIA', 'Social Media'),
        ('EVENT', 'Event'),
        ('OTHER', 'Other'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    LEAD_STATUS = [
        ('COLD', 'Cold Lead'),
        ('WARM', 'Warm Lead'),
        ('HOT', 'Hot Lead'),
        ('CUSTOMER', 'Customer'),
        ('ADVOCATE', 'Advocate'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contacts')
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional Personal Information
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    age_group = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('18-24', '18-24'),
        ('25-34', '25-34'),
        ('35-44', '35-44'),
        ('45-54', '45-54'),
        ('55-64', '55-64'),
        ('65+', '65+'),
    ])
    
    # Company Information
    company = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    company_size = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501+', '501+ employees'),
    ])
    department = models.CharField(max_length=50, blank=True, null=True)
    
    # Location Information
    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Africa/Douala')
    language = models.CharField(max_length=5, default='en', choices=[
        ('en', 'English'),
        ('fr', 'Français'),
    ])
    
    # Subscription Information
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='SUBSCRIBED')
    subscription_source = models.CharField(max_length=20, choices=SUBSCRIPTION_SOURCES, default='MANUAL')
    subscription_date = models.DateTimeField(auto_now_add=True)
    unsubscribe_date = models.DateTimeField(null=True, blank=True)
    unsubscribe_reason = models.TextField(blank=True, null=True)
    
    # Lead Information
    lead_status = models.CharField(max_length=20, choices=LEAD_STATUS, default='COLD')
    lead_score = models.IntegerField(default=0)
    customer_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Engagement Metrics
    engagement_score = models.FloatField(default=0.0, help_text="0-100 engagement score")
    last_engagement = models.DateTimeField(null=True, blank=True)
    total_opens = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_purchases = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Email Preferences
    preferred_send_time = models.TimeField(null=True, blank=True)
    preferred_frequency = models.CharField(max_length=20, default='weekly', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ])
    email_format = models.CharField(max_length=10, default='html', choices=[
        ('html', 'HTML'),
        ('text', 'Text'),
        ('both', 'Both'),
    ])
    
    # Behavioral Data
    interests = models.JSONField(default=list, blank=True)
    purchase_history = models.JSONField(default=list, blank=True)
    website_activity = models.JSONField(default=list, blank=True)
    social_profiles = models.JSONField(default=dict, blank=True)
    
    # Custom Fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Lists and Tags
    contact_lists = models.ManyToManyField(ContactList, related_name='contacts', blank=True)
    tags = TaggableManager(blank=True)
    
    # Tracking
    source_url = models.URLField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    utm_content = models.CharField(max_length=100, blank=True, null=True)
    utm_term = models.CharField(max_length=100, blank=True, null=True)
    
    # Device and Browser Information
    last_device_type = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ])
    last_browser = models.CharField(max_length=50, blank=True, null=True)
    last_os = models.CharField(max_length=50, blank=True, null=True)
    
    # Status Flags
    is_subscribed = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_vip = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_test_contact = models.BooleanField(default=False)
    
    # Quality Score
    data_quality_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'contacts'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        unique_together = ['user', 'email']
        ordering = ['-engagement_score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'email']),
            models.Index(fields=['user', 'subscription_status']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['last_engagement']),
            models.Index(fields=['subscription_date']),
            models.Index(fields=['lead_status']),
            models.Index(fields=['country', 'city']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Get contact's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0].title()
    
    def get_display_name(self):
        """Get display name for templates"""
        return self.get_full_name()
    
    @property
    def is_engaged(self):
        """Check if contact is engaged (opened/clicked recently)"""
        if self.last_engagement:
            days_since_engagement = (timezone.now() - self.last_engagement).days
            return days_since_engagement <= 30
        return False
    
    @property
    def engagement_level(self):
        """Get engagement level category"""
        if self.engagement_score >= 70:
            return 'HIGH'
        elif self.engagement_score >= 40:
            return 'MEDIUM'
        elif self.engagement_score >= 10:
            return 'LOW'
        else:
            return 'INACTIVE'
    
    @property
    def full_location(self):
        """Get full location string"""
        location_parts = [part for part in [self.city, self.state, self.country] if part]
        return ', '.join(location_parts)
    
    def calculate_engagement_score(self):
        """Calculate and update engagement score"""
        from .services.engagement_service import EngagementScorer
        scorer = EngagementScorer()
        self.engagement_score = scorer.calculate_score(self)
        self.save(update_fields=['engagement_score'])
        return self.engagement_score
    
    def calculate_data_quality_score(self):
        """Calculate data quality score based on completeness"""
        score = 0
        total_fields = 20  # Total weighted fields
        
        # Email is mandatory (already validated)
        score += 3
        
        # Name fields
        if self.first_name:
            score += 2
        if self.last_name:
            score += 2
        
        # Contact information
        if self.phone:
            score += 2
        if self.company:
            score += 1
        if self.job_title:
            score += 1
        
        # Location
        if self.country:
            score += 1
        if self.city:
            score += 1
        
        # Engagement data
        if self.total_opens > 0:
            score += 2
        if self.total_clicks > 0:
            score += 2
        if self.last_engagement:
            score += 1
        
        # Additional data
        if self.interests:
            score += 1
        if self.custom_fields:
            score += 1
        
        self.data_quality_score = (score / total_fields) * 100
        self.save(update_fields=['data_quality_score'])
        return self.data_quality_score
    
    def add_interaction(self, interaction_type, metadata=None):
        """Add contact interaction"""
        ContactInteraction.objects.create(
            contact=self,
            interaction_type=interaction_type,
            metadata=metadata or {},
            timestamp=timezone.now()
        )
        
        # Update engagement
        self.last_engagement = timezone.now()
        self.last_activity = timezone.now()
        self.save(update_fields=['last_engagement', 'last_activity'])
    
    def unsubscribe(self, reason=None):
        """Unsubscribe contact"""
        self.is_subscribed = False
        self.subscription_status = 'UNSUBSCRIBED'
        self.unsubscribe_date = timezone.now()
        
        if reason:
            self.unsubscribe_reason = reason
        
        self.save()
        
        # Log the unsubscribe event
        self.add_interaction('UNSUBSCRIBE', {'reason': reason})
    
    def resubscribe(self):
        """Resubscribe contact"""
        self.is_subscribed = True
        self.subscription_status = 'SUBSCRIBED'
        self.unsubscribe_date = None
        self.unsubscribe_reason = None
        self.save()
        
        # Log the resubscribe event
        self.add_interaction('RESUBSCRIBE')
    
    def get_personalization_data(self):
        """Get data for email personalization"""
        data = {
            'first_name': self.first_name or 'Valued Customer',
            'last_name': self.last_name or '',
            'full_name': self.get_full_name(),
            'email': self.email,
            'company': self.company or '',
            'job_title': self.job_title or '',
            'phone': self.phone or '',
            'city': self.city or '',
            'country': self.country or '',
            'industry': self.industry or '',
        }
        
        # Add custom fields
        data.update(self.custom_fields)
        
        return data
    
    def merge_with(self, other_contact):
        """Merge this contact with another contact"""
        if other_contact.user != self.user:
            raise ValueError("Cannot merge contacts from different users")
        
        # Merge fields (keep non-empty values, prefer this contact)
        fields_to_merge = [
            'first_name', 'last_name', 'phone', 'company', 'job_title',
            'country', 'city', 'date_of_birth', 'gender'
        ]
        
        for field in fields_to_merge:
            if not getattr(self, field) and getattr(other_contact, field):
                setattr(self, field, getattr(other_contact, field))
        
        # Merge engagement metrics (sum them up)
        self.total_opens += other_contact.total_opens
        self.total_clicks += other_contact.total_clicks
        self.total_purchases += other_contact.total_purchases
        self.total_revenue += other_contact.total_revenue
        
        # Merge custom fields
        merged_custom_fields = {**other_contact.custom_fields, **self.custom_fields}
        self.custom_fields = merged_custom_fields
        
        # Merge interests
        merged_interests = list(set(self.interests + other_contact.interests))
        self.interests = merged_interests
        
        # Merge tags
        other_tags = list(other_contact.tags.names())
        for tag in other_tags:
            self.tags.add(tag)
        
        # Save changes
        self.save()
        
        # Transfer interactions
        ContactInteraction.objects.filter(contact=other_contact).update(contact=self)
        
        # Delete the other contact
        other_contact.delete()
        
        # Recalculate scores
        self.calculate_engagement_score()
        self.calculate_data_quality_score()


class ContactInteraction(models.Model):
    """Track contact interactions and behaviors"""
    
    INTERACTION_TYPES = [
        ('EMAIL_SENT', 'Email Sent'),
        ('EMAIL_OPENED', 'Email Opened'),
        ('EMAIL_CLICKED', 'Email Clicked'),
        ('EMAIL_BOUNCED', 'Email Bounced'),
        ('EMAIL_COMPLAINED', 'Email Complained'),
        ('WEBSITE_VISIT', 'Website Visit'),
        ('FORM_SUBMISSION', 'Form Submission'),
        ('PURCHASE', 'Purchase Made'),
        ('DOWNLOAD', 'File Download'),
        ('SOCIAL_SHARE', 'Social Share'),
        ('REFERRAL', 'Referral Made'),
        ('SURVEY_RESPONSE', 'Survey Response'),
        ('UNSUBSCRIBE', 'Unsubscribed'),
        ('RESUBSCRIBE', 'Resubscribed'),
        ('PROFILE_UPDATE', 'Profile Updated'),
        ('CUSTOMER_SERVICE', 'Customer Service'),
        ('EVENT_ATTENDANCE', 'Event Attendance'),
        ('WEBINAR_ATTENDANCE', 'Webinar Attendance'),
    ]
    
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Interaction Details
    campaign = models.ForeignKey('Campaign', on_delete=models.SET_NULL, null=True, blank=True)
    email_log = models.ForeignKey('EmailLog', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=20, blank=True, null=True)
    browser = models.CharField(max_length=50, blank=True, null=True)
    operating_system = models.CharField(max_length=50, blank=True, null=True)
    
    # Location Information
    country = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monetary value if applicable")
    
    class Meta:
        db_table = 'contact_interactions'
        verbose_name = 'Contact Interaction'
        verbose_name_plural = 'Contact Interactions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['contact', 'interaction_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['campaign']),
            models.Index(fields=['contact', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.contact.email} - {self.get_interaction_type_display()}"


class ContactImport(models.Model):
    """Track contact import operations"""
    
    IMPORT_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    FILE_FORMATS = [
        ('CSV', 'CSV'),
        ('XLSX', 'Excel (XLSX)'),
        ('XLS', 'Excel (XLS)'),
        ('VCF', 'vCard'),
        ('JSON', 'JSON'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contact_imports')
    
    # Import Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    file_format = models.CharField(max_length=10, choices=FILE_FORMATS)
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_file = models.FileField(upload_to='contact_imports/', null=True, blank=True)
    
    # Import Configuration
    column_mapping = models.JSONField(default=dict, help_text="Mapping of file columns to contact fields")
    import_settings = models.JSONField(default=dict, help_text="Import configuration settings")
    target_lists = models.ManyToManyField(ContactList, blank=True, help_text="Lists to add imported contacts to")
    
    # Import Status
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default='PENDING')
    
    # Import Statistics
    total_rows = models.IntegerField(default=0)
    valid_contacts = models.IntegerField(default=0)
    invalid_contacts = models.IntegerField(default=0)
    duplicate_contacts = models.IntegerField(default=0)
    imported_contacts = models.IntegerField(default=0)
    skipped_contacts = models.IntegerField(default=0)
    
    # Error Tracking
    error_message = models.TextField(blank=True, null=True)
    error_details = models.JSONField(default=list, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Processing Information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    
    # Import Options
    allow_duplicates = models.BooleanField(default=False)
    update_existing = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_imports'
        verbose_name = 'Contact Import'
        verbose_name_plural = 'Contact Imports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.get_status_display()})"
    
    @property
    def success_rate(self):
        """Calculate import success rate"""
        if self.total_rows > 0:
            return (self.imported_contacts / self.total_rows) * 100
        return 0
    
    def start_processing(self):
        """Mark import as started"""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save()
    
    def complete_processing(self, imported_count):
        """Mark import as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.imported_contacts = imported_count
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        self.save()
    
    def fail_processing(self, error_message):
        """Mark import as failed"""
        self.status = 'FAILED'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class ContactCustomField(models.Model):
    """Custom field definitions for contacts"""
    
    FIELD_TYPES = [
        ('TEXT', 'Text'),
        ('NUMBER', 'Number'),
        ('EMAIL', 'Email'),
        ('URL', 'URL'),
        ('DATE', 'Date'),
        ('DATETIME', 'Date/Time'),
        ('BOOLEAN', 'Yes/No'),
        ('CHOICE', 'Multiple Choice'),
        ('TEXTAREA', 'Long Text'),
        ('PHONE', 'Phone Number'),
        ('CURRENCY', 'Currency'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='custom_fields')
    
    # Field Definition
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='TEXT')
    label = models.CharField(max_length=100, help_text="Display label for the field")
    description = models.TextField(blank=True, null=True)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    
    # Field Configuration
    is_required = models.BooleanField(default=False)
    is_searchable = models.BooleanField(default=True)
    is_visible_in_list = models.BooleanField(default=True)
    default_value = models.CharField(max_length=255, blank=True, null=True)
    choices = models.JSONField(default=list, blank=True, help_text="Options for choice fields")
    
    # Validation Rules
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    pattern = models.CharField(max_length=255, blank=True, null=True, help_text="Regex pattern for validation")
    
    # Display Settings
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_custom_fields'
        verbose_name = 'Contact Custom Field'
        verbose_name_plural = 'Contact Custom Fields'
        unique_together = ['user', 'name']
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"
    
    def validate_value(self, value):
        """Validate field value according to field type and rules"""
        if not value and self.is_required:
            raise ValueError(f"{self.label} is required")
        
        if not value:
            return True
        
        # Type-specific validation
        if self.field_type == 'EMAIL':
            validate_email(value)
        elif self.field_type == 'NUMBER':
            try:
                num_value = float(value)
                if self.min_value is not None and num_value < self.min_value:
                    raise ValueError(f"{self.label} must be at least {self.min_value}")
                if self.max_value is not None and num_value > self.max_value:
                    raise ValueError(f"{self.label} must be no more than {self.max_value}")
            except ValueError:
                raise ValueError(f"{self.label} must be a number")
        elif self.field_type == 'URL':
            if not value.startswith(('http://', 'https://')):
                raise ValueError(f"{self.label} must be a valid URL")
        elif self.field_type == 'CHOICE':
            if value not in self.choices:
                raise ValueError(f"{self.label} must be one of: {', '.join(self.choices)}")
        elif self.field_type == 'PHONE':
            # Basic phone validation for African numbers
            if not re.match(r'^\+?[1-9]\d{1,14}$', re.sub(r'\D', '', value)):
                raise ValueError(f"{self.label} must be a valid phone number")
        
        # Length validation
        if self.min_length and len(str(value)) < self.min_length:
            raise ValueError(f"{self.label} must be at least {self.min_length} characters")
        
        if self.max_length and len(str(value)) > self.max_length:
            raise ValueError(f"{self.label} must be no more than {self.max_length} characters")
        
        # Pattern validation
        if self.pattern:
            if not re.match(self.pattern, str(value)):
                raise ValueError(f"{self.label} format is invalid")
        
        return True
    
    def get_form_field(self):
        """Get Django form field for this custom field"""
        from django import forms
        
        field_kwargs = {
            'label': self.label,
            'required': self.is_required,
            'help_text': self.description,
        }
        
        if self.placeholder:
            field_kwargs['widget'] = forms.TextInput(attrs={'placeholder': self.placeholder})
        
        if self.field_type == 'TEXT':
            return forms.CharField(**field_kwargs)
        elif self.field_type == 'NUMBER':
            return forms.FloatField(**field_kwargs)
        elif self.field_type == 'EMAIL':
            return forms.EmailField(**field_kwargs)
        elif self.field_type == 'URL':
            return forms.URLField(**field_kwargs)
        elif self.field_type == 'DATE':
            return forms.DateField(**field_kwargs)
        elif self.field_type == 'DATETIME':
            return forms.DateTimeField(**field_kwargs)
        elif self.field_type == 'BOOLEAN':
            return forms.BooleanField(**field_kwargs)
        elif self.field_type == 'CHOICE':
            choices = [(choice, choice) for choice in self.choices]
            return forms.ChoiceField(choices=choices, **field_kwargs)
        elif self.field_type == 'TEXTAREA':
            field_kwargs['widget'] = forms.Textarea()
            return forms.CharField(**field_kwargs)
        else:
            return forms.CharField(**field_kwargs)