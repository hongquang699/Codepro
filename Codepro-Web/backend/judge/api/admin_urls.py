from django.urls import path
from . import admin_views as v

urlpatterns = [
    path('access', v.AccessView.as_view()),
    path('dashboard', v.DashboardView.as_view()),
    path('workers', v.WorkersView.as_view()),
    path('workers/<str:worker_id>', v.WorkerView.as_view()),
    path('workers/<str:worker_id>/<str:action>', v.WorkerActionView.as_view()),
    path('queue', v.QueueView.as_view()),
    path('queue/<str:action>', v.QueueActionView.as_view()),
    path('queue/<str:job_id>/<str:action>', v.JobActionView.as_view()),
    path('submissions', v.SubmissionsView.as_view()),
    path('submissions/<int:submission_id>', v.SubmissionView.as_view()),
    path('submissions/<int:submission_id>/rejudge', v.RejudgeView.as_view()),
    path('languages', v.LanguagesView.as_view()),
    path('languages/<int:language_id>', v.LanguageView.as_view()),
    path('monitoring', v.MonitoringView.as_view()),
    path('logs', v.LogsView.as_view()),
    path('health', v.HealthView.as_view()),
    path('test/run', v.TestRunView.as_view()),
    path('limits', v.LimitsView.as_view()),
]
