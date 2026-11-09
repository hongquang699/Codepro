import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from backend.auth.models.email_verification import EmailVerification
from backend.auth.security.token import hash_token
from backend.auth.services.registration import initiate_registration, verify_registration_otp, resend_registration_otp


class RegisterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'username': 'newcoder_test',
            'email': 'newcoder@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
            'terms_agreed': True
        }

    def test_initiate_registration_valid(self):
        success, msg, extra = initiate_registration(self.valid_data)
        self.assertTrue(success)
        self.assertEqual(extra['email'], 'newcoder@example.com')

        # Check DB record
        record = EmailVerification.objects.filter(email='newcoder@example.com').first()
        self.assertIsNotNone(record)
        self.assertFalse(record.is_used)
        # Verify OTP is hashed (length 64 for sha256)
        self.assertEqual(len(record.otp_hash), 64)

    def test_initiate_registration_invalid_password_mismatch(self):
        data = self.valid_data.copy()
        data['password_confirm'] = 'Different123!'
        success, msg, extra = initiate_registration(data)
        self.assertFalse(success)
        self.assertIn('password', extra)

    def test_verify_registration_otp_success(self):
        initiate_registration(self.valid_data)
        record = EmailVerification.objects.get(email='newcoder@example.com')
        
        # Test with known OTP by updating record's otp_hash
        test_otp = '654321'
        record.otp_hash = hash_token(test_otp)
        record.save()

        success, msg, user = verify_registration_otp('newcoder@example.com', test_otp)
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newcoder_test')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('Password123!'))

        # Check record marked used
        record.refresh_from_db()
        self.assertTrue(record.is_used)
        self.assertIsNotNone(record.verified_at)

    def test_verify_registration_otp_wrong_increments_attempts(self):
        initiate_registration(self.valid_data)
        success, msg, user = verify_registration_otp('newcoder@example.com', '000000')
        self.assertFalse(success)
        self.assertIsNone(user)

        record = EmailVerification.objects.get(email='newcoder@example.com')
        self.assertEqual(record.attempts, 1)

    def test_resend_cooldown(self):
        initiate_registration(self.valid_data)
        # Immediately try resending without waiting
        success, msg, wait_sec = resend_registration_otp('newcoder@example.com')
        self.assertFalse(success)
        self.assertGreater(wait_sec, 0)
