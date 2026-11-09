from django.test import TestCase
from django.contrib.auth.models import User
from backend.auth.services.two_factor import (
    generate_totp_secret,
    compute_totp,
    verify_totp_code,
    enable_2fa_for_user,
    disable_2fa_for_user,
    get_or_create_2fa,
)


class TwoFactorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='twofauser',
            email='twofauser@example.com',
            password='Password123!'
        )

    def test_totp_generation_and_verification(self):
        secret = generate_totp_secret()
        code = compute_totp(secret)

        self.assertEqual(len(code), 6)
        self.assertTrue(verify_totp_code(secret, code))
        self.assertFalse(verify_totp_code(secret, '000000'))

    def test_enable_and_disable_2fa(self):
        record = get_or_create_2fa(self.user)
        secret = record.secret_key
        current_code = compute_totp(secret)

        success, msg, backup_codes = enable_2fa_for_user(self.user, current_code)
        self.assertTrue(success)
        self.assertEqual(len(backup_codes), 8)

        record.refresh_from_db()
        self.assertTrue(record.is_enabled)

        # Disable using password
        dis_success, dis_msg = disable_2fa_for_user(self.user, 'Password123!')
        self.assertTrue(dis_success)

        record.refresh_from_db()
        self.assertFalse(record.is_enabled)
