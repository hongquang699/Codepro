from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format and uniqueness.
    Returns (is_valid, error_message).
    """
    if not email:
        return False, "Email không được để trống."

    email = email.strip()

    if len(email) > 254:
        return False, "Email không được vượt quá 254 ký tự."

    try:
        django_validate_email(email)
    except ValidationError:
        return False, "Địa chỉ email không hợp lệ."

    if User.objects.filter(email__iexact=email).exists():
        return False, "Email này đã được đăng ký tài khoản."

    return True, ""
