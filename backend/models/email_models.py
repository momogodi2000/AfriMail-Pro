"""
Email Configuration Models for AfriMail Pro
Comprehensive email domain and SMTP management system
"""
from django.db import models
from django.core.validators import validate_email
from django.utils import timezone
from .user_models import CustomUser
import uuid
import base64
import secrets
import json
from datetime import timedelta

class EmailDomainConfig(models.Model):
    """Email domain configuration for users"""
    
    SMTP_PROVIDERS = [
        ('GMAIL', 'Gmail (G Suite)'),
        ('OUTLOOK', 'Outlook 365'),
        ('SENDGRID', 'SendGrid'),
        ('MAILGUN', 'Mailgun'),
        ('AMAZON_SES', 'Amazon SES'),
        ('YAGMAIL', 'Yagmail (Gmail)'),
        ('CUSTOM', 'Custom SMTP'),
        ('PLATFORM', 'AfriMail Pro Platform'),
    ]
    
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('FAILED', 'Verification Failed'),
        ('EXPIRED', 'Verification Expired'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_domains')
    
    # Domain Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain_name = models.CharField(max_length=100, help_text="e.g., mycompany.com")
    from_email = models.EmailField(help_text="e.g., marketing@mycompany.com")
    from_name = models.CharField(max_length=100, help_text="e.g., MyCompany Marketing")
    reply_to_email = models.EmailField(blank=True, null=True)
    
    # SMTP Configuration
    smtp_provider = models.CharField(max_length=20, choices=SMTP_PROVIDERS, default='PLATFORM')
    smtp_host = models.CharField(max_length=100, blank=True, null=True)
    smtp_port = models.IntegerField(default=587)
    smtp_username = models.CharField(max_length=100, blank=True, null=True)
    smtp_password = models.CharField(max_length=500, blank=True, null=True)  # Encrypted
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    
    # Domain Verification
    domain_verified = models.BooleanField(default=False)
    spf_verified = models.BooleanField(default=False)
    dkim_verified = models.BooleanField(default=False)
    dmarc_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    last_verification_check = models.DateTimeField(null=True, blank=True)
    
    # DNS Records (for user reference)
    spf_record = models.TextField(blank=True, null=True)
    dkim_record = models.TextField(blank=True, null=True)
    dmarc_record = models.TextField(blank=True, null=True)
    mx_record = models.TextField(blank=True, null=True)
    
    # Status and Configuration
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    is_default_fallback = models.BooleanField(default=False)
    last_test_sent = models.DateTimeField(null=True, blank=True)
    last_test_result = models.TextField(blank=True, null=True)
    
    # Usage Statistics
    total_emails_sent = models.IntegerField(default=0)
    last_email_sent = models.DateTimeField(null=True, blank=True)
    bounce_rate = models.FloatField(default=0.0)
    delivery_rate = models.FloatField(default=0.0)
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    
    # Rate Limiting
    daily_send_limit = models.IntegerField(default=1000)
    hourly_send_limit = models.IntegerField(default=100)
    current_daily_sent = models.IntegerField(default=0)
    current_hourly_sent = models.IntegerField(default=0)
    last_rate_reset = models.DateTimeField(auto_now_add=True)
    
    # Reputation Management
    reputation_score = models.FloatField(default=100.0)
    blacklist_status = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_domain_configs'
        verbose_name = 'Email Domain Configuration'
        verbose_name_plural = 'Email Domain Configurations'
        unique_together = ['user', 'domain_name']
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['domain_verified']),
            models.Index(fields=['smtp_provider']),
        ]
    
    def __str__(self):
        return f"{self.domain_name} ({self.user.company})"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary domain per user
        if self.is_primary:
            EmailDomainConfig.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # Encrypt password before saving
        if self.smtp_password and not self.smtp_password.startswith('enc_'):
            self.smtp_password = self.encrypt_password(self.smtp_password)
        
        super().save(*args, **kwargs)
    
    def encrypt_password(self, password):
        """Encrypt password for storage"""
        try:
            encoded = base64.b64encode(password.encode()).decode()
            return f"enc_{encoded}"
        except Exception:
            return password
    
    def decrypt_password(self):
        """Decrypt stored password"""
        if self.smtp_password and self.smtp_password.startswith('enc_'):
            try:
                encoded = self.smtp_password[4:]  # Remove 'enc_' prefix
                return base64.b64decode(encoded.encode()).decode()
            except Exception:
                return self.smtp_password
        return self.smtp_password
    
    def get_smtp_config(self):
        """Get SMTP configuration dictionary"""
        if self.smtp_provider == 'PLATFORM':
            return self.get_platform_smtp_config()
        
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.decrypt_password(),
            'use_tls': self.use_tls,
            'use_ssl': self.use_ssl,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'reply_to': self.reply_to_email or self.from_email,
            'provider': self.smtp_provider,
        }
    
    def get_platform_smtp_config(self):
        """Get platform default SMTP configuration"""
        from django.conf import settings
        return {
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'username': settings.EMAIL_HOST_USER,
            'password': settings.EMAIL_HOST_PASSWORD,
            'use_tls': settings.EMAIL_USE_TLS,
            'use_ssl': False,
            'from_email': settings.PLATFORM_EMAIL,
            'from_name': settings.PLATFORM_NAME,
            'reply_to': settings.PLATFORM_EMAIL,
            'provider': 'PLATFORM',
        }
    
    def test_connection(self):
        """Test SMTP connection"""
        try:
            config = self.get_smtp_config()
            
            if self.smtp_provider == 'YAGMAIL':
                return self.test_yagmail_connection(config)
            else:
                return self.test_smtp_connection(config)
                
        except Exception as e:
            self.last_test_result = f"Connection failed: {str(e)}"
            self.save()
            return False, str(e)
    
    def test_yagmail_connection(self, config):
        """Test Yagmail connection"""
        try:
            import yagmail
            
            yag = yagmail.SMTP(
                user=config['username'],
                password=config['password'],
                host=config['host'],
                port=config['port']
            )
            
            # Send test email to user
            yag.send(
                to=self.user.email,
                subject='AfriMail Pro - Domain Test Email',
                contents=f'This is a test email from your configured domain: {self.domain_name}'
            )
            
            self.last_test_sent = timezone.now()
            self.last_test_result = "Yagmail test successful"
            self.save()
            
            return True, "Test email sent successfully via Yagmail"
            
        except Exception as e:
            self.last_test_result = f"Yagmail test failed: {str(e)}"
            self.save()
            return False, str(e)
    
    def test_smtp_connection(self, config):
        """Test standard SMTP connection"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # Create SMTP connection
            if config['use_ssl']:
                server = smtplib.SMTP_SSL(config['host'], config['port'])
            else:
                server = smtplib.SMTP(config['host'], config['port'])
                if config['use_tls']:
                    server.starttls()
            
            # Login
            server.login(config['username'], config['password'])
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = self.user.email
            msg['Subject'] = 'AfriMail Pro - SMTP Test Email'
            
            body = f"This is a test email from your configured SMTP settings for domain: {self.domain_name}"
            msg.attach(MIMEText(body, 'plain'))
            
            # Send test email
            server.send_message(msg)
            server.quit()
            
            self.last_test_sent = timezone.now()
            self.last_test_result = "SMTP test successful"
            self.save()
            
            return True, "SMTP test email sent successfully"
            
        except Exception as e:
            self.last_test_result = f"SMTP test failed: {str(e)}"
            self.save()
            return False, str(e)
    
    def generate_verification_token(self):
        """Generate domain verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        self.save()
        return self.verification_token
    
    def verify_dns_records(self):
        """Verify DNS records for domain"""
        import dns.resolver
        
        try:
            # SPF Record Verification
            try:
                spf_records = dns.resolver.resolve(self.domain_name, 'TXT')
                spf_found = any('v=spf1' in str(record) for record in spf_records)
                self.spf_verified = spf_found
            except:
                self.spf_verified = False
            
            # DKIM Record Verification
            try:
                dkim_selector = 'afrimail'  # Default selector
                dkim_domain = f"{dkim_selector}._domainkey.{self.domain_name}"
                dkim_records = dns.resolver.resolve(dkim_domain, 'TXT')
                dkim_found = any('v=DKIM1' in str(record) for record in dkim_records)
                self.dkim_verified = dkim_found
            except:
                self.dkim_verified = False
            
            # DMARC Record Verification
            try:
                dmarc_domain = f"_dmarc.{self.domain_name}"
                dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
                dmarc_found = any('v=DMARC1' in str(record) for record in dmarc_records)
                self.dmarc_verified = dmarc_found
            except:
                self.dmarc_verified = False
            
            # Overall domain verification
            self.domain_verified = self.spf_verified and self.dkim_verified
            self.verification_status = 'VERIFIED' if self.domain_verified else 'FAILED'
            self.last_verification_check = timezone.now()
            
            self.save()
            
            return {
                'spf_verified': self.spf_verified,
                'dkim_verified': self.dkim_verified,
                'dmarc_verified': self.dmarc_verified,
                'domain_verified': self.domain_verified
            }
            
        except Exception as e:
            self.verification_status = 'FAILED'
            self.last_verification_check = timezone.now()
            self.save()
            return {'error': str(e)}
    
    def get_dns_records(self):
        """Get DNS records that user needs to add"""
        return {
            'spf': f'v=spf1 include:spf.afrimailpro.com ~all',
            'dkim': f'afrimail._domainkey.{self.domain_name} IN TXT "v=DKIM1; k=rsa; p=..."',
            'dmarc': f'_dmarc.{self.domain_name} IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@afrimailpro.com"'
        }
    
    def can_send_email(self):
        """Check if domain can send emails (rate limiting)"""
        now = timezone.now()
        
        # Reset counters if needed
        if (now - self.last_rate_reset).total_seconds() >= 86400:  # 24 hours
            self.current_daily_sent = 0
            self.last_rate_reset = now
            self.save()
        
        if (now - self.last_rate_reset).total_seconds() >= 3600:  # 1 hour
            self.current_hourly_sent = 0
        
        # Check limits
        if self.current_daily_sent >= self.daily_send_limit:
            return False, "Daily send limit reached"
        
        if self.current_hourly_sent >= self.hourly_send_limit:
            return False, "Hourly send limit reached"
        
        return True, "Can send"
    
    def increment_send_count(self):
        """Increment send counters"""
        self.current_daily_sent += 1
        self.current_hourly_sent += 1
        self.total_emails_sent += 1
        self.last_email_sent = timezone.now()
        self.save()


