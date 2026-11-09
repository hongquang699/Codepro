import logging
from backend.judge.bridge import grade_submission
from backend.judge.models import Submission

logger = logging.getLogger('submissions.judge')

class JudgeSubmissionService:
    @classmethod
    def dispatch(cls, submission_id: int):
        """
        Dispatches the submission to the Judge System.
        """
        sub = Submission.objects.filter(id=submission_id).select_related('problem', 'language', 'user').first()
        if not sub:
            logger.error(f"Submission #{submission_id} not found.")
            return False

        try:
            sub.status = 'P' # Processing
            sub.save(update_fields=['status'])
            # Run grading through bridge
            grade_submission(sub.id)
            logger.info(f"Submission #{submission_id} graded with verdict {sub.result}")
            return True
        except Exception as e:
            logger.error(f"Error grading submission #{submission_id}: {e}")
            sub.status = 'D'
            sub.result = 'IE'
            sub.error = str(e)
            sub.save(update_fields=['status', 'result', 'error'])
            return False
