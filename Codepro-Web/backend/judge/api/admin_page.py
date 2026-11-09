from pathlib import Path
from django.conf import settings
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import redirect
from backend.auth.security.auth_required import get_authenticated_user_from_request
from backend.judge.permissions.judge_manager import IsJudgeManager


def judge_admin_page(request):
    user = get_authenticated_user_from_request(request)
    if not user:
        return redirect('/login?next=/admin/judge')
    request.user = user
    if not IsJudgeManager().has_permission(request, None):
        return HttpResponseForbidden('Cần quyền Judge Admin hoặc Judge Manager.')
    page = Path(settings.BASE_DIR) / 'frontend' / 'html' / 'admin' / 'judge' / 'portal.html'
    response = FileResponse(page.open('rb'), content_type='text/html; charset=utf-8')
    response['Cache-Control'] = 'no-store'
    return response
