"""
Analytics Models for AfriMail Pro
Comprehensive analytics and reporting system
"""
from django.db import models
from django.utils import timezone
from .user_models import CustomUser
from .campaign_models import Campaign
from .contact_models import Contact
import uuid
from datetime import timedelta

class CampaignAnalytics(models.Model):
    """Detailed analytics for campaigns"""
    
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='analytics')
    
    # Delivery Metrics
    delivery_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    soft_bounce_rate = models.FloatField(default=0.0)
    hard_bounce_rate = models.FloatField(default=0.0)
    
    # Engagement Metrics
    open_rate = models.FloatField(default=0.0)
    unique_open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    unique_click_rate = models.FloatField(default=0.0)
    click_to_open_rate = models.FloatField(default=0.0)
    unsubscribe_rate = models.FloatField(default=0.0)
    complaint_rate = models.FloatField(default=0.0)
    forward_rate = models.FloatField(default=0.0)
    
    # Advanced Metrics
    social_share_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    revenue_per_email = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    revenue_per_recipient = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    roi = models.FloatField(default=0.0, help_text="Return on Investment")
    
    # Time-based Analysis
    best_send_time = models.TimeField(null=True, blank=True)
    peak_engagement_hour = models.IntegerField(null=True, blank=True)
    peak_engagement_day = models.CharField(max_length=10, blank=True, null=True)
    average_time_to_open = models.DurationField(null=True, blank=True)
    average_time_to_click = models.DurationField(null=True, blank=True)
    
    # Geographic Analysis
    top_countries = models.JSONField(default=list, blank=True)
    top_cities = models.JSONField(default=list, blank=True)
    
    # Device Analysis
    desktop_opens = models.IntegerField(default=0)
    mobile_opens = models.IntegerField(default=0)
    tablet_opens = models.IntegerField(default=0)
    desktop_clicks = models.IntegerField(default=0)
    mobile_clicks = models.IntegerField(default=0)
    tablet_clicks = models.IntegerField(default=0)
    
    # Email Client Analysis
    email_clients = models.JSONField(default=dict, blank=True)
    
    # Link Performance
    link_performance = models.JSONField(default=list, blank=True)
    
    # Hourly Distribution
    hourly_opens = models.JSONField(default=dict, blank=True)
    hourly_clicks = models.JSONField(default=dict, blank=True)
    
    # Daily Distribution
    daily_opens = models.JSONField(default=dict, blank=True)
    daily_clicks = models.JSONField(default=dict, blank=True)
    
    # Industry Benchmarks Comparison
    industry_avg_open_rate = models.FloatField(default=0.0)
    industry_avg_click_rate = models.FloatField(default=0.0)
    performance_vs_industry = models.FloatField(default=0.0)
    
    # Engagement Quality
    high_value_opens = models.IntegerField(default=0)  # Opens from high-value contacts
    high_value_clicks = models.IntegerField(default=0)  # Clicks from high-value contacts
    engagement_quality_score = models.FloatField(default=0.0)
    
    # Campaign Health Score
    deliverability_score = models.FloatField(default=0.0)
    engagement_score = models.FloatField(default=0.0)
    content_quality_score = models.FloatField(default=0.0)
    overall_health_score = models.FloatField(default=0.0)
    
    # Predictive Analytics
    predicted_performance = models.JSONField(default=dict, blank=True)
    anomaly_detection = models.JSONField(default=dict, blank=True)
    
    # Comparison Metrics
    previous_campaign_comparison = models.JSONField(default=dict, blank=True)
    user_average_comparison = models.JSONField(default=dict, blank=True)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'campaign_analytics'
        verbose_name = 'Campaign Analytics'
        verbose_name_plural = 'Campaign Analytics'
    
    def __str__(self):
        return f"Analytics for {self.campaign.name}"
    
    def calculate_all_metrics(self):
        """Calculate all analytics metrics"""
        from backend.services.analytics_service import CampaignAnalyticsService
        service = CampaignAnalyticsService(self.campaign)
        service.calculate_all_metrics()
    
    def get_performance_summary(self):
        """Get performance summary"""
        return {
            'delivery_rate': self.delivery_rate,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'conversion_rate': self.conversion_rate,
            'roi': self.roi,
            'overall_health_score': self.overall_health_score,
        }
    
    def compare_to_industry(self):
        """Compare performance to industry averages"""
        return {
            'open_rate_diff': self.open_rate - self.industry_avg_open_rate,
            'click_rate_diff': self.click_rate - self.industry_avg_click_rate,
            'performance_percentile': self.performance_vs_industry,
        }


