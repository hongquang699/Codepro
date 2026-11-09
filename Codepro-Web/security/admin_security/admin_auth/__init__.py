"""Specialized Admin Authenticator."""
from typing import Tuple
from security.logging import SecurityLogger

class AdminAuthenticator:
    @staticmethod
    def verify_admin_access(user_dict: dict, ip: str = '127.0.0.1') -> Tuple[bool, str]:
        if not user_dict:
            return False, "Yêu cầu đăng nhập quản trị viên."
        username = user_dict.get('username', '')
        is_staff = user_dict.get('is_staff', False) or user_dict.get('role') in ('admin', 'administrator', 'super-admin')
        
        if not is_staff and username.lower() != 'admin':
            SecurityLogger.log_security_alert('UNAUTHORIZED_ADMIN_ACCESS_ATTEMPT', 'HIGH', ip, {'username': username})
            return False, "Từ chối truy cập: Bạn không có quyền truy cập khu vực Quản trị."

        return True, "Xác thực Quản trị thành công."
