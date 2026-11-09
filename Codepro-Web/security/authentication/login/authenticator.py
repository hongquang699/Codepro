"""Core authentication engine with lockout check and audit logging."""
import time
from typing import Tuple, Dict, Any, Optional
from security.authentication.login.brute_force import BruteForceProtector
from security.password.hashing import PasswordHasher
from security.logging import SecurityLogger

class Authenticator:
    @classmethod
    def authenticate(cls, username: str, password_attempt: str, stored_hash: str, ip: str = '127.0.0.1', is_active: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not is_active:
            SecurityLogger.log_auth('LOGIN_FAILED', username, ip, False, {'reason': 'Account disabled'})
            return False, "Tài khoản của bạn đã bị vô hiệu hóa.", None

        # Check brute force lockout
        locked, remaining = BruteForceProtector.is_locked(username)
        if locked:
            SecurityLogger.log_security_alert('BRUTE_FORCE_LOCKOUT', 'MEDIUM', ip, {'username': username, 'remaining_sec': remaining})
            return False, f"Tài khoản bị tạm khóa do nhập sai nhiều lần. Thử lại sau {remaining} giây.", None

        # Verify password
        if not PasswordHasher.verify_password(password_attempt, stored_hash):
            attempts = BruteForceProtector.record_failure(username)
            left = max(0, BruteForceProtector.MAX_ATTEMPTS - attempts)
            SecurityLogger.log_auth('LOGIN_FAILED', username, ip, False, {'attempts': attempts, 'remaining_attempts': left})
            if left == 0:
                return False, "Đăng nhập sai quá 5 lần. Tài khoản tạm khóa 15 phút.", None
            return False, f"Tên đăng nhập hoặc mật khẩu không đúng. Còn {left} lần thử.", None

        # Successful auth
        BruteForceProtector.record_success(username)
        SecurityLogger.log_auth('LOGIN_SUCCESS', username, ip, True, {})
        return True, "Đăng nhập thành công.", {'username': username, 'authenticated_at': time.time()}
