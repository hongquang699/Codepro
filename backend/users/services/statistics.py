from django.contrib.auth.models import User
from ..models import UserStatistics

def get_user_statistics(user):
    from backend.judge.models import Submission, ContestParticipation

    subs = Submission.objects.filter(user__user=user)
    total_submissions = subs.count()
    ac = subs.filter(result='AC').count()
    wa = subs.filter(result='WA').count()
    tle = subs.filter(result='TLE').count()
    mle = subs.filter(result='MLE').count()
    rte = subs.filter(result='RTE').count()
    ce = subs.filter(result='CE').count()

    solved_problems = subs.filter(result='AC').values('problem').distinct().count()
    attempted_problems = subs.values('problem').distinct().count()

    contests = ContestParticipation.objects.filter(user__user=user).count()

    # Get rating
    rating = 0
    try:
        from ..models import UserRating
        ur = UserRating.objects.filter(user=user).first()
        if ur and getattr(ur, 'contest_count', 0) > 0:
            rating = ur.current_rating
        else:
            from backend.judge.models import Profile as JudgeProfile
            jp = JudgeProfile.objects.filter(user=user).first()
            if jp and jp.rating:
                rating = jp.rating
    except Exception:
        pass

    # Public reads must not write a cache row; concurrent profile requests can
    # otherwise contend for the SQLite writer lock.
    contest_wins = UserStatistics.objects.filter(user=user).values_list('contest_wins', flat=True).first() or 0

    ac_rate = round((ac / total_submissions * 100), 1) if total_submissions > 0 else 0.0

    return {
        'total_submissions': total_submissions,
        'accepted_submissions': ac,
        'wrong_answers': wa,
        'compilation_errors': ce,
        'runtime_errors': rte,
        'time_limit_exceeded': tle,
        'memory_limit_exceeded': mle,
        'solved_problems': solved_problems,
        'attempted_problems': attempted_problems,
        'ac_rate': ac_rate,
        'contests': contests,
        'contest_wins': contest_wins,
        'rating': rating,
    }
