"""Email verification token generation and confirmation."""
import hmac
import hashlib
import time
import os
from typing import Tuple

SECRET = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY', '')

class EmailVerificationService:
    TOKEN_LIFETIME = 86400  # 24 hours

    @classmethod
    def generate_token(cls, user_id: int, email: str) -> str:
        if not SECRET:
            raise RuntimeError('DJANGO_SECRET_KEY or SECRET_KEY is required')
        ts = int(time.time())
        data = f"{user_id}:{email}:{ts}"
        sig = hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()
        return f"{data}:{sig}"

    @classmethod
    def verify_token(cls, token: str) -> Tuple[bool, str, int]:
        if not SECRET:
            return False, 'Token signing is not configured', 0
        parts = token.split(':')
        if len(parts) != 4:
            return False, "Token xác thực không hợp lệ", 0
        user_id, email, ts_str, sig = parts
        if time.time() - int(ts_str) > cls.TOKEN_LIFETIME:
            return False, "Link xác thực đã hết hạn", 0
        data = f"{user_id}:{email}:{ts_str}"
        expected = hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False, "Chữ ký xác thực không hợp lệ", 0
        return True, email, int(user_id)
