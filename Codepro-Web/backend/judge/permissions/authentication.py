from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from backend.auth.services.session import validate_auth_session


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'


class JudgeCookieAuthentication(BaseAuthentication):
    """Use the existing HttpOnly cp_session cookie with CSRF on writes."""

    def authenticate(self, request):
        raw = request.COOKIES.get('cp_session')
        if not raw:
            return None
        user = validate_auth_session(raw)
        if not user:
            return None
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            SessionAuthentication().enforce_csrf(request)
        return user, None
