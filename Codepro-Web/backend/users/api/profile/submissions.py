from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from backend.judge.models import Submission

class ProfileSubmissionsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        qs = Submission.objects.filter(user__user=user).select_related('problem', 'language', 'contest')

        # Filters
        verdict = request.GET.get('verdict')
        if verdict:
            qs = qs.filter(result=verdict.upper())

        language = request.GET.get('language')
        if language:
            qs = qs.filter(language__name__icontains=language)

        problem = request.GET.get('problem')
        if problem:
            qs = qs.filter(problem__code__iexact=problem)

        contest = request.GET.get('contest')
        if contest:
            qs = qs.filter(contest__key=contest)

        total_count = qs.count()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        submissions = qs.order_by('-date')[start:end]

        results = []
        for s in submissions:
            results.append({
                'id': s.id,
                'problem_code': s.problem.code if s.problem else (s.problem_code or ''),
                'problem_name': s.problem.name if s.problem else '',
                'language': s.language.name if s.language else 'Code',
                'result': s.result or s.status,
                'time_ms': s.time,
                'memory_kb': s.memory,
                'score': s.points or 0,
                'contest_id': s.contest.key if s.contest else None,
                'contest_name': s.contest.name if s.contest else None,
                'date': s.date.strftime('%H:%M %d/%m/%Y') if s.date else ''
            })

        return Response({
            'status': 'success',
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'results': results
        })
