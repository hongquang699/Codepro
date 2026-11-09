from django.db import models

class LoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField(db_index=True)
    username = models.CharField(max_length=150, db_index=True, blank=True, default='')
    success = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-attempted_at']
