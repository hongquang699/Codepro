from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.conf import settings
from django.core import signing
from backend.auth.security.device import get_client_ip, get_user_agent
from backend.auth.security.auth_required import parse_json_body
from backend.auth.security.ip_whitelist import is_user_admin, is_admin_ip_allowed
from backend.auth.security.brute_force import is_ip_or_user_locked, record_login_attempt
from backend.auth.services.authentication import authenticate_user
from backend.auth.services.session import create_auth_session
from backend.auth.security.token_auth import get_or_rotate_token
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
        response = JsonResponse({
            'success': True,
            'authenticated': False,
            'requires_2fa': True,
            'user_id': user.id,
            'username': user.username,
            'message': message
        }, status=200)
        challenge = signing.dumps(
            {'user_id': user.id, 'ip': ip, 'remember_me': remember_me}, salt='cp-login-2fa'
        )
        response.set_cookie('cp_2fa_challenge', challenge, max_age=300, httponly=True,
                            secure=settings.SESSION_COOKIE_SECURE, samesite='Lax')
        return response

    # Establish session
    raw_token, session = create_auth_session(user, request, remember_me=remember_me)

    is_admin = bool(user.is_active and (user.is_staff or user.is_superuser))
    user_role = 'admin' if is_admin else 'user'

    drf_token_key = get_or_rotate_token(user).key

    user_rating = 0
    rank_title = 'Unrated'
    try:
        from backend.ranking.models.rating import UserRating
        rating_obj = UserRating.objects.filter(user=user).first()
        if rating_obj and rating_obj.contests_participated > 0:
            user_rating = rating_obj.current_rating
            rank_title = rating_obj.rank_tier
    except Exception:
        pass

    response = JsonResponse({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'rating': user_rating,
            'rank_title': rank_title,
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
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=max_age
    )
    if is_admin:
        response.set_cookie(key='role', value='admin', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='is_admin', value='true', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='admin_token')
    else:
        response.set_cookie(key='role', value='user', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='is_admin')
        response.delete_cookie(key='admin_token')

    response.delete_cookie('cp_2fa_challenge')
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
    raw_code = data.get('code') or ''
    code = raw_code.strip() if isinstance(raw_code, str) else ''

    if not user_id or not code:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu mã xác thực hoặc thông tin người dùng.'
        }, status=400)

    ip = get_client_ip(request)
    try:
        challenge = signing.loads(request.COOKIES.get('cp_2fa_challenge', ''),
                                  salt='cp-login-2fa', max_age=300)
    except signing.BadSignature:
        challenge = None
    if not challenge or str(challenge.get('user_id')) != str(user_id) or challenge.get('ip') != ip:
        return JsonResponse({'success': False, 'message': 'Phiên xác thực 2 bước đã hết hạn. Vui lòng đăng nhập lại.'},
                            status=401)
    remember_me = bool(challenge.get('remember_me', False))

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        return JsonResponse({
            'success': False,
            'message': 'Người dùng không tồn tại.'
        }, status=404)

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

    locked, _ = is_ip_or_user_locked(ip, user.username)
    if locked:
        return JsonResponse({'success': False, 'message': 'Quá nhiều lần thử. Vui lòng đăng nhập lại sau.'}, status=429)

    # Check TOTP or backup code
    is_valid = verify_totp_code(two_factor.secret_key, code)
    if not is_valid and two_factor.backup_codes:
        upper_code = code.upper()
        if upper_code in two_factor.backup_codes:
            is_valid = True
            two_factor.backup_codes.remove(upper_code)
            two_factor.save(update_fields=['backup_codes'])

    if not is_valid:
        record_login_attempt(ip, user.username, is_success=False, user_agent=get_user_agent(request))
        return JsonResponse({
            'success': False,
            'message': 'Mã xác thực 2 bước không chính xác.'
        }, status=401)

    record_login_attempt(ip, user.username, is_success=True, user_agent=get_user_agent(request))

    raw_token, session = create_auth_session(user, request, remember_me=remember_me)

    is_admin = bool(user.is_active and (user.is_staff or user.is_superuser))
    user_role = 'admin' if is_admin else 'user'

    drf_token_key = get_or_rotate_token(user).key

    user_rating = 0
    rank_title = 'Unrated'
    try:
        from backend.ranking.models.rating import UserRating
        rating_obj = UserRating.objects.filter(user=user).first()
        if rating_obj and rating_obj.contests_participated > 0:
            user_rating = rating_obj.current_rating
            rank_title = rating_obj.rank_tier
    except Exception:
        pass

    response = JsonResponse({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'rating': user_rating,
            'rank_title': rank_title,
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
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=max_age
    )
    if is_admin:
        response.set_cookie(key='role', value='admin', max_age=max_age, path='/', samesite='Lax')
        response.set_cookie(key='is_admin', value='true', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='admin_token')
    else:
        response.set_cookie(key='role', value='user', max_age=max_age, path='/', samesite='Lax')
        response.delete_cookie(key='is_admin')
        response.delete_cookie(key='admin_token')

    response.delete_cookie('cp_2fa_challenge')
    return response
