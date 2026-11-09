import re
from django.contrib.auth.models import User

RESERVED_USERNAMES = {
    'admin', 'administrator', 'root', 'system', 'superuser',
    'support', 'security', 'moderator', 'staff', 'api',
    'null', 'undefined', 'anonymous', 'guest', 'user', 'users',
    'bot', 'official', 'codepro', 'codeprooj', 'dmoj', 'auth'
}

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-]+$')


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format, length, reserved keywords, and uniqueness.
    Returns (is_valid, error_message).
    """
    if not username:
        return False, "Tên đăng nhập không được để trống."

    username = username.strip()

    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự."

    if len(username) > 30:
        return False, "Tên đăng nhập không được vượt quá 30 ký tự."

    if not USERNAME_REGEX.match(username):
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số, dấu gạch dưới (_) và gạch ngang (-)."

    if username.lower() in RESERVED_USERNAMES:
        return False, "Tên đăng nhập này đã được bảo lưu bởi hệ thống."

    if User.objects.filter(username__iexact=username).exists():
        return False, "Tên đăng nhập này đã được sử dụng."

    return True, ""
