from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from backend.auth.security.crypto_hash import (
    hash_sha256,
    hash_sha512,
    hmac_sha256,
    hmac_sha512,
    pbkdf2_sha256,
    pbkdf2_sha512,
    verify_hash,
    verify_password_hash
)
from backend.auth.security.token import (
    hash_token,
    hash_token_sha256,
    hash_token_sha512,
    verify_token
)


class CryptoHashTestCase(TestCase):
    def test_sha256_hashing_and_verification(self):
        secret_data = "user_secret_data_12345"
        h256 = hash_sha256(secret_data)
        # SHA-256 produces 64 hex characters (256 bits)
        self.assertEqual(len(h256), 64)
        self.assertTrue(verify_hash(secret_data, h256))
        self.assertFalse(verify_hash("wrong_data", h256))

    def test_sha512_hashing_and_verification(self):
        secret_data = "user_secret_data_98765"
        h512 = hash_sha512(secret_data)
        # SHA-512 produces 128 hex characters (512 bits)
        self.assertEqual(len(h512), 128)
        self.assertTrue(verify_hash(secret_data, h512))
        self.assertFalse(verify_hash("wrong_data", h512))

    def test_hmac_sha256_and_sha512(self):
        key = "top_secret_hmac_key"
        msg = "payload_content_to_sign"
        hmac256 = hmac_sha256(key, msg)
        hmac512 = hmac_sha512(key, msg)
        self.assertEqual(len(hmac256), 64)
        self.assertEqual(len(hmac512), 128)
        self.assertNotEqual(hmac256, hmac512)

    def test_pbkdf2_sha512_password_hashing(self):
        pwd = "MySuperSecurePassword2026!"
        hashed = pbkdf2_sha512(pwd, iterations=10_000)
        self.assertTrue(hashed.startswith("pbkdf2_sha512$"))
        self.assertTrue(verify_password_hash(pwd, hashed))
        self.assertFalse(verify_password_hash("WrongPassword", hashed))

    def test_pbkdf2_sha256_password_hashing(self):
        pwd = "MySuperSecurePassword2026!"
        hashed = pbkdf2_sha256(pwd, iterations=10_000)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password_hash(pwd, hashed))
        self.assertFalse(verify_password_hash("WrongPassword", hashed))

    def test_django_user_password_uses_pbkdf2_sha512(self):
        user = User.objects.create_user(
            username='sha512_user',
            password='TestPassword512!'
        )
        # Verify Django uses the primary hasher (PBKDF2SHA512PasswordHasher)
        self.assertTrue(user.password.startswith('pbkdf2_sha512$'))
        self.assertTrue(user.check_password('TestPassword512!'))
        self.assertFalse(user.check_password('WrongPassword!'))

    def test_token_hashing_sha256_and_sha512(self):
        raw_token = "random_otp_token_xyz"
        token_256 = hash_token_sha256(raw_token)
        token_512 = hash_token_sha512(raw_token)

        self.assertEqual(len(token_256), 64)
        self.assertEqual(len(token_512), 128)

        # verify_token automatically detects length and verifies in constant time
        self.assertTrue(verify_token(raw_token, token_256))
        self.assertTrue(verify_token(raw_token, token_512))
        self.assertFalse(verify_token("invalid_token", token_256))
        self.assertFalse(verify_token("invalid_token", token_512))
