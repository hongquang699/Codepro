"""Time limited DRF tokens for the legacy Authorization header clients."""

from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


TOKEN_MAX_AGE = timedelta(days=30)


def token_is_expired(token):
    return token.created <= timezone.now() - TOKEN_MAX_AGE


def get_or_rotate_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    if token_is_expired(token):
        token.delete()
        token = Token.objects.create(user=user)
    return token


class ExpiringTokenAuthentication(DRFTokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if token_is_expired(token):
            raise AuthenticationFailed('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        return user, token
