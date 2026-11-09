from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg
from backend.judge.models import Organization
from backend.ranking.models.ranking import GlobalRanking

class OrganizationRankingController(APIView):
    def get(self, request, org_id=None):
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if not org:
                return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
            qs = GlobalRanking.objects.filter(organization=org).order_by('rank')[:100]
            members = []
            for r in qs:
                members.append({
                    'rank': r.rank,
                    'username': r.user.username,
                    'rating': r.rating,
                    'solved': r.solved,
                    'tier': r.tier
                })
            return Response({'organization': {'id': org.id, 'name': org.name}, 'members': members}, status=status.HTTP_200_OK)

        orgs = Organization.objects.all()
        results = []
        for org in orgs:
            ranks = GlobalRanking.objects.filter(organization=org)
            cnt = ranks.count()
            total_solved = sum(r.solved for r in ranks)
            avg_rating = (sum(r.rating for r in ranks) / cnt) if cnt > 0 else 1500.0
            top = ranks.order_by('rank').first()
            results.append({
                'id': org.id,
                'name': org.name,
                'short_name': org.short_name,
                'members_count': cnt,
                'total_solved': total_solved,
                'avg_rating': round(avg_rating, 1),
                'top_member': top.user.username if top else None
            })

        results.sort(key=lambda x: -x['avg_rating'])
        return Response({'organizations': results}, status=status.HTTP_200_OK)