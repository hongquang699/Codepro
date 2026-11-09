"""Internal Service Mutual Auth (Backend <-> Judge Server)."""
import hmac
import hashlib
import time
import os
from typing import Tuple

SECRET = os.environ.get('JUDGE_SECRET_TOKEN', '')

class APIKeyManager:
    @classmethod
    def generate_signature(cls, payload: str) -> str:
        if not SECRET:
            raise RuntimeError('JUDGE_SECRET_TOKEN is required')
        return hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def verify_request(cls, auth_header: str) -> bool:
        if not auth_header or not SECRET:
            return False
        expected = f"Bearer {SECRET}"
        return hmac.compare_digest(auth_header.strip(), expected)
