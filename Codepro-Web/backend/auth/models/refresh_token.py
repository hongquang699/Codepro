from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class RefreshToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_refresh_tokens'

    def is_valid(self):
        return self.revoked_at is None and timezone.now() < self.expires_at
