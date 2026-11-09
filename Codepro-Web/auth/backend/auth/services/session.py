from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from backend.auth.models.auth_session import AuthSession
from backend.auth.models.refresh_token import RefreshToken
from backend.auth.security.token import generate_secure_token, hash_token
from backend.auth.security.device import get_client_ip, get_user_agent, parse_device_info

DEFAULT_SESSION_DAYS = 1
REMEMBER_ME_DAYS = 30


def create_auth_session(user: User, request, remember_me: bool = False) -> tuple[str, AuthSession]:
    """
    Generate a secure random session token, hash it for DB storage,
    and persist the session record.
    Returns (raw_session_token, AuthSession).
    """
    raw_token = generate_secure_token(48)
    token_hash = hash_token(raw_token)

    ip_address = get_client_ip(request)
    ua_raw = get_user_agent(request)
    device_info = parse_device_info(ua_raw)
    device_name = f"{device_info['browser']} on {device_info['os']}"

    duration_days = REMEMBER_ME_DAYS if remember_me else DEFAULT_SESSION_DAYS
    expires_at = timezone.now() + timedelta(days=duration_days)

    session = AuthSession.objects.create(
        user=user,
        session_token_hash=token_hash,
        ip_address=ip_address,
        user_agent=ua_raw,
        device_name=device_name,
        expires_at=expires_at,
        is_active=True
    )

    return raw_token, session


def validate_auth_session(raw_token: str) -> User | None:
    """
    Verify raw session token against database.
    Updates last_seen_at if valid. Returns User or None.
    """
    if not raw_token:
        return None

    token_hash = hash_token(raw_token)
    session = AuthSession.objects.filter(
        session_token_hash=token_hash,
        is_active=True
    ).select_related('user').first()

    if not session:
        return None

    if session.is_expired:
        session.is_active = False
        session.save(update_fields=['is_active'])
        return None

    # Update last seen timestamp
    session.last_seen_at = timezone.now()
    session.save(update_fields=['last_seen_at'])

    return session.user


def revoke_auth_session(raw_token: str) -> bool:
    """Revoke a specific session."""
    if not raw_token:
        return False
    token_hash = hash_token(raw_token)
    updated = AuthSession.objects.filter(
        session_token_hash=token_hash,
        is_active=True
    ).update(is_active=False)
    return updated > 0


def revoke_all_user_sessions(user: User, except_raw_token: str = None):
    """Revoke all sessions for a user, optionally keeping the current one."""
    qs = AuthSession.objects.filter(user=user, is_active=True)
    if except_raw_token:
        current_hash = hash_token(except_raw_token)
        qs = qs.exclude(session_token_hash=current_hash)
    qs.update(is_active=False)


def get_user_active_sessions(user: User) -> list[dict]:
    """Retrieve list of active sessions with device details."""
    sessions = AuthSession.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).order_by('-last_seen_at')

    return [
        {
            'id': s.id,
            'ip_address': s.ip_address,
            'device_name': s.device_name,
            'user_agent': s.user_agent,
            'created_at': s.created_at.isoformat(),
            'last_seen_at': s.last_seen_at.isoformat(),
            'expires_at': s.expires_at.isoformat(),
        }
        for s in sessions
    ]
