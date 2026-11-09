from django.urls import path
from . import views

urlpatterns = [
    # ── Feed ──
    path('feed', views.FeedView.as_view(), name='community-feed'),

    # ── Posts ──
    path('posts', views.PostListView.as_view(), name='community-posts-list'),
    path('posts/<int:pk>', views.PostDetailView.as_view(), name='community-posts-detail'),
    path('posts/<int:pk>/pin', views.PostPinView.as_view(), name='community-posts-pin'),
    path('posts/<int:pk>/comments', views.PostCommentsView.as_view(), name='community-posts-comments'),

    # ── Reactions ──
    path('reactions', views.ReactionView.as_view(), name='community-reactions'),

    # ── Forum ──
    path('forum/categories', views.ForumCategoriesView.as_view(), name='community-forum-categories'),
    path('forum/categories/<str:slug>/threads', views.ForumCategoryThreadsView.as_view(), name='community-forum-category-threads'),
    path('forum/threads', views.ForumThreadListView.as_view(), name='community-forum-threads-list'),
    path('forum/threads/<int:pk>', views.ForumThreadDetailView.as_view(), name='community-forum-thread-detail'),
    path('forum/threads/<int:pk>/reply', views.ForumThreadReplyView.as_view(), name='community-forum-thread-reply'),
    path('forum/threads/<int:pk>/lock', views.ForumThreadLockView.as_view(), name='community-forum-thread-lock'),
    path('forum/threads/<int:pk>/pin', views.ForumThreadPinView.as_view(), name='community-forum-thread-pin'),

    # ── Groups ──
    path('groups', views.GroupListView.as_view(), name='community-groups-list'),
    path('groups/<int:pk>/join', views.GroupJoinView.as_view(), name='community-groups-join'),
    path('groups/<int:pk>/leave', views.GroupLeaveView.as_view(), name='community-groups-leave'),

    # ── Direct Messages ──
    path('messages/conversations', views.ConversationsView.as_view(), name='community-conversations'),
    path('messages/start', views.StartConversationView.as_view(), name='community-messages-start'),
    path('messages/<int:conversation_id>', views.MessagesView.as_view(), name='community-messages'),

    # ── Notifications ──
    path('notifications', views.NotificationsView.as_view(), name='community-notifications-list'),
    path('notifications/<int:pk>/read', views.NotificationReadView.as_view(), name='community-notification-read'),
    path('notifications/read-all', views.NotificationReadAllView.as_view(), name='community-notifications-read-all'),

    # ── Search ──
    path('search', views.SearchView.as_view(), name='community-search'),

    # ── Reports & Moderation ──
    path('reports', views.ReportsView.as_view(), name='community-reports'),
    path('moderation/action', views.ModerationActionView.as_view(), name='community-moderation-action'),

    # ── Users & Social ──
    path('users/<str:username>/profile', views.UserCommunityProfileView.as_view(), name='community-user-profile'),
    path('users/<str:username>/follow', views.UserFollowView.as_view(), name='community-user-follow'),
]
