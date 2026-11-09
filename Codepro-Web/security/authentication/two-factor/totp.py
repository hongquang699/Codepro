"""RFC 6238 Time-based One-Time Password (TOTP) Authenticator."""
import hmac
import hashlib
import struct
import time
import base64
import secrets
from typing import Tuple, List

class TwoFactorAuthenticator:
    TIME_STEP = 30
    DIGITS = 6

    @classmethod
    def generate_secret(cls) -> str:
        """Generates a 32-character Base32 secret key."""
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode('utf-8').rstrip('=')

    @classmethod
    def generate_backup_codes(cls, count: int = 8) -> List[str]:
        """Generates 8-digit single-use backup recovery codes."""
        return [f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}" for _ in range(count)]

    @classmethod
    def get_totp_code(cls, secret_b32: str, time_offset: int = 0) -> str:
        padding = '=' * ((8 - len(secret_b32) % 8) % 8)
        key = base64.b32decode(secret_b32 + padding, casefold=True)
        counter = int((time.time() + time_offset) // cls.TIME_STEP)
        msg = struct.pack('>Q', counter)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code_int = struct.unpack('>I', h[offset:offset + 4])[0] & 0x7FFFFFFF
        return f"{code_int % (10 ** cls.DIGITS):06d}"

    @classmethod
    def verify_code(cls, secret_b32: str, code: str) -> bool:
        """Verifies code with window allowance for clock drift (-1, 0, +1 step)."""
        if not code or len(code.strip()) != 6:
            return False
        clean_code = code.strip()
        for offset in [-30, 0, 30]:
            if hmac.compare_digest(cls.get_totp_code(secret_b32, offset), clean_code):
                return True
        return False
