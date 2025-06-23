"""
Authentication System for AfriMail Pro
Comprehensive authentication with email verification, password reset, and security features
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from .models import CustomUser, UserProfile, UserActivity
from .services.email_service import EmailService
import secrets
import hashlib
import re
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Comprehensive authentication service"""
    
    def __init__(self):
        self.email_service = None
    
    def register_user(self, user_data, request=None):
        """Register new user with comprehensive validation"""
        try:
            with transaction.atomic():
                # Validate email uniqueness
                if CustomUser.objects.filter(email=user_data['email']).exists():
                    return {'success': False, 'error': 'Email already registered'}
                
                # Validate password strength
                password_validation = self.validate_password_strength(user_data['password'])
                if not password_validation['valid']:
                    return {'success': False, 'error': password_validation['message']}
                
                # Create user
                user = CustomUser.objects.create_user(
                    username=user_data['email'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    company=user_data['company'],
                    phone=user_data.get('phone', ''),
                    country=user_data.get('country', 'CM'),
                    city=user_data.get('city', ''),
                    industry=user_data.get('industry', 'OTHER'),
                    company_size=user_data.get('company_size', '1-5'),
                    role='MARKETING_MANAGER',  # Default role
                    is_active=False,  # Require email verification
                )
                
                # Set additional fields
                user.company_website = user_data.get('company_website', '')
                user.preferred_language = user_data.get('language', 'en')
                user.save()
                
                # Create user profile
                profile = UserProfile.objects.create(
                    user=user,
                    business_type=user_data.get('business_type', 'B2C'),
                    target_audience=user_data.get('target_audience', ''),
                    marketing_goals=user_data.get('marketing_goals', []),
                )
                
                # Start trial
                user.start_trial()
                
                # Generate verification token
                verification_token = user.generate_verification_token()
                
                # Send verification email
                self.send_verification_email(user, verification_token, request)
                
                # Log registration activity
                UserActivity.log_activity(
                    user=user,
                    activity_type='USER_REGISTERED',
                    description='User account created',
                    request=request,
                    metadata={
                        'company': user.company,
                        'country': user.country,
                        'industry': user.industry,
                        'source': user_data.get('source', 'direct')
                    }
                )
                
                logger.info(f"User registered successfully: {user.email}")
                
                return {
                    'success': True,
                    'user_id': user.id,
                    'message': 'Registration successful. Please check your email to verify your account.'
                }
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return {'success': False, 'error': 'Registration failed. Please try again.'}
    
    def authenticate_user(self, email, password, request=None):
        """Authenticate user with enhanced security"""
        try:
            # Check for rate limiting
            if self.is_rate_limited(email, request):
                return {'success': False, 'error': 'Too many login attempts. Please try again later.'}
            
            # Authenticate user
            user = authenticate(username=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    return {'success': False, 'error': 'Account not activated. Please check your email.'}
                
                if not user.is_verified:
                    return {'success': False, 'error': 'Email not verified. Please check your email.'}
                
                # Check subscription status
                can_login, message = user.can_send_emails()
                if not can_login and not user.is_super_admin:
                    return {'success': False, 'error': f'Account access restricted: {message}'}
                
                # Update last login info
                user.last_login = timezone.now()
                if request:
                    user.last_login_ip = self.get_client_ip(request)
                user.save()
                
                # Log successful login
                UserActivity.log_activity(
                    user=user,
                    activity_type='LOGIN',
                    description='Successful login',
                    request=request
                )
                
                # Reset failed login attempts
                self.reset_failed_attempts(email)
                
                logger.info(f"User authenticated successfully: {email}")
                
                return {
                    'success': True,
                    'user': user,
                    'message': 'Login successful'
                }
            else:
                # Log failed attempt
                self.log_failed_attempt(email, request)
                
                logger.warning(f"Failed login attempt: {email}")
                
                return {'success': False, 'error': 'Invalid email or password'}
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': 'Authentication failed. Please try again.'}
    
    def verify_email(self, user_id, token):
        """Verify user email with token"""
        try:
            user = CustomUser.objects.get(id=user_id)
            
            if user.verify_email(token):
                user.is_active = True
                user.save()
                
                # Log email verification
                UserActivity.log_activity(
                    user=user,
                    activity_type='EMAIL_VERIFIED',
                    description='Email address verified'
                )
                
                # Send welcome email
                self.send_welcome_email(user)
                
                logger.info(f"Email verified successfully: {user.email}")
                
                return {'success': True, 'message': 'Email verified successfully'}
            else:
                return {'success': False, 'error': 'Invalid or expired verification token'}
                
        except CustomUser.DoesNotExist:
            return {'success': False, 'error': 'User not found'}
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return {'success': False, 'error': 'Verification failed'}
    
    def request_password_reset(self, email, request=None):
        """Request password reset"""
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Send reset email
            self.send_password_reset_email(user, uid, token, request)
            
            # Log password reset request
            UserActivity.log_activity(
                user=user,
                activity_type='PASSWORD_RESET_REQUESTED',
                description='Password reset requested',
                request=request
            )
            
            logger.info(f"Password reset requested: {email}")
            
            return {'success': True, 'message': 'Password reset email sent'}
            
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not
            return {'success': True, 'message': 'If the email exists, a reset link has been sent'}
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            return {'success': False, 'error': 'Reset request failed'}
    
    def reset_password(self, uid, token, new_password):
        """Reset user password"""
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                # Validate new password
                password_validation = self.validate_password_strength(new_password)
                if not password_validation['valid']:
                    return {'success': False, 'error': password_validation['message']}
                
                # Set new password
                user.set_password(new_password)
                user.save()
                
                # Log password reset
                UserActivity.log_activity(
                    user=user,
                    activity_type='PASSWORD_RESET',
                    description='Password reset completed'
                )
                
                logger.info(f"Password reset completed: {user.email}")
                
                return {'success': True, 'message': 'Password reset successful'}
            else:
                return {'success': False, 'error': 'Invalid or expired reset token'}
                
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return {'success': False, 'error': 'Invalid reset link'}
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return {'success': False, 'error': 'Password reset failed'}
    
    def change_password(self, user, current_password, new_password):
        """Change user password"""
        try:
            # Verify current password
            if not user.check_password(current_password):
                return {'success': False, 'error': 'Current password is incorrect'}
            
            # Validate new password
            password_validation = self.validate_password_strength(new_password)
            if not password_validation['valid']:
                return {'success': False, 'error': password_validation['message']}
            
            # Check if new password is different
            if check_password(new_password, user.password):
                return {'success': False, 'error': 'New password must be different from current password'}
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Log password change
            UserActivity.log_activity(
                user=user,
                activity_type='PASSWORD_CHANGED',
                description='Password changed by user'
            )
            
            logger.info(f"Password changed: {user.email}")
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return {'success': False, 'error': 'Password change failed'}
    
    def validate_password_strength(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return {'valid': False, 'message': 'Password must be at least 8 characters long'}
        
        if not re.search(r'[A-Z]', password):
            return {'valid': False, 'message': 'Password must contain at least one uppercase letter'}
        
        if not re.search(r'[a-z]', password):
            return {'valid': False, 'message': 'Password must contain at least one lowercase letter'}
        
        if not re.search(r'\d', password):
            return {'valid': False, 'message': 'Password must contain at least one number'}
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return {'valid': False, 'message': 'Password must contain at least one special character'}
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            return {'valid': False, 'message': 'Password is too common. Please choose a stronger password'}
        
        return {'valid': True, 'message': 'Password is strong'}
    
    def send_verification_email(self, user, token, request=None):
        """Send email verification email"""
        try:
            # Get site domain
            site = get_current_site(request) if request else None
            domain = site.domain if site else settings.ALLOWED_HOSTS[0]
            
            # Create verification URL
            verification_url = f"http://{domain}/verify-email/{user.id}/{token}/"
            
            # Email context
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': settings.PLATFORM_NAME,
                'company': user.company,
            }
            
            # Send email using platform email
            subject = f"Welcome to {settings.PLATFORM_NAME} - Verify Your Email"
            html_content = render_to_string('emails/verification_email.html', context)
            text_content = render_to_string('emails/verification_email.txt', context)
            
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.PLATFORM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Verification email sent: {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
    
    def send_password_reset_email(self, user, uid, token, request=None):
        """Send password reset email"""
        try:
            # Get site domain
            site = get_current_site(request) if request else None
            domain = site.domain if site else settings.ALLOWED_HOSTS[0]
            
            # Create reset URL
            reset_url = f"http://{domain}/reset-password/{uid}/{token}/"
            
            # Email context
            context = {
                'user': user,
                'reset_url': reset_url,
                'site_name': settings.PLATFORM_NAME,
            }
            
            # Send email
            subject = f"{settings.PLATFORM_NAME} - Password Reset"
            html_content = render_to_string('emails/password_reset_email.html', context)
            text_content = render_to_string('emails/password_reset_email.txt', context)
            
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.PLATFORM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Password reset email sent: {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
    
    def send_welcome_email(self, user):
        """Send welcome email after verification"""
        try:
            # Email context
            context = {
                'user': user,
                'site_name': settings.PLATFORM_NAME,
                'dashboard_url': f"http://{settings.ALLOWED_HOSTS[0]}/dashboard/",
                'trial_days': user.trial_days_remaining,
            }
            
            # Send email
            subject = f"Welcome to {settings.PLATFORM_NAME}!"
            html_content = render_to_string('emails/welcome_email.html', context)
            text_content = render_to_string('emails/welcome_email.txt', context)
            
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.PLATFORM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Welcome email sent: {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
    
    def is_rate_limited(self, email, request):
        """Check if login attempts are rate limited"""
        # Simple rate limiting based on email and IP
        cache_key = f"login_attempts_{email}"
        if request:
            ip = self.get_client_ip(request)
            cache_key += f"_{ip}"
        
        # Use Django cache to track attempts
        from django.core.cache import cache
        attempts = cache.get(cache_key, 0)
        
        return attempts >= 5  # Max 5 attempts
    
    def log_failed_attempt(self, email, request):
        """Log failed login attempt"""
        cache_key = f"login_attempts_{email}"
        if request:
            ip = self.get_client_ip(request)
            cache_key += f"_{ip}"
        
        from django.core.cache import cache
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, 300)  # 5 minutes timeout
    
    def reset_failed_attempts(self, email):
        """Reset failed login attempts"""
        from django.core.cache import cache
        cache_key = f"login_attempts_{email}"
        cache.delete(cache_key)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def logout_user(self, user, request=None):
        """Logout user with activity logging"""
        try:
            # Log logout activity
            UserActivity.log_activity(
                user=user,
                activity_type='LOGOUT',
                description='User logged out',
                request=request
            )
            
            # Clear session
            if request:
                logout(request)
            
            logger.info(f"User logged out: {user.email}")
            
            return {'success': True, 'message': 'Logout successful'}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': 'Logout failed'}
    
    def create_default_users(self):
        """Create default super admin and test users"""
        try:
            # Create Super Admin users
            super_admins = [
                {
                    'email': 'momo@afrimailpro.com',
                    'first_name': 'Momo',
                    'last_name': 'Godi Yvan',
                    'company': 'AfriMail Pro',
                    'phone': '+237123456789',
                    'country': 'CM',
                    'role': 'SUPER_ADMIN'
                },
                {
                    'email': 'admin@afrimailpro.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'company': 'AfriMail Pro',
                    'phone': '+237987654321',
                    'country': 'CM',
                    'role': 'SUPER_ADMIN'
                }
            ]
            
            # Create test clients
            test_clients = [
                {
                    'email': 'client1@test.com',
                    'first_name': 'Jean',
                    'last_name': 'Dupont',
                    'company': 'Boutique Mode Yaoundé',
                    'industry': 'RETAIL',
                    'country': 'CM',
                    'subscription_plan': 'STARTER'
                },
                {
                    'email': 'client2@test.com',
                    'first_name': 'Marie',
                    'last_name': 'Ngono',
                    'company': 'Restaurant Le Palmier',
                    'industry': 'RESTAURANT',
                    'country': 'CM',
                    'subscription_plan': 'PROFESSIONAL'
                },
                {
                    'email': 'client3@test.com',
                    'first_name': 'Paul',
                    'last_name': 'Mbida',
                    'company': 'Agence Voyage Cameroun',
                    'industry': 'TOURISM',
                    'country': 'CM',
                    'subscription_plan': 'ENTERPRISE'
                }
            ]
            
            created_users = []
            
            # Create super admins
            for admin_data in super_admins:
                if not CustomUser.objects.filter(email=admin_data['email']).exists():
                    user = CustomUser.objects.create_user(
                        username=admin_data['email'],
                        email=admin_data['email'],
                        first_name=admin_data['first_name'],
                        last_name=admin_data['last_name'],
                        company=admin_data['company'],
                        phone=admin_data['phone'],
                        country=admin_data['country'],
                        role=admin_data['role'],
                        is_active=True,
                        is_verified=True,
                        is_staff=True,
                        is_superuser=True,
                    )
                    user.set_password('AfriMail2024!@#')
                    user.save()
                    
                    # Create profile
                    UserProfile.objects.create(user=user)
                    
                    created_users.append(user)
                    logger.info(f"Super admin created: {user.email}")
            
            # Create test clients
            for client_data in test_clients:
                if not CustomUser.objects.filter(email=client_data['email']).exists():
                    user = CustomUser.objects.create_user(
                        username=client_data['email'],
                        email=client_data['email'],
                        first_name=client_data['first_name'],
                        last_name=client_data['last_name'],
                        company=client_data['company'],
                        industry=client_data['industry'],
                        country=client_data['country'],
                        subscription_plan=client_data['subscription_plan'],
                        role='MARKETING_MANAGER',
                        is_active=True,
                        is_verified=True,
                    )
                    user.set_password('TestUser123!')
                    user.start_trial()
                    user.save()
                    
                    # Create profile
                    UserProfile.objects.create(user=user)
                    
                    created_users.append(user)
                    logger.info(f"Test client created: {user.email}")
            
            return {
                'success': True,
                'created_count': len(created_users),
                'message': f'Created {len(created_users)} default users'
            }
            
        except Exception as e:
            logger.error(f"Error creating default users: {str(e)}")
            return {'success': False, 'error': str(e)}


class SecurityService:
    """Additional security services"""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data):
        """Hash sensitive data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def check_password_history(user, new_password, history_count=5):
        """Check if password was used recently"""
        # This would require storing password history
        # For now, just check against current password
        return not user.check_password(new_password)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup authentication codes"""
        codes = []
        for _ in range(count):
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    @staticmethod
    def validate_email_domain(email):
        """Validate email domain against blocklist"""
        domain = email.split('@')[1].lower()
        
        # List of suspicious domains to block
        blocked_domains = [
            '10minutemail.com', 'guerrillamail.com', 'tempmail.org',
            'mailinator.com', 'yopmail.com', 'throwaway.email'
        ]
        
        return domain not in blocked_domains
    
    @staticmethod
    def get_user_permissions(user):
        """Get user permissions based on role"""
        if user.is_super_admin:
            return {
                'can_manage_users': True,
                'can_view_analytics': True,
                'can_manage_platform': True,
                'can_access_api': True,
                'can_manage_billing': True,
                'can_export_data': True,
                'can_delete_campaigns': True,
                'can_manage_templates': True,
                'max_contacts': 999999,
                'max_emails_per_month': 999999,
            }
        elif user.is_marketing_manager:
            limits = user.get_plan_limits()
            return {
                'can_manage_users': False,
                'can_view_analytics': True,
                'can_manage_platform': False,
                'can_access_api': 'api_access' in limits['features'],
                'can_manage_billing': True,
                'can_export_data': True,
                'can_delete_campaigns': True,
                'can_manage_templates': True,
                'max_contacts': limits['max_contacts'],
                'max_emails_per_month': limits['max_emails_per_month'],
            }
        else:
            return {
                'can_manage_users': False,
                'can_view_analytics': False,
                'can_manage_platform': False,
                'can_access_api': False,
                'can_manage_billing': False,
                'can_export_data': False,
                'can_delete_campaigns': False,
                'can_manage_templates': False,
                'max_contacts': 0,
                'max_emails_per_month': 0,
            }
    
    @staticmethod
    def check_suspicious_activity(user, request):
        """Check for suspicious login activity"""
        current_ip = SecurityService.get_client_ip(request)
        
        # Check if IP has changed significantly
        if user.last_login_ip and user.last_login_ip != current_ip:
            # This is a simple check - in production you'd want geolocation comparison
            logger.warning(f"IP change detected for user {user.email}: {user.last_login_ip} -> {current_ip}")
            return True
        
        # Check login frequency
        recent_activities = UserActivity.objects.filter(
            user=user,
            activity_type='LOGIN',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_activities > 10:  # More than 10 logins in an hour
            logger.warning(f"Frequent login attempts detected for user {user.email}")
            return True
        
        return False
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    @staticmethod
    def sanitize_input(data):
        """Sanitize user input"""
        if isinstance(data, str):
            # Remove potentially dangerous characters
            data = re.sub(r'[<>"\']', '', data)
            data = data.strip()
        return data
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_session(request):
        """Validate user session"""
        if not request.user.is_authenticated:
            return False
        
        # Check session age
        session_age = request.session.get('login_time')
        if session_age:
            login_time = timezone.datetime.fromisoformat(session_age)
            if timezone.now() - login_time > timedelta(hours=24):
                return False
        
        return True


class TwoFactorAuthService:
    """Two-factor authentication service"""
    
    @staticmethod
    def generate_totp_secret():
        """Generate TOTP secret for 2FA"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_backup_codes():
        """Generate backup codes for 2FA"""
        return SecurityService.generate_backup_codes()
    
    @staticmethod
    def send_sms_code(phone_number, code):
        """Send SMS verification code"""
        # This would integrate with SMS service like Twilio
        # For now, just log the code
        logger.info(f"SMS code {code} would be sent to {phone_number}")
        return True
    
    @staticmethod
    def verify_totp_code(secret, code):
        """Verify TOTP code"""
        # This would use a library like pyotp
        # For now, return True for demo
        return True
    
    @staticmethod
    def enable_2fa_for_user(user, method='app'):
        """Enable 2FA for user"""
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
        
        # Generate secret and backup codes
        secret = TwoFactorAuthService.generate_totp_secret()
        backup_codes = TwoFactorAuthService.generate_backup_codes()
        
        # Store in user profile (you'd want to encrypt these)
        user.profile.two_factor_enabled = True
        user.profile.two_factor_method = method
        user.profile.totp_secret = secret
        user.profile.backup_codes = backup_codes
        user.profile.save()
        
        return {
            'secret': secret,
            'backup_codes': backup_codes,
            'qr_code_url': f"otpauth://totp/AfriMail Pro:{user.email}?secret={secret}&issuer=AfriMail Pro"
        }


class SessionManager:
    """Session management utilities"""
    
    @staticmethod
    def create_session(user, request):
        """Create user session with security measures"""
        # Set session data
        request.session['user_id'] = str(user.id)
        request.session['login_time'] = timezone.now().isoformat()
        request.session['ip_address'] = SecurityService.get_client_ip(request)
        
        # Set session expiry
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        
        # Log session creation
        UserActivity.log_activity(
            user=user,
            activity_type='SESSION_CREATED',
            description='User session created',
            request=request
        )
    
    @staticmethod
    def destroy_session(request):
        """Safely destroy user session"""
        request.session.flush()
    
    @staticmethod
    def get_active_sessions(user):
        """Get active sessions for user"""
        from django.contrib.sessions.models import Session
        from django.contrib.auth import SESSION_KEY
        
        sessions = []
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            data = session.get_decoded()
            if data.get('user_id') == str(user.id):
                sessions.append({
                    'session_key': session.session_key,
                    'ip_address': data.get('ip_address'),
                    'login_time': data.get('login_time'),
                    'expire_date': session.expire_date,
                })
        
        return sessions
    
    @staticmethod
    def invalidate_all_sessions(user):
        """Invalidate all sessions for user"""
        from django.contrib.sessions.models import Session
        
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            data = session.get_decoded()
            if data.get('user_id') == str(user.id):
                session.delete()
        
        UserActivity.log_activity(
            user=user,
            activity_type='ALL_SESSIONS_INVALIDATED',
            description='All user sessions invalidated'
        )