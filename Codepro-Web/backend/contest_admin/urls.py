from django.urls import path
from .api import views

urlpatterns = [
    # Contest Admin Portal List & Create
    path('contests', views.ContestAdminListView.as_view(), name='contest-admin-list'),
    path('contests/', views.ContestAdminListView.as_view(), name='contest-admin-list-slash'),
    
    # Specific Contest Management Endpoints
    path('contests/<str:contest_id>/dashboard', views.ContestAdminDashboardView.as_view(), name='contest-admin-dashboard'),
    path('contests/<str:contest_id>/settings', views.ContestAdminSettingsView.as_view(), name='contest-admin-settings'),
    path('contests/<str:contest_id>/freeze', views.ContestAdminFreezeScoreboardView.as_view(), name='contest-admin-freeze'),
    
    # Problems & Testcases
    path('contests/<str:contest_id>/problems', views.ContestAdminProblemsView.as_view(), name='contest-admin-problems'),
    path('contests/<str:contest_id>/problems/<str:problem_code>/statement', views.ContestAdminProblemStatementView.as_view(), name='contest-admin-statement'),
    path('contests/<str:contest_id>/problems/<str:problem_code>/testcases', views.ContestAdminProblemTestcasesView.as_view(), name='contest-admin-testcases'),
    
    # Participants
    path('contests/<str:contest_id>/participants', views.ContestAdminParticipantsView.as_view(), name='contest-admin-participants'),
    
    # Submissions & Rejudge
    path('contests/<str:contest_id>/submissions', views.ContestAdminSubmissionsView.as_view(), name='contest-admin-submissions'),
    path('contests/<str:contest_id>/submissions/<int:submission_id>', views.ContestAdminSubmissionDetailView.as_view(), name='contest-admin-sub-detail'),
    path('contests/<str:contest_id>/rejudge', views.ContestAdminRejudgeView.as_view(), name='contest-admin-rejudge'),
    
    # Ranking & Scoreboard
    path('contests/<str:contest_id>/ranking', views.ContestAdminRankingView.as_view(), name='contest-admin-ranking'),
    
    # Announcements & Clarifications
    path('contests/<str:contest_id>/announcements', views.ContestAdminAnnouncementsView.as_view(), name='contest-admin-announcements'),
    path('contests/<str:contest_id>/clarifications', views.ContestAdminClarificationsView.as_view(), name='contest-admin-clarifications'),
    
    # Jury & Workers
    path('contests/<str:contest_id>/jury', views.ContestAdminJuryView.as_view(), name='contest-admin-jury'),
    
    # Reports & Statistics
    path('contests/<str:contest_id>/reports', views.ContestAdminReportsView.as_view(), name='contest-admin-reports'),
    
    # Audit Log
    path('contests/<str:contest_id>/audit', views.ContestAdminAuditLogView.as_view(), name='contest-admin-audit'),
]
