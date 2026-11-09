from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from backend.judge.models import ContestParticipation, Contest
from ...models import RatingHistory

class ProfileContestsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        participations = ContestParticipation.objects.filter(user__user=user).select_related('contest').order_by('-id')

        results = []
        for p in participations:
            c = p.contest
            # Rating change lookup
            rh = RatingHistory.objects.filter(user=user, contest_id=c.key).first()
            change = rh.change if rh else 0
            rank = rh.rank if rh else None

            results.append({
                'contest_id': c.key,
                'contest_name': c.name,
                'rank': rank or '—',
                'score': p.score,
                'rating_change': f"{change:+d}" if change != 0 else "0",
                'start_time': c.start_time.strftime('%H:%M %d/%m/%Y') if c.start_time else '',
                'end_time': c.end_time.strftime('%H:%M %d/%m/%Y') if c.end_time else '',
                'is_rated': getattr(c, 'is_rated', True)
            })

        return Response({
            'status': 'success',
            'total': len(results),
            'results': results
        })
