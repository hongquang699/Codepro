from .username import validate_username
from .email import validate_email
from .password import validate_password


def validate_registration_payload(data: dict) -> tuple[bool, dict]:
    """
    Validate all registration inputs.
    Returns (is_valid, errors_dict).
    """
    errors = {}

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    password_confirm = data.get('password_confirm') or ''
    terms = data.get('terms_agreed', True)

    ok_user, err_user = validate_username(username)
    if not ok_user:
        errors['username'] = err_user

    ok_email, err_email = validate_email(email)
    if not ok_email:
        errors['email'] = err_email

    ok_pass, err_pass = validate_password(password, password_confirm)
    if not ok_pass:
        errors['password'] = err_pass

    if not terms:
        errors['terms'] = "Bạn cần đồng ý với điều khoản sử dụng để tiếp tục."

    return (len(errors) == 0), errors
