from django.middleware.csrf import get_token
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
from functools import wraps


def ensure_csrf_cookie(request):
    """Ensure CSRF cookie is set on the request."""
    return get_token(request)


def csrf_protect_cookie_auth(view_func):
    """Require Django CSRF validation when a v1 auth action uses browser cookies.

    Bearer-only clients have no ambient browser credential and can keep using
    these endpoints without obtaining a CSRF cookie.
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        has_cookie_auth = bool(request.COOKIES.get('cp_session'))
        has_django_session = bool(request.COOKIES.get(settings.SESSION_COOKIE_NAME))
        if has_cookie_auth or has_django_session:
            check = CsrfViewMiddleware(lambda _request: None)
            rejection = check.process_view(request, view_func, args, kwargs)
            if rejection is not None:
                return rejection
        return view_func(request, *args, **kwargs)

    return wrapped
