"""Password Hashing Engine using PBKDF2-HMAC-SHA512 and PBKDF2-HMAC-SHA256 with cryptographically secure salts."""
import hashlib
import hmac
import os
import secrets
from typing import Tuple

ITERATIONS = 260_000

class PasswordHasher:
    @staticmethod
    def hash_password_sha512(password: str) -> str:
        """Hashes password with 32-byte salt using pbkdf2_sha512."""
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, ITERATIONS)
        return f"pbkdf2_sha512${ITERATIONS}${salt.hex()}${key.hex()}"

    @staticmethod
    def hash_password_sha256(password: str) -> str:
        """Hashes password with 32-byte salt using pbkdf2_sha256."""
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
        return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${key.hex()}"

    @staticmethod
    def hash_password(password: str, algorithm: str = 'sha512') -> str:
        """Default hashes with SHA-512 or specified algorithm."""
        if algorithm.lower() == 'sha256':
            return PasswordHasher.hash_password_sha256(password)
        return PasswordHasher.hash_password_sha512(password)

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Constant-time verification of password hash (supports pbkdf2_sha512, pbkdf2_sha256, sha512$, sha256$)."""
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
            return hmac.compare_digest(key, parts[2])

        if algo == 'sha256' and len(parts) == 3:
            salt = parts[1].encode('utf-8')
            key = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
            return hmac.compare_digest(key, parts[2])

        return False
