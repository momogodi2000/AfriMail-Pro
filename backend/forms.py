"""
Authentication Forms for AfriMail Pro
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import CustomUser, UserProfile
from .authentication import SecurityService
import re


class UserRegistrationForm(forms.ModelForm):
    """User registration form with comprehensive validation"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a strong password',
            'id': 'password',
        }),
        help_text='Password must be at least 8 characters with uppercase, lowercase, number, and special character.'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'confirm_password',
        }),
        help_text='Re-enter your password for confirmation.'
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'agree_terms',
        }),
        error_messages={
            'required': 'You must agree to the terms and conditions to register.'
        }
    )
    
    marketing_consent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'marketing_consent',
        }),
        help_text='Receive marketing emails and product updates.'
    )
    
    # Business information
    business_type = forms.ChoiceField(
        choices=[
            ('B2B', 'Business to Business'),
            ('B2C', 'Business to Consumer'),
            ('B2B2C', 'Business to Business to Consumer'),
            ('MARKETPLACE', 'Marketplace'),
            ('NON_PROFIT', 'Non-Profit'),
            ('GOVERNMENT', 'Government'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'business_type',
        })
    )
    
    target_audience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your target audience...',
            'id': 'target_audience',
        }),
        help_text='Brief description of your target customers/audience.'
    )
    
    marketing_goals = forms.MultipleChoiceField(
        choices=[
            ('increase_sales', 'Increase Sales'),
            ('build_brand', 'Build Brand Awareness'),
            ('customer_retention', 'Customer Retention'),
            ('lead_generation', 'Lead Generation'),
            ('event_promotion', 'Event Promotion'),
            ('newsletter', 'Newsletter/Content Sharing'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
        help_text='Select your primary marketing goals.'
    )
    
    # Source tracking
    source = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'company', 'phone',
            'country', 'city', 'industry', 'company_size', 'company_website',
            'preferred_language'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
                'required': True,
                'id': 'first_name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
                'required': True,
                'id': 'last_name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': True,
                'id': 'email',
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name',
                'required': True,
                'id': 'company',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 123 456 789',
                'id': 'phone',
            }),
            'country': forms.Select(attrs={
                'class': 'form-control',
                'id': 'country',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
                'id': 'city',
            }),
            'industry': forms.Select(attrs={
                'class': 'form-control',
                'id': 'industry',
            }),
            'company_size': forms.Select(attrs={
                'class': 'form-control',
                'id': 'company_size',
            }),
            'company_website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
                'id': 'company_website',
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control',
                'id': 'preferred_language',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add country choices
        self.fields['country'].choices = CustomUser.COUNTRIES
        
        # Add required asterisk to required fields
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = True
                if 'placeholder' in field.widget.attrs:
                    field.widget.attrs['placeholder'] += ' *'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError('Email is required.')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        
        # Validate email domain
        if not SecurityService.validate_email_domain(email):
            raise ValidationError('This email domain is not allowed.')
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            # Basic phone validation for African numbers
            phone_clean = re.sub(r'\D', '', phone)
            if not re.match(r'^\+?[1-9]\d{8,14}$', phone_clean):
                raise ValidationError('Please enter a valid phone number.')
        
        return phone
    
    def clean_company_website(self):
        website = self.cleaned_data.get('company_website', '').strip()
        
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        return website
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if not password:
            raise ValidationError('Password is required.')
        
        # Use authentication service for validation
        from .authentication import AuthenticationService
        auth_service = AuthenticationService()
        validation_result = auth_service.validate_password_strength(password)
        
        if not validation_result['valid']:
            raise ValidationError(validation_result['message'])
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Check password confirmation
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'Passwords do not match.'
                })
        
        return cleaned_data


class UserLoginForm(forms.Form):
    """User login form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'required': True,
            'id': 'email',
            'autocomplete': 'email',
        }),
        help_text='Enter your registered email address.'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True,
            'id': 'password',
            'autocomplete': 'current-password',
        }),
        help_text='Enter your account password.'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember_me',
        }),
        help_text='Keep me logged in on this device.'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            # Basic validation - actual authentication is done in view
            if not email or not password:
                raise ValidationError('Both email and password are required.')
        
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Password reset request form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True,
            'id': 'email',
            'autocomplete': 'email',
        }),
        help_text='Enter the email address associated with your account.'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        return email


class PasswordResetForm(forms.Form):
    """Password reset form"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'required': True,
            'id': 'new_password',
            'autocomplete': 'new-password',
        }),
        help_text='Password must be at least 8 characters with uppercase, lowercase, number, and special character.'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'required': True,
            'id': 'confirm_password',
            'autocomplete': 'new-password',
        }),
        help_text='Re-enter your new password for confirmation.'
    )
    
    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        
        if not password:
            raise ValidationError('Password is required.')
        
        # Use authentication service for validation
        from .authentication import AuthenticationService
        auth_service = AuthenticationService()
        validation_result = auth_service.validate_password_strength(password)
        
        if not validation_result['valid']:
            raise ValidationError(validation_result['message'])
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'Passwords do not match.'
                })
        
        return cleaned_data


