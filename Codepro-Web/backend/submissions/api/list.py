from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from backend.judge.models import Submission
from ..models.submission_result import SubmissionResult

class SubmissionListAPIView(APIView):
    def get(self, request, username=None, problem_id=None, contest_id=None):
        qs = Submission.objects.select_related('problem', 'user__user', 'language', 'contest').order_by('-date')

        # URL path parameters
        if username:
            qs = qs.filter(user__user__username__iexact=username)
        if problem_id:
            if str(problem_id).isdigit():
                qs = qs.filter(Q(problem_id=int(problem_id)) | Q(problem__code__iexact=str(problem_id)))
            else:
                qs = qs.filter(problem__code__iexact=str(problem_id))
        if contest_id:
            if str(contest_id).isdigit():
                qs = qs.filter(Q(contest_id=int(contest_id)) | Q(contest__key__iexact=str(contest_id)))
            else:
                qs = qs.filter(contest__key__iexact=str(contest_id))

        # Query parameters filters
        user_param = request.GET.get('user')
        if user_param:
            qs = qs.filter(user__user__username__icontains=user_param)

        problem_param = request.GET.get('problem')
        if problem_param:
            qs = qs.filter(problem__code__icontains=problem_param)

        lang_param = request.GET.get('language')
        if lang_param:
            qs = qs.filter(language__key__iexact=lang_param)

        verdict_param = request.GET.get('verdict')
        if verdict_param:
            qs = qs.filter(result__iexact=verdict_param)

        # Pagination
        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(100, max(1, int(request.GET.get('page_size', 20))))
        except ValueError:
            page, page_size = 1, 20

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for s in qs[start:end]:
            verdict_code = s.result or ('QUEUED' if s.status in ('QU', 'P', 'G') else 'PENDING')
            items.append({
                'id': s.id,
                'user': s.user.user.username,
                'problem': s.problem.code,
                'problem_name': s.problem.name,
                'language': s.language.name,
                'language_key': s.language.key,
                'score': s.points or 0.0,
                'verdict': verdict_code,
                'verdict_name': SubmissionResult.get_verdict_name(verdict_code),
                'status': s.status,
                'execution_time': round((s.time or 0.0) * 1000, 1), # ms
                'memory_used': round((s.memory or 0.0) / 1024, 2), # MB
                'date': s.date.strftime('%Y-%m-%d %H:%M:%S'),
                'contest': s.contest.key if s.contest else None
            })

        return Response({
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'items': items
        }, status=status.HTTP_200_OK)
