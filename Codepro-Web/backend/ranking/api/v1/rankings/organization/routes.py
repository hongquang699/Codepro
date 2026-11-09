from django.urls import path
from .controller import OrganizationRankingController

urlpatterns = [
    path('', OrganizationRankingController.as_view(), name='org_rankings'),
    path('<int:org_id>/', OrganizationRankingController.as_view(), name='org_members_ranking'),
]