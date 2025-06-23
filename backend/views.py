"""
Authentication Views for AfriMail Pro - Fixed Version
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views import View
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from .models import CustomUser, UserProfile
from .authentication import AuthenticationService, SecurityService, SessionManager
from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    PasswordResetRequestForm, 
    PasswordResetForm,
    PasswordChangeForm
)
import json
import logging

logger = logging.getLogger(__name__)

# Initialize authentication service
auth_service = AuthenticationService()

class HomePageView(View):
    """Landing page view"""
    
    def get(self, request):
        context = {
            'platform_name': settings.PLATFORM_NAME,
            'features': [
                'Email Marketing Campaigns',
                'Contact Management',
                'Advanced Analytics',
                'Automation Workflows',
                'A/B Testing',
                'Responsive Templates'
            ],
            'pricing': settings.AFRIMAIL_SETTINGS['PRICING'],
            'countries': settings.AFRIMAIL_SETTINGS['SUPPORTED_COUNTRIES'],
        }
        return render(request, 'LandingPage/homepage.html', context)

def homepage(request):
    """Simple homepage function view"""
    return HomePageView.as_view()(request)


class UserRegistrationView(View):
    """User registration view"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = UserRegistrationForm()
        context = {
            'form': form,
            'countries': settings.AFRIMAIL_SETTINGS['SUPPORTED_COUNTRIES'],
            'industries': [choice[0] for choice in CustomUser._meta.get_field('industry').choices],
            'company_sizes': [choice[0] for choice in CustomUser._meta.get_field('company_size').choices],
        }
        return render(request, 'Authentification/register.html', context)
    
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Extract form data
            user_data = {
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'company': form.cleaned_data['company'],
                'phone': form.cleaned_data.get('phone', ''),
                'country': form.cleaned_data.get('country', 'CM'),
                'city': form.cleaned_data.get('city', ''),
                'industry': form.cleaned_data.get('industry', 'OTHER'),
                'company_size': form.cleaned_data.get('company_size', '1-5'),
                'company_website': form.cleaned_data.get('company_website', ''),
                'language': form.cleaned_data.get('language', 'en'),
                'business_type': form.cleaned_data.get('business_type', 'B2C'),
                'target_audience': form.cleaned_data.get('target_audience', ''),
                'marketing_goals': form.cleaned_data.get('marketing_goals', []),
                'source': request.GET.get('source', 'direct'),
            }
            
            # Register user
            result = auth_service.register_user(user_data, request)
            
            if result['success']:
                messages.success(
                    request, 
                    'Registration successful! Please check your email to verify your account.'
                )
                return redirect('login')
            else:
                messages.error(request, result['error'])
        
        context = {
            'form': form,
            'countries': settings.AFRIMAIL_SETTINGS['SUPPORTED_COUNTRIES'],
            'industries': [choice[0] for choice in CustomUser._meta.get_field('industry').choices],
            'company_sizes': [choice[0] for choice in CustomUser._meta.get_field('company_size').choices],
        }
        return render(request, 'Authentification/register.html', context)

def register(request):
    """Simple register function view"""
    return UserRegistrationView.as_view()(request)


