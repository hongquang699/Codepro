import ipaddress
import os


def get_client_ip(request) -> str:
    """Trust the gateway's client IP only when the socket peer is a known proxy."""
    remote = (request.META.get('REMOTE_ADDR') or '').strip()
    trusted = os.getenv('TRUSTED_PROXY_IPS', '127.0.0.1,::1,::ffff:127.0.0.1')
    trusted_ips = [value.strip() for value in trusted.split(',') if value.strip()]
    try:
        remote_ip = ipaddress.ip_address(remote)
        is_trusted = any(remote_ip in ipaddress.ip_network(value, strict=False) for value in trusted_ips)
    except ValueError:
        is_trusted = False
    candidate = remote
    if is_trusted:
        candidate = request.META.get('HTTP_X_REAL_IP') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or remote
    try:
        address = ipaddress.ip_address(candidate.strip())
        return str(getattr(address, 'ipv4_mapped', None) or address)
    except (ValueError, AttributeError):
        return remote or '0.0.0.0'


def get_user_agent(request) -> str:
    """Extract user agent from HttpRequest."""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')[:500]


def parse_device_info(user_agent: str) -> dict:
    """Simple heuristic parser for user agent to browser and OS."""
    ua = user_agent.lower()
    os_name = "Unknown OS"
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"

    browser = "Unknown Browser"
    if "edg/" in ua:
        browser = "Microsoft Edge"
    elif "chrome/" in ua and "safari/" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua and "chrome" not in ua:
        browser = "Safari"

    return {
        "os": os_name,
        "browser": browser,
        "raw": user_agent,
    }
