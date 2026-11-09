from django.contrib.auth.models import User
from ..models.rating import UserRating
from ..models.rating_history import RatingHistoryRecord
from ..models.contest_ranking import ContestRanking
from ..calculators.rating import CodeforcesRatingCalculator
from ..repositories.rating_repository import RatingRepository
from backend.judge.models import Contest, Profile

class RatingService:
    @staticmethod
    def get_leaderboard(page=1, page_size=50, tier=None, search=None):
        items, total = RatingRepository.get_rating_leaderboard(page, page_size, tier, search)
        results = []
        for idx, r in enumerate(items, start=(page - 1) * page_size + 1):
            tier_info = UserRating.get_tier_info(r.current_rating)
            results.append({
                'rank': idx,
                'user_id': r.user.id,
                'username': r.user.username,
                'rating': r.current_rating,
                'max_rating': r.max_rating,
                'tier': tier_info['tier'],
                'tier_color': tier_info['color'],
                'badge': tier_info['badge'],
                'contests_count': r.contests_participated,
            })
        return {
            'page': page,
            'page_size': page_size,
            'total': total,
            'items': results
        }

    @staticmethod
    def get_user_rating_profile(username_or_id):
        user = None
        if isinstance(username_or_id, int) or (isinstance(username_or_id, str) and username_or_id.isdigit()):
            user = User.objects.filter(id=int(username_or_id)).first()
        if not user:
            user = User.objects.filter(username=str(username_or_id)).first()

        if not user:
            return None

        rating_obj = RatingRepository.get_user_rating(user)
        history_records = RatingRepository.get_user_history(user)
        tier_info = UserRating.get_tier_info(rating_obj.current_rating)

        history_data = []
        for h in history_records:
            history_data.append({
                'contest_id': h.contest.id if h.contest else None,
                'contest_name': h.contest_name or (h.contest.name if h.contest else 'Contest'),
                'old_rating': h.old_rating,
                'new_rating': h.new_rating,
                'rating_change': h.rating_change,
                'rank': h.rank_in_contest,
                'performance': h.performance,
                'date': h.timestamp.strftime('%Y-%m-%d %H:%M'),
            })

        return {
            'user_id': user.id,
            'username': user.username,
            'rating': rating_obj.current_rating,
            'max_rating': rating_obj.max_rating,
            'tier': tier_info['tier'],
            'tier_color': tier_info['color'],
            'badge': tier_info['badge'],
            'contests_participated': rating_obj.contests_participated,
            'history': history_data
        }

    @staticmethod
    def calculate_and_apply_contest_ratings(contest_id):
        """
        Runs the rating recalculation on contest completion.
        """
        contest = Contest.objects.filter(id=contest_id).first()
        if not contest:
            return {'error': 'Contest not found'}

        # Only process rating changes for rated contests
        if hasattr(contest, 'is_rated') and not contest.is_rated:
            return {'message': 'Contest is unrated. No ratings changed.', 'updated_count': 0}

        rankings = ContestRanking.objects.filter(contest=contest).select_related('user').order_by('rank')
        if not rankings.exists():
            return {'error': 'No rankings available for this contest'}

        contestants_payload = []
        user_map = {}
        for r in rankings:
            user = r.user
            user_rating_obj = RatingRepository.get_user_rating(user)
            user_map[user.id] = (user, user_rating_obj, r)
            # Users with 0 contests or 0 rating are seeded with 1500 as initial baseline for delta calculation
            calc_rating = user_rating_obj.current_rating if (user_rating_obj.contests_participated > 0 and user_rating_obj.current_rating > 0) else 1500
            contestants_payload.append({
                'user_id': user.id,
                'rating': calc_rating,
                'rank': r.rank
            })

        # Calculate deltas via CodeforcesRatingCalculator
        results = CodeforcesRatingCalculator.calculate_deltas(contestants_payload)

        updated_records = []
        for res in results:
            uid = res['user_id']
            user, rating_obj, rank_entry = user_map[uid]
            old_r = res['rating']
            new_r = res['new_rating']
            delta = res['delta']
            perf = res['performance']

            # Update UserRating
            rating_obj.current_rating = new_r
            if new_r > rating_obj.max_rating:
                rating_obj.max_rating = new_r
            rating_obj.contests_participated += 1
            tier_info = UserRating.get_tier_info(new_r, contests_participated=rating_obj.contests_participated)
            rating_obj.rank_tier = tier_info['tier']
            rating_obj.save()

            # Sync with Profile
            profile = getattr(user, 'profile', None)
            if profile:
                profile.rating = new_r
                profile.update_rating_rank()

            # Sync with users.models.user_rating
            try:
                from backend.users.models.user_rating import UserRating as AppUserRating, RatingHistory as AppRatingHistory
                aur = AppUserRating.objects.filter(user=user).first()
                if aur:
                    aur.current_rating = new_r
                    if new_r > aur.max_rating:
                        aur.max_rating = new_r
                    aur.contest_count += 1
                    aur.rank = aur.calculate_rank()
                    aur.save()
                    AppRatingHistory.objects.create(
                        user=user,
                        contest_id=str(getattr(contest, 'id', '') or getattr(contest, 'key', '')),
                        contest_name=getattr(contest, 'name', '') or str(contest),
                        old_rating=old_r,
                        new_rating=new_r,
                        change=delta,
                        rank=rank_entry.rank
                    )
            except Exception:
                pass

            # Record history
            RatingRepository.record_history(
                user=user,
                contest=contest,
                old_rating=old_r,
                new_rating=new_r,
                delta=delta,
                rank_in_contest=rank_entry.rank,
                performance=perf
            )

            # Update ContestRanking entry
            rank_entry.rating_before = old_r
            rank_entry.rating_after = new_r
            rank_entry.rating_change = delta
            rank_entry.save(update_fields=['rating_before', 'rating_after', 'rating_change'])

            updated_records.append({
                'user_id': uid,
                'username': user.username,
                'old_rating': old_r,
                'new_rating': new_r,
                'delta': delta,
                'rank': rank_entry.rank
            })

        return {'status': 'success', 'updated_count': len(updated_records), 'records': updated_records}
