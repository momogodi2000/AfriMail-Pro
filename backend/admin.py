"""
Django Admin Configuration for AfriMail Pro
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    CustomUser, UserProfile, UserActivity, UserSubscription,
    ContactList, Contact, ContactInteraction, ContactImport, ContactCustomField,
    EmailDomainConfig, EmailTemplate, EmailLog, EmailProvider,
    Campaign, CampaignVariant, AutomationFlow, AutomationStep, AutomationExecution,
    CampaignAnalytics, UserAnalytics, AnalyticsSnapshot, ReportTemplate, ABTestResult, PlatformAnalytics
)


# Inline admin classes
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'avatar', 'company_logo', 'company_description', 'business_type',
        'target_audience', 'default_sender_name', 'default_sender_email',
        'api_key', 'api_active'
    )
    readonly_fields = ('api_key',)


class UserActivityInline(admin.TabularInline):
    model = UserActivity
    extra = 0
    readonly_fields = ('activity_type', 'description', 'ip_address', 'created_at')
    fields = ('activity_type', 'description', 'ip_address', 'created_at')
    max_num = 10
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False


class UserSubscriptionInline(admin.TabularInline):
    model = UserSubscription
    extra = 0
    readonly_fields = ('created_at', 'payment_date', 'invoice_number')
    fields = (
        'plan', 'start_date', 'end_date', 'is_active', 'amount', 'currency',
        'payment_method', 'payment_status', 'created_at'
    )
    max_num = 5
    ordering = ('-created_at',)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ('email', 'first_name', 'last_name', 'subscription_status', 'engagement_score')
    readonly_fields = ('engagement_score',)
    max_num = 10


class CampaignInline(admin.TabularInline):
    model = Campaign
    extra = 0
    fields = ('name', 'campaign_type', 'status', 'sent_count', 'open_rate', 'created_at')
    readonly_fields = ('sent_count', 'open_rate', 'created_at')
    max_num = 5
    ordering = ('-created_at',)


# Main admin classes
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserActivityInline, UserSubscriptionInline, CampaignInline)
    
    list_display = (
        'email', 'get_full_name', 'company', 'role', 'subscription_plan',
        'is_verified', 'is_active', 'total_campaigns', 'total_contacts',
        'trial_status', 'created_at'
    )
    list_filter = (
        'role', 'subscription_plan', 'is_verified', 'is_active', 'is_trial_user',
        'country', 'industry', 'created_at'
    )
    search_fields = ('email', 'first_name', 'last_name', 'company')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone', 'country', 'city', 'preferred_language')
        }),
        ('Company info', {
            'fields': ('company', 'company_website', 'company_size', 'industry')
        }),
        ('Account info', {
            'fields': ('role', 'subscription_plan', 'subscription_active', 'is_verified', 'is_trial_user')
        }),
        ('Trial & Subscription', {
            'fields': ('trial_started', 'trial_ends', 'subscription_started', 'subscription_ends', 'auto_renew')
        }),
        ('Statistics', {
            'fields': ('total_emails_sent', 'total_campaigns', 'total_contacts', 'last_campaign_sent'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'company', 'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def trial_status(self, obj):
        if obj.is_trial_user:
            if obj.is_trial_active:
                return format_html(
                    '<span style="color: green;">Active ({} days left)</span>',
                    obj.trial_days_remaining
                )
            else:
                return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: blue;">Not on trial</span>')
    trial_status.short_description = 'Trial Status'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('profile').prefetch_related('campaigns', 'contacts')
    
    actions = ['activate_users', 'deactivate_users', 'send_welcome_email']
    
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'ip_address', 'country', 'created_at')
    list_filter = ('activity_type', 'country', 'created_at')
    search_fields = ('user__email', 'description', 'ip_address')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'plan', 'payment_status', 'amount', 'currency',
        'payment_method', 'start_date', 'end_date', 'is_active'
    )
    list_filter = ('plan', 'payment_status', 'payment_method', 'is_active', 'created_at')
    search_fields = ('user__email', 'payment_reference', 'invoice_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Subscription', {
            'fields': ('user', 'plan', 'start_date', 'end_date', 'is_active', 'auto_renew')
        }),
        ('Payment', {
            'fields': ('amount', 'currency', 'payment_method', 'payment_status', 'payment_reference', 'payment_date')
        }),
        ('Mobile Money', {
            'fields': ('mobile_money_provider', 'mobile_number'),
            'classes': ('collapse',)
        }),
        ('Invoice', {
            'fields': ('invoice_number', 'invoice_generated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactList)
class ContactListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'list_type', 'contact_count', 'is_active', 'last_updated')
    list_filter = ('list_type', 'is_active', 'is_public', 'user__subscription_plan')
    search_fields = ('name', 'description', 'user__email')
    readonly_fields = ('contact_count', 'last_updated', 'last_calculated')
    ordering = ('-last_updated',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'description', 'list_type')
        }),
        ('Configuration', {
            'fields': ('conditions', 'is_active', 'is_public', 'is_favorite')
        }),
        ('Statistics', {
            'fields': ('contact_count', 'avg_engagement_score', 'last_campaign_sent', 'last_calculated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'get_full_name', 'user', 'subscription_status',
        'engagement_score', 'lead_status', 'country', 'created_at'
    )
    list_filter = (
        'subscription_status', 'lead_status', 'country', 'industry',
        'is_subscribed', 'is_verified', 'is_vip', 'created_at'
    )
    search_fields = ('email', 'first_name', 'last_name', 'company', 'phone')
    readonly_fields = (
        'engagement_score', 'data_quality_score', 'total_opens', 'total_clicks',
        'total_purchases', 'total_revenue', 'created_at', 'updated_at', 'last_activity'
    )
    ordering = ('-engagement_score', '-created_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'email', 'first_name', 'last_name', 'phone')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'gender', 'age_group', 'language'),
            'classes': ('collapse',)
        }),
        ('Company Info', {
            'fields': ('company', 'job_title', 'industry', 'company_size', 'department'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('country', 'state', 'city', 'postal_code', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Subscription', {
            'fields': (
                'subscription_status', 'subscription_source', 'subscription_date',
                'unsubscribe_date', 'unsubscribe_reason'
            )
        }),
        ('Lead Info', {
            'fields': ('lead_status', 'lead_score', 'customer_value')
        }),
        ('Engagement', {
            'fields': (
                'engagement_score', 'last_engagement', 'total_opens', 'total_clicks',
                'total_purchases', 'total_revenue'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('preferred_send_time', 'preferred_frequency', 'email_format'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': (
                'source_url', 'referrer', 'utm_source', 'utm_medium', 'utm_campaign',
                'last_device_type', 'last_browser', 'last_os'
            ),
            'classes': ('collapse',)
        }),
        ('Status Flags', {
            'fields': ('is_subscribed', 'is_verified', 'is_vip', 'is_blocked', 'is_test_contact')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    actions = ['subscribe_contacts', 'unsubscribe_contacts', 'mark_as_vip']
    
    def subscribe_contacts(self, request, queryset):
        count = queryset.update(is_subscribed=True, subscription_status='SUBSCRIBED')
        self.message_user(request, f'{count} contacts subscribed.')
    subscribe_contacts.short_description = 'Subscribe selected contacts'
    
    def unsubscribe_contacts(self, request, queryset):
        count = queryset.update(is_subscribed=False, subscription_status='UNSUBSCRIBED')
        self.message_user(request, f'{count} contacts unsubscribed.')
    unsubscribe_contacts.short_description = 'Unsubscribe selected contacts'
    
    def mark_as_vip(self, request, queryset):
        count = queryset.update(is_vip=True)
        self.message_user(request, f'{count} contacts marked as VIP.')
    mark_as_vip.short_description = 'Mark selected contacts as VIP'


@admin.register(EmailDomainConfig)
class EmailDomainConfigAdmin(admin.ModelAdmin):
    list_display = (
        'domain_name', 'user', 'smtp_provider', 'is_primary', 'domain_verified',
        'total_emails_sent', 'delivery_rate', 'is_active'
    )
    list_filter = (
        'smtp_provider', 'is_primary', 'domain_verified', 'spf_verified',
        'dkim_verified', 'dmarc_verified', 'is_active'
    )
    search_fields = ('domain_name', 'from_email', 'user__email')
    readonly_fields = (
        'total_emails_sent', 'last_email_sent', 'bounce_rate', 'delivery_rate',
        'open_rate', 'click_rate', 'reputation_score', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Domain Info', {
            'fields': ('user', 'domain_name', 'from_email', 'from_name', 'reply_to_email')
        }),
        ('SMTP Configuration', {
            'fields': (
                'smtp_provider', 'smtp_host', 'smtp_port', 'smtp_username',
                'smtp_password', 'use_tls', 'use_ssl'
            )
        }),
        ('Verification', {
            'fields': (
                'domain_verified', 'spf_verified', 'dkim_verified', 'dmarc_verified',
                'verification_status', 'verification_token', 'last_verification_check'
            ),
            'classes': ('collapse',)
        }),
        ('DNS Records', {
            'fields': ('spf_record', 'dkim_record', 'dmarc_record', 'mx_record'),
            'classes': ('collapse',)
        }),
        ('Status & Limits', {
            'fields': (
                'is_active', 'is_primary', 'daily_send_limit', 'hourly_send_limit',
                'current_daily_sent', 'current_hourly_sent'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_emails_sent', 'last_email_sent', 'bounce_rate', 'delivery_rate',
                'open_rate', 'click_rate', 'reputation_score'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_domains', 'test_smtp_connection']
    
    def verify_domains(self, request, queryset):
        for domain in queryset:
            domain.verify_dns_records()
        self.message_user(request, f'Verification initiated for {queryset.count()} domains.')
    verify_domains.short_description = 'Verify DNS records for selected domains'
    
    def test_smtp_connection(self, request, queryset):
        results = []
        for domain in queryset:
            success, message = domain.test_connection()
            results.append(f"{domain.domain_name}: {'✓' if success else '✗'} {message}")
        self.message_user(request, '\n'.join(results))
    test_smtp_connection.short_description = 'Test SMTP connection for selected domains'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user', 'category', 'industry', 'template_type',
        'usage_count', 'rating', 'is_public', 'is_active'
    )
    list_filter = (
        'category', 'industry', 'template_type', 'is_public', 'is_premium',
        'is_active', 'is_responsive', 'created_at'
    )
    search_fields = ('name', 'description', 'user__email')
    readonly_fields = ('usage_count', 'rating', 'rating_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'description', 'category', 'industry', 'template_type')
        }),
        ('Content', {
            'fields': ('subject_line', 'preview_text', 'html_content', 'text_content')
        }),
        ('Configuration', {
            'fields': ('variables', 'blocks', 'parent_template')
        }),
        ('Features', {
            'fields': (
                'is_responsive', 'supports_dark_mode', 'has_social_links',
                'has_unsubscribe_link'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_public', 'is_premium', 'is_favorite')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'rating', 'rating_count', 'avg_open_rate', 'avg_click_rate'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_public', 'make_private', 'duplicate_templates']
    
    def make_public(self, request, queryset):
        count = queryset.update(is_public=True)
        self.message_user(request, f'{count} templates made public.')
    make_public.short_description = 'Make selected templates public'
    
    def make_private(self, request, queryset):
        count = queryset.update(is_public=False)
        self.message_user(request, f'{count} templates made private.')
    make_private.short_description = 'Make selected templates private'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user', 'campaign_type', 'status', 'recipients_count',
        'sent_count', 'open_rate', 'click_rate', 'scheduled_at', 'created_at'
    )
    list_filter = (
        'campaign_type', 'status', 'priority', 'is_ab_test', 'track_opens',
        'track_clicks', 'created_at'
    )
    search_fields = ('name', 'description', 'subject', 'user__email')
    readonly_fields = (
        'recipients_count', 'sent_count', 'delivered_count', 'opened_count',
        'clicked_count', 'unsubscribed_count', 'bounced_count', 'open_rate',
        'click_rate', 'delivery_rate', 'conversion_rate', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'description', 'campaign_type', 'priority')
        }),
        ('Content', {
            'fields': ('subject', 'preview_text', 'html_content', 'text_content', 'template')
        }),
        ('Sender Info', {
            'fields': ('domain_config', 'sender_name', 'sender_email', 'reply_to_email')
        }),
        ('Targeting', {
            'fields': ('target_lists', 'exclude_lists', 'target_segments')
        }),
        ('Scheduling', {
            'fields': ('send_time_option', 'scheduled_at', 'time_zone', 'send_in_recipient_timezone')
        }),
        ('A/B Testing', {
            'fields': (
                'is_ab_test', 'ab_test_percentage', 'ab_winner_criteria',
                'ab_test_duration', 'ab_winner_selected', 'ab_winner_variant'
            ),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('track_opens', 'track_clicks', 'google_analytics_campaign', 'utm_source', 'utm_medium', 'utm_campaign')
        }),
        ('Statistics', {
            'fields': (
                'recipients_count', 'sent_count', 'delivered_count', 'opened_count',
                'clicked_count', 'unsubscribed_count', 'bounced_count', 'open_rate',
                'click_rate', 'delivery_rate', 'conversion_rate', 'revenue_generated'
            ),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('target_lists', 'exclude_lists')
    
    actions = ['duplicate_campaigns', 'pause_campaigns', 'resume_campaigns']
    
    def duplicate_campaigns(self, request, queryset):
        count = 0
        for campaign in queryset:
            campaign.duplicate()
            count += 1
        self.message_user(request, f'{count} campaigns duplicated.')
    duplicate_campaigns.short_description = 'Duplicate selected campaigns'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_email', 'sender_email', 'subject', 'status',
        'campaign', 'contact', 'sent_at', 'opened_at', 'clicked_at'
    )
    list_filter = (
        'status', 'smtp_provider', 'bounce_type', 'queued_at',
        'sent_at', 'device_type', 'browser', 'country'
    )
    search_fields = (
        'recipient_email', 'sender_email', 'subject', 'message_id',
        'user__email', 'contact__email'
    )
    readonly_fields = (
        'message_id', 'queued_at', 'sent_at', 'delivered_at', 'opened_at',
        'clicked_at', 'bounced_at', 'open_count', 'click_count'
    )
    ordering = ('-queued_at',)
    
    fieldsets = (
        ('Email Info', {
            'fields': ('user', 'recipient_email', 'sender_email', 'subject', 'message_id')
        }),
        ('Campaign & Contact', {
            'fields': ('campaign', 'contact', 'domain_config', 'smtp_provider')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'bounce_type', 'bounce_reason')
        }),
        ('Timestamps', {
            'fields': (
                'queued_at', 'sent_at', 'delivered_at', 'opened_at',
                'clicked_at', 'bounced_at', 'complained_at', 'unsubscribed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': (
                'open_count', 'click_count', 'tracking_pixel_id', 'user_agent',
                'ip_address', 'device_type', 'browser', 'operating_system', 'country', 'city'
            ),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('send_time_ms', 'delivery_time_ms'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Platform Analytics Admin (Super Admin only)
@admin.register(PlatformAnalytics)
class PlatformAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'total_users', 'active_users', 'new_users', 'paid_users',
        'total_campaigns', 'total_emails_sent', 'platform_avg_open_rate'
    )
    list_filter = ('date',)
    readonly_fields = ()  # Empty tuple if no fields should be editable
    ordering = ('-date',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Customize admin site
admin.site.site_header = "AfriMail Pro Administration"
admin.site.site_title = "AfriMail Pro Admin"
admin.site.index_title = "Welcome to AfriMail Pro Administration"

# Register remaining models with simple admin
admin.site.register(ContactInteraction)
admin.site.register(ContactImport)
admin.site.register(ContactCustomField)
admin.site.register(EmailProvider)
admin.site.register(CampaignVariant)
admin.site.register(AutomationFlow)
admin.site.register(AutomationStep)
admin.site.register(AutomationExecution)
admin.site.register(CampaignAnalytics)
admin.site.register(UserAnalytics)
admin.site.register(AnalyticsSnapshot)
admin.site.register(ReportTemplate)
admin.site.register(ABTestResult)