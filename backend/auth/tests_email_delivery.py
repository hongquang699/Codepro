"""Regression checks for authentication email delivery failures."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from backend.auth.services.email import send_password_reset_email, send_verification_otp_email
from backend.auth.services.registration import initiate_registration
from backend.auth.services.password import initiate_password_reset
from backend.auth.models.email_verification import EmailVerification
from backend.auth.models.password_reset import PasswordReset


class AuthenticationEmailDeliveryTests(TestCase):
    @patch('backend.auth.services.email.send_mail', side_effect=RuntimeError('SMTP unavailable'))
    def test_verification_otp_is_not_reported_sent_on_failure(self, _send_mail):
        self.assertFalse(send_verification_otp_email('user@example.test', 'user', '123456'))

    @patch('backend.auth.services.email.send_mail', side_effect=RuntimeError('SMTP unavailable'))
    def test_password_reset_is_not_reported_sent_on_failure(self, _send_mail):
        self.assertFalse(send_password_reset_email('user@example.test', 'user', 'https://example.test/reset'))

    @patch('backend.auth.services.registration.send_verification_otp_email', return_value=False)
    def test_registration_clears_undelivered_otp(self, _send_email):
        success, _, _ = initiate_registration({
            'username': 'testperson', 'email': 'test@example.test',
            'password': 'password123', 'password_confirm': 'password123'
        })
        self.assertFalse(success)
        self.assertFalse(EmailVerification.objects.exists())

    @patch('backend.auth.services.password.send_password_reset_email', return_value=False)
    def test_reset_clears_undelivered_token(self, _send_email):
        User.objects.create_user('testperson', email='test@example.test', password='password123')
        initiate_password_reset('testperson', '127.0.0.1')
        self.assertFalse(PasswordReset.objects.exists())
