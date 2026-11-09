"""Secure Password Recovery Service."""
import os
import hashlib
import hmac
import time
import secrets
from typing import Tuple

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY', '')

class PasswordRecoveryService:
    TOKEN_VALIDITY_SECONDS = 3600  # 1 hour

    @classmethod
    def generate_reset_token(cls, username: str, user_id: int) -> str:
        if not SECRET_KEY:
            raise RuntimeError('DJANGO_SECRET_KEY or SECRET_KEY is required')
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        payload = f"{user_id}:{username}:{timestamp}:{nonce}"
        sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}:{sig}"

    @classmethod
    def verify_reset_token(cls, token: str) -> Tuple[bool, str]:
        if not SECRET_KEY:
            return False, 'Token signing is not configured'
        parts = token.split(':')
        if len(parts) != 5:
            return False, "Token không hợp lệ"
        user_id, username, ts_str, nonce, sig = parts
        timestamp = int(ts_str)
        if time.time() - timestamp > cls.TOKEN_VALIDITY_SECONDS:
            return False, "Token đã hết hạn"
        payload = f"{user_id}:{username}:{timestamp}:{nonce}"
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, "Chữ ký token không hợp lệ"
        return True, username
