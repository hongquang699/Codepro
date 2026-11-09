"""ASGI WebSocket routes."""

from django.urls import re_path

from websocket.submission.consumer import SubmissionConsumer

websocket_urlpatterns = [
    re_path(r"^ws/submissions/(?P<submission_id>[1-9][0-9]*)/$", SubmissionConsumer.as_asgi()),
]
