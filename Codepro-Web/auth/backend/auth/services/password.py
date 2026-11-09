from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from backend.auth.models.password_reset import PasswordReset
from backend.auth.security.token import generate_secure_token, hash_token, verify_token
from backend.auth.security.rate_limit import check_password_reset_rate_limit
from backend.auth.validators.password import validate_password
from backend.auth.services.email import send_password_reset_email
from backend.auth.services.session import revoke_all_user_sessions

RESET_TOKEN_EXPIRY_MINUTES = 15


def initiate_password_reset(
    username_or_email: str,
    ip_address: str,
    base_url: str = "https://codeprooj.com"
) -> tuple[bool, str]:
    """
    Initiate password reset flow.
    Always returns a generic message to prevent account enumeration.
    """
    generic_message = "Nếu tài khoản khớp với hệ thống, chúng tôi đã gửi email hướng dẫn đặt lại mật khẩu."

    identifier = (username_or_email or '').strip()
    if not identifier:
        return True, generic_message

    if not check_password_reset_rate_limit(identifier, ip_address):
        return True, generic_message

    user = None
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
    if not user:
        user = User.objects.filter(username__iexact=identifier).first()

    if not user or not user.is_active or not user.email:
        return True, generic_message

    # Invalidate old unused reset requests for this user
    PasswordReset.objects.filter(user=user, used_at__isnull=True).delete()

    raw_token = generate_secure_token(32)
    token_hash = hash_token(raw_token)
    expires_at = timezone.now() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)

    PasswordReset.objects.create(
        user=user,
        email=user.email,
        token_hash=token_hash,
        ip_address=ip_address,
        expires_at=expires_at
    )

    clean_base = base_url.rstrip('/')
    reset_url = f"{clean_base}/reset-password?token={raw_token}"

    send_password_reset_email(user.email, user.username, reset_url)

    return True, generic_message


def verify_password_reset_token(raw_token: str) -> tuple[bool, str, User | None]:
    """
    Validate the reset token.
    Returns (is_valid, message, user).
    """
    if not raw_token:
        return False, "Mã token đặt lại mật khẩu không hợp lệ.", None

    token_hash = hash_token(raw_token)
    reset_req = PasswordReset.objects.filter(
        token_hash=token_hash,
        used_at__isnull=True
    ).select_related('user').first()

    if not reset_req:
        return False, "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã qua sử dụng.", None

    if reset_req.is_expired:
        return False, "Liên kết đặt lại mật khẩu đã hết hạn. Vui lòng gửi lại yêu cầu mới.", None

    return True, "Token hợp lệ.", reset_req.user


def complete_password_reset(raw_token: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Set new password for user after verifying token.
    Revokes all previous active sessions.
    """
    is_valid, msg, user = verify_password_reset_token(raw_token)
    if not is_valid:
        return False, msg

    ok_pass, err_pass = validate_password(new_password, confirm_password)
    if not ok_pass:
        return False, err_pass

    token_hash = hash_token(raw_token)
    reset_req = PasswordReset.objects.get(token_hash=token_hash, used_at__isnull=True)

    user.set_password(new_password)
    user.save()

    reset_req.used_at = timezone.now()
    reset_req.save(update_fields=['used_at'])

    # Invalidate all user sessions for safety
    revoke_all_user_sessions(user)

    return True, "Mật khẩu đã được đặt lại thành công. Bạn có thể đăng nhập bằng mật khẩu mới."


def change_user_password(user: User, current_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Change password for an authenticated user.
    """
    if not user.check_password(current_password):
        return False, "Mật khẩu hiện tại không chính xác."

    ok_pass, err_pass = validate_password(new_password, confirm_password)
    if not ok_pass:
        return False, err_pass

    if current_password == new_password:
        return False, "Mật khẩu mới không được trùng với mật khẩu hiện tại."

    user.set_password(new_password)
    user.save()

    return True, "Đổi mật khẩu thành công!"
