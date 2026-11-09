"""Secure Cookie Header Builder."""
from typing import Dict, Any

class SecureCookieBuilder:
    @staticmethod
    def build_set_cookie(name: str, value: str, max_age: int = 86400, path: str = '/', http_only: bool = True, secure: bool = True, same_site: str = 'Lax') -> str:
        parts = [f"{name}={value}", f"Path={path}", f"Max-Age={max_age}"]
        if http_only:
            parts.append("HttpOnly")
        if secure:
            parts.append("Secure")
        if same_site:
            parts.append(f"SameSite={same_site}")
        return "; ".join(parts)
