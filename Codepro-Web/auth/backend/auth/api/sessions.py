from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from backend.auth.security.auth_required import auth_required, parse_json_body
from backend.auth.services.session import get_user_active_sessions, revoke_all_user_sessions
from backend.auth.models.auth_session import AuthSession


@require_GET
@auth_required
def list_sessions_view(request):
    """
    GET /api/v1/auth/sessions
    Returns list of active sessions for current user.
    """
    sessions = get_user_active_sessions(request.auth_user)
    return JsonResponse({
        'success': True,
        'sessions': sessions
    }, status=200)


@csrf_exempt
@require_POST
@auth_required
def revoke_other_sessions_view(request):
    """
    POST /api/v1/auth/sessions/revoke-others
    Revokes all sessions except the current one.
    """
    raw_token = request.COOKIES.get('cp_session')
    if not raw_token:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            raw_token = auth_header[7:].strip()

    revoke_all_user_sessions(request.auth_user, except_raw_token=raw_token)

    return JsonResponse({
        'success': True,
        'message': 'Đã đăng xuất khỏi tất cả các thiết bị khác.'
    }, status=200)


@csrf_exempt
@require_POST
@auth_required
def revoke_session_by_id_view(request, session_id):
    """
    POST /api/v1/auth/sessions/<session_id>/revoke
    Revokes a specific session by id.
    """
    session = AuthSession.objects.filter(
        id=session_id,
        user=request.auth_user,
        is_active=True
    ).first()

    if not session:
        return JsonResponse({
            'success': False,
            'message': 'Phiên đăng nhập không tồn tại hoặc đã hết hạn.'
        }, status=404)

    session.is_active = False
    session.save(update_fields=['is_active'])

    return JsonResponse({
        'success': True,
        'message': 'Đã thu hồi phiên đăng nhập thành công.'
    }, status=200)
