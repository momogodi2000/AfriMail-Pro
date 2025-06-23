"""
Tracking Service for AfriMail Pro
Handles email open tracking, click tracking, and analytics
"""
import re
import base64
import uuid
from urllib.parse import urlencode, quote
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class TrackingService:
    """Service for email tracking functionality"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'SITE_URL', 'https://afrimailpro.com')
    
    def add_tracking_pixel(self, html_content, email_log_id):
        """Add invisible tracking pixel to email content"""
        
        # Generate tracking pixel URL
        tracking_url = f"{self.base_url}/t/open/{email_log_id}/"
        
        # Create 1x1 transparent pixel
        tracking_pixel = f'''<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="" />'''
        
        # Add tracking pixel before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
        else:
            # If no body tag, add at the end
            html_content += tracking_pixel
        
        return html_content
    
    def add_click_tracking(self, html_content, email_log_id):
        """Add click tracking to all links in email content"""
        
        # Pattern to match href attributes
        link_pattern = r'href=["\']([^"\']+)["\']'
        
        def replace_link(match):
            original_url = match.group(1)
            
            # Skip if already a tracking URL or special URLs
            if (original_url.startswith(self.base_url) or 
                original_url.startswith('mailto:') or 
                original_url.startswith('tel:') or 
                original_url.startswith('#') or
                'unsubscribe' in original_url.lower()):
                return match.group(0)
            
            # Create tracking URL
            tracking_url = self.create_click_tracking_url(original_url, email_log_id)
            
            return f'href="{tracking_url}"'
        
        # Replace all links with tracking URLs
        tracked_content = re.sub(link_pattern, replace_link, html_content)
        
        return tracked_content
    
    def create_click_tracking_url(self, original_url, email_log_id):
        """Create click tracking URL"""
        
        # Encode the original URL
        encoded_url = base64.urlsafe_b64encode(original_url.encode()).decode()
        
        # Create tracking URL
        tracking_url = f"{self.base_url}/t/click/{email_log_id}/?url={encoded_url}"
        
        return tracking_url
    
    def track_email_open(self, email_log_id, request):
        """Track email open event"""
        from ..models import EmailLog
        
        try:
            email_log = EmailLog.objects.get(id=email_log_id)
            
            # Get tracking information
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_info = self.parse_user_agent(user_agent)
            
            # Mark as opened
            email_log.mark_opened(
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info
            )
            
            # Track contact interaction
            if email_log.contact:
                email_log.contact.add_interaction(
                    'EMAIL_OPENED',
                    {
                        'campaign_id': email_log.campaign.id if email_log.campaign else None,
                        'email_log_id': str(email_log.id),
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'device_type': device_info.get('device_type'),
                        'browser': device_info.get('browser'),
                        'os': device_info.get('os'),
                    }
                )
            
            # Update campaign statistics
            if email_log.campaign:
                self.update_campaign_open_stats(email_log.campaign, email_log.contact)
            
            logger.info(f"Email open tracked: {email_log_id}")
            return True
            
        except EmailLog.DoesNotExist:
            logger.warning(f"Email log not found: {email_log_id}")
            return False
        except Exception as e:
            logger.error(f"Error tracking email open: {str(e)}")
            return False
    
    def track_email_click(self, email_log_id, original_url, request):
        """Track email click event"""
        from ..models import EmailLog
        
        try:
            email_log = EmailLog.objects.get(id=email_log_id)
            
            # Get tracking information
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_info = self.parse_user_agent(user_agent)
            
            # Mark as clicked
            email_log.mark_clicked(
                link_url=original_url,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Track contact interaction
            if email_log.contact:
                email_log.contact.add_interaction(
                    'EMAIL_CLICKED',
                    {
                        'campaign_id': email_log.campaign.id if email_log.campaign else None,
                        'email_log_id': str(email_log.id),
                        'link_url': original_url,
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'device_type': device_info.get('device_type'),
                        'browser': device_info.get('browser'),
                        'os': device_info.get('os'),
                    }
                )
            
            # Update campaign statistics
            if email_log.campaign:
                self.update_campaign_click_stats(email_log.campaign, email_log.contact)
            
            logger.info(f"Email click tracked: {email_log_id} -> {original_url}")
            return True
            
        except EmailLog.DoesNotExist:
            logger.warning(f"Email log not found: {email_log_id}")
            return False
        except Exception as e:
            logger.error(f"Error tracking email click: {str(e)}")
            return False
    
    def update_campaign_open_stats(self, campaign, contact):
        """Update campaign open statistics"""
        try:
            # Check if this is a unique open
            from ..models import EmailLog
            
            previous_opens = EmailLog.objects.filter(
                campaign=campaign,
                contact=contact,
                status__in=['OPENED', 'CLICKED']
            ).count()
            
            if previous_opens == 1:  # First open for this contact
                campaign.unique_opens_count += 1
            
            campaign.opened_count += 1
            campaign.save(update_fields=['opened_count', 'unique_opens_count'])
            
            # Recalculate campaign metrics
            campaign.calculate_metrics()
            
        except Exception as e:
            logger.error(f"Error updating campaign open stats: {str(e)}")
    
    def update_campaign_click_stats(self, campaign, contact):
        """Update campaign click statistics"""
        try:
            # Check if this is a unique click
            from ..models import EmailLog
            
            previous_clicks = EmailLog.objects.filter(
                campaign=campaign,
                contact=contact,
                status='CLICKED'
            ).count()
            
            if previous_clicks == 1:  # First click for this contact
                campaign.unique_clicks_count += 1
            
            campaign.clicked_count += 1
            campaign.save(update_fields=['clicked_count', 'unique_clicks_count'])
            
            # Recalculate campaign metrics
            campaign.calculate_metrics()
            
        except Exception as e:
            logger.error(f"Error updating campaign click stats: {str(e)}")
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def parse_user_agent(self, user_agent):
        """Parse user agent string to extract device information"""
        if not user_agent:
            return {}
        
        user_agent = user_agent.lower()
        
        # Detect device type
        device_type = 'desktop'
        if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipod']):
            device_type = 'mobile'
        elif any(tablet in user_agent for tablet in ['tablet', 'ipad']):
            device_type = 'tablet'
        
        # Detect browser
        browser = 'unknown'
        if 'chrome' in user_agent:
            browser = 'Chrome'
        elif 'firefox' in user_agent:
            browser = 'Firefox'
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            browser = 'Safari'
        elif 'edge' in user_agent:
            browser = 'Edge'
        elif 'opera' in user_agent:
            browser = 'Opera'
        elif 'internet explorer' in user_agent or 'msie' in user_agent:
            browser = 'Internet Explorer'
        
        # Detect operating system
        os = 'unknown'
        if 'windows' in user_agent:
            os = 'Windows'
        elif 'mac' in user_agent:
            os = 'macOS'
        elif 'linux' in user_agent:
            os = 'Linux'
        elif 'android' in user_agent:
            os = 'Android'
        elif 'iphone' in user_agent or 'ipad' in user_agent:
            os = 'iOS'
        
        return {
            'device_type': device_type,
            'browser': browser,
            'os': os,
            'raw_user_agent': user_agent
        }
    
    def track_unsubscribe(self, contact, request, reason=None):
        """Track unsubscribe event"""
        try:
            # Get tracking information
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Unsubscribe contact
            contact.unsubscribe(reason)
            
            # Track interaction
            contact.add_interaction(
                'UNSUBSCRIBE',
                {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Unsubscribe tracked: {contact.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking unsubscribe: {str(e)}")
            return False
    
    def generate_tracking_report(self, campaign):
        """Generate tracking report for campaign"""
        from ..models import EmailLog
        from django.db.models import Count, Q
        
        try:
            # Get email logs for campaign
            email_logs = EmailLog.objects.filter(campaign=campaign)
            
            # Basic statistics
            stats = email_logs.aggregate(
                total_sent=Count('id'),
                delivered=Count('id', filter=Q(status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
                opened=Count('id', filter=Q(status__in=['OPENED', 'CLICKED'])),
                clicked=Count('id', filter=Q(status='CLICKED')),
                bounced=Count('id', filter=Q(status__contains='BOUNCED')),
                complained=Count('id', filter=Q(status='COMPLAINED')),
                unsubscribed=Count('id', filter=Q(status='UNSUBSCRIBED'))
            )
            
            # Device breakdown
            device_stats = {}
            for log in email_logs.filter(device_type__isnull=False):
                device = log.device_type or 'unknown'
                device_stats[device] = device_stats.get(device, 0) + 1
            
            # Time-based analysis
            hourly_opens = {}
            for log in email_logs.filter(opened_at__isnull=False):
                hour = log.opened_at.hour
                hourly_opens[hour] = hourly_opens.get(hour, 0) + 1
            
            # Geographic analysis
            country_stats = {}
            for log in email_logs.filter(country__isnull=False):
                country = log.country
                country_stats[country] = country_stats.get(country, 0) + 1
            
            # Link performance
            link_stats = {}
            for log in email_logs.filter(metadata__clicked_links__isnull=False):
                for link_data in log.metadata.get('clicked_links', []):
                    url = link_data.get('url', 'unknown')
                    link_stats[url] = link_stats.get(url, 0) + 1
            
            return {
                'basic_stats': stats,
                'device_breakdown': device_stats,
                'hourly_opens': hourly_opens,
                'geographic_distribution': country_stats,
                'link_performance': link_stats,
                'tracking_enabled': {
                    'opens': campaign.track_opens,
                    'clicks': campaign.track_clicks,
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating tracking report: {str(e)}")
            return {}
    
    def get_contact_engagement_timeline(self, contact, days=30):
        """Get engagement timeline for a contact"""
        from ..models import ContactInteraction
        from datetime import timedelta
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            interactions = ContactInteraction.objects.filter(
                contact=contact,
                timestamp__gte=start_date,
                interaction_type__in=['EMAIL_SENT', 'EMAIL_OPENED', 'EMAIL_CLICKED', 'UNSUBSCRIBE']
            ).order_by('timestamp')
            
            timeline = []
            for interaction in interactions:
                timeline.append({
                    'date': interaction.timestamp.date(),
                    'time': interaction.timestamp.time(),
                    'type': interaction.interaction_type,
                    'campaign': interaction.campaign.name if interaction.campaign else None,
                    'metadata': interaction.metadata
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting engagement timeline: {str(e)}")
            return []
    
    def decode_tracking_url(self, encoded_url):
        """Decode tracking URL to get original URL"""
        try:
            decoded_bytes = base64.urlsafe_b64decode(encoded_url.encode())
            original_url = decoded_bytes.decode()
            return original_url
        except Exception as e:
            logger.error(f"Error decoding tracking URL: {str(e)}")
            return None
    
    def is_bot_request(self, user_agent):
        """Check if request is from a bot/crawler"""
        if not user_agent:
            return True
        
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'parser',
            'googlebot', 'bingbot', 'slurp', 'duckduckbot',
            'baiduspider', 'yandexbot', 'facebookexternalhit',
            'twitterbot', 'linkedinbot', 'whatsapp', 'telegram',
            'preview', 'prefetch', 'preload'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(indicator in user_agent_lower for indicator in bot_indicators)
    
    def track_social_share(self, contact, platform, url):
        """Track social media sharing"""
        try:
            contact.add_interaction(
                'SOCIAL_SHARE',
                {
                    'platform': platform,
                    'shared_url': url,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Social share tracked: {contact.email} shared on {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking social share: {str(e)}")
            return False
    
    def track_forward(self, original_email_log_id, new_recipient_email):
        """Track email forwarding"""
        from ..models import EmailLog
        
        try:
            original_log = EmailLog.objects.get(id=original_email_log_id)
            
            # Create metadata for tracking
            forward_data = {
                'original_recipient': original_log.recipient_email,
                'forwarded_to': new_recipient_email,
                'original_campaign': original_log.campaign.id if original_log.campaign else None,
                'timestamp': timezone.now().isoformat()
            }
            
            # Track as interaction on original contact
            if original_log.contact:
                original_log.contact.add_interaction('EMAIL_FORWARDED', forward_data)
            
            # Update campaign forward statistics
            if original_log.campaign:
                original_log.campaign.forwards += 1
                original_log.campaign.save(update_fields=['forwards'])
            
            logger.info(f"Email forward tracked: {original_email_log_id} -> {new_recipient_email}")
            return True
            
        except EmailLog.DoesNotExist:
            logger.warning(f"Original email log not found: {original_email_log_id}")
            return False
        except Exception as e:
            logger.error(f"Error tracking email forward: {str(e)}")
            return False