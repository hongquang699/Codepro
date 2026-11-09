from backend.judge.models import Problem, Submission
from ..models.rating import UserRating

class ScoreService:
    @staticmethod
    def get_problem_top_solvers(problem_code, limit=50):
        problem = Problem.objects.filter(code=problem_code).first()
        if not problem:
            return {'error': 'Problem not found', 'solvers': []}

        # Best submissions: AC, sorted by time (runtime) ASC, memory ASC, date ASC
        ac_subs = Submission.objects.filter(problem=problem, result='AC').select_related('user__user').order_by('time', 'memory', 'date')[:limit]

        solvers = []
        for idx, s in enumerate(ac_subs, 1):
            user = s.user.user
            rating_val = s.user.rating or 1500
            tier_info = UserRating.get_tier_info(rating_val)
            solvers.append({
                'rank': idx,
                'submission_id': s.id,
                'username': user.username,
                'rating': rating_val,
                'tier': tier_info['tier'],
                'tier_color': tier_info['color'],
                'time': s.time or 0.0,
                'memory': s.memory or 0.0,
                'language': s.language.name if s.language else 'C++',
                'date': s.date.strftime('%Y-%m-%d %H:%M'),
            })

        return {
            'problem_code': problem.code,
            'problem_name': problem.name,
            'total_ac': Submission.objects.filter(problem=problem, result='AC').count(),
            'solvers': solvers
        }
