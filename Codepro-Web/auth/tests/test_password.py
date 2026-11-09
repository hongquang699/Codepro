import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from backend.auth.models.password_reset import PasswordReset
from backend.auth.security.token import hash_token
from backend.auth.services.password import initiate_password_reset, complete_password_reset, change_user_password


class PasswordTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'passuser'
        self.email = 'passuser@example.com'
        self.password = 'InitialPassword123!'
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

    def test_forgot_password_generic_response(self):
        # Existing user
        res1 = self.client.post(
            '/api/v1/auth/forgot-password',
            data=json.dumps({'username_or_email': self.email}),
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 200)

        # Non-existing user returns IDENTICAL success response (no user enumeration!)
        res2 = self.client.post(
            '/api/v1/auth/forgot-password',
            data=json.dumps({'username_or_email': 'nobody@nonexistent.org'}),
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res1.json()['message'], res2.json()['message'])

    def test_complete_password_reset(self):
        # Create token
        initiate_password_reset(self.email, ip_address='127.0.0.1')
        record = PasswordReset.objects.filter(user=self.user, used_at__isnull=True).first()
        self.assertIsNotNone(record)

        # Test completing reset with token
        test_raw_token = 'secret_reset_token_test'
        record.token_hash = hash_token(test_raw_token)
        record.save()

        success, msg = complete_password_reset(test_raw_token, 'BrandNewPass123!', 'BrandNewPass123!')
        self.assertTrue(success)

        # Verify user password updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewPass123!'))

        # Verify token used
        record.refresh_from_db()
        self.assertTrue(record.is_used)

    def test_change_user_password(self):
        success, msg = change_user_password(self.user, self.password, 'UpdatedPass456!', 'UpdatedPass456!')
        self.assertTrue(success)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('UpdatedPass456!'))
