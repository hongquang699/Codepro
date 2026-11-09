from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from backend.auth.security.auth_required import parse_json_body
from backend.auth.services.password import verify_password_reset_token, complete_password_reset


@csrf_exempt
@require_GET
def check_reset_token_view(request):
    """
    GET /api/v1/auth/reset-password/validate?token=...
    Checks if a reset token is valid before rendering the form.
    """
    token = request.GET.get('token', '')
    is_valid, message, user = verify_password_reset_token(token)

    if not is_valid:
        return JsonResponse({
            'valid': False,
            'message': message
        }, status=400)

    return JsonResponse({
        'valid': True,
        'username': user.username if user else ''
    }, status=200)


@csrf_exempt
@require_POST
def reset_password_view(request):
    """
    POST /api/v1/auth/reset-password
    Applies the new password using token.
    """
    data = parse_json_body(request)
    token = data.get('token', '')
    password = data.get('password', '')
    password_confirm = data.get('password_confirm', '')

    success, message = complete_password_reset(token, password, password_confirm)
    if not success:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': message
    }, status=200)
