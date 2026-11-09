from django.db import models
from django.contrib.auth.models import User

class RatingHistoryRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rating_history')
    contest = models.ForeignKey('judge.Contest', on_delete=models.CASCADE, null=True, blank=True, related_name='rating_histories')
    contest_name = models.CharField(max_length=256, blank=True, default='')
    old_rating = models.IntegerField()
    new_rating = models.IntegerField()
    rating_change = models.IntegerField()
    rank_in_contest = models.IntegerField(default=1)
    performance = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['contest']),
        ]

    def __str__(self):
        sign = '+' if self.rating_change >= 0 else ''
        return f"{self.user.username}: {self.old_rating} -> {self.new_rating} ({sign}{self.rating_change})"
