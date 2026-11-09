"""CSRF Token Protection."""
import secrets
import hmac
from typing import Tuple

class CSRFGuard:
    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def verify(cookie_token: str, header_token: str) -> bool:
        if not cookie_token or not header_token:
            return False
        return hmac.compare_digest(cookie_token.strip(), header_token.strip())
