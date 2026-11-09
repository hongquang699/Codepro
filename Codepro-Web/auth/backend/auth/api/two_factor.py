from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from backend.auth.security.auth_required import auth_required, parse_json_body
from backend.auth.services.two_factor import (
    get_or_create_2fa,
    get_totp_uri,
    enable_2fa_for_user,
    disable_2fa_for_user
)
from backend.auth.models.two_factor import TwoFactorAuth


@require_GET
@auth_required
def status_2fa_view(request):
    """GET /api/v1/auth/2fa/status"""
    record = TwoFactorAuth.objects.filter(user=request.auth_user).first()
    is_enabled = bool(record and record.is_enabled)
    return JsonResponse({
        'is_enabled': is_enabled,
        'has_backup_codes': bool(record and record.backup_codes)
    })


@require_GET
@auth_required
def setup_2fa_view(request):
    """
    GET /api/v1/auth/2fa/setup
    Generates TOTP secret and returns URI for Authenticator apps.
    """
    record = get_or_create_2fa(request.auth_user)
    uri = get_totp_uri(request.auth_user, record.secret_key)

    return JsonResponse({
        'secret': record.secret_key,
        'otpauth_uri': uri,
        'issuer': 'CodeProOJ',
        'account': request.auth_user.username
    })


@csrf_exempt
@require_POST
@auth_required
def enable_2fa_view(request):
    """
    POST /api/v1/auth/2fa/enable
    Verifies code and enables 2FA.
    """
    data = parse_json_body(request)
    code = (data.get('code') or '').strip()

    if not code:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng nhập mã từ ứng dụng xác thực.'
        }, status=400)

    success, message, backup_codes = enable_2fa_for_user(request.auth_user, code)
    if not success:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': message,
        'backup_codes': backup_codes
    }, status=200)


@csrf_exempt
@require_POST
@auth_required
def disable_2fa_view(request):
    """
    POST /api/v1/auth/2fa/disable
    Disables 2FA.
    """
    data = parse_json_body(request)
    password_or_code = (data.get('password') or data.get('code') or '').strip()

    if not password_or_code:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng nhập mật khẩu hoặc mã xác thực để tiếp tục.'
        }, status=400)

    success, message = disable_2fa_for_user(request.auth_user, password_or_code)
    if not success:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': message
    }, status=200)
