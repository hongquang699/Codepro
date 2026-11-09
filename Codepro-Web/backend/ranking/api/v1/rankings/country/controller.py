from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg
from backend.ranking.models.ranking import GlobalRanking

class CountryRankingController(APIView):
    def get(self, request, country_name=None):
        if country_name:
            # Users in specific country
            qs = GlobalRanking.objects.filter(country__iexact=country_name).order_by('rank')[:100]
            items = []
            for r in qs:
                items.append({
                    'rank': r.rank,
                    'username': r.user.username,
                    'rating': r.rating,
                    'solved': r.solved,
                    'tier': r.tier,
                    'school': r.school
                })
            return Response({'country': country_name, 'users': items}, status=status.HTTP_200_OK)

        # Aggregated stats per country
        stats = GlobalRanking.objects.values('country').annotate(
            users_count=Count('id'),
            total_solved=Sum('solved'),
            avg_rating=Avg('rating')
        ).order_by('-avg_rating')

        results = []
        for s in stats:
            country = s['country'] or 'Unknown'
            top = GlobalRanking.objects.filter(country=country).order_by('rank').first()
            results.append({
                'country': country,
                'users_count': s['users_count'],
                'total_solved': s['total_solved'] or 0,
                'avg_rating': round(s['avg_rating'] or 1500.0, 1),
                'top_user': top.user.username if top else None
            })

        return Response({'countries': results}, status=status.HTTP_200_OK)