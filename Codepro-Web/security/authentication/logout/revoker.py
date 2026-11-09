"""Session and token revoker on logout."""
import time
from typing import Set
from security.logging import SecurityLogger

class TokenRevoker:
    # Set of revoked token identifiers (jti)
    _revoked_tokens: Set[str] = set()

    @classmethod
    def revoke(cls, jti: str, username: str = '', ip: str = '127.0.0.1'):
        if jti:
            cls._revoked_tokens.add(jti)
            SecurityLogger.log_auth('LOGOUT', username, ip, True, {'jti': jti})

    @classmethod
    def is_revoked(cls, jti: str) -> bool:
        return jti in cls._revoked_tokens
