from backend.judge.models import Submission
from backend.judge.bridge import grade_submission

def rejudge_contest_submission(submission_id):
    """Rejudge a single submission."""
    sub = Submission.objects.filter(id=submission_id).first()
    if not sub:
        return False, "Không tìm thấy bài nộp"
    sub.is_rejudged = True
    sub.save(update_fields=['is_rejudged'])
    grade_submission(sub.id)
    return True, f"Đã gửi chấm lại bài nộp #{sub.id}"

def rejudge_contest_problem(contest, problem):
    """Rejudge all submissions for a problem in this contest."""
    subs = Submission.objects.filter(contest=contest, problem=problem)
    count = subs.count()
    for s in subs:
        s.is_rejudged = True
        s.save(update_fields=['is_rejudged'])
        grade_submission(s.id)
    return count

def rejudge_entire_contest(contest):
    """Rejudge all submissions across all problems in this contest."""
    subs = Submission.objects.filter(contest=contest)
    count = subs.count()
    for s in subs:
        s.is_rejudged = True
        s.save(update_fields=['is_rejudged'])
        grade_submission(s.id)
    return count
