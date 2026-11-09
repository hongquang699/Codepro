from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from backend.auth.services.session import revoke_auth_session
from backend.auth.security.csrf import csrf_protect_cookie_auth


@csrf_exempt
@require_POST
@csrf_protect_cookie_auth
def logout_view(request):
    """
    POST /api/v1/auth/logout
    Revokes the current session and clears the session cookie.
    """
    raw_token = request.COOKIES.get('cp_session')
    if not raw_token:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            raw_token = auth_header[7:].strip()

    if raw_token:
        revoke_auth_session(raw_token)

    response = JsonResponse({
        'success': True,
        'message': 'Đăng xuất thành công.'
    }, status=200)

    response.delete_cookie('cp_session')
    return response
