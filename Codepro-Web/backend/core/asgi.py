import os
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from websocket.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')

http_application = get_asgi_application()
if settings.DEBUG:
    http_application = ASGIStaticFilesHandler(http_application)

application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns)),
})
