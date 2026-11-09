import threading
from backend.judge.models import Submission, SubmissionTestCase
from .judge_submission import JudgeSubmissionService

class RejudgeService:
    @staticmethod
    def rejudge(submission_id, async_judge=True):
        sub = Submission.objects.filter(id=submission_id).first()
        if not sub:
            return False, "Không tìm thấy bài nộp."

        # Clear existing testcase results
        SubmissionTestCase.objects.filter(submission=sub).delete()

        # Reset submission status
        sub.status = 'QU'
        sub.result = None
        sub.points = 0.0
        sub.time = 0.0
        sub.memory = 0.0
        sub.error = ''
        sub.is_rejudged = True
        sub.save()

        # Dispatch rejudge
        if async_judge:
            t = threading.Thread(target=JudgeSubmissionService.dispatch, args=(sub.id,))
            t.daemon = True
            t.start()
        else:
            JudgeSubmissionService.dispatch(sub.id)
            sub.refresh_from_db()

        return True, "Đã đưa bài nộp vào hàng đợi chấm lại (Rejudge)."
