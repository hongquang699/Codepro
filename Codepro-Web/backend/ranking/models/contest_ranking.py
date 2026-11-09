from django.db import models
from django.contrib.auth.models import User

class ContestRanking(models.Model):
    contest = models.ForeignKey('judge.Contest', on_delete=models.CASCADE, related_name='rankings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_rankings')
    rank = models.IntegerField(default=1, db_index=True)
    solved = models.IntegerField(default=0)
    score = models.FloatField(default=0.0)
    penalty = models.IntegerField(default=0) # Total penalty in minutes
    rating_before = models.IntegerField(null=True, blank=True)
    rating_after = models.IntegerField(null=True, blank=True)
    rating_change = models.IntegerField(default=0)
    problem_details = models.JSONField(default=dict) 
    # e.g.: {"A": {"status": "AC", "tries": 1, "time": 15, "first_ac": True, "score": 100}, "B": {"status": "WA", "tries": 2, "time": 0, "score": 0}}
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank']
        unique_together = ('contest', 'user')
        indexes = [
            models.Index(fields=['contest', 'rank']),
            models.Index(fields=['contest', '-solved', 'penalty']),
        ]

    def __str__(self):
        return f"[{self.contest.key}] #{self.rank} {self.user.username} ({self.solved} solved, {self.penalty}m)"
