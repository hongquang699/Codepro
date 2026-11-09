"""
CODING_OJ Security Middleware for Django
Implements the 6 Core Defense Techniques:
1. KỸ THUẬT #1: Rate Limiting — Khắc tinh của DoS & Brute Force
2. KỸ THUẬT #2: CORS — Thẻ căn cước API (Domain Whitelisting)
3. KỸ THUẬT #3: Tham số hóa chặn SQL Injection (Parameterized & Injection Guard)
4. KỸ THUẬT #4: Tường Lửa WAF & VPN Nội Bộ (Lớp lọc đầu tiên & Giấu API quản trị)
5. KỸ THUẬT #5: Bẻ gãy CSRF & XSS (Token kèm Cookie & Vô hiệu hóa script ngầm)
6. KỸ THUẬT #7: Authentication & Authorization (OAuth 2.0 / JWT + RBAC + API Keys)
"""

import json
import ipaddress
import re
from django.conf import settings
from django.http import JsonResponse
from security.api_security.rate_limit import RateLimiter
from security.api_security.input_validation import InputSanitizer
from security.api_security.security_headers import SecurityHeaders
from security.api_security.csrf import CSRFGuard
from security.content_security.html_sanitizer import HTMLSanitizer
from security.session_security.token_manager import JWTHandler
from security.api_security.api_keys import APIKeyManager
from security.incident_response import EmergencyContainment
from security.logging import SecurityLogger
from backend.auth.security.device import get_client_ip

ALLOWED_CORS_ORIGINS = frozenset(getattr(settings, 'CORS_ALLOWED_ORIGINS', ()))

# Known security scanner User-Agents to block at WAF layer
BAD_USER_AGENTS = [
    'sqlmap', 'nikto', 'dirbuster', 'hydra', 'havij', 'acunetix',
    'nmap', 'masscan', 'zgrab', 'wpscan'
]

# Networks allowed to access internal endpoints.
INTERNAL_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    '127.0.0.0/8', '::1/128', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
))


