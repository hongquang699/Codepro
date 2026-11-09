"""Access control for viewing submission source code."""
from typing import Tuple

class SourceProtectionGuard:
    @staticmethod
    def can_view(request_user: str, submission_user: str, user_role: str, contest_status: str = 'none') -> Tuple[bool, str]:
        if not request_user:
            return False, "Yêu cầu đăng nhập."
        
        # Staff and Admins can always inspect
        if user_role in ('admin', 'administrator', 'super-admin'):
            return True, "Authorized"

        # Owner can view their own submission (unless contest strictly forbids)
        if request_user.lower() == submission_user.lower():
            if contest_status == 'running_blind':
                return False, "Cuộc thi đang trong giai đoạn bảo mật mã nguồn."
            return True, "Authorized"

        return False, "Bạn không có quyền xem mã nguồn bài nộp của thí sinh khác."
