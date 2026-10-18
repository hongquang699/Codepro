"""Publish public submission status after database commits."""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.judge.models import Submission

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Submission, dispatch_uid='submission_websocket_status')
def publish_submission_status(sender, instance, **kwargs):
    data = {
        'id': instance.pk,
        'status': 'FINISHED' if instance.status == 'D' else {
            'QU': 'QUEUED', 'P': 'PROCESSING', 'G': 'GRADING'
        }.get(instance.status, instance.status),
        'verdict': instance.result or 'JUDGING',
        'score': instance.points or 0,
        'time': round((instance.time or 0) * 1000, 1),
        'memory': round((instance.memory or 0) / 1024, 2),
        'finished': instance.status == 'D',
    }

    def publish():
        try:
            from websocket.submission.consumer import broadcast_submission_update
            broadcast_submission_update(instance.pk, data)
        except Exception:
            logger.exception('Failed to publish submission %s status', instance.pk)

    transaction.on_commit(publish)
