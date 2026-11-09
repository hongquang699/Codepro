from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class EmailVerification(models.Model):
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='email_verifications')
    username = models.CharField(max_length=150, blank=True, default='')
    password_hash = models.CharField(max_length=256, blank=True, default='')
    otp_hash = models.CharField(max_length=128)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_locked(self):
        return self.attempts >= 5

    @property
    def is_used(self):
        return self.verified_at is not None

    def __str__(self):
        return f"OTP for {self.email} (expires: {self.expires_at})"
