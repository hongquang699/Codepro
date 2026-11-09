import secrets
from django.conf import settings
from backend.auth.security.crypto_hash import (
    hash_sha256,
    hash_sha512,
    verify_hash
)


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    rng = secrets.SystemRandom()
    low = 10 ** (length - 1)
    high = (10 ** length) - 1
    return str(rng.randint(low, high))


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str, salt: str = '', algorithm: str = 'sha256') -> str:
    """
    Hash a token or OTP with SHA-256 or SHA-512 and django secret key as salt.
    Never store raw OTPs or reset tokens in database.
    """
    secret = salt or settings.SECRET_KEY
    if algorithm.lower() == 'sha512':
        return hash_sha512(token, salt=secret)
    return hash_sha256(token, salt=secret)


def hash_token_sha256(token: str, salt: str = '') -> str:
    """Explicitly hash with SHA-256 (64 hex characters)."""
    return hash_token(token, salt=salt, algorithm='sha256')


def hash_token_sha512(token: str, salt: str = '') -> str:
    """Explicitly hash with SHA-512 (128 hex characters)."""
    return hash_token(token, salt=salt, algorithm='sha512')


def verify_token(token: str, token_hash: str, salt: str = '') -> bool:
    """
    Compare token against expected hash in constant time.
    Automatically detects SHA-512 (128 chars) or SHA-256 (64 chars).
    """
    secret = salt or settings.SECRET_KEY
    return verify_hash(token, expected_hash=token_hash, salt=secret)
