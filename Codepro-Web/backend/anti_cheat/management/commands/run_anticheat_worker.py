import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from backend.anti_cheat.models import AntiCheatSettings, ScanJob
from backend.anti_cheat.services.scanner import claim_scan, enqueue_scan, process_scan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process anti-cheat scans outside the request and judge workers'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--poll-seconds', type=float, default=2.0)

    def handle(self, *args, **options):
        stale = timezone.now() - timedelta(minutes=30)
        ScanJob.objects.filter(status='RUNNING', started_at__lt=stale).update(status='PENDING')
        last_schedule_check = 0
        while True:
            close_old_connections()
            if time.monotonic() - last_schedule_check >= 60:
                cutoff = timezone.now() - timedelta(hours=1)
                for config in AntiCheatSettings.objects.filter(enabled=True, scan_mode='scheduled').select_related('contest'):
                    latest = ScanJob.objects.filter(contest=config.contest, target_submission__isnull=True).order_by('-created_at').first()
                    if not latest or latest.created_at < cutoff:
                        enqueue_scan(config.contest)
                last_schedule_check = time.monotonic()
            job_id = claim_scan()
            if job_id:
                try:
                    process_scan(job_id)
                except Exception:
                    logger.exception('Anti-cheat scan %s failed', job_id)
            elif options['once']:
                break
            else:
                time.sleep(max(0.2, options['poll_seconds']))
            if options['once']:
                break
