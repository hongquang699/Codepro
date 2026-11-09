"""Input Injection Sanitizer & Path Traversal Guard."""
import re
from typing import Tuple

class InputSanitizer:
    SQLI_PATTERNS = [
        r"(--|#|/\*).*$",
        r"\b(union|select|insert|update|delete|drop|alter|truncate|exec|xp_)\b",
        r'\b(or|and)\s+[\w\'"]+\s*=\s*[\w\'"]+',
    ]

    CMD_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\b(nc|ncat|bash|sh|cmd|powershell|curl|wget)\b",
    ]

    @classmethod
    def check_sqli(cls, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        for p in cls.SQLI_PATTERNS:
            if re.search(p, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_cmd_injection(cls, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        for p in cls.CMD_INJECTION_PATTERNS:
            if re.search(p, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        r"""Strips directory traversal sequences (../, ..\)."""
        if not path:
            return ""
        # Remove null bytes
        p = path.replace('\0', '')
        # Remove traversal
        p = re.sub(r'\.\.+[/\\]', '', p)
        return p.lstrip('/\\')
