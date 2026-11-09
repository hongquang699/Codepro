"""Move legacy problem and contest files through a private S3 snapshot."""

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings

from .service import s3


DATASETS = ('problem-data', 'contest-data', 'storage/contests')
MANIFEST = 'archive-manifest.json'
DEFAULT_PREFIX = 'codepro-data/v1'
MAX_FILES = 50000
MAX_UNPACKED = 4 * 1024 * 1024 * 1024
MAX_ARCHIVE = 4 * 1024 * 1024 * 1024
MAX_MANIFEST = 16 * 1024 * 1024
CHUNK = 1024 * 1024


def _digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(CHUNK), b''):
            sha.update(chunk)
    return sha.hexdigest()


def _safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe archive path: {name!r}')
    parts = PurePosixPath(name).parts
    if (name.startswith('/') or any(part in ('', '.', '..') for part in name.split('/'))
            or not any(name.startswith(dataset + '/') for dataset in DATASETS)
            or len(name) > 400 or parts[-1] == MANIFEST):
        raise ValueError(f'Unsafe archive path: {name!r}')
    for part in parts:
        if part.rstrip(' .') != part or part.upper().split('.')[0] in {
                'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
                *(f'LPT{i}' for i in range(1, 10))}:
            raise ValueError(f'Unsafe archive path: {name!r}')
    return name


def _files(source_root):
    if not (source_root / 'problem-data' / 'problems').is_dir():
        raise ValueError('Source does not contain problem-data/problems')
    for dataset in DATASETS:
        root = source_root / dataset
        if not root.exists():
            continue
        if root.is_symlink():
            raise ValueError(f'Symlink is not allowed: {root}')
        for path in sorted(root.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'Symlink is not allowed: {path}')
            if path.is_file():
                name = _safe_name(path.relative_to(source_root).as_posix())
                yield name, path


def _prefix(value):
    value = value.strip('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/_-]{0,150}', value) or '//' in value:
        raise ValueError('Invalid object prefix')
    return value


def upload(source_root, *, client=None, bucket=None, prefix=DEFAULT_PREFIX):
    source_root = Path(source_root).resolve()
    client = client or s3()
    bucket = bucket or settings.PROBLEM_STORAGE_PRIVATE_BUCKET
    prefix = _prefix(prefix)
    with tempfile.TemporaryDirectory(prefix='codepro-data-upload-') as temporary:
        archive_path = Path(temporary) / 'snapshot.zip'
        manifest = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                    'files': {}, 'directories': []}
        total = 0
        with ZipFile(archive_path, 'w', ZIP_DEFLATED, allowZip64=True) as archive:
            for name, path in _files(source_root):
                if len(manifest['files']) >= MAX_FILES:
                    raise ValueError('Too many data files')
                size = path.stat().st_size
                total += size
                if total > MAX_UNPACKED:
                    raise ValueError('Problem data exceeds size limit')
                sha = hashlib.sha256()
                copied = 0
                with path.open('rb') as source, archive.open(name, 'w') as target:
                    for chunk in iter(lambda: source.read(CHUNK), b''):
                        copied += len(chunk)
                        sha.update(chunk)
                        target.write(chunk)
                if copied != size:
                    raise ValueError(f'File changed while archiving: {name}')
                manifest['files'][name] = {'bytes': copied, 'sha256': sha.hexdigest()}
            if not manifest['files']:
                raise ValueError('No problem data files found')
            for dataset in DATASETS:
                root = source_root / dataset
                if root.exists():
                    for directory in (root, *sorted(p for p in root.rglob('*') if p.is_dir())):
                        if directory.is_symlink():
                            raise ValueError(f'Symlink is not allowed: {directory}')
                        name = directory.relative_to(source_root).as_posix()
                        _safe_name(name + '/.directory')
                        manifest['directories'].append(name)
            archive.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False))
        archive_size = archive_path.stat().st_size
        if archive_size > MAX_ARCHIVE:
            raise ValueError('Snapshot archive exceeds size limit')
        digest = _digest(archive_path)
        key = f'{prefix}/objects/{digest}.zip'
        client.upload_file(str(archive_path), bucket, key)
        index = {'schema_version': 1, 'key': key, 'sha256': digest,
                 'bytes': archive_size, 'file_count': len(manifest['files']),
                 'created_at': manifest['created_at']}
        client.put_object(Bucket=bucket, Key=f'{prefix}/latest.json',
                          Body=json.dumps(index).encode('utf-8'),
                          ContentType='application/json')
        return index


