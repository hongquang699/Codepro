from ..models.rating import UserRating
from ..models.rating_history import RatingHistoryRecord

class RatingRepository:
    @staticmethod
    def get_rating_leaderboard(page=1, page_size=50, tier=None, search=None):
        qs = UserRating.objects.select_related('user').filter(contests_participated__gt=0)
        if tier:
            qs = qs.filter(rank_tier__iexact=tier)
        if search:
            qs = qs.filter(user__username__icontains=search)
            
        total_count = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = list(qs.order_by('-current_rating')[start:end])
        return items, total_count

    @staticmethod
    def get_user_rating(user):
        rating_obj = UserRating.objects.filter(user=user).first()
        if not rating_obj:
            rating_obj = UserRating.objects.create(
                user=user,
                current_rating=0,
                max_rating=0,
                rank_tier='Unrated',
                contests_participated=0
            )
        return rating_obj

    @staticmethod
    def get_user_history(user):
        return list(RatingHistoryRecord.objects.filter(user=user).order_by('timestamp'))

    @staticmethod
    def record_history(user, contest, old_rating, new_rating, delta, rank_in_contest, performance=None):
        contest_name = contest.name if contest else 'Contest'
        return RatingHistoryRecord.objects.create(
            user=user,
            contest=contest,
            contest_name=contest_name,
            old_rating=old_rating,
            new_rating=new_rating,
            rating_change=delta,
            rank_in_contest=rank_in_contest,
            performance=performance
        )
