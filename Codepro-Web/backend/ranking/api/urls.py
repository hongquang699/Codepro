from django.urls import path, include

urlpatterns = [
    path('', include('backend.ranking.api.v1.rankings.urls')),
]
