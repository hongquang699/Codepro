from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AuthSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_sessions')
    session_token_hash = models.CharField(max_length=128, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    device_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'auth_sessions'
        ordering = ['-last_seen_at']

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Session {self.user.username} ({self.ip_address})"
