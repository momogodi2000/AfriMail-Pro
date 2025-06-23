"""
Models package for AfriMail Pro Backend
Import all models here to make them available
"""

# User Models
from .user_models import (
    CustomUser,
    UserProfile,
    UserActivity,
    UserSubscription,
)

# Contact Models
from .contact_models import (
    ContactList,
    Contact,
    ContactInteraction,
    ContactImport,
    ContactCustomField,
)

# Email Models
from .email_models import (
    EmailDomainConfig,
    EmailTemplate,
    EmailLog,
    EmailProvider,
)

# Campaign Models
from .campaign_models import (
    Campaign,
    CampaignVariant,
    AutomationFlow,
    AutomationStep,
    AutomationExecution,
)

# Analytics Models
from .analytics_models import (
    CampaignAnalytics,
    UserAnalytics,
    AnalyticsSnapshot,
    ReportTemplate,
    ABTestResult,
    PlatformAnalytics,
)

__all__ = [
    # User Models
    'CustomUser',
    'UserProfile',
    'UserActivity',
    'UserSubscription',
    
    # Contact Models
    'ContactList',
    'Contact',
    'ContactInteraction',
    'ContactImport',
    'ContactCustomField',
    
    # Email Models
    'EmailDomainConfig',
    'EmailTemplate',
    'EmailLog',
    'EmailProvider',
    
    # Campaign Models
    'Campaign',
    'CampaignVariant',
    'AutomationFlow',
    'AutomationStep',
    'AutomationExecution',
    
    # Analytics Models
    'CampaignAnalytics',
    'UserAnalytics',
    'AnalyticsSnapshot',
    'ReportTemplate',
    'ABTestResult',
    'PlatformAnalytics',
]