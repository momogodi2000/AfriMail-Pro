"""
Campaign Models for AfriMail Pro
Comprehensive campaign management with automation and analytics
"""
from django.db import models
from django.utils import timezone
from django.urls import reverse
from .user_models import CustomUser
from .contact_models import Contact, ContactList
from .email_models import EmailTemplate, EmailDomainConfig
import uuid
from datetime import timedelta
import json

class Campaign(models.Model):
    """Email marketing campaigns"""
    
    CAMPAIGN_TYPES = [
        ('NEWSLETTER', 'Newsletter'),
        ('PROMOTIONAL', 'Promotional'),
        ('TRANSACTIONAL', 'Transactional'),
        ('AUTOMATED', 'Automated'),
        ('A_B_TEST', 'A/B Test'),
        ('DRIP', 'Drip Campaign'),
        ('ANNOUNCEMENT', 'Announcement'),
        ('EVENT', 'Event Invitation'),
        ('FOLLOW_UP', 'Follow Up'),
        ('WELCOME', 'Welcome Campaign'),
        ('SURVEY', 'Survey'),
        ('SEASONAL', 'Seasonal'),
    ]
    
    CAMPAIGN_STATUS = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('SENDING', 'Sending'),
        ('SENT', 'Sent'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    SEND_TIME_OPTIMIZATION = [
        ('IMMEDIATE', 'Send Immediately'),
        ('SCHEDULED', 'Send at Specific Time'),
        ('OPTIMIZED', 'Send at Optimal Time'),
        ('TIME_ZONE', 'Send by Recipient Time Zone'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low Priority'),
        ('NORMAL', 'Normal Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='campaigns')
    
    # Campaign Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES, default='NEWSLETTER')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='NORMAL')
    
    # Email Content
    subject = models.CharField(max_length=200)
    preview_text = models.CharField(max_length=150, blank=True, null=True, help_text="Email preview text")
    html_content = models.TextField()
    text_content = models.TextField(blank=True, null=True)
    
    # Template and Design
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    is_template_customized = models.BooleanField(default=False)
    
    # Sending Configuration
    domain_config = models.ForeignKey(EmailDomainConfig, on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(max_length=100, blank=True, null=True)
    sender_email = models.EmailField(blank=True, null=True)
    reply_to_email = models.EmailField(blank=True, null=True)
    
    # Audience Targeting
    target_lists = models.ManyToManyField(ContactList, blank=True, related_name='campaigns')
    exclude_lists = models.ManyToManyField(ContactList, blank=True, related_name='excluded_campaigns')
    target_segments = models.JSONField(default=dict, blank=True, help_text="Dynamic segment conditions")
    
    # Scheduling
    send_time_option = models.CharField(max_length=20, choices=SEND_TIME_OPTIMIZATION, default='IMMEDIATE')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    time_zone = models.CharField(max_length=50, default='Africa/Douala')
    send_in_recipient_timezone = models.BooleanField(default=False)
    
    # A/B Testing
    is_ab_test = models.BooleanField(default=False)
    ab_test_percentage = models.IntegerField(default=50, help_text="Percentage for A/B test split")
    ab_winner_criteria = models.CharField(max_length=20, default='open_rate', choices=[
        ('open_rate', 'Open Rate'),
        ('click_rate', 'Click Rate'),
        ('conversion_rate', 'Conversion Rate'),
        ('revenue', 'Revenue Generated'),
    ])
    ab_test_duration = models.IntegerField(default=24, help_text="A/B test duration in hours")
    ab_winner_selected = models.BooleanField(default=False)
    ab_winner_variant = models.CharField(max_length=1, blank=True, null=True, choices=[('A', 'Variant A'), ('B', 'Variant B')])
    
    # Campaign Status
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='DRAFT')
    
    # Sending Statistics
    recipients_count = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    unique_opens_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    unique_clicks_count = models.IntegerField(default=0)
    unsubscribed_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    soft_bounced_count = models.IntegerField(default=0)
    hard_bounced_count = models.IntegerField(default=0)
    complained_count = models.IntegerField(default=0)
    
    # Performance Metrics
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    click_to_open_rate = models.FloatField(default=0.0)
    unsubscribe_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    delivery_rate = models.FloatField(default=0.0)
    
    # Revenue Tracking
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    conversion_count = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Engagement Metrics
    total_engagement_time = models.IntegerField(default=0, help_text="Total engagement time in seconds")
    social_shares = models.IntegerField(default=0)
    forwards = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Settings
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    google_analytics_campaign = models.CharField(max_length=100, blank=True, null=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, default='email')
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    
    # Personalization Settings
    personalization_level = models.CharField(max_length=20, default='basic', choices=[
        ('none', 'No Personalization'),
        ('basic', 'Basic (Name, Company)'),
        ('advanced', 'Advanced (Behavior, Preferences)'),
        ('ai_powered', 'AI-Powered Personalization'),
    ])
    
    # Budget and Cost Tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        db_table = 'campaigns'
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['campaign_type']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        return reverse('campaign_detail', kwargs={'pk': self.pk})
    
    @property
    def is_sent(self):
        return self.status in ['SENT', 'COMPLETED']
    
    @property
    def can_edit(self):
        return self.status in ['DRAFT', 'SCHEDULED']
    
    @property
    def can_send(self):
        return self.status == 'DRAFT' and self.html_content and self.subject
    
    @property
    def can_duplicate(self):
        return True
    
    @property
    def can_delete(self):
        return self.status in ['DRAFT', 'FAILED', 'CANCELLED']
    
    @property
    def performance_score(self):
        """Calculate overall performance score (0-100)"""
        if not self.sent_count:
            return 0
        
        # Weighted scoring
        open_score = (self.open_rate / 100) * 40  # 40% weight
        click_score = (self.click_rate / 100) * 30  # 30% weight
        delivery_score = (self.delivery_rate / 100) * 20  # 20% weight
        unsub_score = max(0, (1 - self.unsubscribe_rate / 100)) * 10  # 10% weight
        
        return round(open_score + click_score + delivery_score + unsub_score, 2)
    
    @property
    def roi(self):
        """Calculate Return on Investment"""
        if self.actual_cost > 0:
            return ((self.revenue_generated - self.actual_cost) / self.actual_cost) * 100
        return 0
    
    def calculate_metrics(self):
        """Calculate campaign performance metrics"""
        if self.sent_count > 0:
            self.delivery_rate = (self.delivered_count / self.sent_count) * 100
            self.open_rate = (self.unique_opens_count / self.delivered_count) * 100 if self.delivered_count > 0 else 0
            self.click_rate = (self.unique_clicks_count / self.delivered_count) * 100 if self.delivered_count > 0 else 0
            self.click_to_open_rate = (self.unique_clicks_count / self.unique_opens_count) * 100 if self.unique_opens_count > 0 else 0
            self.unsubscribe_rate = (self.unsubscribed_count / self.delivered_count) * 100 if self.delivered_count > 0 else 0
            self.bounce_rate = (self.bounced_count / self.sent_count) * 100
            
            if self.conversion_count > 0:
                self.conversion_rate = (self.conversion_count / self.delivered_count) * 100 if self.delivered_count > 0 else 0
                self.average_order_value = self.revenue_generated / self.conversion_count
        
        self.save(update_fields=[
            'delivery_rate', 'open_rate', 'click_rate', 'click_to_open_rate',
            'unsubscribe_rate', 'bounce_rate', 'conversion_rate', 'average_order_value'
        ])
    
    def get_target_contacts(self):
        """Get all target contacts for this campaign"""
        from django.db.models import Q
        
        # Start with all user contacts
        contacts = Contact.objects.filter(user=self.user, is_subscribed=True)
        
        # Apply list targeting
        if self.target_lists.exists():
            list_contacts = Contact.objects.none()
            for contact_list in self.target_lists.all():
                list_contacts = list_contacts.union(contact_list.get_contacts())
            contacts = contacts.filter(id__in=list_contacts.values_list('id', flat=True))
        
        # Apply exclusion lists
        if self.exclude_lists.exists():
            exclude_contacts = Contact.objects.none()
            for exclude_list in self.exclude_lists.all():
                exclude_contacts = exclude_contacts.union(exclude_list.get_contacts())
            contacts = contacts.exclude(id__in=exclude_contacts.values_list('id', flat=True))
        
        # Apply dynamic segments
        if self.target_segments:
            from backend.services.segmentation_service import SegmentationService
            service = SegmentationService(self.user)
            segment_contacts = service.get_segment_contacts(self.target_segments)
            contacts = contacts.filter(id__in=segment_contacts.values_list('id', flat=True))
        
        return contacts
    
    def update_recipients_count(self):
        """Update the recipients count"""
        self.recipients_count = self.get_target_contacts().count()
        self.save(update_fields=['recipients_count'])
    
    def duplicate(self, new_name=None):
        """Create a duplicate of this campaign"""
        new_name = new_name or f"{self.name} (Copy)"
        
        # Create new campaign
        new_campaign = Campaign.objects.create(
            user=self.user,
            name=new_name,
            description=self.description,
            campaign_type=self.campaign_type,
            subject=self.subject,
            preview_text=self.preview_text,
            html_content=self.html_content,
            text_content=self.text_content,
            template=self.template,
            domain_config=self.domain_config,
            sender_name=self.sender_name,
            sender_email=self.sender_email,
            reply_to_email=self.reply_to_email,
            target_segments=self.target_segments.copy(),
            track_opens=self.track_opens,
            track_clicks=self.track_clicks,
            personalization_level=self.personalization_level,
        )
        
        # Copy target lists
        new_campaign.target_lists.set(self.target_lists.all())
        new_campaign.exclude_lists.set(self.exclude_lists.all())
        
        return new_campaign
    
    def get_best_send_time(self):
        """Get optimal send time based on target audience"""
        from backend.services.optimization_service import SendTimeOptimizer
        optimizer = SendTimeOptimizer(self.user)
        return optimizer.get_optimal_send_time(self.get_target_contacts())
    
    def estimate_cost(self):
        """Estimate campaign cost based on recipients and plan"""
        # This would depend on your pricing model
        # For now, return a basic calculation
        base_cost_per_email = 0.001  # 1 FCFA per email
        self.estimated_cost = self.recipients_count * base_cost_per_email
        self.save(update_fields=['estimated_cost'])
        return self.estimated_cost


class CampaignVariant(models.Model):
    """A/B test variants for campaigns"""
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='variants')
    
    # Variant Information
    name = models.CharField(max_length=100)
    variant_type = models.CharField(max_length=1, choices=[('A', 'Variant A'), ('B', 'Variant B')])
    percentage = models.IntegerField(default=50, help_text="Percentage of audience for this variant")
    
    # Variant Content (what's different)
    subject = models.CharField(max_length=200, blank=True, null=True)
    preview_text = models.CharField(max_length=150, blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)
    sender_name = models.CharField(max_length=100, blank=True, null=True)
    send_time = models.DateTimeField(blank=True, null=True)
    
    # Variant Statistics
    recipients_count = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    conversion_count = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Performance Metrics
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    
    # Winner Selection
    is_winner = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    statistical_significance = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_variants'
        verbose_name = 'Campaign Variant'
        verbose_name_plural = 'Campaign Variants'
        unique_together = ['campaign', 'variant_type']
        ordering = ['variant_type']
    
    def __str__(self):
        return f"{self.campaign.name} - Variant {self.variant_type}"
    
    def calculate_metrics(self):
        """Calculate variant performance metrics"""
        if self.sent_count > 0:
            self.open_rate = (self.opened_count / self.sent_count) * 100
            self.click_rate = (self.clicked_count / self.sent_count) * 100
            self.conversion_rate = (self.conversion_count / self.sent_count) * 100
        
        self.save(update_fields=['open_rate', 'click_rate', 'conversion_rate'])
    
    def get_content(self):
        """Get variant content, falling back to campaign content"""
        return {
            'subject': self.subject or self.campaign.subject,
            'preview_text': self.preview_text or self.campaign.preview_text,
            'html_content': self.html_content or self.campaign.html_content,
            'sender_name': self.sender_name or self.campaign.sender_name,
        }


class AutomationFlow(models.Model):
    """Marketing automation workflows"""
    
    TRIGGER_TYPES = [
        ('WELCOME', 'Welcome Series'),
        ('ABANDONED_CART', 'Abandoned Cart'),
        ('BIRTHDAY', 'Birthday'),
        ('ANNIVERSARY', 'Anniversary'),
        ('INACTIVE', 'Inactive Subscriber'),
        ('POST_PURCHASE', 'Post Purchase'),
        ('BEHAVIORAL', 'Behavioral Trigger'),
        ('DATE_BASED', 'Date Based'),
        ('FORM_SUBMISSION', 'Form Submission'),
        ('TAG_ADDED', 'Tag Added'),
        ('LIST_JOINED', 'List Joined'),
        ('CUSTOM_EVENT', 'Custom Event'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='automation_flows')
    
    # Flow Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    
    # Trigger Configuration
    trigger_conditions = models.JSONField(default=dict, help_text="Conditions that trigger this automation")
    trigger_delay = models.DurationField(default=timedelta(hours=0), help_text="Delay before starting automation")
    
    # Flow Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    
    # Audience Settings
    target_lists = models.ManyToManyField(ContactList, blank=True)
    exclude_lists = models.ManyToManyField(ContactList, blank=True, related_name='excluded_automations')
    
    # Flow Control
    max_participants = models.IntegerField(null=True, blank=True, help_text="Maximum number of contacts in flow")
    allow_re_entry = models.BooleanField(default=False, help_text="Allow contacts to re-enter this flow")
    exit_conditions = models.JSONField(default=dict, blank=True, help_text="Conditions to exit the flow")
    
    # Performance Tracking
    total_entered = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
    total_active = models.IntegerField(default=0)
    total_exited = models.IntegerField(default=0)
    total_emails_sent = models.IntegerField(default=0)
    
    # Analytics
    avg_completion_rate = models.FloatField(default=0.0)
    avg_completion_time = models.DurationField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'automation_flows'
        verbose_name = 'Automation Flow'
        verbose_name_plural = 'Automation Flows'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['trigger_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
    
    @property
    def completion_rate(self):
        """Calculate completion rate"""
        if self.total_entered > 0:
            return (self.total_completed / self.total_entered) * 100
        return 0
    
    @property
    def active_participants(self):
        """Get number of active participants"""
        return self.executions.filter(status='ACTIVE').count()
    
    def can_enter_contact(self, contact):
        """Check if contact can enter this automation"""
        if not self.is_active or self.status != 'ACTIVE':
            return False
        
        # Check max participants
        if self.max_participants and self.total_active >= self.max_participants:
            return False
        
        # Check if contact is already in flow
        if not self.allow_re_entry:
            existing = AutomationExecution.objects.filter(
                automation=self,
                contact=contact,
                status__in=['ACTIVE', 'COMPLETED']
            ).exists()
            if existing:
                return False
        
        # Check target/exclude lists
        if self.target_lists.exists():
            if not any(contact in target_list.get_contacts() for target_list in self.target_lists.all()):
                return False
        
        if self.exclude_lists.exists():
            if any(contact in exclude_list.get_contacts() for exclude_list in self.exclude_lists.all()):
                return False
        
        return True
    
    def trigger_for_contact(self, contact):
        """Trigger automation for a specific contact"""
        if self.can_enter_contact(contact):
            execution = AutomationExecution.objects.create(
                automation=self,
                contact=contact,
                status='ACTIVE'
            )
            
            # Update stats
            self.total_entered += 1
            self.total_active += 1
            self.last_triggered = timezone.now()
            self.save()
            
            return execution
        return None


class AutomationStep(models.Model):
    """Individual steps in an automation flow"""
    
    STEP_TYPES = [
        ('EMAIL', 'Send Email'),
        ('WAIT', 'Wait/Delay'),
        ('CONDITION', 'Condition/Branch'),
        ('ACTION', 'Perform Action'),
        ('TAG', 'Add/Remove Tag'),
        ('LIST', 'Add/Remove from List'),
        ('WEBHOOK', 'Send Webhook'),
        ('UPDATE_FIELD', 'Update Contact Field'),
        ('SCORE', 'Update Lead Score'),
        ('NOTIFICATION', 'Send Notification'),
    ]
    
    ACTION_TYPES = [
        ('ADD_TAG', 'Add Tag'),
        ('REMOVE_TAG', 'Remove Tag'),
        ('ADD_TO_LIST', 'Add to List'),
        ('REMOVE_FROM_LIST', 'Remove from List'),
        ('UPDATE_FIELD', 'Update Custom Field'),
        ('UPDATE_SCORE', 'Update Lead Score'),
        ('SEND_WEBHOOK', 'Send Webhook'),
        ('STOP_AUTOMATION', 'Stop Automation'),
        ('SEND_NOTIFICATION', 'Send Internal Notification'),
    ]
    
    automation = models.ForeignKey(AutomationFlow, on_delete=models.CASCADE, related_name='steps')
    
    # Step Configuration
    name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    step_order = models.IntegerField(default=0)
    
    # Delay Settings (for WAIT steps)
    delay_amount = models.IntegerField(default=0)
    delay_unit = models.CharField(max_length=10, choices=[
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ], default='hours')
    
    # Email Settings (for EMAIL steps)
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    email_subject = models.CharField(max_length=200, blank=True, null=True)
    email_content = models.TextField(blank=True, null=True)
    
    # Condition Settings (for CONDITION steps)
    condition_rules = models.JSONField(default=dict, blank=True)
    
    # Action Settings (for ACTION steps)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, blank=True, null=True)
    action_config = models.JSONField(default=dict, blank=True)
    
    # Step Statistics
    contacts_entered = models.IntegerField(default=0)
    contacts_completed = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    
    # Next Steps (for branching)
    next_step_true = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_true')
    next_step_false = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_false')
    next_step_default = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_default')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'automation_steps'
        verbose_name = 'Automation Step'
        verbose_name_plural = 'Automation Steps'
        ordering = ['automation', 'step_order']
        unique_together = ['automation', 'step_order']
    
    def __str__(self):
        return f"{self.automation.name} - Step {self.step_order}: {self.name}"
    
    def get_delay_timedelta(self):
        """Get delay as timedelta"""
        if self.delay_unit == 'minutes':
            return timedelta(minutes=self.delay_amount)
        elif self.delay_unit == 'hours':
            return timedelta(hours=self.delay_amount)
        elif self.delay_unit == 'days':
            return timedelta(days=self.delay_amount)
        elif self.delay_unit == 'weeks':
            return timedelta(weeks=self.delay_amount)
        return timedelta()
    
    def execute_for_contact(self, contact, execution):
        """Execute this step for a specific contact"""
        try:
            if self.step_type == 'EMAIL':
                return self.execute_email_step(contact, execution)
            elif self.step_type == 'WAIT':
                return self.execute_wait_step(contact, execution)
            elif self.step_type == 'CONDITION':
                return self.execute_condition_step(contact, execution)
            elif self.step_type == 'ACTION':
                return self.execute_action_step(contact, execution)
            elif self.step_type == 'TAG':
                return self.execute_tag_step(contact, execution)
            elif self.step_type == 'LIST':
                return self.execute_list_step(contact, execution)
            else:
                return {'success': False, 'error': f'Unknown step type: {self.step_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute_email_step(self, contact, execution):
        """Execute email sending step"""
        from backend.services.email_service import EmailService
        
        # Use template or custom content
        if self.email_template:
            content = self.email_template.render_preview(contact.get_personalization_data())
            subject = content['subject']
            html_content = content['html_content']
        else:
            subject = self.email_subject
            html_content = self.email_content
        
        # Send email
        email_service = EmailService(self.automation.user)
        result = email_service.send_automation_email(
            contact=contact,
            subject=subject,
            html_content=html_content,
            automation=self.automation
        )
        
        if result['success']:
            self.emails_sent += 1
            self.save()
        
        return result
    
    def execute_wait_step(self, contact, execution):
        """Execute wait step"""
        delay = self.get_delay_timedelta()
        execution.next_execution_time = timezone.now() + delay
        execution.save()
        
        return {
            'success': True,
            'action': 'wait',
            'delay': delay.total_seconds(),
            'next_execution': execution.next_execution_time
        }
    
    def execute_condition_step(self, contact, execution):
        """Execute condition/branching step"""
        from backend.services.condition_service import ConditionEvaluator
        
        evaluator = ConditionEvaluator()
        result = evaluator.evaluate_conditions(self.condition_rules, contact)
        
        # Determine next step based on condition result
        if result:
            next_step = self.next_step_true
        else:
            next_step = self.next_step_false
        
        return {
            'success': True,
            'action': 'condition',
            'result': result,
            'next_step': next_step.id if next_step else None
        }
    
    def execute_action_step(self, contact, execution):
        """Execute action step"""
        action_type = self.action_type
        config = self.action_config
        
        if action_type == 'ADD_TAG':
            tag_name = config.get('tag_name')
            if tag_name:
                contact.tags.add(tag_name)
                return {'success': True, 'action': 'tag_added', 'tag': tag_name}
        
        elif action_type == 'UPDATE_FIELD':
            field_name = config.get('field_name')
            field_value = config.get('field_value')
            if field_name and field_value is not None:
                contact.custom_fields[field_name] = field_value
                contact.save()
                return {'success': True, 'action': 'field_updated', 'field': field_name}
        
        # Add more action types as needed
        
        return {'success': False, 'error': f'Unknown action type: {action_type}'}


class AutomationExecution(models.Model):
    """Track individual contact progress through automation flows"""
    
    EXECUTION_STATUS = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('EXITED', 'Exited'),
    ]
    
    automation = models.ForeignKey(AutomationFlow, on_delete=models.CASCADE, related_name='executions')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='automation_executions')
    
    # Execution Status
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS, default='ACTIVE')
    current_step = models.ForeignKey(AutomationStep, on_delete=models.SET_NULL, null=True, blank=True)
    next_execution_time = models.DateTimeField(null=True, blank=True)
    
    # Progress Tracking
    steps_completed = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Execution History
    execution_log = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'automation_executions'
        verbose_name = 'Automation Execution'
        verbose_name_plural = 'Automation Executions'
        unique_together = ['automation', 'contact']
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', 'next_execution_time']),
            models.Index(fields=['automation', 'status']),
            models.Index(fields=['contact']),
        ]
    
    def __str__(self):
        return f"{self.contact.email} in {self.automation.name}"
    
    def log_step_execution(self, step, result, details=None):
        """Log step execution"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'step_id': step.id,
            'step_name': step.name,
            'step_type': step.step_type,
            'result': result,
            'details': details or {}
        }
        
        self.execution_log.append(log_entry)
        self.save(update_fields=['execution_log', 'last_activity'])
    
    def complete_execution(self):
        """Mark execution as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Update automation stats
        self.automation.total_completed += 1
        self.automation.total_active = max(0, self.automation.total_active - 1)
        self.automation.save()
    
    def pause_execution(self):
        """Pause execution"""
        self.status = 'PAUSED'
        self.save()
    
    def resume_execution(self):
        """Resume execution"""
        self.status = 'ACTIVE'
        self.save()
    
    def cancel_execution(self, reason=None):
        """Cancel execution"""
        self.status = 'CANCELLED'
        if reason:
            self.error_message = reason
        self.save()
        
        # Update automation stats
        self.automation.total_active = max(0, self.automation.total_active - 1)
        self.automation.save()