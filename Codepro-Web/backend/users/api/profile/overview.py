from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ...services.profile import get_profile_data, update_profile
from ...services.statistics import get_user_statistics
from ...services.rating import get_user_rating
from backend.judge.models import Submission

class ProfileOverviewAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        profile_data = get_profile_data(username)
        stats = get_user_statistics(user)
        rating_info = get_user_rating(user)

        # Recent 5 submissions
        recent_subs = Submission.objects.filter(user__user=user).select_related('problem', 'language').order_by('-date')[:5]
        subs_list = []
        for s in recent_subs:
            subs_list.append({
                'id': s.id,
                'problem_code': s.problem.code if s.problem else (s.problem_code or ''),
                'problem_name': s.problem.name if s.problem else '',
                'language': s.language.name if s.language else 'Code',
                'result': s.result or s.status,
                'time_ms': s.time,
                'memory_kb': s.memory,
                'score': s.points or 0,
                'date': s.date.strftime('%H:%M %d/%m/%Y') if s.date else ''
            })

        return Response({
            'status': 'success',
            'profile': profile_data,
            'statistics': stats,
            'rating': rating_info,
            'recent_submissions': subs_list
        })

    def patch(self, request, username):
        # Verification: check bearer token
        token_key = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
        elif auth_header.startswith('Bearer '):
            token_key = auth_header.split(' ')[1]

        target_user = User.objects.filter(username=username).first()
        if not target_user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        # Check authorization
        authorized = False
        if token_key:
            from rest_framework.exceptions import AuthenticationFailed
            from backend.auth.security.token_auth import ExpiringTokenAuthentication
            try:  # same checks as the API (expiry, inactive user), not a raw key lookup
                token_user, _ = ExpiringTokenAuthentication().authenticate_credentials(token_key)
            except AuthenticationFailed:
                token_user = None
            if token_user and (token_user == target_user or token_user.is_superuser or (
                    token_user.is_staff and not (target_user.is_staff or target_user.is_superuser))):
                authorized = True

        if not authorized:
            return Response({'error': 'Bạn không có quyền chỉnh sửa hồ sơ này'}, status=status.HTTP_403_FORBIDDEN)

        updated_prof = update_profile(target_user, request.data)
        return Response({
            'status': 'success',
            'message': 'Cập nhật hồ sơ thành công',
            'profile': get_profile_data(username)
        })
