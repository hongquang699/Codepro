from django.urls import path
from .views import (
    ContestListAPIView, ContestDetailAPIView, ContestRegisterAPIView, ContestLeaveAPIView,
    ContestDashboardAPIView, ContestProblemsListAPIView,
    ContestProblemDetailAPIView, ContestProblemSubmitAPIView,
    ContestSubmissionsListAPIView, ContestRankingAPIView,
    ContestAnnouncementsAPIView, ContestClarificationsAPIView,
    SubmissionUnifiedDetailAPIView, SubmissionStatusPollAPIView
)

urlpatterns = [
    # Contest List
    path('', ContestListAPIView.as_view(), name='contest-list'),

    # Contest Core
    path('<str:contest_id>/', ContestDetailAPIView.as_view(), name='contest-detail'),
    path('<str:contest_id>/register', ContestRegisterAPIView.as_view(), name='contest-register'),
    path('<str:contest_id>/leave', ContestLeaveAPIView.as_view(), name='contest-leave'),
    path('<str:contest_id>/dashboard', ContestDashboardAPIView.as_view(), name='contest-dashboard'),

    # Problems in Contest
    path('<str:contest_id>/problems', ContestProblemsListAPIView.as_view(), name='contest-problems'),
    path('<str:contest_id>/problems/<str:problem_id>', ContestProblemDetailAPIView.as_view(), name='contest-problem-detail'),
    path('<str:contest_id>/problems/<str:problem_id>/submit', ContestProblemSubmitAPIView.as_view(), name='contest-problem-submit'),

    # Submissions in Contest
    path('<str:contest_id>/submissions', ContestSubmissionsListAPIView.as_view(), name='contest-submissions'),

    # Scoreboard / Ranking
    path('<str:contest_id>/ranking', ContestRankingAPIView.as_view(), name='contest-ranking'),

    # Notices & Clarifications
    path('<str:contest_id>/announcements', ContestAnnouncementsAPIView.as_view(), name='contest-announcements'),
    path('<str:contest_id>/clarifications', ContestClarificationsAPIView.as_view(), name='contest-clarifications'),
]
