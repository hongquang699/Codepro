"""Import curated CodeContests Codeforces problems as admin-only OJ packages.

The manifest is collected from deepmind/code_contests (CC BY 4.0).
Each problem retains its original Codeforces link and test provenance.
"""
import html
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.judge import problem_package as pkg
from backend.judge.models import Problem, ProblemType


MANIFEST = settings.CODEPRO_DATA_ROOT / 'problem-data' / 'imports' / 'codecontests_cf_candidates.jsonl'
FLOAT_MARKERS = (
    'relative or absolute error', 'absolute or relative error',
    'absolute error', 'relative error', 'decimal places',
)
SAFE_CONSTRUCTIVE = {
    'CF500C', 'CF609B', 'CF779A', 'CF513A', 'CF740B',
    'CF1408B', 'CF676A', 'CF14C', 'CF680A', 'CF931B',
    'CF1037A', 'CF40A',
}


def eligible(item):
    tags = item.get('tags', [])
    description = item['description'].lower()
    if '*special' in tags or 'arbitrary case' in description:
        return False
    if 'constructive algorithms' in tags and item['code'] not in SAFE_CONSTRUCTIVE:
        return False
    if any(marker in description for marker in FLOAT_MARKERS):
        return False
    if not 8 <= len(item['tests']) <= 25:
        return False
    return True


def statement(item):
    source = item['source']
    description = re.sub(
        r'<image>', f'\n\n[Hình minh họa trong đề gốc]({source})\n\n',
        item['description'], flags=re.IGNORECASE,
    )
    original = html.escape(description, quote=False)
    return (
        f'# {html.escape(item["name"], quote=False)}\n\n{original}\n\n'
        f'---\n\nNguồn: [Codeforces]({source}). '
        'Dữ liệu đề và test: [CodeContests]'
        '(https://github.com/google-deepmind/code_contests), '
        '[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n'
    )


class Command(BaseCommand):
    help = 'Import approximately 200 Codeforces tasks with tests, hidden from non-admins'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--limit', type=int, default=205)

    def handle(self, *args, **options):
        if not MANIFEST.is_file():
            raise CommandError(f'Missing manifest: {MANIFEST}')
        with MANIFEST.open(encoding='utf-8') as handle:
            items = [json.loads(line) for line in handle if line.strip()]
        selected = sorted(
            (item for item in items if eligible(item)),
            key=lambda item: ('<image>' in item['description'].lower(), item['code']),
        )[:options['limit']]
        if len(selected) < 200 and options['limit'] >= 200:
            raise CommandError(f'Only {len(selected)} eligible tasks; need at least 200')
        existing = set(Problem.objects.filter(
            code__in=[item['code'] for item in selected]
        ).values_list('code', flat=True))
        if not options['apply']:
            self.stdout.write(
                f'Would import {len(selected)-len(existing)} new hidden tasks '
                f'({len(existing)} already present), '
                f'{sum(len(item["tests"]) for item in selected)} test pairs.'
            )
            return
        inserted = 0
        for item in selected:
            code = item['code']
            if code in existing:
                continue
            root = Path(pkg.get_problem_dir(code))
            if root.exists() and any(path.is_file() for path in root.rglob('*')):
                raise CommandError(f'{code} package already contains files: {root}')
            memory_mb = min(512, max(64, (int(item['memory_limit_bytes'] or 268435456) + 1048575) // 1048576))
            rating = item['rating']
            difficulty = 'easy' if rating <= 1100 else 'medium' if rating <= 1500 else 'hard'
            pkg.init_package(code, {
                'title': item['name'], 'time_limit': item['time_limit'],
                'memory_limit': memory_mb, 'points': 100,
                'difficulty': difficulty, 'status': 'ready',
            })
            body = statement(item)
            pkg.save_statement(code, body)
            for index, (case_input, case_output) in enumerate(item['tests'], 1):
                pkg.save_testcase(
                    code, f'{index:02d}', case_input, case_output,
                    points=100 / len(item['tests']), sample=index == 1,
                )
            with transaction.atomic():
                problem = Problem.objects.create(
                    code=code, name=item['name'], description=body,
                    time_limit=item['time_limit'], memory_limit=memory_mb * 1024,
                    points=100, difficulty=difficulty,
                    status='ready', is_public=False,
                    bendo_data={
                        'source_url': item['source'],
                        'dataset': 'deepmind/code_contests',
                        'cf_rating': rating,
                    },
                )
                for tag_name in item['tags'][:3]:
                    tag, _ = ProblemType.objects.get_or_create(
                        name=tag_name, defaults={'full_name': tag_name.title()})
                    problem.types.add(tag)
            inserted += 1
            if inserted % 25 == 0:
                self.stdout.write(f'Imported {inserted}/{len(selected)-len(existing)}', ending='\n')
        self.stdout.write(self.style.SUCCESS(
            f'Imported {inserted} hidden Codeforces tasks with '
            f'{sum(len(item["tests"]) for item in selected)} test pairs'))
