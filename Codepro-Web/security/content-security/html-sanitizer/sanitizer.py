"""HTML Sanitizer stripping harmful tags and event handlers."""
import re
from typing import Set

ALLOWED_TAGS: Set[str] = {
    'p', 'br', 'b', 'i', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'pre', 'code', 'span', 'blockquote', 'a', 'img', 'hr', 'div'
}

class HTMLSanitizer:
    @classmethod
    def sanitize(cls, html: str) -> str:
        if not html:
            return ""
        # 1. Remove dangerous script, iframe, object, embed tags completely
        clean = re.sub(r'<(script|iframe|object|embed|applet|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<(script|iframe|object|embed|applet|style)[^>]*>', '', clean, flags=re.IGNORECASE)
        
        # 2. Remove javascript: pseudo-protocol
        clean = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', clean, flags=re.IGNORECASE)
        
        # 3. Strip all inline event handlers (onload, onerror, onclick, onmouseover, etc.)
        clean = re.sub(r'\s+on[a-zA-Z]+\s*=\s*["\'][^"\']*["\']', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+on[a-zA-Z]+\s*=\s*[^\s>]+', '', clean, flags=re.IGNORECASE)
        
        return clean
