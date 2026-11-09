from django.db import models


class RankingSnapshot(models.Model):
    snapshot_type = models.CharField(max_length=32, default='global', db_index=True) # global, country, school, contest
    snapshot_key = models.CharField(max_length=64, db_index=True)
    data = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Snapshot {self.snapshot_type}:{self.snapshot_key} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
