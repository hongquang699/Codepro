"""Context-aware XSS escaping."""
import html

class XSSFilter:
    @staticmethod
    def escape_text(text: str) -> str:
        if not text:
            return ""
        return html.escape(text, quote=True)
