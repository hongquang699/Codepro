from django.db import models
from django.contrib.auth.models import User

class UserRating(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rating_profile')
    current_rating = models.IntegerField(default=0, db_index=True)
    max_rating = models.IntegerField(default=0)
    rank_tier = models.CharField(max_length=32, default='Unrated')
    volatility = models.FloatField(default=300.0)
    contests_participated = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-current_rating']
        indexes = [
            models.Index(fields=['-current_rating']),
            models.Index(fields=['rank_tier']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.current_rating} ({self.rank_tier})"

    @staticmethod
    def get_tier_info(rating, contests_participated=None):
        r = rating or 0
        if contests_participated == 0 or r == 0:
            return {'tier': 'Unrated', 'color': '#94a3b8', 'badge': 'UR', 'hex': '#94a3b8'}
        if r >= 3000:
            return {'tier': 'Legendary Grandmaster', 'color': '#ef4444', 'badge': 'LGM', 'hex': '#000000'}
        elif r >= 2600:
            return {'tier': 'International Grandmaster', 'color': '#ef4444', 'badge': 'IGM', 'hex': '#ef4444'}
        elif r >= 2400:
            return {'tier': 'Grandmaster', 'color': '#ef4444', 'badge': 'GM', 'hex': '#ef4444'}
        elif r >= 2300:
            return {'tier': 'International Master', 'color': '#f97316', 'badge': 'IM', 'hex': '#f97316'}
        elif r >= 2100:
            return {'tier': 'Master', 'color': '#f97316', 'badge': 'M', 'hex': '#f97316'}
        elif r >= 1900:
            return {'tier': 'Candidate Master', 'color': '#a855f7', 'badge': 'CM', 'hex': '#a855f7'}
        elif r >= 1600:
            return {'tier': 'Expert', 'color': '#3b82f6', 'badge': 'EXP', 'hex': '#3b82f6'}
        elif r >= 1400:
            return {'tier': 'Specialist', 'color': '#10b981', 'badge': 'SPEC', 'hex': '#10b981'}
        elif r >= 1200:
            return {'tier': 'Pupil', 'color': '#06b6d4', 'badge': 'PUP', 'hex': '#06b6d4'}
        else:
            return {'tier': 'Newbie', 'color': '#94a3b8', 'badge': 'NEW', 'hex': '#94a3b8'}

    def update_tier(self):
        info = self.get_tier_info(self.current_rating, self.contests_participated)
        self.rank_tier = info['tier']
        if self.current_rating > self.max_rating:
            self.max_rating = self.current_rating
        self.save(update_fields=['rank_tier', 'max_rating', 'updated_at'])
