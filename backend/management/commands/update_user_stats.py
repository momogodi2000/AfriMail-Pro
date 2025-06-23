backend/management/commands/update_user_stats.py
"""
Management command to update user statistics
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from backend.models import CustomUser, Campaign, Contact


class Command(BaseCommand):
    help = 'Update user statistics'
    
    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        updated_count = 0
        
        for user in users:
            # Update campaign count
            campaign_count = Campaign.objects.filter(user=user).count()
            
            # Update contact count
            contact_count = Contact.objects.filter(user=user, is_subscribed=True).count()
            
            # Update total emails sent
            total_emails = Campaign.objects.filter(user=user).aggregate(
                total=Sum('sent_count')
            )['total'] or 0
            
            # Update user
            user.total_campaigns = campaign_count
            user.total_contacts = contact_count
            user.total_emails_sent = total_emails
            user.save(update_fields=['total_campaigns', 'total_contacts', 'total_emails_sent'])
            
            updated_count += 1
            
            if updated_count % 100 == 0:
                self.stdout.write(f'Updated {updated_count} users...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated statistics for {updated_count} users')
        )
