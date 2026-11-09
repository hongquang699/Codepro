import json
from functools import wraps
from django.http import JsonResponse
from backend.auth.services.session import validate_auth_session


def get_authenticated_user_from_request(request):
    """
    Extract authenticated User from:
    1. 'cp_session' cookie
    2. 'Authorization: Bearer <token>' header
    3. Standard Django request.user (if already logged in)
    """
    # 1. Cookie
    raw_token = request.COOKIES.get('cp_session')
    if raw_token:
        user = validate_auth_session(raw_token)
        if user:
            return user

    # 2. Authorization Header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        bearer_token = auth_header[7:].strip()
        user = validate_auth_session(bearer_token)
        if user:
            return user

    # 3. Django session fallback
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user

    return None


def auth_required(view_func):
    """Decorator to enforce authentication on API views."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = get_authenticated_user_from_request(request)
        if not user:
            return JsonResponse({
                'success': False,
                'authenticated': False,
                'message': 'Yêu cầu đăng nhập để thực hiện thao tác này.'
            }, status=401)
        request.auth_user = user
        return view_func(request, *args, **kwargs)
    return wrapped_view


def parse_json_body(request) -> dict:
    """Helper to safely parse JSON body from HttpRequest."""
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}
