"""Private, versioned contest exports. Never serve these files as public media."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core.serializers import serialize
from django.db import transaction
from django.utils import timezone

from backend.judge.models import (
    Clarification, Contest, ContestParticipation, ContestProblem, Language,
    Problem, Profile, RatingHistory, Submission, SubmissionTestCase,
)
from backend.judge.problem_package import get_problem_dir


def _rows(queryset):
    return json.loads(serialize('json', queryset.order_by('pk')))


def export_contest(key, destination):
    """Export a finished contest to a new ZIP, without modifying live data.

    IDs in data.json are original database IDs, not portable import identifiers.
    Test packages retain their at-rest encryption; restoring them needs the
    original encryption key, which is deliberately excluded from this archive.
    """
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with transaction.atomic():
        contest = Contest.objects.select_for_update().get(key=key)
        if contest.end_time > timezone.now():
            raise ValueError('Chỉ lưu trữ cuộc thi đã kết thúc.')
        submissions = Submission.objects.filter(contest=contest)
        clarifications = Clarification.objects.filter(contest=contest)
        problem_ids = set(ContestProblem.objects.filter(contest=contest).values_list('problem_id', flat=True))
        problem_ids.update(submissions.values_list('problem_id', flat=True))
        problem_ids.update(clarifications.exclude(problem=None).values_list('problem_id', flat=True))
        problems = Problem.objects.filter(pk__in=problem_ids)
        profile_ids = set(ContestParticipation.objects.filter(contest=contest).values_list('user_id', flat=True))
        profile_ids.update(submissions.values_list('user_id', flat=True))
        profile_ids.update(clarifications.values_list('user_id', flat=True))
        profile_ids.update(clarifications.exclude(answered_by=None).values_list('answered_by_id', flat=True))
        ratings = RatingHistory.objects.filter(contest=contest)
        profile_ids.update(ratings.values_list('user_id', flat=True))
        # Export identity labels only: no passwords, tokens, emails or sessions.
        identities = list(Profile.objects.filter(pk__in=profile_ids).order_by('pk').values('id', 'user__username'))
        data = {
            'contest': _rows(Contest.objects.filter(pk=contest.pk)),
            'problems': _rows(problems),
            'contest_problems': _rows(ContestProblem.objects.filter(contest=contest)),
            'participants': _rows(ContestParticipation.objects.filter(contest=contest)),
            'identities': identities,
            'languages': _rows(Language.objects.filter(pk__in=submissions.values('language_id'))),
            'submissions': _rows(submissions),
            'test_results': _rows(SubmissionTestCase.objects.filter(submission__contest=contest)),
            'clarifications': _rows(clarifications),
            'ratings': _rows(ratings),
        }
        codes = list(problems.order_by('code').values_list('code', flat=True))

    handle, temporary = tempfile.mkstemp(prefix='.contest-', suffix='.zip', dir=destination.parent)
    os.close(handle)
    manifest = {'schema_version': 1, 'contest_key': key, 'created_at': timezone.now().isoformat(),
                'files': {}, 'missing_packages': [], 'encrypted_packages': True}
    try:
        with ZipFile(temporary, 'w', ZIP_DEFLATED) as archive:
            def write(name, content):
                archive.writestr(name, content)
                manifest['files'][name] = {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}

            write('data.json', json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
            root = Path(settings.DMOJ_PROBLEM_DATA_ROOT).resolve()
            for code in codes:
                package = Path(get_problem_dir(code))
                if package.is_symlink() or not package.resolve().is_relative_to(root):
                    raise ValueError('Gói bài toán nằm ngoài kho dữ liệu.')
                if not package.is_dir():
                    manifest['missing_packages'].append(code)
                    continue
                for path in sorted(package.rglob('*')):
                    if path.is_symlink() or not path.resolve().is_relative_to(package.resolve()):
                        raise ValueError('Không chấp nhận liên kết trong gói bài toán.')
                    if path.is_file():
                        write(f'problems/{code}/{path.relative_to(package).as_posix()}', path.read_bytes())
            archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        # Exclusive creation prevents accidentally replacing an earlier backup.
        os.link(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return manifest


def verify_archive(path):
    """Check every member, its size and digest without extracting private data."""
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Archive chứa tên tệp trùng lặp.')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('schema_version') != 1:
            raise ValueError('Phiên bản archive không được hỗ trợ.')
        if set(names) != set(manifest['files']) | {'manifest.json'}:
            raise ValueError('Danh sách tệp không khớp manifest.')
        for name, expected in manifest['files'].items():
            content = archive.read(name)
            if len(content) != expected['bytes'] or hashlib.sha256(content).hexdigest() != expected['sha256']:
                raise ValueError(f'Tệp không toàn vẹn: {name}')
    return manifest
