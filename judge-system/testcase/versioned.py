"""Load a pinned, digest-verified private problem package for one judge job."""
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from contextlib import contextmanager

import boto3
from botocore.client import Config


@contextmanager
def materialize_version(ref):
    if not isinstance(ref, dict) or not re.fullmatch(r'[a-f0-9-]{36}', str(ref.get('id', ''))):
        raise ValueError('Invalid problem version')
    key = ref.get('key', '')
    digest = ref.get('sha256', '')
    if not re.fullmatch(r'problems/\d+/versions/[a-f0-9-]{36}/[a-f0-9]{64}\.zip', key) or not re.fullmatch(r'[a-f0-9]{64}', digest):
        raise ValueError('Invalid version object reference')
    if f'/versions/{ref["id"]}/' not in key or not key.endswith(f'/{digest}.zip'):
        raise ValueError('Version reference mismatch')
    client = boto3.client('s3', endpoint_url=os.environ['PROBLEM_STORAGE_ENDPOINT'],
        aws_access_key_id=os.environ['PROBLEM_STORAGE_ACCESS_KEY'],
        aws_secret_access_key=os.environ['PROBLEM_STORAGE_SECRET_KEY'],
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}))
    obj = client.get_object(Bucket=os.environ.get('PROBLEM_STORAGE_PRIVATE_BUCKET', 'problem-private'), Key=key)
    if obj['ContentLength'] > 20 * 1024 * 1024:
        raise ValueError('Problem package too large')
    data = obj['Body'].read(20 * 1024 * 1024 + 1)
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Problem package digest mismatch')
    with tempfile.TemporaryDirectory(prefix='judge-problem-') as directory:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > 1000 or sum(x.file_size for x in members) > 100 * 1024 * 1024:
                raise ValueError('Problem package exceeds limits')
            raw_manifest = archive.read('manifest.json')
            manifest = json.loads(raw_manifest.decode('utf-8'))
            cases = []
            subtasks = []
            for index, group in enumerate(manifest['groups'], start=1):
                names = [item['name'] for item in group['cases']]
                points = int(group['points'])
                subtasks.append({'id': index, 'points': points, 'depends_on': [],
                    'scoring_method': 'all_or_nothing'})
                for name in names:
                    cases.append({'id': name, 'subtask': index,
                        'points': points / len(names), 'sample': False})
            with open(os.path.join(directory, 'testcases.json'), 'w', encoding='utf-8') as output:
                json.dump({'cases': cases, 'subtasks': subtasks}, output)
            for info in members:
                if not re.fullmatch(r'cases/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(in|out)', info.filename):
                    continue
                if info.file_size > 20 * 1024 * 1024:
                    raise ValueError('Testcase exceeds limit')
                target = os.path.join(directory, info.filename)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with archive.open(info) as source, open(target, 'wb') as output:
                    output.write(source.read(info.file_size + 1))
        yield directory
