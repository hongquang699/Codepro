from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from backend.auth.security.device import get_client_ip, get_user_agent
from backend.auth.security.auth_required import parse_json_body
from backend.auth.security.ip_whitelist import is_user_admin, is_admin_ip_allowed
from backend.auth.services.authentication import authenticate_user
from backend.auth.services.session import create_auth_session
from backend.auth.services.two_factor import verify_totp_code
from backend.auth.models.two_factor import TwoFactorAuth


@csrf_exempt
@require_POST
def login_view(request):
    """
    POST /api/v1/auth/login
    Authenticates user, checks brute force, verifies Admin IP Whitelist, provisions session.
    """
    data = parse_json_body(request)
    identifier = data.get('username') or data.get('email') or ''
    password = data.get('password') or ''
    remember_me = bool(data.get('remember_me', False))

    ip = get_client_ip(request)
    ua = get_user_agent(request)

    success, message, user, requires_2fa = authenticate_user(
        identifier,
        password,
        ip_address=ip,
        user_agent=ua
    )

    if not success:
        status_code = 403 if "IP được ủy quyền" in message else 401
        return JsonResponse({
            'success': False,
            'authenticated': False,
            'message': message,
            'error_code': 'ADMIN_IP_RESTRICTED' if status_code == 403 else 'INVALID_CREDENTIALS'
        }, status=status_code)

    if requires_2fa:
        return JsonResponse({
            'success': True,
            'authenticated': False,
            'requires_2fa': True,
            'user_id': user.id,
            'username': user.username,
            'message': message
        }, status=200)

    # Establish session
    raw_token, session = create_auth_session(user, request, remember_me=remember_me)

    is_admin = bool(user.is_staff or user.is_superuser or user.username.lower() in ['admin', 'root'])
    user_role = 'admin' if is_admin else 'user'

    drf_token_key = raw_token
    try:
        from rest_framework.authtoken.models import Token
        drf_token, _ = Token.objects.get_or_create(user=user)
        drf_token_key = drf_token.key
    except Exception:
        pass

    response = JsonResponse({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user_role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_admin': is_admin,
        },
        'session_token': raw_token,
        'token': drf_token_key,
    }, status=200)

    max_age = (30 * 86400) if remember_me else 86400

    response.set_cookie(
        key='cp_session',
        value=raw_token,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=max_age
    )
    if is_admin:
        response.set_cookie(key='role', value='admin', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='is_admin', value='true', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='admin_token', value=drf_token_key, max_age=max_age, path='/', samesite='Lax')
    else:
        response.set_cookie(key='role', value='user', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='is_admin')
        response.delete_cookie(key='admin_token')

    return response


@csrf_exempt
@require_POST
def verify_2fa_login_view(request):
    """
    POST /api/v1/auth/2fa/verify-login
    Validates second factor during login, enforcing Admin IP Whitelist.
    """
    data = parse_json_body(request)
    user_id = data.get('user_id')
    code = (data.get('code') or '').strip()
    remember_me = bool(data.get('remember_me', False))

    if not user_id or not code:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu mã xác thực hoặc thông tin người dùng.'
        }, status=400)

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        return JsonResponse({
            'success': False,
            'message': 'Người dùng không tồn tại.'
        }, status=404)

    ip = get_client_ip(request)
    if is_user_admin(user) and not is_admin_ip_allowed(ip):
        return JsonResponse({
            'success': False,
            'authenticated': False,
            'message': f'Đăng nhập bị từ chối: Tài khoản Quản trị viên (Admin) chỉ được phép đăng nhập từ IP được ủy quyền. Địa chỉ IP của bạn ({ip}) không nằm trong danh sách cho phép.',
            'error_code': 'ADMIN_IP_RESTRICTED'
        }, status=403)

    two_factor = TwoFactorAuth.objects.filter(user=user, is_enabled=True).first()
    if not two_factor:
        return JsonResponse({
            'success': False,
            'message': 'Xác thực 2 bước chưa được bật.'
        }, status=400)

    # Check TOTP or backup code
    is_valid = verify_totp_code(two_factor.secret_key, code)
    if not is_valid and two_factor.backup_codes:
        upper_code = code.upper()
        if upper_code in two_factor.backup_codes:
            is_valid = True
            two_factor.backup_codes.remove(upper_code)
            two_factor.save(update_fields=['backup_codes'])

    if not is_valid:
        return JsonResponse({
            'success': False,
            'message': 'Mã xác thực 2 bước không chính xác.'
        }, status=401)

    raw_token, session = create_auth_session(user, request, remember_me=remember_me)

    is_admin = bool(user.is_staff or user.is_superuser or user.username.lower() in ['admin', 'root'])
    user_role = 'admin' if is_admin else 'user'

    drf_token_key = raw_token
    try:
        from rest_framework.authtoken.models import Token
        drf_token, _ = Token.objects.get_or_create(user=user)
        drf_token_key = drf_token.key
    except Exception:
        pass

    response = JsonResponse({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user_role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_admin': is_admin,
        },
        'session_token': raw_token,
        'token': drf_token_key,
    }, status=200)

    max_age = (30 * 86400) if remember_me else 86400
    response.set_cookie(
        key='cp_session',
        value=raw_token,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=max_age
    )
    if is_admin:
        response.set_cookie(key='role', value='admin', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='is_admin', value='true', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='admin_token', value=drf_token_key, max_age=max_age, path='/', samesite='Lax')
    else:
        response.set_cookie(key='role', value='user', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='is_admin')
        response.delete_cookie(key='admin_token')

    return response
