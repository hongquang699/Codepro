"""Submission payload validation."""
from typing import Tuple, Set

SUPPORTED_LANGUAGES: Set[str] = {
    'CPP17', 'CPP14', 'CPP20', 'C', 'PY3', 'PYTHON3',
    'JAVA', 'JAVA17', 'RUST', 'GO', 'PASCAL', 'KOTLIN', 'CSHARP'
}

class SubmissionValidator:
    MAX_CODE_SIZE_BYTES = 64 * 1024  # 64 KB
    MIN_CODE_SIZE_BYTES = 2          # At least 2 characters

    @classmethod
    def validate(cls, source_code: str, language: str) -> Tuple[bool, str]:
        if not source_code or len(source_code.strip()) < cls.MIN_CODE_SIZE_BYTES:
            return False, "Mã nguồn không được để trống."

        byte_len = len(source_code.encode('utf-8'))
        if byte_len > cls.MAX_CODE_SIZE_BYTES:
            return False, f"Kích thước mã nguồn ({byte_len} bytes) vượt quá giới hạn tối đa 64 KB."

        lang_upper = (language or '').upper()
        if lang_upper not in SUPPORTED_LANGUAGES:
            return False, f"Ngôn ngữ '{language}' không được hỗ trợ. Các ngôn ngữ hợp lệ: {', '.join(sorted(SUPPORTED_LANGUAGES))}"

        # Null bytes check
        if '\0' in source_code:
            return False, "Mã nguồn chứa ký tự không hợp lệ (null bytes)."

        return True, ""
