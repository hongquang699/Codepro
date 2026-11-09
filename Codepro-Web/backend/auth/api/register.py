from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from backend.auth.security.device import get_client_ip
from backend.auth.security.auth_required import parse_json_body
from backend.auth.services.registration import initiate_registration, resend_registration_otp


@csrf_exempt
@require_POST
def register_view(request):
    """
    POST /api/v1/auth/register
    Initiates registration, checks validation and sends 6-digit OTP email.
    """
    data = parse_json_body(request)
    ip = get_client_ip(request)

    success, message, extra = initiate_registration(data, ip_address=ip)
    if not success:
        return JsonResponse({
            'success': False,
            'message': message,
            'errors': extra if isinstance(extra, dict) and 'wait_seconds' not in extra else {},
            'wait_seconds': extra.get('wait_seconds', 0) if isinstance(extra, dict) else 0
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': message,
        'data': extra
    }, status=201)


@csrf_exempt
@require_POST
def resend_verification_view(request):
    """
    POST /api/v1/auth/resend-verification
    Resends 6-digit verification OTP if cooldown allows.
    """
    data = parse_json_body(request)
    email = data.get('email', '')
    ip = get_client_ip(request)

    success, message, wait_sec = resend_registration_otp(email, ip_address=ip)
    if not success:
        return JsonResponse({
            'success': False,
            'message': message,
            'wait_seconds': wait_sec
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': message,
        'wait_seconds': wait_sec
    }, status=200)
