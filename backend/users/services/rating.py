from django.contrib.auth.models import User
from ..models import UserRating, RatingHistory

def calculate_rank(rating):
    if rating >= 3000: return 'Legendary Grandmaster'
    if rating >= 2400: return 'Grandmaster'
    if rating >= 2100: return 'Master'
    if rating >= 1900: return 'Candidate Master'
    if rating >= 1600: return 'Expert'
    if rating >= 1400: return 'Specialist'
    if rating >= 1200: return 'Pupil'
    return 'Newbie'

def get_user_rating(user):
    ur = UserRating.objects.filter(user=user).first()
    if not ur:
        return {'rating': 0, 'max_rating': 0, 'rank': 'Unrated', 'contest_count': 0}

    disp_rating = ur.current_rating if ur.contest_count > 0 else 0
    disp_rank = ur.rank if ur.contest_count > 0 else 'Unrated'

    return {
        'rating': disp_rating,
        'max_rating': ur.max_rating if ur.contest_count > 0 else 0,
        'rank': disp_rank,
        'contest_count': ur.contest_count,
    }

def get_rating_history(user):
    histories = RatingHistory.objects.filter(user=user).order_by('created_at')
    
    data = []
    if histories.exists():
        for h in histories:
            data.append({
                'contest_id': h.contest_id,
                'contest_name': h.contest_name,
                'old_rating': h.old_rating,
                'new_rating': h.new_rating,
                'change': h.change,
                'rank': h.rank,
                'date': h.created_at.strftime('%Y-%m-%d')
            })
    else:
        try:
            from backend.ranking.models.rating_history import RatingHistoryRecord
            r_records = RatingHistoryRecord.objects.filter(user=user).order_by('timestamp')
            for r in r_records:
                data.append({
                    'contest_id': str(r.contest.id) if r.contest else '',
                    'contest_name': r.contest_name,
                    'old_rating': r.old_rating,
                    'new_rating': r.new_rating,
                    'change': r.rating_change,
                    'rank': r.rank_in_contest,
                    'date': r.timestamp.strftime('%Y-%m-%d') if hasattr(r, 'timestamp') and r.timestamp else ''
                })
        except Exception:
            pass

    return data
