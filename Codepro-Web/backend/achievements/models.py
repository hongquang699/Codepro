from django.db import models
from django.contrib.auth.models import User

class Achievement(models.Model):
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, default='🏆')
    points = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.icon} {self.title}"

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.title}"
