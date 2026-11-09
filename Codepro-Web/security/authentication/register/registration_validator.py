"""Input validator for new user registration."""
import re
from typing import Tuple, List
from security.password.policy import PasswordPolicyValidator
from security.password.breach_check import BreachChecker

class RegistrationValidator:
    USERNAME_REGEX = r'^[a-zA-Z0-9_]{3,30}$'
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    @classmethod
    def validate(cls, username: str, email: str, password: str) -> Tuple[bool, List[str]]:
        errors = []
        if not re.match(cls.USERNAME_REGEX, username or ''):
            errors.append("Tên đăng nhập từ 3 đến 30 ký tự, chỉ gồm chữ cái, số và dấu gạch dưới (_).")
        
        if not re.match(cls.EMAIL_REGEX, email or ''):
            errors.append("Địa chỉ email không đúng định dạng.")

        # Password policy check
        valid_pwd, pwd_errors = PasswordPolicyValidator.validate(password, username)
        if not valid_pwd:
            errors.extend(pwd_errors)

        # Breach check
        if BreachChecker.is_common_password(password):
            errors.append("Mật khẩu này quá phổ biến và dễ bị đoán. Vui lòng chọn mật khẩu khác.")

        return len(errors) == 0, errors
