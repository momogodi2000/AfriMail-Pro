"""
Email Service for AfriMail Pro
Handles all email sending operations with Yagmail and SMTP
"""
import yagmail
import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context
from ..models import EmailDomainConfig, EmailLog, Contact, Campaign
from .tracking_service import TrackingService
import uuid
import re

logger = logging.getLogger(__name__)

class EmailService:
    """Comprehensive email sending service with multiple provider support"""
    
    def __init__(self, user):
        self.user = user
        self.tracking_service = TrackingService()
        
    def get_sending_config(self, domain_config=None):
        """Get email sending configuration"""
        if domain_config:
            return domain_config.get_smtp_config()
        
        # Get user's primary domain config
        primary_config = EmailDomainConfig.objects.filter(
            user=self.user,
            is_primary=True,
            is_active=True
        ).first()
        
        if primary_config:
            return primary_config.get_smtp_config()
        
        # Fallback to platform default
        return {
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'username': settings.EMAIL_HOST_USER,
            'password': settings.EMAIL_HOST_PASSWORD,
            'use_tls': settings.EMAIL_USE_TLS,
            'from_email': settings.PLATFORM_EMAIL,
            'from_name': settings.PLATFORM_NAME,
            'provider': 'PLATFORM',
        }
    
    def send_single_email(self, recipient_email, subject, html_content, 
                         text_content=None, domain_config=None, 
                         contact=None, campaign=None, attachments=None):
        """Send a single email"""
        
        # Get sending configuration
        config = self.get_sending_config(domain_config)
        
        # Create email log entry
        email_log = EmailLog.objects.create(
            user=self.user,
            recipient_email=recipient_email,
            sender_email=config['from_email'],
            subject=subject,
            smtp_provider=config['provider'],
            domain_config=domain_config,
            contact=contact,
            campaign=campaign,
            status='QUEUED'
        )
        
        try:
            # Add tracking pixels if enabled
            if campaign and campaign.track_opens:
                html_content = self.tracking_service.add_tracking_pixel(
                    html_content, email_log.id
                )
            
            # Add click tracking if enabled
            if campaign and campaign.track_clicks:
                html_content = self.tracking_service.add_click_tracking(
                    html_content, email_log.id
                )
            
            # Add unsubscribe link
            html_content = self.add_unsubscribe_link(html_content, contact)
            
            # Send based on provider
            if config['provider'] == 'YAGMAIL':
                result = self._send_with_yagmail(
                    config, recipient_email, subject, html_content, 
                    text_content, attachments
                )
            else:
                result = self._send_with_smtp(
                    config, recipient_email, subject, html_content, 
                    text_content, attachments
                )
            
            if result['success']:
                email_log.mark_sent(result.get('send_time_ms'))
                
                # Update domain statistics
                if domain_config:
                    domain_config.increment_send_count()
                
                # Update contact interaction
                if contact:
                    contact.add_interaction('EMAIL_SENT', {
                        'campaign_id': campaign.id if campaign else None,
                        'subject': subject
                    })
                
                logger.info(f"Email sent successfully to {recipient_email}")
                return {'success': True, 'email_log_id': email_log.id}
            else:
                email_log.status = 'FAILED'
                email_log.error_message = result['error']
                email_log.save()
                
                logger.error(f"Failed to send email to {recipient_email}: {result['error']}")
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            email_log.status = 'FAILED'
            email_log.error_message = str(e)
            email_log.save()
            
            logger.error(f"Exception sending email to {recipient_email}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_with_yagmail(self, config, recipient_email, subject, 
                          html_content, text_content=None, attachments=None):
        """Send email using Yagmail"""
        start_time = time.time()
        
        try:
            # Initialize Yagmail
            yag = yagmail.SMTP(
                user=config['username'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
                smtp_starttls=config['use_tls'],
                smtp_ssl=config.get('use_ssl', False)
            )
            
            # Prepare content
            if text_content:
                content = [text_content, yagmail.inline(html_content)]
            else:
                content = yagmail.inline(html_content)
            
            # Send email
            yag.send(
                to=recipient_email,
                subject=subject,
                contents=content,
                attachments=attachments,
                headers={'From': f"{config['from_name']} <{config['from_email']}>"}
            )
            
            yag.close()
            
            send_time_ms = int((time.time() - start_time) * 1000)
            return {'success': True, 'send_time_ms': send_time_ms}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_with_smtp(self, config, recipient_email, subject, 
                       html_content, text_content=None, attachments=None):
        """Send email using standard SMTP"""
        start_time = time.time()
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg['Reply-To'] = config.get('reply_to', config['from_email'])
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Create SMTP connection
            if config.get('use_ssl'):
                server = smtplib.SMTP_SSL(config['host'], config['port'])
            else:
                server = smtplib.SMTP(config['host'], config['port'])
                if config['use_tls']:
                    server.starttls()
            
            # Login and send
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            send_time_ms = int((time.time() - start_time) * 1000)
            return {'success': True, 'send_time_ms': send_time_ms}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _add_attachment(self, msg, attachment):
        """Add attachment to email message"""
        try:
            if hasattr(attachment, 'read'):
                # File-like object
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment.name}'
                )
                msg.attach(part)
            else:
                # File path
                with open(attachment, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.split("/")[-1]}'
                    )
                    msg.attach(part)
        except Exception as e:
            logger.warning(f"Failed to add attachment: {str(e)}")
    
    def send_bulk_emails(self, recipients, subject, html_content, 
                        text_content=None, domain_config=None, 
                        campaign=None, batch_size=50):
        """Send emails to multiple recipients in batches"""
        
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            for recipient in batch:
                if isinstance(recipient, dict):
                    email = recipient['email']
                    contact = recipient.get('contact')
                    personalized_content = self.personalize_content(
                        html_content, contact
                    )
                    personalized_subject = self.personalize_content(
                        subject, contact
                    )
                else:
                    email = recipient
                    contact = None
                    personalized_content = html_content
                    personalized_subject = subject
                
                result = self.send_single_email(
                    recipient_email=email,
                    subject=personalized_subject,
                    html_content=personalized_content,
                    text_content=text_content,
                    domain_config=domain_config,
                    contact=contact,
                    campaign=campaign
                )
                
                if result['success']:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'email': email,
                        'error': result['error']
                    })
                
                # Rate limiting - small delay between emails
                time.sleep(0.1)
            
            # Longer delay between batches
            if i + batch_size < len(recipients):
                time.sleep(1)
        
        return results
    
    def personalize_content(self, content, contact):
        """Personalize email content for contact"""
        if not contact or not content:
            return content
        
        personalization_data = contact.get_personalization_data()
        
        # Replace placeholders
        for key, value in personalization_data.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        
        return content
    
    def add_unsubscribe_link(self, html_content, contact):
        """Add unsubscribe link to email content"""
        if not contact:
            return html_content
        
        unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{contact.id}/"
        unsubscribe_link = f'''
        <div style="text-align: center; font-size: 12px; color: #666; margin-top: 20px; padding: 20px;">
            <p>
                You received this email because you are subscribed to our mailing list.<br>
                <a href="{unsubscribe_url}" style="color: #666;">Unsubscribe</a> | 
                <a href="{settings.SITE_URL}/preferences/{contact.id}/" style="color: #666;">Update Preferences</a>
            </p>
            <p style="margin-top: 10px;">
                {self.user.company}<br>
                {getattr(self.user.profile, 'company_address', '') if hasattr(self.user, 'profile') else ''}
            </p>
        </div>
        '''
        
        # Add unsubscribe link before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{unsubscribe_link}</body>')
        else:
            html_content += unsubscribe_link
        
        return html_content
    
    def send_test_email(self, test_email, subject, html_content, 
                       text_content=None, domain_config=None):
        """Send test email"""
        return self.send_single_email(
            recipient_email=test_email,
            subject=f"[TEST] {subject}",
            html_content=html_content,
            text_content=text_content,
            domain_config=domain_config
        )
    
    def send_transactional_email(self, template_name, recipient_email, 
                                context_data, domain_config=None):
        """Send transactional email using template"""
        from ..models import EmailTemplate
        
        try:
            # Get template
            template = EmailTemplate.objects.get(
                name=template_name,
                template_type__in=['SYSTEM', 'USER'],
                is_active=True
            )
            
            # Render template with context
            rendered = template.render_preview(context_data)
            
            return self.send_single_email(
                recipient_email=recipient_email,
                subject=rendered['subject'],
                html_content=rendered['html_content'],
                text_content=rendered.get('text_content'),
                domain_config=domain_config
            )
            
        except EmailTemplate.DoesNotExist:
            logger.error(f"Template {template_name} not found")
            return {'success': False, 'error': f'Template {template_name} not found'}
    
    def send_automation_email(self, contact, subject, html_content, 
                             automation=None):
        """Send email as part of automation flow"""
        return self.send_single_email(
            recipient_email=contact.email,
            subject=subject,
            html_content=html_content,
            contact=contact
        )
    
    def validate_email_address(self, email):
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_email_deliverability_score(self, domain_config=None):
        """Get deliverability score for domain"""
        config = domain_config or self.get_sending_config()
        
        # Basic scoring based on configuration
        score = 0
        
        # Domain verification
        if hasattr(config, 'domain_verified') and config.domain_verified:
            score += 30
        
        # SPF verification
        if hasattr(config, 'spf_verified') and config.spf_verified:
            score += 25
        
        # DKIM verification
        if hasattr(config, 'dkim_verified') and config.dkim_verified:
            score += 25
        
        # DMARC verification
        if hasattr(config, 'dmarc_verified') and config.dmarc_verified:
            score += 20
        
        return min(score, 100)
    
    def get_sending_statistics(self, days=30):
        """Get sending statistics for user"""
        from django.db.models import Count, Q
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        stats = EmailLog.objects.filter(
            user=self.user,
            created_at__gte=start_date
        ).aggregate(
            total_sent=Count('id'),
            delivered=Count('id', filter=Q(status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
            opened=Count('id', filter=Q(status__in=['OPENED', 'CLICKED'])),
            clicked=Count('id', filter=Q(status='CLICKED')),
            bounced=Count('id', filter=Q(status__in=['BOUNCED', 'HARD_BOUNCED', 'SOFT_BOUNCED'])),
            complained=Count('id', filter=Q(status='COMPLAINED')),
            unsubscribed=Count('id', filter=Q(status='UNSUBSCRIBED'))
        )
        
        # Calculate rates
        total = stats['total_sent'] or 1
        delivered = stats['delivered'] or 0
        
        return {
            'total_sent': stats['total_sent'],
            'delivered': delivered,
            'delivery_rate': (delivered / total) * 100,
            'open_rate': (stats['opened'] / delivered) * 100 if delivered > 0 else 0,
            'click_rate': (stats['clicked'] / delivered) * 100 if delivered > 0 else 0,
            'bounce_rate': (stats['bounced'] / total) * 100,
            'complaint_rate': (stats['complained'] / total) * 100,
            'unsubscribe_rate': (stats['unsubscribed'] / total) * 100,
        }