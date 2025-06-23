"""
URL Configuration for AfriMail Pro Backend - Fixed Version
"""
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from . import views

# Authentication URLs
auth_patterns = [
    # Public authentication pages
    path('', views.homepage, name='homepage'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password management
    path('forgot-password/', views.ForgotPassword, name='forgot_password'),
    path('reset-password/<str:uid>/<str:token>/', views.PasswordResetView.as_view(), name='password_reset'),
    # Fix: Remove .as_view() since PasswordChangeView is decorated with @login_required
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),

    # Email verification
    path('verify-email/<uuid:user_id>/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    
    # Legal pages
    path('conditions/', views.condiction, name='conditions'),
    path('policy/', views.policy, name='policy'),
    
    # AJAX API endpoints
    path('check-email/', views.check_email_availability, name='check_email_availability'),
    path('validate-password/', views.validate_password_strength, name='validate_password_strength'),
    path('user-profile/', views.user_profile_api, name='user_profile_api'),
    path('active-sessions/', views.get_active_sessions, name='get_active_sessions'),
    path('invalidate-sessions/', views.invalidate_all_sessions, name='invalidate_all_sessions'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]

# Dashboard URLs
dashboard_patterns = [
    # Main dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # User settings
    path('settings/', TemplateView.as_view(template_name='Dashboard/settings/settings.html'), name='dashboard_settings'),
    path('settings/profile/', TemplateView.as_view(template_name='Dashboard/settings/profile.html'), name='profile_settings'),
    path('settings/security/', TemplateView.as_view(template_name='Dashboard/settings/security.html'), name='security_settings'),
    path('settings/billing/', TemplateView.as_view(template_name='Dashboard/settings/billing.html'), name='billing_settings'),
    path('settings/api/', TemplateView.as_view(template_name='Dashboard/settings/api.html'), name='api_settings'),
]

# Campaign URLs (placeholder for future development)
campaign_patterns = [
    path('campaigns/', TemplateView.as_view(template_name='Dashboard/campaigns/campaigns.html'), name='campaigns'),
    path('campaigns/create/', TemplateView.as_view(template_name='Dashboard/campaigns/create.html'), name='create_campaign'),
    path('campaigns/<uuid:pk>/', TemplateView.as_view(template_name='Dashboard/campaigns/detail.html'), name='campaign_detail'),
    path('campaigns/<uuid:pk>/edit/', TemplateView.as_view(template_name='Dashboard/campaigns/edit.html'), name='edit_campaign'),
    path('campaigns/<uuid:pk>/duplicate/', TemplateView.as_view(template_name='Dashboard/campaigns/duplicate.html'), name='duplicate_campaign'),
    path('campaigns/<uuid:pk>/analytics/', TemplateView.as_view(template_name='Dashboard/campaigns/analytics.html'), name='campaign_analytics'),
]

# Contact URLs (placeholder for future development)
contact_patterns = [
    path('contacts/', TemplateView.as_view(template_name='Dashboard/contacts/contacts.html'), name='contacts'),
    path('contacts/import/', TemplateView.as_view(template_name='Dashboard/contacts/import.html'), name='import_contacts'),
    path('contacts/lists/', TemplateView.as_view(template_name='Dashboard/contacts/lists.html'), name='contact_lists'),
    path('contacts/segments/', TemplateView.as_view(template_name='Dashboard/contacts/segments.html'), name='contact_segments'),
    path('contacts/<uuid:pk>/', TemplateView.as_view(template_name='Dashboard/contacts/detail.html'), name='contact_detail'),
]

# Template URLs (placeholder for future development)
template_patterns = [
    path('templates/', TemplateView.as_view(template_name='Dashboard/templates/templates.html'), name='templates'),
    path('templates/create/', TemplateView.as_view(template_name='Dashboard/templates/create.html'), name='create_template'),
    path('templates/<uuid:pk>/', TemplateView.as_view(template_name='Dashboard/templates/detail.html'), name='template_detail'),
    path('templates/<uuid:pk>/edit/', TemplateView.as_view(template_name='Dashboard/templates/edit.html'), name='edit_template'),
]

# Analytics URLs (placeholder for future development)
analytics_patterns = [
    path('analytics/', TemplateView.as_view(template_name='Dashboard/analytics/analytics.html'), name='analytics'),
    path('analytics/reports/', TemplateView.as_view(template_name='Dashboard/analytics/reports.html'), name='analytics_reports'),
    path('analytics/audience/', TemplateView.as_view(template_name='Dashboard/analytics/audience.html'), name='audience_analytics'),
]

# Automation URLs (placeholder for future development)
automation_patterns = [
    path('automation/', TemplateView.as_view(template_name='Dashboard/automation/automation.html'), name='automation'),
    path('automation/create/', TemplateView.as_view(template_name='Dashboard/automation/create.html'), name='create_automation'),
    path('automation/<uuid:pk>/', TemplateView.as_view(template_name='Dashboard/automation/detail.html'), name='automation_detail'),
]

# Tracking URLs (for email open/click tracking)
tracking_patterns = [
    path('t/open/<uuid:email_log_id>/', TemplateView.as_view(template_name='tracking/pixel.html'), name='track_open'),
    path('t/click/<uuid:email_log_id>/', TemplateView.as_view(template_name='tracking/redirect.html'), name='track_click'),
    path('unsubscribe/<uuid:contact_id>/', TemplateView.as_view(template_name='tracking/unsubscribe.html'), name='unsubscribe'),
    path('preferences/<uuid:contact_id>/', TemplateView.as_view(template_name='tracking/preferences.html'), name='email_preferences'),
]

# Admin URLs (for super admin)
admin_patterns = [
    path('admin/users/', TemplateView.as_view(template_name='Dashboard/admin/users.html'), name='admin_users'),
    path('admin/analytics/', TemplateView.as_view(template_name='Dashboard/admin/analytics.html'), name='admin_analytics'),
    path('admin/system/', TemplateView.as_view(template_name='Dashboard/admin/system.html'), name='admin_system'),
    path('admin/billing/', TemplateView.as_view(template_name='Dashboard/admin/billing.html'), name='admin_billing'),
    path('admin/support/', TemplateView.as_view(template_name='Dashboard/admin/support.html'), name='admin_support'),
]

# Combine all URL patterns
urlpatterns = auth_patterns + dashboard_patterns + campaign_patterns + contact_patterns + template_patterns + analytics_patterns + automation_patterns + tracking_patterns + admin_patterns

# Add app name for namespacing
app_name = 'backend'