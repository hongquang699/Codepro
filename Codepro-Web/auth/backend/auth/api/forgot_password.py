from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from backend.auth.security.device import get_client_ip
from backend.auth.security.auth_required import parse_json_body
from backend.auth.services.password import initiate_password_reset


@csrf_exempt
@require_POST
def forgot_password_view(request):
    """
    POST /api/v1/auth/forgot-password
    Triggers password reset flow. Non-enumerating.
    """
    data = parse_json_body(request)
    identifier = data.get('username') or data.get('email') or ''
    ip = get_client_ip(request)

    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    base_url = f"{scheme}://{host}"

    success, message = initiate_password_reset(identifier, ip_address=ip, base_url=base_url)

    return JsonResponse({
        'success': True,
        'message': message
    }, status=200)
