from django.db import models
from django.contrib.auth.models import User

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_settings')
    # Preferences
    language = models.CharField(max_length=30, default='vi')
    theme = models.CharField(max_length=30, default='dark')
    editor_theme = models.CharField(max_length=50, default='vs-dark')
    editor_keymap = models.CharField(max_length=30, default='standard')
    tab_size = models.IntegerField(default=4)
    default_code_language = models.CharField(max_length=30, default='CPP17')
    timezone = models.CharField(max_length=60, default='Asia/Ho_Chi_Minh')
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    contest_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    # Privacy
    privacy_profile = models.CharField(max_length=20, default='public')  # public, friends, private
    privacy_submissions = models.CharField(max_length=20, default='public')
    privacy_activity = models.CharField(max_length=20, default='public')

    # Security
    two_factor_enabled = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_settings'

    def __str__(self):
        return f"{self.user.username} Settings"
