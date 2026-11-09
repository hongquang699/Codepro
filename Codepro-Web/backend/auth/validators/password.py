import re

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_password(password: str, confirm_password: str = None) -> tuple[bool, str]:
    """
    Validate password length, complexity, and confirmation match.
    Returns (is_valid, error_message).
    """
    if not password:
        return False, "Mật khẩu không được để trống."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Mật khẩu phải chứa ít nhất {MIN_PASSWORD_LENGTH} ký tự."

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Mật khẩu không được vượt quá {MAX_PASSWORD_LENGTH} ký tự."

    if confirm_password is not None and password != confirm_password:
        return False, "Mật khẩu xác nhận không khớp."

    # Require at least one letter and one number for solid security
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_digit = bool(re.search(r'\d', password))

    if not (has_letter and has_digit):
        return False, "Mật khẩu cần chứa ít nhất một chữ cái và một chữ số."

    return True, ""
