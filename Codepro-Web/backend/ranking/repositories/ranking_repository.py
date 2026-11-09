from django.db.models import Q
from ..models.ranking import GlobalRanking

class RankingRepository:
    @staticmethod
    def get_global_rankings(page=1, page_size=50, country=None, school=None, org_id=None, search=None):
        qs = GlobalRanking.objects.select_related('user', 'organization').all()
        
        if country:
            qs = qs.filter(country__iexact=country)
        if school:
            qs = qs.filter(school__icontains=school)
        if org_id:
            qs = qs.filter(organization_id=org_id)
        if search:
            qs = qs.filter(Q(user__username__icontains=search) | Q(school__icontains=search))
            
        total_count = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = list(qs.order_by('rank')[start:end])
        return items, total_count

    @staticmethod
    def get_by_user(user):
        return GlobalRanking.objects.filter(user=user).first()

    @staticmethod
    def upsert_ranking(user, rank=1, rating=1500, score=0.0, solved=0, submissions=0, country='Vietnam', school='', org=None, tier='Specialist'):
        ranking_obj, _ = GlobalRanking.objects.update_or_create(
            user=user,
            defaults={
                'rank': rank,
                'rating': rating,
                'score': score,
                'solved': solved,
                'submissions': submissions,
                'country': country,
                'school': school,
                'organization': org,
                'tier': tier,
            }
        )
        return ranking_obj
