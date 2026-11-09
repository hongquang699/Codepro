from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ...models import UserProfile

class ProfileOrganizationsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        orgs = []
        # From UserProfile
        prof = UserProfile.objects.filter(user=user).first()
        if prof and prof.organization:
            orgs.append({
                'id': 'org-primary',
                'name': prof.organization,
                'role': 'Thành viên chính thức',
                'type': 'organization'
            })
        if prof and prof.school:
            orgs.append({
                'id': 'school-primary',
                'name': prof.school,
                'role': 'Học sinh / Sinh viên',
                'type': 'school'
            })

        # From judge.models.Profile organizations
        try:
            from backend.judge.models import Profile as JudgeProfile
            jp = JudgeProfile.objects.filter(user=user).first()
            if jp:
                for o in jp.organizations.all():
                    if not any(item['name'] == o.name for item in orgs):
                        orgs.append({
                            'id': o.id,
                            'name': o.name,
                            'role': 'Thành viên',
                            'type': 'organization'
                        })
        except Exception:
            pass

        # If none, provide default community membership
        if not orgs:
            orgs.append({
                'id': 'codepro-org',
                'name': 'Cộng đồng Lập trình CodeProOJ',
                'role': 'Coder',
                'type': 'community'
            })

        return Response({
            'status': 'success',
            'total': len(orgs),
            'results': orgs
        })
