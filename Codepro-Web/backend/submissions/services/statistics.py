from django.db.models import Count
from backend.judge.models import Submission

class SubmissionStatisticsService:
    @staticmethod
    def get_stats(user_id=None, problem_id=None, contest_id=None):
        qs = Submission.objects.all()
        if user_id:
            qs = qs.filter(user_id=user_id)
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        if contest_id:
            qs = qs.filter(contest_id=contest_id)

        total = qs.count()
        verdicts = dict(qs.values('result').annotate(count=Count('id')).values_list('result', 'count'))
        ac_count = verdicts.get('AC', 0)
        ac_rate = round((ac_count / total * 100), 1) if total > 0 else 0.0

        return {
            'total_submissions': total,
            'ac_count': ac_count,
            'ac_rate': ac_rate,
            'verdicts': verdicts
        }
