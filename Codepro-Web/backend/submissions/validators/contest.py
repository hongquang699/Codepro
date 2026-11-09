from django.utils import timezone
from backend.judge.models import Contest, ContestParticipation, ContestProblem

class ContestValidator:
    @staticmethod
    def validate(contest_identifier, user=None, problem=None):
        if not contest_identifier:
            return True, "", None # Not a contest submission

        contest = None
        if str(contest_identifier).isdigit():
            contest = Contest.objects.filter(id=int(contest_identifier)).first()
        if not contest:
            contest = Contest.objects.filter(key__iexact=str(contest_identifier)).first()

        if not contest:
            return False, f"Kỳ thi '{contest_identifier}' không tồn tại.", None

        if not user or not user.is_authenticated or not user.is_active:
            return False, "Vui lòng đăng nhập để nộp bài.", None

        now = timezone.now()
        if not contest.is_visible or not contest.start_time <= now <= contest.end_time:
            return False, "Kỳ thi chưa mở hoặc đã kết thúc.", None

        if problem is None or not ContestProblem.objects.filter(contest=contest, problem=problem).exists():
            return False, "Bài tập không thuộc kỳ thi này.", None

        participation = ContestParticipation.objects.filter(contest=contest, user__user=user).first()
        if not participation or participation.is_disqualified:
            return False, "Bạn chưa đăng ký hoặc đã bị loại khỏi kỳ thi này.", None

        from backend.organizations.models import OrganizationContest, OrganizationMember
        org_contest = OrganizationContest.objects.filter(contest=contest).select_related('organization').first()
        if org_contest and not (user.is_staff or user.is_superuser):
            org = org_contest.organization
            if org.owner_id != user.id and not OrganizationMember.objects.filter(
                    organization=org, user=user, status='active').exists():
                return False, "Bạn không có quyền truy cập kỳ thi nội bộ này.", None

        return True, "", contest
