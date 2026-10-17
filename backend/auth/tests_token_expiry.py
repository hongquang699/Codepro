"""Legacy API tokens must expire even when their DB row still exists."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from backend.auth.security.token_auth import ExpiringTokenAuthentication, get_or_rotate_token


class ExpiringTokenTests(TestCase):
    def test_new_password_uses_argon2_and_legacy_hash_upgrades(self):
        user = User.objects.create_user('hash_user', password='password123')
        self.assertTrue(user.password.startswith('argon2$'))
        user.password = make_password('password123', hasher='pbkdf2_sha512')
        user.save(update_fields=['password'])
        self.assertTrue(user.check_password('password123'))
        user.refresh_from_db()
        self.assertTrue(user.password.startswith('argon2$'))

    def test_expired_token_is_rejected_and_rotated_at_login(self):
        user = User.objects.create_user('expiring_user', password='password123')
        old_token = Token.objects.create(user=user)
        Token.objects.filter(pk=old_token.pk).update(created=timezone.now() - timedelta(days=31))

        with self.assertRaises(AuthenticationFailed):
            ExpiringTokenAuthentication().authenticate_credentials(old_token.key)

        new_token = get_or_rotate_token(user)
        self.assertNotEqual(new_token.key, old_token.key)
        self.assertEqual(ExpiringTokenAuthentication().authenticate_credentials(new_token.key)[0], user)
