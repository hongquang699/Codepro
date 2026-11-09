from django.db import models
from django.contrib.auth.models import User

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    badge_key = models.CharField(max_length=60)  # first-ac, 100-solved, 500-solved, contest-participant, contest-winner, streak, problem-setter
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, default='🏆')
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = ('user', 'badge_key')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"
