


# backend/management/commands/create_default_templates.py
"""
Management command to create default email templates
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.models import EmailTemplate, CustomUser


class Command(BaseCommand):
    help = 'Create default email templates for AfriMail Pro'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default email templates...')
        
        templates = [
            {
                'name': 'Welcome Email',
                'category': 'WELCOME',
                'industry': 'GENERAL',
                'template_type': 'SYSTEM',
                'subject_line': 'Welcome to {{company}} - Let\'s Get Started!',
                'html_content': self.get_welcome_template(),
                'text_content': self.get_welcome_text(),
                'is_public': True,
                'description': 'A warm welcome email for new subscribers',
            },
            {
                'name': 'Newsletter Template',
                'category': 'NEWSLETTER',
                'industry': 'GENERAL',
                'template_type': 'SYSTEM',
                'subject_line': '{{company}} Newsletter - {{month}} {{year}}',
                'html_content': self.get_newsletter_template(),
                'text_content': self.get_newsletter_text(),
                'is_public': True,
                'description': 'Professional newsletter template',
            },
            {
                'name': 'Promotional Offer',
                'category': 'PROMOTIONAL',
                'industry': 'RETAIL',
                'template_type': 'SYSTEM',
                'subject_line': 'Special Offer: {{offer_percentage}}% Off Everything!',
                'html_content': self.get_promotional_template(),
                'text_content': self.get_promotional_text(),
                'is_public': True,
                'description': 'Eye-catching promotional email template',
            },
            {
                'name': 'Event Invitation',
                'category': 'EVENT',
                'industry': 'GENERAL',
                'template_type': 'SYSTEM',
                'subject_line': 'You\'re Invited: {{event_name}}',
                'html_content': self.get_event_template(),
                'text_content': self.get_event_text(),
                'is_public': True,
                'description': 'Professional event invitation template',
            }
        ]
        
        created_count = 0
        
        try:
            with transaction.atomic():
                for template_data in templates:
                    template, created = EmailTemplate.objects.get_or_create(
                        name=template_data['name'],
                        template_type='SYSTEM',
                        defaults=template_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'Created template: {template.name}')
                    else:
                        self.stdout.write(f'Template already exists: {template.name}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} email templates'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating templates: {str(e)}')
            )
    
    def get_welcome_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to {{company}}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #0F172A; color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; background: #f9f9f9; }
                .button { display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {{company}}!</h1>
                    <p>We're excited to have you on board, {{first_name}}!</p>
                </div>
                <div class="content">
                    <h2>Thanks for joining us</h2>
                    <p>Hi {{first_name}},</p>
                    <p>Welcome to {{company}}! We're thrilled to have you as part of our community.</p>
                    <p>Here's what you can expect from us:</p>
                    <ul>
                        <li>Regular updates about our products and services</li>
                        <li>Exclusive offers and discounts</li>
                        <li>Helpful tips and insights</li>
                    </ul>
                    <p style="text-align: center;">
                        <a href="{{dashboard_url}}" class="button">Get Started</a>
                    </p>
                </div>
                <div class="footer">
                    <p>{{company}}<br>{{company_address}}</p>
                    <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_welcome_text(self):
        return '''
        Welcome to {{company}}!
        
        Hi {{first_name}},
        
        Welcome to {{company}}! We're thrilled to have you as part of our community.
        
        Here's what you can expect from us:
        - Regular updates about our products and services
        - Exclusive offers and discounts
        - Helpful tips and insights
        
        Get started: {{dashboard_url}}
        
        Best regards,
        The {{company}} Team
        
        {{company}}
        {{company_address}}
        
        Unsubscribe: {{unsubscribe_url}}
        '''
    
    def get_newsletter_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{company}} Newsletter</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                .container { max-width: 600px; margin: 0 auto; }
                .header { background: #1E293B; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .article { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
                .button { display: inline-block; background: #10B981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{company}} Newsletter</h1>
                    <p>{{month}} {{year}} Edition</p>
                </div>
                <div class="content">
                    <p>Hello {{first_name}},</p>
                    
                    <div class="article">
                        <h2>Article Title 1</h2>
                        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                        <a href="#" class="button">Read More</a>
                    </div>
                    
                    <div class="article">
                        <h2>Article Title 2</h2>
                        <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
                        <a href="#" class="button">Read More</a>
                    </div>
                    
                    <div class="article">
                        <h2>Article Title 3</h2>
                        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
                        <a href="#" class="button">Read More</a>
                    </div>
                </div>
                <div class="footer">
                    <p>{{company}}<br>{{company_address}}</p>
                    <p><a href="{{unsubscribe_url}}">Unsubscribe</a> | <a href="{{preferences_url}}">Update Preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_newsletter_text(self):
        return '''
        {{company}} Newsletter - {{month}} {{year}} Edition
        
        Hello {{first_name}},
        
        Article Title 1
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        Read More: [LINK]
        
        Article Title 2
        Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        Read More: [LINK]
        
        Article Title 3
        Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        Read More: [LINK]
        
        {{company}}
        {{company_address}}
        
        Unsubscribe: {{unsubscribe_url}}
        Update Preferences: {{preferences_url}}
        '''
    
    def get_promotional_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Special Offer from {{company}}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }
                .offer { background: #FF6B6B; color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }
                .content { padding: 30px; text-align: center; }
                .cta-button { display: inline-block; background: #FF6B6B; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-size: 18px; font-weight: bold; margin: 20px 0; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 SPECIAL OFFER 🎉</h1>
                    <p>Don't miss out on this amazing deal!</p>
                </div>
                <div class="offer">
                    {{offer_percentage}}% OFF EVERYTHING!
                </div>
                <div class="content">
                    <h2>Hi {{first_name}},</h2>
                    <p>For a limited time only, we're offering <strong>{{offer_percentage}}% off</strong> everything in our store!</p>
                    <p>This incredible offer ends on <strong>{{offer_end_date}}</strong>, so don't wait!</p>
                    <a href="{{shop_url}}" class="cta-button">SHOP NOW</a>
                    <p><small>Use code: <strong>{{offer_code}}</strong> at checkout</small></p>
                </div>
                <div class="footer">
                    <p>{{company}}<br>{{company_address}}</p>
                    <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_promotional_text(self):
        return '''
        🎉 SPECIAL OFFER from {{company}} 🎉
        
        {{offer_percentage}}% OFF EVERYTHING!
        
        Hi {{first_name}},
        
        For a limited time only, we're offering {{offer_percentage}}% off everything in our store!
        
        This incredible offer ends on {{offer_end_date}}, so don't wait!
        
        Shop now: {{shop_url}}
        Use code: {{offer_code}} at checkout
        
        {{company}}
        {{company_address}}
        
        Unsubscribe: {{unsubscribe_url}}
        '''
    
    def get_event_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>You're Invited: {{event_name}}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f9f9f9; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: #2D3748; color: white; padding: 30px; text-align: center; }
                .event-details { background: #EDF2F7; padding: 30px; }
                .detail-item { margin: 15px 0; }
                .detail-label { font-weight: bold; color: #4A5568; }
                .rsvp-button { display: inline-block; background: #48BB78; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 You're Invited!</h1>
                    <h2>{{event_name}}</h2>
                </div>
                <div class="event-details">
                    <p>Hi {{first_name}},</p>
                    <p>We're excited to invite you to our upcoming event:</p>
                    
                    <div class="detail-item">
                        <span class="detail-label">Event:</span> {{event_name}}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Date:</span> {{event_date}}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Time:</span> {{event_time}}
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Location:</span> {{event_location}}
                    </div>
                    
                    <p>{{event_description}}</p>
                    
                    <div style="text-align: center;">
                        <a href="{{rsvp_url}}" class="rsvp-button">RSVP NOW</a>
                    </div>
                    
                    <p><small>Please RSVP by {{rsvp_deadline}}</small></p>
                </div>
                <div class="footer">
                    <p>{{company}}<br>{{company_address}}</p>
                    <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def get_event_text(self):
        return '''
        📅 You're Invited: {{event_name}}
        
        Hi {{first_name}},
        
        We're excited to invite you to our upcoming event:
        
        Event: {{event_name}}
        Date: {{event_date}}
        Time: {{event_time}}
        Location: {{event_location}}
        
        {{event_description}}
        
        RSVP: {{rsvp_url}}
        Please RSVP by {{rsvp_deadline}}
        
        {{company}}
        {{company_address}}
        
        Unsubscribe: {{unsubscribe_url}}
        '''