class UserLoginView(View):
    """User login view"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = UserLoginForm()
        context = {
            'form': form,
            'next': request.GET.get('next', ''),
        }
        return render(request, 'Authentification/Login.html', context)
    
    def post(self, request):
        form = UserLoginForm(request.POST)
        next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Authenticate user
            result = auth_service.authenticate_user(email, password, request)
            
            if result['success']:
                user = result['user']
                
                # Check for suspicious activity
                if SecurityService.check_suspicious_activity(user, request):
                    # You might want to require additional verification here
                    logger.warning(f"Suspicious login activity for {user.email}")
                
                # Login user
                auth_login(request, user)
                
                # Create session
                SessionManager.create_session(user, request)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to appropriate dashboard
                if user.is_super_admin:
                    return redirect('admin_dashboard')
                else:
                    return redirect(next_url)
            else:
                messages.error(request, result['error'])
        
        context = {
            'form': form,
            'next': next_url,
        }
        return render(request, 'Authentification/Login.html', context)

def login(request):
    """Simple login function view"""
    return UserLoginView.as_view()(request)


@login_required
def logout_view(request):
    """User logout view"""
    user = request.user
    
    # Log logout activity
    result = auth_service.logout_user(user, request)
    
    # Destroy session
    SessionManager.destroy_session(request)
    
    # Logout user
    auth_logout(request)
    
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')


class EmailVerificationView(View):
    """Email verification view"""
    
    def get(self, request, user_id, token):
        result = auth_service.verify_email(user_id, token)
        
        if result['success']:
            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, result['error'])
            return redirect('homepage')


class PasswordResetRequestView(View):
    """Password reset request view"""
    
    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, 'Authentification/Forgot_passwords.html', {'form': form})
    
    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            result = auth_service.request_password_reset(email, request)
            
            messages.success(
                request, 
                'If the email exists in our system, a password reset link has been sent.'
            )
            return redirect('login')
        
        return render(request, 'Authentification/Forgot_passwords.html', {'form': form})

def ForgotPassword(request):
    """Simple forgot password function view"""
    return PasswordResetRequestView.as_view()(request)


class PasswordResetView(View):
    """Password reset view"""
    
    def get(self, request, uid, token):
        form = PasswordResetForm()
        context = {
            'form': form,
            'uid': uid,
            'token': token,
        }
        return render(request, 'Authentification/password_reset.html', context)
    
    def post(self, request, uid, token):
        form = PasswordResetForm(request.POST)
        
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            result = auth_service.reset_password(uid, token, new_password)
            
            if result['success']:
                messages.success(request, 'Password reset successfully! You can now log in.')
                return redirect('login')
            else:
                messages.error(request, result['error'])
        
        context = {
            'form': form,
            'uid': uid,
            'token': token,
        }
        return render(request, 'Authentification/password_reset.html', context)


# Fixed: Use method_decorator instead of applying decorator directly to class
@method_decorator(login_required, name='dispatch')
class PasswordChangeView(View):
    """Password change view for authenticated users"""
    
    def get(self, request):
        form = PasswordChangeForm()
        return render(request, 'Dashboard/settings/change_password.html', {'form': form})
    
    def post(self, request):
        form = PasswordChangeForm(request.POST)
        
        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            
            result = auth_service.change_password(request.user, current_password, new_password)
            
            if result['success']:
                messages.success(request, 'Password changed successfully!')
                return redirect('dashboard_settings')
            else:
                messages.error(request, result['error'])
        
        return render(request, 'Dashboard/settings/change_password.html', {'form': form})


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_super_admin:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Get platform statistics
    from .models import Campaign, Contact, UserSubscription
    from django.db.models import Count, Sum
    
    context = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'trial_users': CustomUser.objects.filter(is_trial_user=True).count(),
        'paid_users': CustomUser.objects.filter(
            is_trial_user=False, 
            subscription_active=True
        ).count(),
        'total_campaigns': Campaign.objects.count(),
        'total_contacts': Contact.objects.count(),
        'total_emails_sent': Campaign.objects.aggregate(
            total=Sum('sent_count')
        )['total'] or 0,
        'recent_users': CustomUser.objects.order_by('-created_at')[:10],
        'platform_revenue': UserSubscription.objects.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'Dashboard/admin/admin_dashboard.html', context)


@login_required
def dashboard(request):
    """Main user dashboard"""
    user = request.user
    
    if user.is_super_admin:
        return redirect('admin_dashboard')
    
    # Get user statistics
    from .models import Campaign, Contact
    from django.db.models import Count, Sum, Avg
    
    user_campaigns = Campaign.objects.filter(user=user)
    user_contacts = Contact.objects.filter(user=user)
    
    context = {
        'user': user,
        'total_campaigns': user_campaigns.count(),
        'total_contacts': user_contacts.filter(is_subscribed=True).count(),
        'total_emails_sent': user_campaigns.aggregate(
            total=Sum('sent_count')
        )['total'] or 0,
        'avg_open_rate': user_campaigns.aggregate(
            avg=Avg('open_rate')
        )['avg'] or 0,
        'recent_campaigns': user_campaigns.order_by('-created_at')[:5],
        'trial_days_remaining': user.trial_days_remaining if user.is_trial_user else None,
        'plan_limits': user.get_plan_limits(),
        'monthly_usage': user.get_monthly_email_usage(),
    }
    
    return render(request, 'Dashboard/marketing/dashboard.html', context)


# API Views for AJAX requests

@csrf_exempt
@require_POST
def check_email_availability(request):
    """Check if email is available for registration"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').lower().strip()
        
        if not email:
            return JsonResponse({'available': False, 'message': 'Email is required'})
        
        # Check if email exists
        exists = CustomUser.objects.filter(email=email).exists()
        
        if exists:
            return JsonResponse({'available': False, 'message': 'Email already registered'})
        
        # Check domain validity
        if not SecurityService.validate_email_domain(email):
            return JsonResponse({'available': False, 'message': 'Email domain not allowed'})
        
        return JsonResponse({'available': True, 'message': 'Email available'})
        
    except Exception as e:
        logger.error(f"Error checking email availability: {str(e)}")
        return JsonResponse({'available': False, 'message': 'Error checking email'})


