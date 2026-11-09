from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    display_name = models.CharField(max_length=120, blank=True, default='')
    avatar = models.CharField(max_length=300, blank=True, default='')
    cover = models.CharField(max_length=300, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='Vietnam')
    school = models.CharField(max_length=180, blank=True, default='')
    organization = models.CharField(max_length=180, blank=True, default='')
    website = models.URLField(max_length=255, blank=True, default='')
    github = models.CharField(max_length=120, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} Profile"
