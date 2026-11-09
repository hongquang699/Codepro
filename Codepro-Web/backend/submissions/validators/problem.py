from backend.judge.models import Problem

class ProblemValidator:
    @staticmethod
    def validate(problem_identifier, user=None, contest_id=None):
        if not problem_identifier:
            return False, "Vui lòng chọn bài tập.", None

        problem = None
        if str(problem_identifier).isdigit():
            problem = Problem.objects.filter(id=int(problem_identifier)).first()
        if not problem:
            problem = Problem.objects.filter(code__iexact=str(problem_identifier)).first()

        if not problem:
            return False, f"Bài tập '{problem_identifier}' không tồn tại.", None

        is_admin = bool(user and user.is_active and (user.is_staff or user.is_superuser))
        if problem.is_organization_private and not is_admin:
            if not user or not user.is_authenticated or not user.is_active:
                return False, "Bạn không có quyền nộp bài cho bài tập này.", None
            from backend.organizations.models import OrganizationMember
            if not any(org.owner_id == user.id or OrganizationMember.objects.filter(
                    organization=org, user=user, status='active').exists()
                    for org in problem.organizations.all()):
                return False, "Bạn không có quyền nộp bài cho bài tập này.", None

        # A private contest problem is checked against its contest below.
        if not problem.is_public and not problem.is_organization_private and not contest_id and not is_admin:
            return False, "Bạn không có quyền nộp bài cho bài tập này.", None

        return True, "", problem
