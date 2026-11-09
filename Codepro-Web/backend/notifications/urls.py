from django.urls import URLPattern, path
from .views import NotificationsListView

urlpatterns: list[URLPattern] = [
    path('', NotificationsListView.as_view(), name='notifications-list'),
]
