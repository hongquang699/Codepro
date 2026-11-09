from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from backend.auth.security.auth_required import auth_required, parse_json_body
from backend.auth.security.csrf import csrf_protect_cookie_auth
from backend.auth.services.password import change_user_password
from backend.auth.services.session import revoke_all_user_sessions


@csrf_exempt
@require_POST
@csrf_protect_cookie_auth
@auth_required
def change_password_view(request):
    """
    POST /api/v1/auth/change-password
    Changes password for logged in user.
    """
    data = parse_json_body(request)
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    new_password_confirm = data.get('new_password_confirm', '')

    success, message = change_user_password(
        request.auth_user,
        current_password,
        new_password,
        new_password_confirm
    )

    if not success:
        return JsonResponse({
            'success': False,
            'message': message
        }, status=400)

    # A password change must log out whoever else holds the old credentials.
    revoke_all_user_sessions(request.auth_user, except_raw_token=request.COOKIES.get('cp_session'))
    return JsonResponse({
        'success': True,
        'message': message
    }, status=200)
