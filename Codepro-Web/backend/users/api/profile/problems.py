from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from backend.judge.models import Submission, Problem

class ProfileProblemsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        subs = Submission.objects.filter(user__user=user)

        # Solved problems
        solved_prob_ids = subs.filter(result='AC').values_list('problem_id', flat=True).distinct()
        solved_probs = Problem.objects.filter(id__in=solved_prob_ids).values('id', 'code', 'name', 'points', 'difficulty')

        # Attempted problems (attempted but not yet AC)
        attempted_prob_ids = subs.exclude(result='AC').values_list('problem_id', flat=True).distinct()
        # Exclude solved
        attempted_unsolved_ids = set(attempted_prob_ids) - set(solved_prob_ids)
        attempted_probs = Problem.objects.filter(id__in=attempted_unsolved_ids).values('id', 'code', 'name', 'points', 'difficulty')

        return Response({
            'status': 'success',
            'solved_count': len(solved_probs),
            'attempted_count': len(attempted_probs),
            'solved': list(solved_probs),
            'attempted': list(attempted_probs)
        })
