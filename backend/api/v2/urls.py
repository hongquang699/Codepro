from django.urls import path
from . import views
from .contest_archive import ContestArchiveDownload
from backend.judge.api import admin_views as judge_admin

urlpatterns = [
    path('admin/contest/<str:contest>/archive', ContestArchiveDownload.as_view(), name='api-contest-archive'),
    path('code-shares', views.APICodeShareList.as_view(), name='api-code-shares'),
    path('code-share/<str:token>', views.APICodeShareDetail.as_view(), name='api-code-share'),
    # ── USERS & RANKINGS ────────────────────────────────────────────────────
    path('users', views.APIUserList.as_view(), name='api-users'),
    path('user/<str:username>', views.APIUserDetail.as_view(), name='api-user-detail'),
    path('user/profile', views.APIUserDetail.as_view(), name='api-user-profile-update'),
    path('rankings', views.APIRankings.as_view(), name='api-rankings'),
    path('rating-history/<str:username>', views.APIUserRatingHistory.as_view(), name='api-rating-history'),

    # ── PROBLEMS ────────────────────────────────────────────────────────────
    path('problems', views.APIProblemList.as_view(), name='api-problems'),
    path('problem/<str:problem>', views.APIProblemDetail.as_view(), name='api-problem-detail'),
    path('problem/<str:problem>/statement', views.APIProblemStatement.as_view(), name='api-problem-statement'),
    path('problem/<str:problem>/testcases', views.APIProblemTestcases.as_view(), name='api-problem-testcases'),
    path('problem/<str:problem>/testcases/upload', views.APIProblemTestcasesUpload.as_view(), name='api-problem-testcases-upload'),
    path('problem/<str:problem>/publish', views.APIProblemPublish.as_view(), name='api-problem-publish'),
    path('problem/<str:problem>/clarifications', views.APIClarifications.as_view(), name='api-problem-clarifications'),

    # ── CONTESTS ────────────────────────────────────────────────────────────
    path('contests', views.APIContestList.as_view(), name='api-contests'),
    path('contest/<str:contest>', views.APIContestDetail.as_view(), name='api-contest-detail'),
    path('contest/<str:contest>/join', views.APIContestJoin.as_view(), name='api-contest-join'),
    path('contest/<str:contest>/leave', views.APIContestLeave.as_view(), name='api-contest-leave'),
    path('contest/<str:contest>/scoreboard', views.APIContestScoreboard.as_view(), name='api-contest-scoreboard'),
    path('scoreboard/<str:contest>', views.APIContestScoreboard.as_view(), name='api-scoreboard-alias'),
    path('contest/<str:contest>/clarifications', views.APIClarifications.as_view(), name='api-contest-clarifications'),

    # ── SUBMISSIONS & REJUDGE ───────────────────────────────────────────────
    path('submissions', views.APISubmissionList.as_view(), name='api-submissions'),
    path('submission/<int:submission_id>', views.APISubmissionDetail.as_view(), name='api-submission-detail'),
    path('submit', views.APISubmitView.as_view(), name='api-submit'),
    path('submission/submit', views.APISubmitView.as_view(), name='api-submission-submit'),
    path('rejudge/<int:submission_id>', judge_admin.RejudgeView.as_view(), name='api-rejudge'),
    path('rejudge/problem/<str:problem>', views.APIRejudgeProblemView.as_view(), name='api-rejudge-problem'),

    # ── CLARIFICATIONS ──────────────────────────────────────────────────────
    path('clarifications', views.APIClarifications.as_view(), name='api-clarifications'),
    path('clarification/<int:clarification_id>/answer', views.APIClarificationAnswer.as_view(), name='api-clarification-answer'),

    # ── BLOGS & COMMENTS ────────────────────────────────────────────────────
    path('blogs', views.APIBlogList.as_view(), name='api-blogs'),
    path('blog/<str:slug>', views.APIBlogDetail.as_view(), name='api-blog-detail'),
    path('comments', views.APICommentList.as_view(), name='api-comments'),

    # ── LANGUAGES & JUDGE SERVERS ───────────────────────────────────────────
    path('languages', views.APILanguageList.as_view(), name='api-languages'),
    path('language/<str:key>', views.APILanguageDetail.as_view(), name='api-language-detail'),
    path('judges', views.APIJudgeList.as_view(), name='api-judges'),
    path('judge/heartbeat', views.APIJudgeHeartbeat.as_view(), name='api-judge-heartbeat'),
    path('judge/<str:name>', views.APIJudgeDetail.as_view(), name='api-judge-detail'),

    # ── ORGANIZATIONS ───────────────────────────────────────────────────────
    path('organizations', views.APIOrganizationList.as_view(), name='api-organizations'),
    path('organization/<str:slug>', views.APIOrganizationDetail.as_view(), name='api-organization-detail'),

    # ── AUTHENTICATION & ADMIN SECURITY ───────────────────────────────────────
    path('auth/login', views.APILoginView.as_view(), name='api-auth-login'),
    path('auth/register', views.APIRegisterView.as_view(), name='api-auth-register'),
    path('auth/logout', views.APILogoutView.as_view(), name='api-auth-logout'),
    path('auth/profile', views.APIAuthProfileView.as_view(), name='api-auth-profile'),
    path('auth/admin-check', views.APIAdminCheckView.as_view(), name='api-auth-admin-check'),
    path('admin/overview', views.APIAdminOverviewView.as_view(), name='api-admin-overview'),
    path('admin/judge-workers', judge_admin.WorkersView.as_view(), name='api-admin-judge-workers'),
    path('admin/users/<str:username>/role', views.APIAdminUserRoleView.as_view(), name='api-admin-user-role'),
    path('admin/system', views.APIAdminSystemView.as_view(), name='api-admin-system'),
    path('admin/system/metrics', views.APIAdminSystemMetricsView.as_view(), name='api-admin-system-metrics'),
    path('admin/contest/<str:contest>/manage', views.APIAdminContestManageDetailView.as_view(), name='api-admin-contest-manage'),
    path('admin/judge/queue', judge_admin.QueueView.as_view(), name='api-admin-judge-queue'),
    path('admin/judge/logs', judge_admin.LogsView.as_view(), name='api-admin-judge-logs'),
    path('admin/rejudge/batch', views.APIAdminBatchRejudgeView.as_view(), name='api-admin-rejudge-batch'),
    path('search', views.APISearchUnifiedView.as_view(), name='api-search-unified'),
    path('rejudge/contest/<str:contest>', views.APIRejudgeContestView.as_view(), name='api-rejudge-contest'),
]
