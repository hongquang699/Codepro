"""Mutual authentication between Judge Dispatcher and Worker Nodes."""
import hmac
import hashlib
import os
from typing import Tuple

SECRET = os.environ.get('JUDGE_SECRET_TOKEN', '')

class WorkerAuthenticator:
    @classmethod
    def verify_token(cls, token: str) -> bool:
        if not token or not SECRET:
            return False
        clean = token.replace('Bearer ', '').strip()
        return hmac.compare_digest(clean, SECRET)
