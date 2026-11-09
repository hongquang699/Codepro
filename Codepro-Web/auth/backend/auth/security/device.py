def get_client_ip(request) -> str:
    """Extract client IP address from HttpRequest."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip or '127.0.0.1'


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
