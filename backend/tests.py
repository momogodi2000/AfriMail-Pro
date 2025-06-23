from django.test import TestCase

# Create your tests here.
"""
Tests for authentication system
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from backend.authentication import AuthenticationService, SecurityService

User = get_user_model()


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_service = AuthenticationService()
        
        # Test user data
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company',
            'country': 'CM',
        }
    
    def test_user_registration(self):
        """Test user registration"""
        result = self.auth_service.register_user(self.user_data)
        self.assertTrue(result['success'])
        
        # Check user was created
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.company, 'Test Company')
        self.assertFalse(user.is_active)  # Should be inactive until verified
    
    def test_duplicate_email_registration(self):
        """Test registration with duplicate email"""
        # Create first user
        self.auth_service.register_user(self.user_data)
        
        # Try to register again with same email
        result = self.auth_service.register_user(self.user_data)
        self.assertFalse(result['success'])
        self.assertIn('already registered', result['error'])
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        weak_password = '123'
        result = self.auth_service.validate_password_strength(weak_password)
        self.assertFalse(result['valid'])
        
        strong_password = 'StrongPass123!'
        result = self.auth_service.validate_password_strength(strong_password)
        self.assertTrue(result['valid'])
    
    def test_user_authentication(self):
        """Test user authentication"""
        # Register and activate user
        self.auth_service.register_user(self.user_data)
        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.is_verified = True
        user.save()
        
        # Test authentication
        result = self.auth_service.authenticate_user(
            self.user_data['email'],
            self.user_data['password']
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['user'].email, self.user_data['email'])


class SecurityServiceTestCase(TestCase):
    def test_email_domain_validation(self):
        """Test email domain validation"""
        valid_email = 'test@gmail.com'
        self.assertTrue(SecurityService.validate_email_domain(valid_email))
        
        invalid_email = 'test@10minutemail.com'
        self.assertFalse(SecurityService.validate_email_domain(invalid_email))
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token = SecurityService.generate_secure_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)
        
        # Test different tokens are generated
        token2 = SecurityService.generate_secure_token()
        self.assertNotEqual(token, token2)