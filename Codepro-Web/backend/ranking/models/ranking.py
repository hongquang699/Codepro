from django.db import models
from django.contrib.auth.models import User

class GlobalRanking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='global_ranking')
    rank = models.IntegerField(default=1, db_index=True)
    rating = models.IntegerField(default=1500, db_index=True)
    score = models.FloatField(default=0.0)
    solved = models.IntegerField(default=0)
    submissions = models.IntegerField(default=0)
    country = models.CharField(max_length=64, default='Vietnam', db_index=True, blank=True)
    school = models.CharField(max_length=128, default='', db_index=True, blank=True)
    organization = models.ForeignKey('judge.Organization', null=True, blank=True, on_delete=models.SET_NULL, related_name='rankings')
    tier = models.CharField(max_length=32, default='Specialist')
    last_active = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank']
        indexes = [
            models.Index(fields=['rank']),
            models.Index(fields=['rating']),
            models.Index(fields=['country', 'rank']),
            models.Index(fields=['school', 'rank']),
        ]

    def __str__(self):
        return f"#{self.rank} {self.user.username} ({self.rating})"
