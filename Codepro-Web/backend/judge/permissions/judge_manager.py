from rest_framework.permissions import BasePermission


class IsJudgeManager(BasePermission):
    message = 'Cần quyền Judge Admin hoặc Judge Manager.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__in=['judge_admin', 'judge_manager']).exists():
            return True
        profile = getattr(user, 'profile', None)
        return bool(profile and profile.role in ('admin', 'judge_admin', 'judge_manager'))
