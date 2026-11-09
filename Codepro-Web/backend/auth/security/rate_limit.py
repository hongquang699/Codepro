from datetime import timedelta
from django.utils import timezone
from backend.auth.models.email_verification import EmailVerification
from backend.auth.models.password_reset import PasswordReset

RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFICATIONS_PER_HOUR = 10
MAX_RESETS_PER_HOUR = 5


def check_otp_resend_cooldown(email: str) -> tuple[bool, int]:
    """
    Check if the user must wait before requesting a new OTP.
    Returns (can_resend, wait_seconds).
    """
    latest = EmailVerification.objects.filter(
        email=email.lower().strip()
    ).order_by('-created_at').first()

    if not latest:
        return True, 0

    elapsed = (timezone.now() - latest.created_at).total_seconds()
    if elapsed < RESEND_COOLDOWN_SECONDS:
        return False, int(RESEND_COOLDOWN_SECONDS - elapsed)

    return True, 0


def check_verification_rate_limit(ip_address: str, email: str) -> bool:
    """Check if IP or email exceeded maximum verifications per hour."""
    cutoff = timezone.now() - timedelta(hours=1)
    ip_count = EmailVerification.objects.filter(ip_address=ip_address, created_at__gte=cutoff).count()
    email_count = EmailVerification.objects.filter(email=email.lower().strip(), created_at__gte=cutoff).count()
    return ip_count < MAX_VERIFICATIONS_PER_HOUR and email_count < MAX_VERIFICATIONS_PER_HOUR


def check_password_reset_rate_limit(email: str, ip_address: str) -> bool:
    """Check if password reset requests exceeded limit."""
    cutoff = timezone.now() - timedelta(hours=1)
    email_count = PasswordReset.objects.filter(email=email.lower().strip(), created_at__gte=cutoff).count()
    ip_count = PasswordReset.objects.filter(ip_address=ip_address, created_at__gte=cutoff).count()
    return email_count < MAX_RESETS_PER_HOUR and ip_count < MAX_RESETS_PER_HOUR * 2
