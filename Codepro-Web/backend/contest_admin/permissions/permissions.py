from backend.judge.models import Contest

# Role capability mapping
ROLE_PERMISSIONS = {
    'owner': ['*'],
    'contest_manager': [
        'contest.view', 'contest.edit', 'participant.manage', 'announcement.manage',
        'clarification.manage', 'ranking.manage', 'reports.view', 'problem.view',
        'submission.view', 'audit.view', 'anti_cheat.view', 'anti_cheat.manage',
        'anti_cheat.review', 'anti_cheat.penalize'
    ],
    'problem_setter': [
        'contest.view', 'problem.view', 'problem.create', 'problem.edit',
        'testcase.manage', 'checker.manage', 'validator.manage', 'solution.manage',
        'submission.view'
    ],
    'jury_manager': [
        'contest.view', 'submission.view', 'submission.rejudge', 'judge.view',
        'ranking.manage', 'reports.view', 'audit.view', 'anti_cheat.view',
        'anti_cheat.manage', 'anti_cheat.review'
    ],
    'moderator': [
        'contest.view', 'participant.manage', 'clarification.manage', 'announcement.manage',
        'submission.view'
    ],
    'observer': [
        'contest.view', 'ranking.manage', 'reports.view', 'submission.view'
    ]
}

def resolve_admin_user(request):
    """Use only the account authenticated by DRF for contest administration."""
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_active:
        return request.user
    return None

def has_contest_permission(user, contest, permission_name):
    """
    Check if user has specific permission in this contest.
    Active superusers, staff, and organization owners have full rights.
    """
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or user.is_staff:
        return True

    # Check if contest was created by user or linked through organization owned by user
    from backend.organizations.models import OrganizationContest
    oc = OrganizationContest.objects.filter(contest=contest).select_related('organization').first()
    if oc and oc.organization.owner_id == getattr(user, 'id', None):
        return True

    from ..models.models import ContestAdminRole
    role_obj = ContestAdminRole.objects.filter(contest=contest, user=user).first()
    if not role_obj:
        return False

    role = role_obj.role
    perms = ROLE_PERMISSIONS.get(role, [])
    if '*' in perms or permission_name in perms:
        return True
    
    prefix = permission_name.split('.')[0] + '.*'
    if prefix in perms:
        return True

    return False

def public_results_cutoff(user, contest):
    """None = viewer may see live results; otherwise only results submitted before this time."""
    from django.utils import timezone
    if not contest.hide_scoreboard or timezone.now() > contest.end_time:
        return None
    if has_contest_permission(user, contest, 'ranking.manage'):
        return None
    return contest.scoreboard_freeze or contest.start_time

def get_user_contest_role(user, contest):
    """Return user's assigned role name or 'Admin' for superusers."""
    if not user or not user.is_authenticated or not user.is_active:
        return None
    if user.is_superuser or user.is_staff:
        return 'Contest Administrator'
    
    from backend.organizations.models import OrganizationContest
    oc = OrganizationContest.objects.filter(contest=contest).select_related('organization').first()
    if oc and oc.organization.owner_id == getattr(user, 'id', None):
        return 'Contest Owner'

    from ..models.models import ContestAdminRole
    role_obj = ContestAdminRole.objects.filter(contest=contest, user=user).first()
    if role_obj:
        return role_obj.get_role_display()
    
    return None
