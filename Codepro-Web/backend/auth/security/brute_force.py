from datetime import timedelta
from django.utils import timezone
from backend.auth.models.login_attempt import LoginAttempt

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def is_ip_or_user_locked(ip_address: str, username: str = None) -> tuple[bool, int]:
    """
    Check if IP address or username has exceeded MAX_FAILED_ATTEMPTS within LOCKOUT_MINUTES.
    Returns (is_locked, remaining_seconds).
    """
    cutoff = timezone.now() - timedelta(minutes=LOCKOUT_MINUTES)
    
    # Check by IP
    failed_attempts_ip = LoginAttempt.objects.filter(
        ip_address=ip_address,
        success=False,
        attempted_at__gte=cutoff
    ).order_by('-attempted_at')

    if failed_attempts_ip.count() >= MAX_FAILED_ATTEMPTS:
        last_attempt = failed_attempts_ip.first()
        elapsed = (timezone.now() - last_attempt.attempted_at).total_seconds()
        remaining = max(0, int(LOCKOUT_MINUTES * 60 - elapsed))
        return True, remaining

    # Check by username if provided
    if username:
        failed_attempts_user = LoginAttempt.objects.filter(
            username=username,
            success=False,
            attempted_at__gte=cutoff
        ).order_by('-attempted_at')

        if failed_attempts_user.count() >= MAX_FAILED_ATTEMPTS:
            last_attempt = failed_attempts_user.first()
            elapsed = (timezone.now() - last_attempt.attempted_at).total_seconds()
            remaining = max(0, int(LOCKOUT_MINUTES * 60 - elapsed))
            return True, remaining

    return False, 0


def record_login_attempt(ip_address: str, username: str, is_success: bool, user_agent: str = ""):
    """Record a login attempt."""
    LoginAttempt.objects.create(
        ip_address=ip_address,
        username=username or "",
        success=is_success,
        user_agent=user_agent or ""
    )
    if is_success and username:
        # Clear recent failed attempts for this username upon successful login
        LoginAttempt.objects.filter(username=username, success=False).delete()
