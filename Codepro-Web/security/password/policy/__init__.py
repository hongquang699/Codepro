"""Password Policy Validator."""
import re
import math
from typing import Tuple, List

class PasswordPolicyValidator:
    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str, username: str = None) -> Tuple[bool, List[str]]:
        errors = []
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Mật khẩu phải có tối thiểu {cls.MIN_LENGTH} ký tự.")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Mật khẩu không được vượt quá {cls.MAX_LENGTH} ký tự.")
        if not re.search(r'[A-Z]', password):
            errors.append("Mật khẩu phải chứa ít nhất một chữ hoa (A-Z).")
        if not re.search(r'[a-z]', password):
            errors.append("Mật khẩu phải chứa ít nhất một chữ thường (a-z).")
        if not re.search(r'[0-9]', password):
            errors.append("Mật khẩu phải chứa ít nhất một chữ số (0-9).")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
            errors.append("Mật khẩu phải chứa ít nhất một ký tự đặc biệt.")
        if username and username.lower() in password.lower():
            errors.append("Mật khẩu không được chứa tên đăng nhập.")
        
        return len(errors) == 0, errors

    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calculates Shannon entropy in bits."""
        if not password:
            return 0.0
        charset_size = 0
        if re.search(r'[a-z]', password): charset_size += 26
        if re.search(r'[A-Z]', password): charset_size += 26
        if re.search(r'[0-9]', password): charset_size += 10
        if re.search(r'[^a-zA-Z0-9]', password): charset_size += 32
        if charset_size == 0:
            return 0.0
        return len(password) * math.log2(charset_size)
