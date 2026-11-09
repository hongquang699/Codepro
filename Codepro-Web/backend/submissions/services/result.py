from backend.judge.models import Submission, SubmissionTestCase
from backend.judge.permissions.submissions import can_view_submission_details
from ..models.submission_result import SubmissionResult

class ResultService:
    @staticmethod
    def get_detail(submission_id, requesting_user=None):
        sub = Submission.objects.filter(id=submission_id).select_related(
            'problem', 'user__user', 'language', 'contest'
        ).first()

        if not sub:
            return None

        # Determine if source code can be viewed: Only Admin or the Submission Author
        can_view_source = can_view_submission_details(requesting_user, sub)

        status_display = {
            'QU': 'QUEUED',
            'P': 'PROCESSING',
            'G': 'GRADING',
            'D': 'FINISHED'
        }.get(sub.status, sub.status)

        verdict_code = sub.result or ('QUEUED' if sub.status in ('QU', 'P', 'G') else 'PENDING')
        verdict_name = SubmissionResult.get_verdict_name(verdict_code)

        return {
            'id': sub.id,
            'problem': {
                'id': sub.problem.id,
                'code': sub.problem.code,
                'name': sub.problem.name,
                'points': sub.problem.points,
            },
            'user': {
                'id': sub.user.user.id,
                'username': sub.user.user.username,
            },
            'contest': {
                'id': sub.contest.id,
                'key': sub.contest.key,
                'name': sub.contest.name,
            } if sub.contest else None,
            'language': {
                'id': sub.language.id,
                'key': sub.language.key,
                'name': sub.language.name,
            },
            'status': status_display,
            'verdict': verdict_code,
            'verdict_name': verdict_name,
            'score': sub.points or 0.0,
            'execution_time': round((sub.time or 0.0) * 1000, 1), # in ms
            'memory_used': round((sub.memory or 0.0) / 1024, 2), # in MB
            'compile_time': None,
            'source_code': sub.source if can_view_source else None,
            'error': (sub.error or '') if can_view_source else '',
            'created_at': sub.date.strftime('%Y-%m-%d %H:%M:%S'),
            'is_rejudged': sub.is_rejudged
        }

    @staticmethod
    def get_testcases(submission_id):
        cases = SubmissionTestCase.objects.filter(submission_id=submission_id).order_by('case')
        results = []
        for c in cases:
            results.append({
                'case': c.case,
                'verdict': c.status,
                'verdict_name': SubmissionResult.get_verdict_name(c.status),
                'time': round(c.time * 1000, 1), # ms
                'memory': round(c.memory / 1024, 2), # MB
                'score': c.points,
                'total_points': c.total_points,
                'checker_message': c.feedback or ''
                # Hidden test inputs are purposefully NOT included here for security
            })
        return results
