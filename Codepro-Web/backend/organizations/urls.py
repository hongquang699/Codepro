from django.urls import path
from .views import (
    OrganizationListCreateAPIView,
    OrganizationDetailAPIView,
    OrganizationJoinAPIView,
    OrganizationLeaveAPIView,
    OrganizationMembersAPIView,
    OrganizationMemberDetailAPIView,
    OrganizationContestsAPIView,
    OrganizationProblemsAPIView,
    OrganizationRankingAPIView,
    OrganizationBlogAPIView,
    OrganizationBlogDetailAPIView,
    OrganizationAnnouncementsAPIView,
    OrganizationActivityAPIView,
    OrganizationAdminStatsAPIView,
    OrganizationAdminRolesAPIView,
    OrganizationAdminInvitationsAPIView,
    OrganizationAdminAuditLogAPIView
)

urlpatterns = [
    path('', OrganizationListCreateAPIView.as_view(), name='org-list-create'),
    path('<slug:slug>/', OrganizationDetailAPIView.as_view(), name='org-detail'),
    path('<slug:slug>/join/', OrganizationJoinAPIView.as_view(), name='org-join'),
    path('<slug:slug>/leave/', OrganizationLeaveAPIView.as_view(), name='org-leave'),
    path('<slug:slug>/members/', OrganizationMembersAPIView.as_view(), name='org-members'),
    path('<slug:slug>/members/<str:username>/', OrganizationMemberDetailAPIView.as_view(), name='org-member-detail'),
    path('<slug:slug>/contests/', OrganizationContestsAPIView.as_view(), name='org-contests'),
    path('<slug:slug>/problems/', OrganizationProblemsAPIView.as_view(), name='org-problems'),
    path('<slug:slug>/ranking/', OrganizationRankingAPIView.as_view(), name='org-ranking'),
    path('<slug:slug>/blog/', OrganizationBlogAPIView.as_view(), name='org-blog'),
    path('<slug:slug>/blog/<int:post_id>/', OrganizationBlogDetailAPIView.as_view(), name='org-blog-detail'),
    path('<slug:slug>/announcements/', OrganizationAnnouncementsAPIView.as_view(), name='org-announcements'),
    path('<slug:slug>/activity/', OrganizationActivityAPIView.as_view(), name='org-activity'),
    
    # Admin endpoints
    path('<slug:slug>/admin/stats/', OrganizationAdminStatsAPIView.as_view(), name='org-admin-stats'),
    path('<slug:slug>/admin/roles/', OrganizationAdminRolesAPIView.as_view(), name='org-admin-roles'),
    path('<slug:slug>/admin/invitations/', OrganizationAdminInvitationsAPIView.as_view(), name='org-admin-invitations'),
    path('<slug:slug>/admin/audit-log/', OrganizationAdminAuditLogAPIView.as_view(), name='org-admin-audit-log'),
]
