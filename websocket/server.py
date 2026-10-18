"""ASGI entry point for the WebSocket service.

Run with ``uvicorn websocket.server:application --port 8000``. The HTTP and
WebSocket routes share the Django ASGI application and its channel layer.
"""

from backend.core.asgi import application
