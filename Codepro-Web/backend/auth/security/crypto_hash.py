"""
Cryptographic Hashing Engine (SHA-256 & SHA-512)
Provides enterprise-grade hashing and verification using
SHA-256, SHA-512, and PBKDF2-HMAC (SHA-256/SHA-512) with cryptographically secure salts.
"""
import hashlib
import hmac
import secrets
from typing import Optional
from django.conf import settings
from django.contrib.auth.hashers import BasePasswordHasher, PBKDF2PasswordHasher, mask_hash

DEFAULT_PBKDF2_ITERATIONS = 260_000


def get_default_salt() -> str:
    """Retrieve system salt or Django SECRET_KEY."""
    return settings.SECRET_KEY


# ─────────────────────────────────────────────────────────────────────────────
# 1. Raw & Salted Hashing Functions (SHA-256 & SHA-512)
# ─────────────────────────────────────────────────────────────────────────────

def hash_sha256(data: str, salt: str = '') -> str:
    """
    Compute cryptographic SHA-256 digest (64 hex characters).
    Optional salt is concatenated with data before hashing.
    """
    salt_val = salt or get_default_salt()
    combined = f"{data}:{salt_val}".encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


def hash_sha512(data: str, salt: str = '') -> str:
    """
    Compute cryptographic SHA-512 digest (128 hex characters).
    Optional salt is concatenated with data before hashing.
    """
    salt_val = salt or get_default_salt()
    combined = f"{data}:{salt_val}".encode('utf-8')
    return hashlib.sha512(combined).hexdigest()


def hmac_sha256(key: str, data: str) -> str:
    """Compute HMAC-SHA256 hex digest using secret key."""
    return hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()


def hmac_sha512(key: str, data: str) -> str:
    """Compute HMAC-SHA512 hex digest using secret key."""
    return hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha512).hexdigest()


def pbkdf2_sha256(password: str, salt: Optional[bytes] = None, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> str:
    """
    Hash password using PBKDF2-HMAC-SHA256 with 32-byte cryptographically secure salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt_bytes = salt or secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${salt_bytes.hex()}${key.hex()}"


def pbkdf2_sha512(password: str, salt: Optional[bytes] = None, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> str:
    """
    Hash password using PBKDF2-HMAC-SHA512 with 32-byte cryptographically secure salt.
    Format: pbkdf2_sha512$<iterations>$<salt_hex>$<hash_hex>
    """
    salt_bytes = salt or secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt_bytes, iterations)
    return f"pbkdf2_sha512${iterations}${salt_bytes.hex()}${key.hex()}"


def verify_hash(data: str, expected_hash: str, salt: str = '') -> bool:
    """
    Constant-time comparison for SHA-256 (64 chars) or SHA-512 (128 chars).
    Auto-detects algorithm based on hash length or explicit format.
    """
    if not expected_hash:
        return False

    clean_expected = expected_hash.strip().lower()
    salt_val = salt or get_default_salt()

    if len(clean_expected) == 128:
        # SHA-512
        computed = hash_sha512(data, salt=salt_val)
        return secrets.compare_digest(computed.lower(), clean_expected)
    elif len(clean_expected) == 64:
        # SHA-256
        computed = hash_sha256(data, salt=salt_val)
        return secrets.compare_digest(computed.lower(), clean_expected)

    return False


def verify_password_hash(password: str, hashed: str) -> bool:
    """
    Constant-time verification of PBKDF2 (SHA-512 / SHA-256) or raw SHA hashes.
    """
    if not hashed or '$' not in hashed:
        return False

    parts = hashed.split('$')
    algo = parts[0].lower()

    if algo == 'pbkdf2_sha512' and len(parts) == 4:
        iters = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
        key = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, iters)
        return hmac.compare_digest(key, expected)

    if algo == 'pbkdf2_sha256' and len(parts) == 4:
        iters = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iters)
        return hmac.compare_digest(key, expected)

    if algo == 'sha512' and len(parts) == 3:
        salt = parts[1].encode('utf-8')
        key = hashlib.sha512(salt + password.encode('utf-8')).hexdigest()
        return secrets.compare_digest(key, parts[2])

    if algo == 'sha256' and len(parts) == 3:
        salt = parts[1].encode('utf-8')
        key = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
        return secrets.compare_digest(key, parts[2])

    return False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Django Custom Password Hashers (Plugged into settings.PASSWORD_HASHERS)
# ─────────────────────────────────────────────────────────────────────────────

class PBKDF2SHA512PasswordHasher(PBKDF2PasswordHasher):
    """
    Secure password hasher using PBKDF2-HMAC with SHA-512 digest.
    Provides superior security margins over standard SHA-256.
    """
    algorithm = "pbkdf2_sha512"
    digest = hashlib.sha512


class SHA512PasswordHasher(BasePasswordHasher):
    """Salted SHA-512 password hasher."""
    algorithm = "sha512"

    def salt(self):
        return secrets.token_hex(16)

    def encode(self, password, salt):
        assert password is not None
        assert salt and "$" not in salt
        hash_val = hashlib.sha512(f"{salt}{password}".encode('utf-8')).hexdigest()
        return f"{self.algorithm}${salt}${hash_val}"

    def decode(self, encoded):
        algorithm, salt, hash_val = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {
            "hash": hash_val,
            "iteration": 0,
            "salt": salt,
            "algorithm": algorithm,
        }

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        encoded_2 = self.encode(password, decoded["salt"])
        return secrets.compare_digest(encoded, encoded_2)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            "algorithm": decoded["algorithm"],
            "salt": mask_hash(decoded["salt"], show=2),
            "hash": mask_hash(decoded["hash"]),
        }


class SHA256PasswordHasher(BasePasswordHasher):
    """Salted SHA-256 password hasher."""
    algorithm = "sha256"

    def salt(self):
        return secrets.token_hex(16)

    def encode(self, password, salt):
        assert password is not None
        assert salt and "$" not in salt
        hash_val = hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()
        return f"{self.algorithm}${salt}${hash_val}"

    def decode(self, encoded):
        algorithm, salt, hash_val = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {
            "hash": hash_val,
            "iteration": 0,
            "salt": salt,
            "algorithm": algorithm,
        }

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        encoded_2 = self.encode(password, decoded["salt"])
        return secrets.compare_digest(encoded, encoded_2)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            "algorithm": decoded["algorithm"],
            "salt": mask_hash(decoded["salt"], show=2),
            "hash": mask_hash(decoded["hash"]),
        }
