"""Upload Validator with Magic Number and Extension verification."""
import os
import uuid
from typing import Tuple, List

MAGIC_BYTES = {
    'png': bytes([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    'jpg': bytes([0xff, 0xd8, 0xff]),
    'zip': bytes([0x50, 0x4b, 0x03, 0x04]),
}

class UploadValidator:
    MAX_IMAGE_BYTES = 5 * 1024 * 1024       # 5MB
    MAX_TESTCASE_BYTES = 100 * 1024 * 1024  # 100MB

    @classmethod
    def validate_file(cls, filename: str, content: bytes, file_type: str = 'testcase') -> Tuple[bool, str, str]:
        """Validates extension and magic bytes. Returns (valid, safe_stored_filename, error_msg)."""
        ext = os.path.splitext(filename)[1].lower()
        
        if file_type == 'image':
            if len(content) > cls.MAX_IMAGE_BYTES:
                return False, "", "Kích thước ảnh vượt quá giới hạn 5MB."
            if ext not in ('.png', '.jpg', '.jpeg'):
                return False, "", "Chỉ chấp nhận file ảnh .png, .jpg."
            magic_key = 'png' if ext == '.png' else 'jpg'
            if not content.startswith(MAGIC_BYTES[magic_key]):
                return False, "", "Nội dung file không khớp với định dạng ảnh."

        elif file_type == 'testcase':
            if len(content) > cls.MAX_TESTCASE_BYTES:
                return False, "", "File testcase vượt quá giới hạn 100MB."
            if ext != '.zip':
                return False, "", "Testcases phải được nén dưới định dạng .zip."
            if not content.startswith(MAGIC_BYTES['zip']):
                return False, "", "File zip không hợp lệ."

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        return True, safe_filename, ""
