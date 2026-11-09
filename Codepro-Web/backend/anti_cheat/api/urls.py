from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.DashboardView.as_view()),
    path('settings', views.SettingsView.as_view()),
    path('scans', views.ScansView.as_view()),
    path('scans/<int:scan_id>', views.ScanDetailView.as_view()),
    path('scans/<int:scan_id>/retry', views.RetryScanView.as_view()),
    path('similarities', views.SimilaritiesView.as_view()),
    path('groups', views.GroupsView.as_view()),
    path('cases', views.CasesView.as_view()),
    path('cases/<int:case_id>', views.CaseDetailView.as_view()),
    path('cases/<int:case_id>/evidence', views.EvidenceView.as_view()),
    path('cases/<int:case_id>/confirm', views.CaseDecisionView.as_view(action='confirm')),
    path('cases/<int:case_id>/dismiss', views.CaseDecisionView.as_view(action='dismiss')),
    path('cases/<int:case_id>/penalties', views.PenaltiesView.as_view()),
    path('penalties', views.PenaltiesView.as_view()),
    path('appeals', views.AppealsView.as_view()),
    path('appeals/<int:appeal_id>/resolve', views.ResolveAppealView.as_view()),
    path('audit', views.AuditView.as_view()),
]
