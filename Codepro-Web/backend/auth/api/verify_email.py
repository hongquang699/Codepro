from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from backend.auth.security.auth_required import parse_json_body
from backend.auth.services.registration import verify_registration_otp
from backend.auth.services.session import create_auth_session


@csrf_exempt
@require_POST
def verify_email_view(request):
    """
    POST /api/v1/auth/verify-email
    Verifies 6-digit OTP, provisions user, automatically establishes session.
    """
    data = parse_json_body(request)
    email = data.get('email', '')
    otp = data.get('otp', '')

    success, message, user = verify_registration_otp(email, otp)
    if not success or not user:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)

    # Establish session
    raw_token, session = create_auth_session(user, request, remember_me=True)

    response = JsonResponse({
        'success': True,
        'message': message,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'session_token': raw_token
    }, status=200)

    # Set HttpOnly Cookie
    response.set_cookie(
        key='cp_session',
        value=raw_token,
        httponly=True,
        samesite='Lax',
        secure=False,  # Set to True when HTTPS is enabled
        max_age=30 * 86400
    )

    return response
