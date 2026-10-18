from django.urls import path

from . import views

urlpatterns = [
    path('internal/validate', views.InternalValidateView.as_view()),
    path('problems/<str:code>/versions', views.VersionsView.as_view()),
    path('problems/<str:code>/versions/<uuid:version_id>', views.VersionView.as_view()),
    path('problems/<str:code>/versions/<uuid:version_id>/complete', views.CompleteView.as_view()),
    path('problems/<str:code>/versions/<uuid:version_id>/publish', views.PublishView.as_view()),
]