class UserAnalytics(models.Model):
    """Overall analytics for users"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='analytics')
    
    # Overall Statistics
    total_campaigns = models.IntegerField(default=0)
    total_emails_sent = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Average Performance Metrics
    avg_open_rate = models.FloatField(default=0.0)
    avg_click_rate = models.FloatField(default=0.0)
    avg_conversion_rate = models.FloatField(default=0.0)
    avg_unsubscribe_rate = models.FloatField(default=0.0)
    avg_bounce_rate = models.FloatField(default=0.0)
    avg_delivery_rate = models.FloatField(default=0.0)
    
    # Growth Metrics
    contact_growth_rate = models.FloatField(default=0.0)
    engagement_growth_rate = models.FloatField(default=0.0)
    revenue_growth_rate = models.FloatField(default=0.0)
    
    # Activity Metrics
    campaigns_this_month = models.IntegerField(default=0)
    emails_this_month = models.IntegerField(default=0)
    revenue_this_month = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Top Performers
    best_performing_campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='best_for_users')
    most_engaged_segment = models.JSONField(default=dict, blank=True)
    top_performing_content_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Optimization Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    optimization_score = models.FloatField(default=0.0)
    
    # Benchmarking
    industry_percentile = models.FloatField(default=0.0)
    
    # Time Series Data (last 12 months)
    monthly_metrics = models.JSONField(default=dict, blank=True)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_analytics'
        verbose_name = 'User Analytics'
        verbose_name_plural = 'User Analytics'
    
    def __str__(self):
        return f"Analytics for {self.user.email}"
    
    def update_metrics(self):
        """Update all user metrics"""
        from backend.services.analytics_service import UserAnalyticsService
        service = UserAnalyticsService(self.user)
        service.update_all_metrics()


class AnalyticsSnapshot(models.Model):
    """Periodic snapshots of analytics data"""
    
    SNAPSHOT_TYPES = [
        ('DAILY', 'Daily Snapshot'),
        ('WEEKLY', 'Weekly Snapshot'),
        ('MONTHLY', 'Monthly Snapshot'),
        ('QUARTERLY', 'Quarterly Snapshot'),
        ('YEARLY', 'Yearly Snapshot'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='analytics_snapshots')
    
    # Snapshot Info
    snapshot_type = models.CharField(max_length=20, choices=SNAPSHOT_TYPES)
    snapshot_date = models.DateField()
    
    # Campaign Metrics
    campaigns_sent = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_delivered = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    
    # Performance Metrics
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    delivery_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    unsubscribe_rate = models.FloatField(default=0.0)
    
    # Revenue Metrics
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    conversions = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    
    # Contact Metrics
    total_contacts = models.IntegerField(default=0)
    new_contacts = models.IntegerField(default=0)
    unsubscribed_contacts = models.IntegerField(default=0)
    
    # Engagement Metrics
    avg_engagement_score = models.FloatField(default=0.0)
    high_engaged_contacts = models.IntegerField(default=0)
    low_engaged_contacts = models.IntegerField(default=0)
    
    # Growth Metrics
    contact_growth_rate = models.FloatField(default=0.0)
    revenue_growth_rate = models.FloatField(default=0.0)
    engagement_growth_rate = models.FloatField(default=0.0)
    
    # Additional Data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_snapshots'
        verbose_name = 'Analytics Snapshot'
        verbose_name_plural = 'Analytics Snapshots'
        unique_together = ['user', 'snapshot_type', 'snapshot_date']
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['user', 'snapshot_type']),
            models.Index(fields=['snapshot_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_snapshot_type_display()} - {self.snapshot_date}"


class ReportTemplate(models.Model):
    """Report templates for scheduled reporting"""
    
    REPORT_TYPES = [
        ('CAMPAIGN_SUMMARY', 'Campaign Summary'),
        ('PERFORMANCE_OVERVIEW', 'Performance Overview'),
        ('AUDIENCE_INSIGHTS', 'Audience Insights'),
        ('REVENUE_REPORT', 'Revenue Report'),
        ('GROWTH_ANALYSIS', 'Growth Analysis'),
        ('ENGAGEMENT_REPORT', 'Engagement Report'),
        ('DELIVERABILITY_REPORT', 'Deliverability Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ON_DEMAND', 'On Demand'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='report_templates')
    
    # Template Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    
    # Configuration
    metrics_included = models.JSONField(default=list, help_text="List of metrics to include")
    filters = models.JSONField(default=dict, help_text="Report filters")
    date_range_type = models.CharField(max_length=20, default='last_30_days')
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    schedule_time = models.TimeField(default='08:00')
    schedule_day = models.IntegerField(null=True, blank=True, help_text="Day of week (0=Monday) or month")
    
    # Delivery
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='PDF')
    email_recipients = models.JSONField(default=list, help_text="Email addresses to send report to")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    next_generation = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    def generate_report(self):
        """Generate report based on template"""
        from backend.services.report_service import ReportGenerator
        generator = ReportGenerator(self)
        return generator.generate()
    
    def calculate_next_generation(self):
        """Calculate next report generation time"""
        if not self.is_active:
            return None
        
        now = timezone.now()
        
        if self.frequency == 'DAILY':
            next_date = now.replace(hour=self.schedule_time.hour, minute=self.schedule_time.minute, second=0, microsecond=0)
            if next_date <= now:
                next_date += timedelta(days=1)
        elif self.frequency == 'WEEKLY':
            # Schedule for specific day of week
            days_ahead = self.schedule_day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = now + timedelta(days=days_ahead)
            next_date = next_date.replace(hour=self.schedule_time.hour, minute=self.schedule_time.minute, second=0, microsecond=0)
        elif self.frequency == 'MONTHLY':
            # Schedule for specific day of month
            if now.day < self.schedule_day:
                next_date = now.replace(day=self.schedule_day, hour=self.schedule_time.hour, minute=self.schedule_time.minute, second=0, microsecond=0)
            else:
                if now.month == 12:
                    next_date = now.replace(year=now.year + 1, month=1, day=self.schedule_day, hour=self.schedule_time.hour, minute=self.schedule_time.minute, second=0, microsecond=0)
                else:
                    next_date = now.replace(month=now.month + 1, day=self.schedule_day, hour=self.schedule_time.hour, minute=self.schedule_time.minute, second=0, microsecond=0)
        else:
            return None
        
        self.next_generation = next_date
        self.save()
        return next_date


class ABTestResult(models.Model):
    """A/B test results and statistical analysis"""
    
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='ab_test_result')
    
    # Test Configuration
    test_start_time = models.DateTimeField()
    test_end_time = models.DateTimeField(null=True, blank=True)
    test_duration_hours = models.IntegerField()
    test_sample_size = models.IntegerField()
    
    # Variant A Results
    variant_a_sent = models.IntegerField(default=0)
    variant_a_opened = models.IntegerField(default=0)
    variant_a_clicked = models.IntegerField(default=0)
    variant_a_converted = models.IntegerField(default=0)
    variant_a_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Variant B Results
    variant_b_sent = models.IntegerField(default=0)
    variant_b_opened = models.IntegerField(default=0)
    variant_b_clicked = models.IntegerField(default=0)
    variant_b_converted = models.IntegerField(default=0)
    variant_b_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Statistical Analysis
    confidence_level = models.FloatField(default=95.0)
    p_value = models.FloatField(null=True, blank=True)
    confidence_interval = models.JSONField(default=dict, blank=True)
    statistical_significance = models.BooleanField(default=False)
    
    # Winner Selection
    winning_variant = models.CharField(max_length=1, blank=True, null=True, choices=[('A', 'Variant A'), ('B', 'Variant B')])
    improvement_percentage = models.FloatField(default=0.0)
    projected_annual_impact = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Test Validity
    test_valid = models.BooleanField(default=True)
    validity_notes = models.TextField(blank=True, null=True)
    
    # Analysis Details
    effect_size = models.FloatField(null=True, blank=True)
    power_analysis = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ab_test_results'
        verbose_name = 'A/B Test Result'
        verbose_name_plural = 'A/B Test Results'
    
    def __str__(self):
        return f"A/B Test Result for {self.campaign.name}"
    
    def calculate_statistical_significance(self):
        """Calculate statistical significance of A/B test"""
        from backend.services.statistics_service import ABTestAnalyzer
        analyzer = ABTestAnalyzer()
        result = analyzer.analyze_test(self)
        
        self.p_value = result['p_value']
        self.statistical_significance = result['significant']
        self.confidence_interval = result['confidence_interval']
        self.effect_size = result['effect_size']
        
        self.save()
        return result
    
    def get_winner_summary(self):
        """Get summary of winning variant"""
        if not self.winning_variant:
            return None
        
        if self.winning_variant == 'A':
            return {
                'variant': 'A',
                'sent': self.variant_a_sent,
                'opened': self.variant_a_opened,
                'clicked': self.variant_a_clicked,
                'converted': self.variant_a_converted,
                'revenue': self.variant_a_revenue,
                'improvement': self.improvement_percentage,
            }
        else:
            return {
                'variant': 'B',
                'sent': self.variant_b_sent,
                'opened': self.variant_b_opened,
                'clicked': self.variant_b_clicked,
                'converted': self.variant_b_converted,
                'revenue': self.variant_b_revenue,
                'improvement': self.improvement_percentage,
            }


class PlatformAnalytics(models.Model):
    """Platform-wide analytics for super admin"""
    
    # Date and Time
    date = models.DateField(unique=True)
    
    # User Metrics
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    trial_users = models.IntegerField(default=0)
    paid_users = models.IntegerField(default=0)
    churned_users = models.IntegerField(default=0)
    
    # Usage Metrics
    total_campaigns = models.IntegerField(default=0)
    total_emails_sent = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)
    
    # Performance Metrics
    platform_avg_open_rate = models.FloatField(default=0.0)
    platform_avg_click_rate = models.FloatField(default=0.0)
    platform_avg_delivery_rate = models.FloatField(default=0.0)
    platform_avg_bounce_rate = models.FloatField(default=0.0)
    
    # Revenue Metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Monthly Recurring Revenue
    arr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Annual Recurring Revenue
    
    # Plan Distribution
    starter_users = models.IntegerField(default=0)
    professional_users = models.IntegerField(default=0)
    enterprise_users = models.IntegerField(default=0)
    
    # Geographic Distribution
    countries_active = models.JSONField(default=dict, blank=True)
    
    # System Health
    system_uptime = models.FloatField(default=100.0)
    average_response_time = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)
    
    # Email Provider Performance
    provider_performance = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'platform_analytics'
        verbose_name = 'Platform Analytics'
        verbose_name_plural = 'Platform Analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Platform Analytics - {self.date}"
    
    @classmethod
    def generate_daily_snapshot(cls, date=None):
        """Generate daily platform analytics snapshot"""
        if not date:
            date = timezone.now().date()
        
        from backend.services.platform_analytics_service import PlatformAnalyticsService
        service = PlatformAnalyticsService()
        return service.generate_daily_snapshot(date)