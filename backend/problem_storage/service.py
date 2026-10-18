"""Versioned problem packages. Only the validation worker reads private ZIP objects."""
import hashlib
import io
import json
import re
import uuid
import zipfile

import boto3
from botocore.client import Config
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import ProblemRelease, ProblemVersion, TestCase, TestGroup

MAX_ZIP = 20 * 1024 * 1024
MAX_UNPACKED = 100 * 1024 * 1024
MAX_FILE = 20 * 1024 * 1024
MAX_FILES = 1000
SAFE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$')


def s3(public=False):
    endpoint = settings.PROBLEM_STORAGE_PUBLIC_ENDPOINT if public else settings.PROBLEM_STORAGE_ENDPOINT
    if not endpoint or not settings.PROBLEM_STORAGE_ACCESS_KEY or not settings.PROBLEM_STORAGE_SECRET_KEY:
        raise RuntimeError('Problem Storage MinIO credentials are not configured')
    return boto3.client('s3', endpoint_url=endpoint,
        aws_access_key_id=settings.PROBLEM_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.PROBLEM_STORAGE_SECRET_KEY,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}))


def private_bucket():
    return settings.PROBLEM_STORAGE_PRIVATE_BUCKET


def initiate(problem, user):
    with transaction.atomic():
        from backend.judge.models import Problem
        Problem.objects.select_for_update().get(pk=problem.pk)
        previous = ProblemVersion.objects.filter(problem=problem).order_by('-number').first()
        number = previous.number + 1 if previous else 1
        version = ProblemVersion.objects.create(problem=problem, number=number, created_by=user,
            private_key=f'staging/{problem.id}/{uuid.uuid4().hex}.zip')
    upload = s3(public=True).generate_presigned_post(Bucket=private_bucket(),
        Key=version.private_key, Fields={'Content-Type': 'application/zip'},
        Conditions=[['content-length-range', 1, MAX_ZIP],
                    {'Content-Type': 'application/zip'}], ExpiresIn=900)
    return version, upload


def _checked_zip(payload):
    if len(payload) > MAX_ZIP or not payload.startswith(b'PK\x03\x04'):
        raise ValueError('ZIP must be at most 20 MiB')
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise ValueError('Invalid ZIP') from exc
    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_FILES:
            raise ValueError('Invalid file count')
        total = 0
        files = {}
        for info in infos:
            name = info.filename
            parts = name.split('/')
            mode = (info.external_attr >> 16) & 0o170000
            if (info.is_dir() or '\\' in name or len(parts) > 2 or
                    any(not SAFE_NAME.fullmatch(part) for part in parts) or
                    mode not in (0, 0o100000) or
                    info.flag_bits & 1 or info.file_size > MAX_FILE or
                    info.compress_size == 0 and info.file_size or
                    info.compress_size and info.file_size > info.compress_size * 100):
                raise ValueError('Unsafe ZIP member')
            if name in files:
                raise ValueError('Duplicate ZIP member')
            total += info.file_size
            if total > MAX_UNPACKED:
                raise ValueError('ZIP expands beyond limit')
            with archive.open(info) as stream:
                data = stream.read(info.file_size + 1)
            if len(data) != info.file_size:
                raise ValueError('Invalid ZIP size')
            files[name] = data
    return files


def validate_package(payload):
    files = _checked_zip(payload)
    if 'manifest.json' not in files or 'statement.md' not in files:
        raise ValueError('manifest.json and statement.md are required')
    if len(files['statement.md']) > 1024 * 1024 or len(files['manifest.json']) > 1024 * 1024:
        raise ValueError('Statement or manifest is too large')
    try:
        statement = files['statement.md'].decode('utf-8')
        manifest = json.loads(files['manifest.json'].decode('utf-8'))
    except (UnicodeError, ValueError) as exc:
        raise ValueError('Invalid UTF-8 or manifest JSON') from exc
    if (not isinstance(manifest, dict) or not isinstance(manifest.get('groups'), list)
            or len(manifest['groups']) > 100):
        raise ValueError('Manifest needs groups')
    groups = []
    used = {'manifest.json', 'statement.md'}
    group_names = set()
    case_count = 0
    for order, group in enumerate(manifest['groups']):
        if (not isinstance(group, dict) or not isinstance(group.get('name'), str)
                or not SAFE_NAME.fullmatch(group['name'])):
            raise ValueError('Invalid group name')
        if group['name'] in group_names:
            raise ValueError('Duplicate group name')
        group_names.add(group['name'])
        cases = group.get('cases')
        points = group.get('points')
        if (not isinstance(cases, list) or not cases or len(cases) > 500
                or type(points) is not int or not 0 <= points <= 100):
            raise ValueError('Invalid group cases or points')
        case_count += len(cases)
        if case_count > 500:
            raise ValueError('Too many testcases')
        checked = []
        for case_order, case in enumerate(cases):
            if (not isinstance(case, dict) or not isinstance(case.get('name'), str)
                    or not SAFE_NAME.fullmatch(case['name'])):
                raise ValueError('Invalid testcase name')
            name = case['name']
            input_path, output_path = f'cases/{name}.in', f'cases/{name}.out'
            if input_path not in files or output_path not in files or input_path in used:
                raise ValueError('Missing or duplicate testcase pair')
            used.update((input_path, output_path))
            checked.append({'name': name, 'input_path': input_path, 'output_path': output_path,
                'input_sha256': hashlib.sha256(files[input_path]).hexdigest(),
                'output_sha256': hashlib.sha256(files[output_path]).hexdigest(),
                'sample': case.get('sample') is True, 'order': case_order})
        groups.append({'name': group['name'], 'points': points, 'order': order, 'cases': checked})
    if not groups or len(used) != len(files):
        raise ValueError('Unreferenced files or no test groups')
    if sum(group['points'] for group in groups) != 100:
        raise ValueError('Group points must sum to 100')
    return statement, groups


