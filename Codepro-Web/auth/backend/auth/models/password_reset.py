from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    email = models.EmailField(max_length=254, blank=True, default='', db_index=True)
    token_hash = models.CharField(max_length=128, db_index=True)
    otp_hash = models.CharField(max_length=128, blank=True, default='')
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'password_resets'
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None
