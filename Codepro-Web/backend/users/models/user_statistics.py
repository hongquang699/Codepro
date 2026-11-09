from django.db import models
from django.contrib.auth.models import User

class UserStatistics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_statistics')
    total_submissions = models.IntegerField(default=0)
    accepted_submissions = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    compilation_errors = models.IntegerField(default=0)
    runtime_errors = models.IntegerField(default=0)
    time_limit_exceeded = models.IntegerField(default=0)
    memory_limit_exceeded = models.IntegerField(default=0)
    solved_problems = models.IntegerField(default=0)
    attempted_problems = models.IntegerField(default=0)
    contests = models.IntegerField(default=0)
    contest_wins = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_statistics'

    def __str__(self):
        return f"{self.user.username} Stats ({self.solved_problems} solved)"
