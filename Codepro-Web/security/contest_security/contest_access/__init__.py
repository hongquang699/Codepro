"""Contest entry access control (Password, IP lock)."""
import hmac
from typing import Tuple, Optional

class ContestAccessGuard:
    @staticmethod
    def check_access(user: str, contest_password_hash: Optional[str], provided_password: Optional[str], allowed_ip_prefix: Optional[str] = None, user_ip: str = '127.0.0.1') -> Tuple[bool, str]:
        # 1. IP Whitelist for onsite contest
        if allowed_ip_prefix and not user_ip.startswith(allowed_ip_prefix):
            return False, "Kỳ thi chỉ cho phép truy cập từ mạng phòng thi (IP restricted)."

        # 2. Password check
        if contest_password_hash:
            if not provided_password:
                return False, "Kỳ thi yêu cầu mật khẩu truy cập."
            # Constant-time comparison
            if not hmac.compare_digest(contest_password_hash, provided_password):
                return False, "Mật khẩu kỳ thi không chính xác."

        return True, "Authorized"