def validate_version(version_id):
    version = ProblemVersion.objects.get(pk=version_id)
    if version.state not in (ProblemVersion.State.PENDING, ProblemVersion.State.VALIDATING):
        return version
    version.state = ProblemVersion.State.VALIDATING
    version.save(update_fields=['state'])
    client = s3()
    staging_key = version.private_key
    try:
        obj = client.get_object(Bucket=private_bucket(), Key=staging_key)
        if obj['ContentLength'] > MAX_ZIP:
            raise ValueError('ZIP is too large')
        payload = obj['Body'].read(MAX_ZIP + 1)
        statement, groups = validate_package(payload)
        digest = hashlib.sha256(payload).hexdigest()
        final_key = f'problems/{version.problem_id}/versions/{version.id}/{digest}.zip'
        client.copy_object(Bucket=private_bucket(), Key=final_key,
            CopySource={'Bucket': private_bucket(), 'Key': staging_key},
            CopySourceIfMatch=obj['ETag'], MetadataDirective='COPY')
        # A public bucket contains statements only. Private test data never enters it.
        public_key = f'problems/{version.problem_id}/versions/{version.id}/statement.md'
        client.put_object(Bucket=settings.PROBLEM_STORAGE_PUBLIC_BUCKET, Key=public_key,
            Body=statement.encode('utf-8'), ContentType='text/markdown; charset=utf-8')
        with transaction.atomic():
            locked = ProblemVersion.objects.select_for_update().get(pk=version.pk)
            if locked.state != ProblemVersion.State.VALIDATING:
                return locked
            for group in groups:
                db_group = TestGroup.objects.create(version=locked, name=group['name'],
                    points=group['points'], order=group['order'])
                TestCase.objects.bulk_create([TestCase(group=db_group, **case) for case in group['cases']])
            locked.private_key, locked.public_key = final_key, public_key
            locked.sha256, locked.size_bytes = digest, len(payload)
            locked.manifest = {'groups': [{'name': g['name'], 'points': g['points'],
                'cases': [c['name'] for c in g['cases']]} for g in groups]}
            locked.statement = statement
            locked.state = ProblemVersion.State.READY
            locked.save()
        client.delete_object(Bucket=private_bucket(), Key=staging_key)
        return locked
    except (ValueError, zipfile.BadZipFile) as exc:
        ProblemVersion.objects.filter(pk=version.pk, state=ProblemVersion.State.VALIDATING).update(
            state=ProblemVersion.State.REJECTED, error=str(exc)[:500])
        raise
    except Exception:
        ProblemVersion.objects.filter(pk=version.pk, state=ProblemVersion.State.VALIDATING).update(
            state=ProblemVersion.State.PENDING)
        raise


def publish(version):
    with transaction.atomic():
        version = ProblemVersion.objects.select_for_update().get(pk=version.pk)
        if version.state not in (ProblemVersion.State.READY, ProblemVersion.State.PUBLISHED):
            raise ValueError('Version must be validated before publication')
        version.state = ProblemVersion.State.PUBLISHED
        version.published_at = timezone.now()
        version.save(update_fields=['state', 'published_at'])
        ProblemRelease.objects.update_or_create(problem=version.problem, defaults={'version': version})
        from backend.judge.models import Problem
        Problem.objects.filter(pk=version.problem_id).update(description=version.statement)
    return version
