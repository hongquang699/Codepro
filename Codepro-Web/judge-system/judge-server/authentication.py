"""
Authentication Middleware for Judge Server.
Validates Bearer tokens for secure inter-service communication.
"""

from typing import Optional
from hmac import compare_digest

class Authenticator:
    def __init__(self, secret_token: str):
        self.secret_token = secret_token

    def verify_auth_header(self, auth_header: Optional[str]) -> bool:
        """
        Validates Authorization header (Bearer <token> or direct token).
        """
        if not self.secret_token:
            return False

        if not auth_header:
            return False

        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return compare_digest(parts[1], self.secret_token)
        elif len(parts) == 1:
            return compare_digest(parts[0], self.secret_token)

        return False