@csrf_exempt
@require_POST
def validate_password_strength(request):
    """Validate password strength via AJAX"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        
        result = auth_service.validate_password_strength(password)
        
        return JsonResponse({
            'valid': result['valid'],
            'message': result['message'],
            'strength': 'strong' if result['valid'] else 'weak'
        })
        
    except Exception as e:
        logger.error(f"Error validating password: {str(e)}")
        return JsonResponse({'valid': False, 'message': 'Error validating password'})


@login_required
@require_POST
def invalidate_all_sessions(request):
    """Invalidate all user sessions except current one"""
    try:
        user = request.user
        current_session_key = request.session.session_key
        
        # Get all sessions and invalidate them except current
        sessions = SessionManager.get_active_sessions(user)
        invalidated_count = 0
        
        from django.contrib.sessions.models import Session
        for session_info in sessions:
            if session_info['session_key'] != current_session_key:
                try:
                    session = Session.objects.get(session_key=session_info['session_key'])
                    session.delete()
                    invalidated_count += 1
                except Session.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'message': f'Invalidated {invalidated_count} sessions',
            'invalidated_count': invalidated_count
        })
        
    except Exception as e:
        logger.error(f"Error invalidating sessions: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error invalidating sessions'})


@login_required
def get_active_sessions(request):
    """Get list of active sessions for user"""
    try:
        sessions = SessionManager.get_active_sessions(request.user)
        current_session_key = request.session.session_key
        
        # Format sessions for frontend
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                'session_key': session['session_key'][:10] + '...',  # Truncate for security
                'ip_address': session['ip_address'],
                'login_time': session['login_time'],
                'is_current': session['session_key'] == current_session_key,
                'location': 'Unknown',  # You could add geolocation here
                'device': 'Unknown',    # You could parse user agent here
            })
        
        return JsonResponse({
            'success': True,
            'sessions': formatted_sessions
        })
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error retrieving sessions'})


@login_required
def user_profile_api(request):
    """API endpoint for user profile data"""
    try:
        user = request.user
        profile = getattr(user, 'profile', None)
        
        data = {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'company': user.company,
            'phone': user.phone,
            'country': user.country,
            'city': user.city,
            'role': user.get_role_display(),
            'subscription_plan': user.get_subscription_plan_display(),
            'is_trial_user': user.is_trial_user,
            'trial_days_remaining': user.trial_days_remaining,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'profile': {
                'avatar_url': profile.get_avatar_url() if profile else '/static/images/default-avatar.png',
                'company_logo_url': profile.get_company_logo_url() if profile else '/static/images/default-company-logo.png',
                'business_type': getattr(profile, 'business_type', ''),
                'api_key': getattr(profile, 'api_key', ''),
                'api_active': getattr(profile, 'api_active', False),
            } if profile else {}
        }
        
        return JsonResponse({'success': True, 'user': data})
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error retrieving profile'})


def condiction(request):
    """Terms and conditions page"""
    return render(request, 'LandingPage/conditions-utilisation.html')


def policy(request):
    """Privacy policy page"""
    return render(request, 'LandingPage/politique-confidentialite.html')


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


# Error handlers
def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)


def handler403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)


def handler400(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)