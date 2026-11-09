from django.urls import path, include

urlpatterns = [
    path('global/', include('backend.ranking.api.v1.rankings.global.routes')),
    path('contest/', include('backend.ranking.api.v1.rankings.contest.routes')),
    path('country/', include('backend.ranking.api.v1.rankings.country.routes')),
    path('school/', include('backend.ranking.api.v1.rankings.school.routes')),
    path('organization/', include('backend.ranking.api.v1.rankings.organization.routes')),
    path('users/', include('backend.ranking.api.v1.rankings.users.routes')),
    path('problems/', include('backend.ranking.api.v1.rankings.problems.routes')),
    path('rating/', include('backend.ranking.api.v1.rankings.rating.routes')),
    path('history/', include('backend.ranking.api.v1.rankings.history.routes')),
    path('statistics/', include('backend.ranking.api.v1.rankings.statistics.routes')),
    path('search/', include('backend.ranking.api.v1.rankings.search.routes')),

    # Root default: global rankings
    path('', include('backend.ranking.api.v1.rankings.global.routes')),
]