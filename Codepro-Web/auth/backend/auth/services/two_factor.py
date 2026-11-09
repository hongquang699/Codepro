import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote
from django.contrib.auth.models import User
from backend.auth.models.two_factor import TwoFactorAuth


def generate_totp_secret() -> str:
    """Generate 20-byte random Base32 encoded secret."""
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode('utf-8').replace('=', '')


def compute_totp(secret: str, timestamp: int = None, time_step: int = 30) -> str:
    """Compute standard 6-digit RFC 6238 TOTP code."""
    if timestamp is None:
        timestamp = int(time.time())
    
    # Pad secret if needed
    padded = secret + '=' * (-len(secret) % 8)
    secret_bytes = base64.b32decode(padded, casefold=True)
    
    counter = struct.pack('>Q', timestamp // time_step)
    hmac_hash = hmac.new(secret_bytes, counter, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0] & 0x7fffffff
    code = code % 1000000
    return str(code).zfill(6)


def verify_totp_code(secret: str, user_code: str, window: int = 1) -> bool:
    """
    Verify TOTP code within a time window (tolerance of +/- window steps).
    """
    if not secret or not user_code or len(user_code.strip()) != 6:
        return False
    
    user_code = user_code.strip()
    current_time = int(time.time())
    step = 30

    for w in range(-window, window + 1):
        expected = compute_totp(secret, timestamp=current_time + (w * step))
        if secrets.compare_digest(expected, user_code):
            return True

    return False


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate alphanumeric backup codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def get_or_create_2fa(user: User) -> TwoFactorAuth:
    """Retrieve or create a 2FA instance for user."""
    record, _ = TwoFactorAuth.objects.get_or_create(
        user=user,
        defaults={'secret_key': generate_totp_secret()}
    )
    if not record.secret_key:
        record.secret_key = generate_totp_secret()
        record.save()
    return record


def get_totp_uri(user: User, secret: str) -> str:
    """Generate otpauth URI for QR codes."""
    issuer = "CodeProOJ"
    username = quote(user.username)
    return f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"


def enable_2fa_for_user(user: User, code: str) -> tuple[bool, str, list[str]]:
    """Verify code and enable 2FA."""
    record = get_or_create_2fa(user)
    if not verify_totp_code(record.secret_key, code):
        return False, "Mã xác thực không hợp lệ. Vui lòng thử lại.", []

    backup_codes = generate_backup_codes()
    record.backup_codes = backup_codes
    record.is_enabled = True
    record.save()

    return True, "Xác thực 2 bước đã được kích hoạt thành công.", backup_codes


def disable_2fa_for_user(user: User, password_or_code: str) -> tuple[bool, str]:
    """Disable 2FA for user after password or OTP verification."""
    record = TwoFactorAuth.objects.filter(user=user, is_enabled=True).first()
    if not record:
        return False, "2FA chưa được kích hoạt cho tài khoản này."

    # Allow disabling if code matches or user's password matches
    code_match = verify_totp_code(record.secret_key, password_or_code)
    pass_match = user.check_password(password_or_code)

    if not (code_match or pass_match):
        return False, "Mã 2FA hoặc mật khẩu không chính xác."

    record.is_enabled = False
    record.backup_codes = []
    record.save()

    return True, "Đã tắt xác thực 2 bước thành công."
