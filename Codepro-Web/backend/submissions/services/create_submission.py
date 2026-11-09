import hashlib
from backend.judge.models import Submission, Profile
from ..validators.source import SourceCodeValidator
from ..validators.language import LanguageValidator
from ..validators.problem import ProblemValidator
from ..validators.contest import ContestValidator

class CreateSubmissionService:
    @classmethod
    def create(cls, user, problem_id, language_id, source_code, contest_id=None):
        """
        Validates all inputs and creates a new Submission in QUEUED state.
        """
        # 1. Validate User
        if not user or not user.is_authenticated or not user.is_active:
            return None, "Vui lòng đăng nhập bằng tài khoản đang hoạt động để nộp bài."
        
        profile, _ = Profile.objects.get_or_create(user=user)

        # 2. Validate Source Code
        ok, err = SourceCodeValidator.validate(source_code)
        if not ok:
            return None, err

        # 3. Validate Language
        ok, err, lang = LanguageValidator.validate(language_id)
        if not ok:
            return None, err

        # 4. Validate Problem
        ok, err, problem = ProblemValidator.validate(problem_id, user=user, contest_id=contest_id)
        if not ok:
            return None, err

        # 5. Validate Contest
        ok, err, contest = ContestValidator.validate(contest_id, user=user, problem=problem)
        if not ok:
            return None, err

        # 6. Create Submission
        sub = Submission.objects.create(
            user=profile,
            problem=problem,
            language=lang,
            contest=contest,
            source=source_code,
            status='QU',
            result=None,
            points=0.0
        )

        return sub, ""
