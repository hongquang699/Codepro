"""Problem visibility access controller."""
from typing import Tuple

class ProblemAccessControl:
    @staticmethod
    def can_access(problem_status: str, is_public: bool, request_user: str, author: str, user_role: str) -> Tuple[bool, str]:
        # Public problems
        if is_public and problem_status == 'published':
            return True, "Public"

        # Admins can access everything
        if user_role in ('admin', 'administrator', 'super-admin'):
            return True, "Admin access"

        # Problem Setter / Author
        if request_user and request_user.lower() == (author or '').lower():
            return True, "Author access"

        # Hidden / Draft problem
        return False, "Bài tập này đang ở chế độ riêng tư (Draft) hoặc chỉ mở trong cuộc thi."
