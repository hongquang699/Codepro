"""Restore the three sample statements damaged by shell dollar expansion."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.judge.models import Problem


EXPECTED_HASHES = {
    'APLUS': 'b30137617a35b044d7af7a84595956c8aca88073092272a79ab9ff6d9cd047b5',
    'KNAPSACK': 'a77e23340374451b11148c389765147d9836114f51c5c5a6fcd0939b6aa343f8',
    'MAXSUM': 'a05e89ae86be66215ee192e70589ec0dc48b1fc0ca4e7580e1580889ccf29004',
}


class Command(BaseCommand):
    help = 'Restore APLUS, KNAPSACK and MAXSUM descriptions from reviewed Markdown files.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Back up and update matching database rows.')

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR) / 'problem-data'
        changes = {}
        for code, expected_hash in EXPECTED_HASHES.items():
            problem = Problem.objects.filter(code=code).first()
            if not problem:
                raise CommandError(f'{code}: problem not found')
            source = root / 'problems' / code / 'statement' / 'statement.md'
            repaired = source.read_text(encoding='utf-8')
            current_hash = hashlib.sha256(problem.description.encode('utf-8')).hexdigest()
            if problem.description.strip() == repaired.strip():
                self.stdout.write(f'{code}: already repaired')
            elif current_hash == expected_hash:
                changes[code] = (problem, repaired)
                self.stdout.write(f'{code}: repair needed')
            else:
                raise CommandError(f'{code}: description changed; refusing to overwrite it')

        if not options['apply'] or not changes:
            return
        backup_dir = root / 'repairs'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"statements-before-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        backup_path.write_text(json.dumps({code: problem.description for code, (problem, _) in changes.items()}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        with transaction.atomic():
            for problem, repaired in changes.values():
                problem.description = repaired
                problem.save(update_fields=['description'])
        self.stdout.write(self.style.SUCCESS(f'Repaired {len(changes)} statements; backup: {backup_path}'))
