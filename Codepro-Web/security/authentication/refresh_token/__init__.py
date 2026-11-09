"""Rotating Refresh Token Service."""
import secrets
import time
from typing import Dict, Optional, Tuple

class TokenRotator:
    EXPIRY_DAYS = 30

    # In-memory mapping {refresh_token: (user_id, username, expires_at)}
    _tokens: Dict[str, Tuple[int, str, float]] = {}

    @classmethod
    def issue(cls, user_id: int, username: str) -> str:
        token = secrets.token_urlsafe(48)
        expires = time.time() + (cls.EXPIRY_DAYS * 86400)
        cls._tokens[token] = (user_id, username, expires)
        return token

    @classmethod
    def rotate(cls, old_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Invalidates old token and generates a new one. Detects token reuse."""
        if old_token not in cls._tokens:
            return False, None, "Refresh token không hợp lệ hoặc đã bị thu hồi"
        user_id, username, expires = cls._tokens.pop(old_token)
        if time.time() > expires:
            return False, None, "Refresh token đã hết hạn"
        new_token = cls.issue(user_id, username)
        return True, new_token, username