def download(destination, *, client=None, bucket=None, prefix=DEFAULT_PREFIX):
    destination = Path(destination).resolve()
    project = Path(settings.BASE_DIR).resolve()
    if destination == project or destination.is_relative_to(project):
        raise ValueError('Destination must be outside the source repository')
    if destination.exists():
        raise ValueError('Destination already exists; use a new directory for each snapshot')
    if not destination.parent.is_dir():
        raise ValueError('Destination parent does not exist')
    client = client or s3()
    bucket = bucket or settings.PROBLEM_STORAGE_PRIVATE_BUCKET
    prefix = _prefix(prefix)
    response = client.get_object(Bucket=bucket, Key=f'{prefix}/latest.json')
    raw_index = response['Body'].read(65537)
    if len(raw_index) > 65536:
        raise ValueError('Snapshot index is too large')
    index = json.loads(raw_index)
    digest = index.get('sha256')
    key = index.get('key')
    if (index.get('schema_version') != 1 or not isinstance(digest, str)
            or not re.fullmatch(r'[0-9a-f]{64}', digest)
            or key != f'{prefix}/objects/{digest}.zip'
            or not isinstance(index.get('bytes'), int)
            or not 0 < index['bytes'] <= MAX_ARCHIVE):
        raise ValueError('Invalid snapshot index')
    with tempfile.TemporaryDirectory(prefix='codepro-data-download-') as temporary:
        archive_path = Path(temporary) / 'snapshot.zip'
        client.download_file(bucket, key, str(archive_path))
        if archive_path.stat().st_size != index['bytes'] or _digest(archive_path) != digest:
            raise ValueError('Snapshot archive checksum mismatch')
        stage = Path(tempfile.mkdtemp(prefix=f'.{destination.name}-', dir=destination.parent))
        try:
            with ZipFile(archive_path) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_FILES + 1 or len({info.filename for info in infos}) != len(infos):
                    raise ValueError('Invalid file list in snapshot')
                try:
                    manifest_info = archive.getinfo(MANIFEST)
                except KeyError as exc:
                    raise ValueError('Snapshot manifest is missing') from exc
                if manifest_info.file_size > MAX_MANIFEST:
                    raise ValueError('Snapshot manifest is too large')
                manifest = json.loads(archive.read(MANIFEST))
                files = manifest.get('files')
                if (manifest.get('schema_version') != 1 or not isinstance(files, dict)
                        or len(files) != index.get('file_count')):
                    raise ValueError('Invalid snapshot manifest')
                directories = manifest.get('directories')
                if (not isinstance(directories, list) or len(directories) > MAX_FILES
                        or len(directories) != len(set(directories))):
                    raise ValueError('Invalid snapshot directories')
                if set(files) != {info.filename for info in infos if info.filename != MANIFEST}:
                    raise ValueError('Snapshot manifest does not match archive')
                for name in directories:
                    if not isinstance(name, str):
                        raise ValueError('Invalid snapshot directory')
                    _safe_name(name + '/.directory')
                    stage.joinpath(*PurePosixPath(name).parts).mkdir(parents=True, exist_ok=True)
                total = 0
                for info in infos:
                    if info.filename == MANIFEST:
                        continue
                    name = _safe_name(info.filename)
                    if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                        raise ValueError('Directories and symlinks are not allowed in snapshot')
                    record = files[name]
                    if (not isinstance(record, dict) or not isinstance(record.get('bytes'), int)
                            or not isinstance(record.get('sha256'), str)
                            or not re.fullmatch(r'[0-9a-f]{64}', record['sha256'])
                            or record['bytes'] != info.file_size):
                        raise ValueError(f'Invalid manifest entry: {name}')
                    total += info.file_size
                    if total > MAX_UNPACKED:
                        raise ValueError('Snapshot exceeds unpacked size limit')
                    target = stage.joinpath(*PurePosixPath(name).parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    sha = hashlib.sha256()
                    copied = 0
                    with archive.open(info) as source, target.open('xb') as output:
                        for chunk in iter(lambda: source.read(CHUNK), b''):
                            copied += len(chunk)
                            if copied > record['bytes']:
                                raise ValueError(f'File exceeds manifest size: {name}')
                            sha.update(chunk)
                            output.write(chunk)
                    if copied != record['bytes'] or sha.hexdigest() != record['sha256']:
                        raise ValueError(f'File checksum mismatch: {name}')
            if not (stage / 'problem-data' / 'problems').is_dir():
                raise ValueError('Snapshot contains no problem-data/problems')
            os.replace(stage, destination)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return index
