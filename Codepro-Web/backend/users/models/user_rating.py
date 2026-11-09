from django.db import models
from django.contrib.auth.models import User

class UserRating(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_rating')
    current_rating = models.IntegerField(default=0)
    max_rating = models.IntegerField(default=0)
    rank = models.CharField(max_length=50, default='Unrated')
    contest_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_ratings'

    def __str__(self):
        return f"{self.user.username} - {self.current_rating} ({self.rank})"

    def calculate_rank(self):
        if self.contest_count == 0 or self.current_rating == 0:
            return 'Unrated'
        r = self.current_rating
        if r >= 3000: return 'Legendary Grandmaster'
        if r >= 2400: return 'Grandmaster'
        if r >= 2100: return 'Master'
        if r >= 1900: return 'Candidate Master'
        if r >= 1600: return 'Expert'
        if r >= 1400: return 'Specialist'
        if r >= 1200: return 'Pupil'
        return 'Newbie'


class RatingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rating_histories')
    contest_id = models.CharField(max_length=100, blank=True, default='')
    contest_name = models.CharField(max_length=200, blank=True, default='')
    old_rating = models.IntegerField(default=1500)
    new_rating = models.IntegerField(default=1500)
    change = models.IntegerField(default=0)
    rank = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_rating_history'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} @ {self.contest_name}: {self.new_rating} ({self.change:+d})"
