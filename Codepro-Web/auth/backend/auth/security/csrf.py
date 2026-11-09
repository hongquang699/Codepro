from django.middleware.csrf import get_token


def ensure_csrf_cookie(request):
    """Ensure CSRF cookie is set on the request."""
    return get_token(request)
