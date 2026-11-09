"""Testcase protection guard preventing directory traversal and unauthorized downloads."""
import os
import re
from typing import Tuple

class TestcaseGuard:
    @staticmethod
    def sanitize_testcase_path(base_dir: str, problem_code: str, filename: str) -> Tuple[bool, str]:
        """Prevents path traversal, ensuring target path stays strictly inside problem directory."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', problem_code):
            return False, "Mã bài toán không hợp lệ."

        # Disallow directory traversal characters
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Tên file testcase không hợp lệ (path traversal detected)."

        clean_path = os.path.normpath(os.path.join(base_dir, problem_code, 'cases', filename))
        expected_prefix = os.path.normpath(os.path.join(base_dir, problem_code, 'cases'))

        if not clean_path.startswith(expected_prefix):
            return False, "Đường dẫn testcase vi phạm sandbox biên giới."

        return True, clean_path
