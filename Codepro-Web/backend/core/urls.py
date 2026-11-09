import os
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic.base import RedirectView
from django.views.static import serve
from django.conf import settings
from backend.judge.api.admin_page import judge_admin_page

urlpatterns = [
    path('api/v1/problem-storage/', include('backend.problem_storage.urls')),
    path('api/v1/admin/contests/<str:contest_id>/anti-cheat/', include('backend.anti_cheat.api.urls')),
    path('api/v1/anti-cheat/', include('backend.anti_cheat.api.personal_urls')),
    path('internal/judge-admin-page', judge_admin_page),
    path('api/v1/admin/judge/', include('backend.judge.api.admin_urls')),
    # Root redirects directly to /admin/
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    
    # Django Native Admin
    path('admin/', admin.site.urls),
    path('accounts/profile/', RedirectView.as_view(url='/admin/', permanent=False)),
    
    # Authentication Platform API v1
    path('api/v1/auth/', include('backend.auth.urls')),
    path('api/auth/', include('backend.auth.urls')),

    # CodeProOJ Community Platform API
    path('api/v1/community/', include('backend.community.api.urls')),
    path('api/v2/community/', include('backend.community.api.urls')),

    # CodeProOJ / Codeforces Ranking API
    path('api/v1/rankings/', include('backend.ranking.api.urls')),
    path('api/rankings/', include('backend.ranking.api.urls')),

    # Submissions Subsystem API v1
    path('api/v1/submissions/', include('backend.submissions.api.urls')),
    path('api/submissions/', include('backend.submissions.api.urls')),

    # Contests Subsystem API v1
    path('api/v1/contests/', include('backend.api.v1.contests.urls')),
    path('api/contests/', include('backend.api.v1.contests.urls')),

    # User Profile Subsystem API v1
    path('api/v1/users/', include('backend.users.api.urls')),
    path('api/users/', include('backend.users.api.urls')),

    # Organizations Module API v1
    path('api/v1/organizations/', include('backend.organizations.urls')),
    path('api/organizations/', include('backend.organizations.urls')),

    # Contest Administration Subsystem API
    path('api/v1/contest-admin/', include('backend.contest_admin.urls')),
    path('api/contest-admin/', include('backend.contest_admin.urls')),

    # CodeProOJ / DMOJ API v2
    path('api/v2/', include('backend.api.v2.urls')),
    # CodeProOJ Problem Authoring API v1
    path('api/v1/', include('backend.api.v1.urls')),
    path('api/', include('backend.api.v2.urls')),
    
    # Allow serving frontend pages directly through port 8000 as well
    re_path(r'^frontend/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.BASE_DIR, 'frontend')}),
]
