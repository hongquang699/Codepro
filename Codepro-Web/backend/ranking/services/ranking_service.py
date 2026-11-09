from django.contrib.auth.models import User
from django.db.models import Count, Sum, F, Q
from ..models.ranking import GlobalRanking
from ..models.rating import UserRating
from ..repositories.ranking_repository import RankingRepository
from backend.judge.models import Submission, Profile

class RankingService:
    @staticmethod
    def get_global_rankings(page=1, page_size=50, country=None, school=None, org_id=None, search=None):
        items, total = RankingRepository.get_global_rankings(page, page_size, country, school, org_id, search)
        results = []
        for r in items:
            contests_count = getattr(getattr(r.user, 'rating_profile', None), 'contests_participated', 0)
            tier_info = UserRating.get_tier_info(r.rating, contests_count)
            is_verified = False
            try:
                prof = Profile.objects.filter(user=r.user).first()
                if prof:
                    is_verified = getattr(prof, 'is_verified', False)
            except Exception:
                pass

            results.append({
                'rank': r.rank,
                'user_id': r.user.id,
                'username': r.user.username,
                'rating': r.rating,
                'score': r.score,
                'solved': r.solved,
                'submissions': r.submissions,
                'country': r.country,
                'school': r.school,
                'organization': r.organization.name if r.organization else None,
                'tier': tier_info['tier'],
                'tier_color': tier_info['color'],
                'badge': tier_info['badge'],
                'is_verified': is_verified,
            })
        return {
            'page': page,
            'page_size': page_size,
            'total': total,
            'items': results
        }

    @staticmethod
    def recalculate_all_global_rankings():
        """
        Recalculates global rankings based on solved problems and ratings.
        """
        profiles = Profile.objects.select_related('user').all()
        user_stats = []

        for p in profiles:
            user = p.user
            rating_obj = UserRating.objects.filter(user=user).first()
            current_rating = rating_obj.current_rating if rating_obj else (p.rating if p.rating is not None else 0)
            contests_count = rating_obj.contests_participated if rating_obj else 0

            # Count distinct AC problems
            ac_count = Submission.objects.filter(user=p, result='AC').values('problem_id').distinct().count()
            sub_count = Submission.objects.filter(user=p).count()
            score = float(p.points or (ac_count * 100.0))

            user_stats.append({
                'user': user,
                'rating': current_rating,
                'contests_count': contests_count,
                'score': score,
                'solved': ac_count,
                'submissions': sub_count,
            })

        # Sort primarily by rating DESC, then score DESC, then solved DESC
        user_stats.sort(key=lambda x: (-x['rating'], -x['score'], -x['solved']))

        for rank_num, stat in enumerate(user_stats, 1):
            tier_info = UserRating.get_tier_info(stat['rating'], stat['contests_count'])
            GlobalRanking.objects.update_or_create(
                user=stat['user'],
                defaults={
                    'rank': rank_num,
                    'rating': stat['rating'],
                    'score': stat['score'],
                    'solved': stat['solved'],
                    'submissions': stat['submissions'],
                    'tier': tier_info['tier']
                }
            )

        return len(user_stats)
