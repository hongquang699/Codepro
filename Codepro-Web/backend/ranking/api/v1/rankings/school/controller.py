from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg
from backend.ranking.models.ranking import GlobalRanking

class SchoolRankingController(APIView):
    def get(self, request, school_name=None):
        if school_name:
            qs = GlobalRanking.objects.filter(school__icontains=school_name).order_by('rank')[:100]
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
            return Response({'school': school_name, 'students': items}, status=status.HTTP_200_OK)

        stats = GlobalRanking.objects.exclude(school='').values('school').annotate(
            students_count=Count('id'),
            total_solved=Sum('solved'),
            avg_rating=Avg('rating')
        ).order_by('-avg_rating')

        results = []
        for s in stats:
            school = s['school']
            top = GlobalRanking.objects.filter(school=school).order_by('rank').first()
            results.append({
                'school': school,
                'students_count': s['students_count'],
                'total_solved': s['total_solved'] or 0,
                'avg_rating': round(s['avg_rating'] or 1500.0, 1),
                'top_student': top.user.username if top else None
            })

        return Response({'schools': results}, status=status.HTTP_200_OK)