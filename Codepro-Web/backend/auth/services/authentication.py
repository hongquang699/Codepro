from django.contrib.auth.models import User
from django.utils import timezone
from backend.auth.models.two_factor import TwoFactorAuth
from backend.auth.security.brute_force import is_ip_or_user_locked, record_login_attempt
from backend.auth.security.device import parse_device_info
from backend.auth.security.ip_whitelist import is_user_admin, is_admin_ip_allowed
from backend.auth.services.email import send_login_alert_email


def authenticate_user(
    username_or_email: str,
    password: str,
    ip_address: str,
    user_agent: str = ""
) -> tuple[bool, str, User | None, bool]:
    """
    Authenticate user credentials with brute-force protection and Admin IP Whitelist.
    Returns (success, message, user, requires_2fa).
    """
    identifier = username_or_email.strip() if isinstance(username_or_email, str) else ''
    if not identifier or not isinstance(password, str) or not password:
        return False, "Vui lòng nhập tên đăng nhập/email và mật khẩu.", None, False

    # Check brute force lock
    is_locked, remaining_seconds = is_ip_or_user_locked(ip_address, identifier)
    if is_locked:
        minutes = max(1, remaining_seconds // 60)
        return False, f"Tài khoản hoặc IP tạm thời bị khóa do nhiều lần thử thất bại. Vui lòng thử lại sau {minutes} phút.", None, False

    # Find user by username or email
    user = None
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
    if not user:
        user = User.objects.filter(username__iexact=identifier).first()

    if not user:
        record_login_attempt(ip_address, identifier, is_success=False, user_agent=user_agent)
        return False, "Tài khoản hoặc mật khẩu không chính xác.", None, False

    if not user.check_password(password):
        record_login_attempt(ip_address, user.username, is_success=False, user_agent=user_agent)
        return False, "Tài khoản hoặc mật khẩu không chính xác.", None, False

    if not user.is_active:
        return False, "Tài khoản của bạn đã bị vô hiệu hóa hoặc chưa kích hoạt.", None, False

    # ══════════════════════════════════════════════════════════════════════════
    # ADMIN IP WHITELIST ENFORCEMENT:
    # Tài khoản Admin chỉ được phép đăng nhập từ IP được ủy quyền.
    # Dù mật khẩu và tên đăng nhập đúng, nếu IP không trùng khớp thì không vào được.
    # ══════════════════════════════════════════════════════════════════════════
    if is_user_admin(user) and not is_admin_ip_allowed(ip_address):
        record_login_attempt(ip_address, user.username, is_success=False, user_agent=user_agent)
        return False, f"Đăng nhập bị từ chối: Tài khoản Quản trị viên (Admin) chỉ được phép đăng nhập từ IP được ủy quyền. Địa chỉ IP của bạn ({ip_address}) không được phép truy cập tài khoản này.", None, False

    # Check if 2FA is enabled
    two_factor = TwoFactorAuth.objects.filter(user=user, is_enabled=True).first()
    if two_factor:
        # Don't mark login as fully completed yet; requires 2FA step
        return True, "Yêu cầu mã xác thực hai bước (2FA).", user, True

    # Record successful attempt
    record_login_attempt(ip_address, user.username, is_success=True, user_agent=user_agent)

    # Optional: Send login alert asynchronously / fail-silently
    device_info = parse_device_info(user_agent)
    send_login_alert_email(
        email=user.email,
        username=user.username,
        ip_address=ip_address,
        device_os=device_info['os'],
        browser=device_info['browser'],
        timestamp=timezone.now().strftime('%H:%M:%S %d/%m/%Y')
    )

    return True, "Đăng nhập thành công!", user, False
