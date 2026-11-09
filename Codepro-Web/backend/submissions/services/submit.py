import threading
from .create_submission import CreateSubmissionService
from .judge_submission import JudgeSubmissionService

class SubmitService:
    @classmethod
    def submit(cls, user, problem_id, language_id, source_code, contest_id=None, async_judge=True):
        """
        Coordinates full submission lifecycle:
        1. Validate & Create in DB (status=QUEUED)
        2. Dispatches to Judge Server
        """
        sub, err = CreateSubmissionService.create(
            user=user,
            problem_id=problem_id,
            language_id=language_id,
            source_code=source_code,
            contest_id=contest_id
        )

        if err:
            return {'success': False, 'error': err}

        # Dispatch grading
        if async_judge:
            # Spawn in thread to return QUEUED immediately
            t = threading.Thread(target=JudgeSubmissionService.dispatch, args=(sub.id,))
            t.daemon = True
            t.start()
        else:
            JudgeSubmissionService.dispatch(sub.id)
            sub.refresh_from_db()

        return {
            'success': True,
            'id': sub.id,
            'status': 'QUEUED',
            'problem': sub.problem.code,
            'language': sub.language.name,
            'created_at': sub.date.isoformat()
        }