class PasswordChangeForm(forms.Form):
    """Password change form for authenticated users"""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password',
            'required': True,
            'id': 'current_password',
            'autocomplete': 'current-password',
        }),
        help_text='Enter your current password for verification.'
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password',
            'required': True,
            'id': 'new_password',
            'autocomplete': 'new-password',
        }),
        help_text='Password must be at least 8 characters with uppercase, lowercase, number, and special character.'
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'required': True,
            'id': 'confirm_password',
            'autocomplete': 'new-password',
        }),
        help_text='Re-enter your new password for confirmation.'
    )
    
    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        
        if not password:
            raise ValidationError('Password is required.')
        
        # Use authentication service for validation
        from .authentication import AuthenticationService
        auth_service = AuthenticationService()
        validation_result = auth_service.validate_password_strength(password)
        
        if not validation_result['valid']:
            raise ValidationError(validation_result['message'])
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'Passwords do not match.'
                })
        
        if current_password and new_password:
            if current_password == new_password:
                raise ValidationError({
                    'new_password': 'New password must be different from current password.'
                })
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone', 'company', 'company_website',
            'city', 'industry', 'company_size', 'preferred_language',
            'email_notifications', 'marketing_notifications'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+237 123 456 789',
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name',
            }),
            'company_website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'industry': forms.Select(attrs={
                'class': 'form-control',
            }),
            'company_size': forms.Select(attrs={
                'class': 'form-control',
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control',
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'marketing_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class UserProfileExtendedForm(forms.ModelForm):
    """Extended user profile form"""
    
    class Meta:
        model = UserProfile
        fields = [
            'company_description', 'business_type', 'target_audience',
            'default_sender_name', 'default_sender_email', 'default_reply_to',
            'email_signature', 'daily_summary', 'weekly_report', 'campaign_alerts'
        ]
        
        widgets = {
            'company_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your company...',
            }),
            'business_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'target_audience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your target audience...',
            }),
            'default_sender_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Default Sender Name',
            }),
            'default_sender_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'sender@yourcompany.com',
            }),
            'default_reply_to': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'replyto@yourcompany.com',
            }),
            'email_signature': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your email signature...',
            }),
            'daily_summary': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'weekly_report': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'campaign_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class TwoFactorSetupForm(forms.Form):
    """Two-factor authentication setup form"""
    
    method = forms.ChoiceField(
        choices=[
            ('app', 'Authenticator App'),
            ('sms', 'SMS'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        help_text='Choose your preferred 2FA method.'
    )
    
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+237 123 456 789',
            'id': 'phone_number',
        }),
        help_text='Required for SMS verification.'
    )
    
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'id': 'verification_code',
            'maxlength': 6,
        }),
        help_text='Enter the 6-digit code from your authenticator app or SMS.'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        phone_number = cleaned_data.get('phone_number')
        
        if method == 'sms' and not phone_number:
            raise ValidationError({
                'phone_number': 'Phone number is required for SMS verification.'
            })
        
        return cleaned_data


class ContactForm(forms.Form):
    """Contact form for support/inquiries"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name',
            'required': True,
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email',
            'required': True,
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject',
            'required': True,
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message...',
            'required': True,
        })
    )
    
    category = forms.ChoiceField(
        choices=[
            ('support', 'Technical Support'),
            ('sales', 'Sales Inquiry'),
            ('billing', 'Billing Question'),
            ('feature', 'Feature Request'),
            ('bug', 'Bug Report'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )


class NewsletterSubscriptionForm(forms.Form):
    """Newsletter subscription form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'required': True,
        })
    )
    
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name (Optional)',
        })
    )
    
    interests = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('email_marketing', 'Email Marketing Tips'),
            ('product_updates', 'Product Updates'),
            ('case_studies', 'Case Studies'),
            ('industry_news', 'Industry News'),
            ('tutorials', 'Tutorials & Guides'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        })
    )