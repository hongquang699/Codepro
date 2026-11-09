import os
import json
import logging
import ipaddress
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_IPS = [
    '127.0.0.1',
    '::1',
    '172.20.10.2',
    '2001:ee0:1ad1:241b:7af5:7ed:1f72:e0de',
]


def get_config_file_path() -> Path:
    """Resolve path to admin_ip_whitelist.json safely."""
    try:
        if hasattr(settings, 'BASE_DIR'):
            return Path(settings.BASE_DIR) / 'config' / 'admin_ip_whitelist.json'
    except Exception:
        pass
    # Fallback to relative walk
    return Path(__file__).resolve().parent.parent.parent.parent / 'config' / 'admin_ip_whitelist.json'


def load_whitelist_config() -> dict:
    config_path = get_config_file_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading admin IP whitelist from {config_path}: {e}")
    return {
        "enabled": True,
        "allowed_ips": DEFAULT_ALLOWED_IPS
    }


def get_admin_allowed_ips() -> list[str]:
    """Retrieve list of whitelisted admin IPs."""
    env_ips = os.getenv('ADMIN_ALLOWED_IPS')
    if env_ips:
        return [ip.strip() for ip in env_ips.split(',') if ip.strip()]

    cfg = load_whitelist_config()
    return cfg.get('allowed_ips', DEFAULT_ALLOWED_IPS)


def is_admin_ip_whitelisting_enabled() -> bool:
    """Check if the admin IP restriction feature is active."""
    env_enabled = os.getenv('ADMIN_IP_WHITELIST_ENABLED')
    if env_enabled is not None:
        return env_enabled.lower() in ('1', 'true', 'yes')
    cfg = load_whitelist_config()
    return cfg.get('enabled', True)


def normalize_ip(raw_ip: str) -> str:
    """Normalize IP, strip ports and IPv4-mapped IPv6 prefixes."""
    ip = (raw_ip or '').strip()
    if not ip:
        return '127.0.0.1'
    if ip.startswith('::ffff:'):
        ip = ip[7:]
    if ':' in ip and '.' in ip:  # e.g. 127.0.0.1:8000
        ip = ip.split(':')[0]
    return ip


def is_admin_ip_allowed(client_ip: str) -> bool:
    """
    Check if the client_ip is permitted to access/login to an Admin account.
    Non-admin accounts do not pass through this check.
    """
    if not is_admin_ip_whitelisting_enabled():
        return True

    norm_client = normalize_ip(client_ip)
    allowed_list = get_admin_allowed_ips()

    # 1. Exact string match check
    for allowed in allowed_list:
        norm_allowed = normalize_ip(allowed)
        if norm_client == norm_allowed:
            return True

    # 2. IP / Subnet check via ipaddress library
    try:
        client_obj = ipaddress.ip_address(norm_client)
        for allowed in allowed_list:
            norm_allowed = normalize_ip(allowed)
            try:
                if '/' in norm_allowed:
                    net = ipaddress.ip_network(norm_allowed, strict=False)
                    if client_obj in net:
                        return True
                else:
                    addr = ipaddress.ip_address(norm_allowed)
                    if client_obj == addr:
                        return True
            except ValueError:
                continue
    except ValueError:
        pass

    return False


def is_user_admin(user) -> bool:
    """Determine if a user has admin privileges."""
    return bool(user and user.is_active and (user.is_staff or user.is_superuser))