class EmailTemplate(models.Model):
    """Email templates for campaigns"""
    
    TEMPLATE_CATEGORIES = [
        ('NEWSLETTER', 'Newsletter'),
        ('PROMOTIONAL', 'Promotional'),
        ('TRANSACTIONAL', 'Transactional'),
        ('WELCOME', 'Welcome Series'),
        ('ABANDONED_CART', 'Abandoned Cart'),
        ('EVENT', 'Event Invitation'),
        ('ANNOUNCEMENT', 'Announcement'),
        ('SURVEY', 'Survey/Feedback'),
        ('SEASONAL', 'Seasonal/Holiday'),
        ('FOLLOW_UP', 'Follow Up'),
        ('THANK_YOU', 'Thank You'),
        ('CUSTOM', 'Custom'),
    ]
    
    INDUSTRIES = [
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
        ('NON_PROFIT', 'Non-Profit'),
        ('GOVERNMENT', 'Government'),
        ('GENERAL', 'General Business'),
    ]
    
    TEMPLATE_TYPES = [
        ('USER', 'User Template'),
        ('SYSTEM', 'System Template'),
        ('PREMIUM', 'Premium Template'),
        ('SHARED', 'Shared Template'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_templates', null=True, blank=True)
    
    # Template Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES, default='CUSTOM')
    industry = models.CharField(max_length=20, choices=INDUSTRIES, default='GENERAL')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='USER')
    
    # Template Content
    subject_line = models.CharField(max_length=200, blank=True, null=True)
    html_content = models.TextField()
    text_content = models.TextField(blank=True, null=True)
    preview_text = models.CharField(max_length=150, blank=True, null=True)
    
    # Template Metadata
    thumbnail = models.ImageField(upload_to='template_thumbnails/', blank=True, null=True)
    variables = models.JSONField(default=list, help_text="List of template variables")
    blocks = models.JSONField(default=list, help_text="Template blocks configuration")
    
    # Template Features
    is_responsive = models.BooleanField(default=True)
    supports_dark_mode = models.BooleanField(default=False)
    has_social_links = models.BooleanField(default=False)
    has_unsubscribe_link = models.BooleanField(default=True)
    
    # Template Status
    is_premium = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)  # Available to all users
    is_active = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    
    # Usage Statistics
    usage_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    
    # SEO and Performance
    avg_open_rate = models.FloatField(default=0.0)
    avg_click_rate = models.FloatField(default=0.0)
    
    # Version Control
    version = models.CharField(max_length=10, default='1.0')
    parent_template = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['-usage_count', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['category', 'industry']),
            models.Index(fields=['is_public', 'is_premium']),
            models.Index(fields=['usage_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage(self):
        """Increment template usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def get_variables(self):
        """Get list of template variables from content"""
        import re
        
        # Extract variables from content
        variables = set()
        content = self.html_content + (self.text_content or '') + (self.subject_line or '')
        
        # Find {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, content)
        
        for match in matches:
            variables.add(match.strip())
        
        return list(variables)
    
    def render_preview(self, sample_data=None):
        """Render template with sample data"""
        if not sample_data:
            sample_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'company': 'Sample Company',
                'email': 'john@example.com',
                'unsubscribe_url': '#unsubscribe',
                'company_address': '123 Business St, Yaoundé, Cameroon',
            }
        
        content = self.html_content
        subject = self.subject_line or ''
        
        # Replace variables
        for key, value in sample_data.items():
            content = content.replace(f'{{{{{key}}}}}', str(value))
            subject = subject.replace(f'{{{{{key}}}}}', str(value))
        
        return {
            'html_content': content,
            'subject': subject,
            'text_content': self.text_content,
            'preview_text': self.preview_text,
        }
    
    def duplicate(self, user=None, name_suffix="Copy"):
        """Create a duplicate of this template"""
        new_name = f"{self.name} - {name_suffix}"
        
        new_template = EmailTemplate.objects.create(
            user=user or self.user,
            name=new_name,
            description=self.description,
            category=self.category,
            industry=self.industry,
            template_type='USER',
            subject_line=self.subject_line,
            html_content=self.html_content,
            text_content=self.text_content,
            preview_text=self.preview_text,
            variables=self.variables.copy(),
            blocks=self.blocks.copy(),
            is_responsive=self.is_responsive,
            supports_dark_mode=self.supports_dark_mode,
            has_social_links=self.has_social_links,
            parent_template=self,
        )
        
        return new_template
    
    def add_rating(self, rating):
        """Add rating to template"""
        if 1 <= rating <= 5:
            total_rating = (self.rating * self.rating_count) + rating
            self.rating_count += 1
            self.rating = total_rating / self.rating_count
            self.save(update_fields=['rating', 'rating_count'])


class EmailLog(models.Model):
    """Log of all email sending activities"""
    
    EMAIL_STATUS = [
        ('QUEUED', 'Queued'),
        ('SENDING', 'Sending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('OPENED', 'Opened'),
        ('CLICKED', 'Clicked'),
        ('BOUNCED', 'Bounced'),
        ('SOFT_BOUNCED', 'Soft Bounced'),
        ('HARD_BOUNCED', 'Hard Bounced'),
        ('COMPLAINED', 'Complained'),
        ('UNSUBSCRIBED', 'Unsubscribed'),
        ('FAILED', 'Failed'),
        ('REJECTED', 'Rejected'),
        ('DEFERRED', 'Deferred'),
    ]
    
    BOUNCE_TYPES = [
        ('SOFT', 'Soft Bounce'),
        ('HARD', 'Hard Bounce'),
        ('TECHNICAL', 'Technical Bounce'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_logs')
    
    # Email Details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient_email = models.EmailField()
    sender_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Sending Information
    smtp_provider = models.CharField(max_length=20, blank=True, null=True)
    domain_config = models.ForeignKey(EmailDomainConfig, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Campaign Reference
    campaign = models.ForeignKey('Campaign', on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=EMAIL_STATUS, default='QUEUED')
    error_message = models.TextField(blank=True, null=True)
    bounce_type = models.CharField(max_length=20, choices=BOUNCE_TYPES, blank=True, null=True)
    bounce_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    complained_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking Information
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    tracking_pixel_id = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Device and Location
    device_type = models.CharField(max_length=20, blank=True, null=True)
    browser = models.CharField(max_length=50, blank=True, null=True)
    operating_system = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    
    # Performance Metrics
    send_time_ms = models.IntegerField(null=True, blank=True)
    delivery_time_ms = models.IntegerField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    webhook_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        ordering = ['-queued_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['campaign']),
            models.Index(fields=['contact']),
            models.Index(fields=['message_id']),
            models.Index(fields=['status', 'queued_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} to {self.recipient_email} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Generate message ID if not provided
        if not self.message_id:
            import time
            timestamp = str(int(time.time() * 1000))
            random_part = secrets.token_hex(8)
            self.message_id = f"afrimail-{timestamp}-{random_part}"
        
        super().save(*args, **kwargs)
    
    def mark_sent(self, send_time_ms=None):
        """Mark email as sent"""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        if send_time_ms:
            self.send_time_ms = send_time_ms
        self.save()
    
    def mark_delivered(self, delivery_time_ms=None):
        """Mark email as delivered"""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        if delivery_time_ms:
            self.delivery_time_ms = delivery_time_ms
        self.save()
    
    def mark_opened(self, ip_address=None, user_agent=None, device_info=None):
        """Mark email as opened"""
        if self.status not in ['OPENED', 'CLICKED']:
            self.status = 'OPENED'
            self.opened_at = timezone.now()
        
        self.open_count += 1
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        
        if device_info:
            self.device_type = device_info.get('device_type')
            self.browser = device_info.get('browser')
            self.operating_system = device_info.get('os')
        
        self.save()
    
    def mark_clicked(self, link_url=None, ip_address=None, user_agent=None):
        """Mark email link as clicked"""
        self.status = 'CLICKED'
        if not self.clicked_at:
            self.clicked_at = timezone.now()
        
        self.click_count += 1
        
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        
        if link_url:
            if 'clicked_links' not in self.metadata:
                self.metadata['clicked_links'] = []
            self.metadata['clicked_links'].append({
                'url': link_url,
                'timestamp': timezone.now().isoformat()
            })
        
        self.save()
    
    def mark_bounced(self, bounce_type='SOFT', reason=None):
        """Mark email as bounced"""
        if bounce_type == 'HARD':
            self.status = 'HARD_BOUNCED'
        elif bounce_type == 'SOFT':
            self.status = 'SOFT_BOUNCED'
        else:
            self.status = 'BOUNCED'
        
        self.bounce_type = bounce_type
        self.bounce_reason = reason
        self.bounced_at = timezone.now()
        self.save()
    
    def mark_complained(self, reason=None):
        """Mark email as complained (spam)"""
        self.status = 'COMPLAINED'
        self.complained_at = timezone.now()
        if reason:
            self.metadata['complaint_reason'] = reason
        self.save()
    
    def mark_unsubscribed(self, reason=None):
        """Mark email as unsubscribed"""
        self.status = 'UNSUBSCRIBED'
        self.unsubscribed_at = timezone.now()
        if reason:
            self.metadata['unsubscribe_reason'] = reason
        self.save()
    
    @property
    def is_delivered(self):
        """Check if email was successfully delivered"""
        return self.status in ['DELIVERED', 'OPENED', 'CLICKED']
    
    @property
    def is_engaged(self):
        """Check if email was engaged with (opened or clicked)"""
        return self.status in ['OPENED', 'CLICKED']
    
    @property
    def delivery_time(self):
        """Get delivery time from sent to delivered"""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None


class EmailProvider(models.Model):
    """Email provider configurations for the platform"""
    
    PROVIDER_TYPES = [
        ('SMTP', 'SMTP Server'),
        ('API', 'API Service'),
        ('WEBHOOK', 'Webhook Service'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    
    # Configuration
    api_endpoint = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=200, blank=True, null=True)
    api_secret = models.CharField(max_length=200, blank=True, null=True)
    
    # SMTP Configuration
    smtp_host = models.CharField(max_length=100, blank=True, null=True)
    smtp_port = models.IntegerField(default=587)
    default_use_tls = models.BooleanField(default=True)
    
    # Rate Limits
    daily_limit = models.IntegerField(default=10000)
    hourly_limit = models.IntegerField(default=1000)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    # Monitoring
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_status = models.CharField(max_length=20, default='UNKNOWN')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_providers'
        verbose_name = 'Email Provider'
        verbose_name_plural = 'Email Providers'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.provider_type})"