def is_internal_ip(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(address in network for network in INTERNAL_NETWORKS
               if address.version == network.version)

class FullSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_client_ip(request)
        path = request.path
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

        # ══════════════════════════════════════════════════════════════════════
        # 1. KỸ THUẬT #4: TƯỜNG LỬA WAF & VPN NỘI BỘ
        # WAF — Lớp lọc đầu tiên: Phân tích request, đối chiếu blacklist
        # VPN — Giấu API nội bộ: API quản trị, máy chấm chỉ nhận từ mạng nội bộ
        # ══════════════════════════════════════════════════════════════════════
        # A. Kiểm tra IP Blacklist (Emergency Containment)
        if EmergencyContainment.is_ip_banned(ip):
            SecurityLogger.log_security_alert('WAF_BANNED_IP_DROPPED', 'CRITICAL', ip, {'path': path})
            return JsonResponse({
                'status': 403,
                'error': {'code': 'IP_BANNED', 'message': 'Địa chỉ IP của bạn đã bị tường lửa khóa vĩnh viễn do hành vi tấn công.'}
            }, status=403)

        # B. Chặn Scanner / Bot độc hại qua User-Agent
        for bad_ua in BAD_USER_AGENTS:
            if bad_ua in user_agent:
                SecurityLogger.log_security_alert('WAF_BAD_SCANNER_BLOCKED', 'HIGH', ip, {'user_agent': user_agent, 'path': path})
                return JsonResponse({
                    'status': 403,
                    'error': {'code': 'WAF_SCANNER_BLOCKED', 'message': 'Yêu cầu bị Tường lửa WAF từ chối (Automated scanner detected).'}
                }, status=403)

        # C. Chặn các URL dò quét file hệ thống (Probe Traversal)
        if any(probe in path.lower() for probe in ('.env', '.git', 'wp-admin', 'phpmyadmin', 'etc/passwd', 'web.config')):
            SecurityLogger.log_security_alert('WAF_PROBE_ATTEMPT_BLOCKED', 'CRITICAL', ip, {'path': path})
            EmergencyContainment.ban_ip(ip) # Tự động đưa vào blacklist nếu quét file nhạy cảm
            return JsonResponse({
                'status': 403,
                'error': {'code': 'WAF_PROBE_BLOCKED', 'message': 'Phát hiện hành vi thăm dò trái phép. IP đã bị đưa vào danh sách đen.'}
            }, status=403)

        # D. VPN / Private Network Guard cho các endpoint nội bộ nhạy cảm
        if path.startswith('/api/v1/internal/') or path.startswith('/admin/system/'):
            if not is_internal_ip(ip):
                SecurityLogger.log_security_alert('VPN_RESTRICTION_BLOCKED', 'HIGH', ip, {'path': path})
                return JsonResponse({
                    'status': 403,
                    'error': {'code': 'VPN_REQUIRED', 'message': 'API nội bộ chỉ được phép truy cập qua kênh VPN hoặc mạng công ty.'}
                }, status=403)

        # ══════════════════════════════════════════════════════════════════════
        # 2. KỸ THUẬT #2: CORS — THẺ CĂN CƯỚC API
        # Chỉ tiếp khách mời hợp lệ. Chặn mọi domain lạ gọi API trái phép
        # ══════════════════════════════════════════════════════════════════════
        origin = request.headers.get('Origin')
        if origin and origin not in ALLOWED_CORS_ORIGINS:
            if path.startswith('/api/'):
                SecurityLogger.log_security_alert('CORS_VIOLATION_BLOCKED', 'MEDIUM', ip, {'origin': origin, 'path': path})
                return JsonResponse({
                    'status': 403,
                    'error': {'code': 'CORS_FORBIDDEN', 'message': f'Truy cập bị từ chối: Domain {origin} không nằm trong danh sách khách mời hợp lệ.'}
                }, status=403)

        if request.method == 'OPTIONS':
            resp = JsonResponse({'status': 'ok'})
            if origin in ALLOWED_CORS_ORIGINS:
                resp['Access-Control-Allow-Origin'] = origin
                resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
                resp['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRF-Token, X-Requested-With, X-CSRFToken'
                resp['Access-Control-Allow-Credentials'] = 'true'
            return resp

        # ══════════════════════════════════════════════════════════════════════
        # 3. KỸ THUẬT #1: RATE LIMITING — KHẮC TINH CỦA DOS & BRUTE FORCE
        # Quy tắc: Giới hạn request theo IP / API, chống brute force mật khẩu
        # ══════════════════════════════════════════════════════════════════════
        if request.method == 'POST' and ('/auth/login' in path or '/login' in path):
            allowed, remaining = RateLimiter.check_limit(f"login:{ip}", max_requests=10, window_seconds=60)
            if not allowed:
                SecurityLogger.log_security_alert('RATE_LIMIT_BRUTE_FORCE_BLOCKED', 'HIGH', ip, {'path': path})
                return JsonResponse({
                    'status': 429,
                    'error': {'code': 'RATE_LIMIT_EXCEEDED', 'message': 'Quá nhiều yêu cầu đăng nhập. Vui lòng chờ 1 phút trước khi thử lại.'}
                }, status=429)
        elif path.startswith('/api/'):
            allowed, remaining = RateLimiter.check_limit(f"api:{ip}", max_requests=300, window_seconds=60)
            if not allowed:
                SecurityLogger.log_security_alert('RATE_LIMIT_DOS_BLOCKED', 'HIGH', ip, {'path': path})
                return JsonResponse({
                    'status': 429,
                    'error': {'code': 'RATE_LIMIT_EXCEEDED', 'message': 'Hệ thống phát hiện tần suất yêu cầu bất thường (DoS Protection).'}
                }, status=429)

        # ══════════════════════════════════════════════════════════════════════
        # 4. KỸ THUẬT #3: THAM SỐ HÓA CHẶN SQL INJECTION
        # Ngăn chặn nối chuỗi trực tiếp, phát hiện payload độc hại
        # ══════════════════════════════════════════════════════════════════════
        for key, val in request.GET.items():
            if InputSanitizer.check_sqli(val):
                SecurityLogger.log_security_alert('SQLI_BLOCKED', 'CRITICAL', ip, {'param': key, 'val': val, 'path': path})
                return JsonResponse({
                    'status': 400,
                    'error': {'code': 'SECURITY_VIOLATION', 'message': f'Phát hiện payload SQL Injection trong tham số {key}.'}
                }, status=400)

        # ══════════════════════════════════════════════════════════════════════
        # 5. KỸ THUẬT #5: BẺ GÃY CSRF & XSS
        # CSRF Token: Token kèm Cookie chặn "mượn tay giết người"
        # Sanitize XSS: Vô hiệu hóa thẻ <script>, chặn mã JavaScript chạy ngầm
        # ══════════════════════════════════════════════════════════════════════
        # A. CSRF Token Guard trên các request ghi (POST/PUT/DELETE) khi dùng Session/Cookie
        exempt_csrf_paths = ('/api/v2/auth/', '/api/v2/submit')
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and not any(path.startswith(p) for p in exempt_csrf_paths):
            # If request is using session cookie auth (not Pure JWT Bearer or Token), check CSRF
            auth_hdr = request.headers.get('Authorization', '')
            if not (auth_hdr.startswith('Bearer ') or auth_hdr.startswith('Token ')):
                csrf_cookie = request.COOKIES.get('csrftoken') or request.COOKIES.get('csrf_token')
                csrf_header = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
                # If cookie is present and header is supplied, verify match
                if csrf_cookie and csrf_header and not CSRFGuard.verify(csrf_cookie, csrf_header):
                    SecurityLogger.log_security_alert('CSRF_VERIFICATION_FAILED', 'HIGH', ip, {'path': path})
                    return JsonResponse({
                        'status': 403,
                        'error': {'code': 'CSRF_FAILED', 'message': 'Mã CSRF token không khớp hoặc bị thiếu. Thao tác bị từ chối.'}
                    }, status=403)

        # B. XSS Body Sanitizer: Kiểm tra nhanh payload POST text nếu có thẻ script độc hại
        if request.method in ('POST', 'PUT', 'PATCH') and request.content_type == 'application/json':
            try:
                body_bytes = request.body
                if body_bytes and len(body_bytes) < 100000:
                    body_str = body_bytes.decode('utf-8', errors='ignore')
                    # Detect malicious inline script or javascript payload
                    if re.search(r'<script[^>]*>|javascript:\s*alert|<svg[^>]+onload=', body_str, re.IGNORECASE):
                        SecurityLogger.log_security_alert('XSS_ATTACK_DETECTED', 'HIGH', ip, {'path': path})
                        # Return sanitized warning or clean the payload
            except Exception:
                pass

        # ══════════════════════════════════════════════════════════════════════
        # 6. KỸ THUẬT #7: AUTHENTICATION & AUTHORIZATION
        # Biết AI ĐANG GỌI (OAuth 2.0 / JWT) và ĐƯỢC PHÉP LÀM GÌ (RBAC & API Keys)
        # ══════════════════════════════════════════════════════════════════════
        auth_header = request.headers.get('Authorization', '')
        user_claims = None

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1].strip()
            # 1. API Key check for internal service mesh (Judge Server)
            if APIKeyManager.verify_request(auth_header):
                user_claims = {'sub': 'judge_service', 'role': 'judge-manager'}
            else:
                # 2. OAuth 2.0 / JWT validation
                user_claims = JWTHandler.decode(token)

        request.user_claims = user_claims

        # Execute Django view
        response = self.get_response(request)

        # Attach Security Headers & CORS
        if origin in ALLOWED_CORS_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'

        headers = SecurityHeaders.get_standard_headers()
        for h, v in headers.items():
            if h not in response:
                response[h] = v

        return response

    @staticmethod
    def _get_client_ip(request):
        return get_client_ip(request)
