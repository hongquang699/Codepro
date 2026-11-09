from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ..services.statistics import get_user_statistics

from .profile import (
    ProfileOverviewAPIView,
    ProfileSubmissionsAPIView,
    ProfileContestsAPIView,
    ProfileProblemsAPIView,
    ProfileRatingAPIView,
    ProfileRatingHistoryAPIView,
    ProfileOrganizationsAPIView,
    ProfileAchievementsAPIView,
    ProfileActivityAPIView,
    ProfileBlogAPIView,
    ProfileSettingsAPIView,
)

class ProfileStatisticsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
        stats = get_user_statistics(user)
        return Response({'status': 'success', 'statistics': stats})


urlpatterns = [
    # Profile & Overview
    path('<str:username>', ProfileOverviewAPIView.as_view(), name='user-overview'),
    path('<str:username>/', ProfileOverviewAPIView.as_view(), name='user-overview-slash'),
    path('<str:username>/profile', ProfileOverviewAPIView.as_view(), name='user-profile'),
    path('<str:username>/profile/', ProfileOverviewAPIView.as_view(), name='user-profile-slash'),

    # Statistics
    path('<str:username>/statistics', ProfileStatisticsAPIView.as_view(), name='user-stats'),
    path('<str:username>/statistics/', ProfileStatisticsAPIView.as_view(), name='user-stats-slash'),

    # Submissions
    path('<str:username>/submissions', ProfileSubmissionsAPIView.as_view(), name='user-submissions'),
    path('<str:username>/submissions/', ProfileSubmissionsAPIView.as_view(), name='user-submissions-slash'),

    # Contests
    path('<str:username>/contests', ProfileContestsAPIView.as_view(), name='user-contests'),
    path('<str:username>/contests/', ProfileContestsAPIView.as_view(), name='user-contests-slash'),

    # Problems
    path('<str:username>/problems', ProfileProblemsAPIView.as_view(), name='user-problems'),
    path('<str:username>/problems/', ProfileProblemsAPIView.as_view(), name='user-problems-slash'),

    # Rating & History
    path('<str:username>/rating', ProfileRatingAPIView.as_view(), name='user-rating'),
    path('<str:username>/rating/', ProfileRatingAPIView.as_view(), name='user-rating-slash'),
    path('<str:username>/rating/history', ProfileRatingHistoryAPIView.as_view(), name='user-rating-history'),
    path('<str:username>/rating/history/', ProfileRatingHistoryAPIView.as_view(), name='user-rating-history-slash'),

    # Organizations
    path('<str:username>/organizations', ProfileOrganizationsAPIView.as_view(), name='user-organizations'),
    path('<str:username>/organizations/', ProfileOrganizationsAPIView.as_view(), name='user-organizations-slash'),

    # Achievements
    path('<str:username>/achievements', ProfileAchievementsAPIView.as_view(), name='user-achievements'),
    path('<str:username>/achievements/', ProfileAchievementsAPIView.as_view(), name='user-achievements-slash'),

    # Activity
    path('<str:username>/activity', ProfileActivityAPIView.as_view(), name='user-activity'),
    path('<str:username>/activity/', ProfileActivityAPIView.as_view(), name='user-activity-slash'),

    # Blog
    path('<str:username>/blog', ProfileBlogAPIView.as_view(), name='user-blog'),
    path('<str:username>/blog/', ProfileBlogAPIView.as_view(), name='user-blog-slash'),

    # Settings
    path('<str:username>/settings', ProfileSettingsAPIView.as_view(), name='user-settings'),
    path('<str:username>/settings/', ProfileSettingsAPIView.as_view(), name='user-settings-slash'),
]
