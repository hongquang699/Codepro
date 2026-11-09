import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.judge.models import Submission
from .models import AntiCheatSettings, ScanJob

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Submission)
def queue_contest_submission_scan(sender, instance, created, **kwargs):
    if not created or not instance.contest_id:
        return

    submission_id, contest_id = instance.pk, instance.contest_id

    def enqueue():
        try:
            config, _ = AntiCheatSettings.objects.get_or_create(contest_id=contest_id)
            if config.enabled and config.scan_mode == 'realtime':
                ScanJob.objects.get_or_create(
                    contest_id=contest_id, target_submission_id=submission_id,
                    status='PENDING', defaults={'total': 1}
                )
        except Exception:
            logger.exception('Could not queue anti-cheat scan for submission %s', submission_id)

    transaction.on_commit(enqueue)
