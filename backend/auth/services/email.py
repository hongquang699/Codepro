import os
import logging
from pathlib import Path
from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context

logger = logging.getLogger('auth_email')
EMAILS_DIR = Path(__file__).resolve().parent.parent / 'emails'


def _load_and_render_template(template_name: str, context_dict: dict) -> str:
    """Load HTML template from auth/emails/ and render with context."""
    filepath = EMAILS_DIR / template_name
    if not filepath.exists():
        return ""
    with open(filepath, 'r', encoding='utf-8') as f:
        template_str = f.read()
    t = Template(template_str)
    return t.render(Context(context_dict))


def send_verification_otp_email(email: str, username: str, otp: str) -> bool:
    """
    Send OTP email for account registration verification.
    """
    subject = "[CodeProOJ] Mã xác nhận đăng ký tài khoản"
    context = {
        'username': username,
        'otp': otp,
    }
    html_content = _load_and_render_template('verification.html', context)
    plain_content = f"Mã xác thực CodeProOJ của bạn là: {otp}. Mã có hiệu lực trong 5 phút."

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@codeprooj.com')

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False
        )
        logger.info("Verification email sent")
        return True
    except Exception:
        logger.exception("Verification email delivery failed")
        return False


def send_password_reset_email(email: str, username: str, reset_url: str) -> bool:
    """
    Send password reset email with direct token link.
    """
    subject = "[CodeProOJ] Hướng dẫn khôi phục mật khẩu tài khoản"
    context = {
        'username': username,
        'reset_url': reset_url,
    }
    html_content = _load_and_render_template('password_reset.html', context)
    plain_content = f"Liên kết đặt lại mật khẩu CodeProOJ của bạn: {reset_url}. Hết hạn sau 15 phút."

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@codeprooj.com')

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False
        )
        logger.info("Password reset email sent")
        return True
    except Exception:
        logger.exception("Password reset email delivery failed")
        return False


def send_login_alert_email(email: str, username: str, ip_address: str, device_os: str, browser: str, timestamp: str) -> bool:
    """
    Send login alert email when suspicious or new login occurs.
    """
    subject = "[CodeProOJ] Cảnh báo đăng nhập tài khoản mới"
    context = {
        'username': username,
        'ip_address': ip_address,
        'device_os': device_os,
        'browser': browser,
        'timestamp': timestamp,
    }
    html_content = _load_and_render_template('login_alert.html', context)
    plain_content = f"Tài khoản của bạn vừa đăng nhập từ IP {ip_address} ({device_os}, {browser}) lúc {timestamp}."

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@codeprooj.com')

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=True
        )
        return True
    except Exception:
        return False
