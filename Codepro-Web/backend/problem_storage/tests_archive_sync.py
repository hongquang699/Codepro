import hashlib
import io
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile

from django.test import SimpleTestCase

from .archive_sync import DEFAULT_PREFIX, download, upload


class MemoryS3:
    def __init__(self):
        self.objects = {}

    def upload_file(self, filename, bucket, key):
        self.objects[(bucket, key)] = Path(filename).read_bytes()

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket, Key):
        return {'Body': io.BytesIO(self.objects[(Bucket, Key)])}

    def download_file(self, bucket, key, filename):
        Path(filename).write_bytes(self.objects[(bucket, key)])


class ProblemArchiveTests(SimpleTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        (self.source / 'problem-data' / 'problems' / 'SUM' / 'cases').mkdir(parents=True)
        (self.source / 'problem-data' / 'problems' / 'EMPTY').mkdir(parents=True)
        (self.source / 'contest-data' / 'contests' / 'ROUND1').mkdir(parents=True)
        (self.source / 'problem-data' / 'problems' / 'SUM' / 'cases' / '01.in').write_text('2 3\n')
        (self.source / 'contest-data' / 'contests' / 'ROUND1' / 'contest.yml').write_text('key: ROUND1\n')
        self.client = MemoryS3()

    def test_upload_and_download_verified_snapshot(self):
        index = upload(self.source, client=self.client, bucket='private')
        destination = self.root / 'downloaded'
        self.assertEqual(download(destination, client=self.client, bucket='private'), index)
        self.assertEqual((destination / 'problem-data/problems/SUM/cases/01.in').read_text(), '2 3\n')
        self.assertEqual((destination / 'contest-data/contests/ROUND1/contest.yml').read_text(),
                         'key: ROUND1\n')
        self.assertTrue((destination / 'problem-data/problems/EMPTY').is_dir())
        with self.assertRaisesRegex(ValueError, 'already exists'):
            download(destination, client=self.client, bucket='private')

    def test_tampered_archive_is_rejected_without_destination(self):
        index = upload(self.source, client=self.client, bucket='private')
        key = index['key']
        self.client.objects[('private', key)] += b'tampered'
        destination = self.root / 'untrusted'
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            download(destination, client=self.client, bucket='private')
        self.assertFalse(destination.exists())

    def test_archive_path_traversal_is_rejected(self):
        name = 'problem-data/problems/SUM/../escape.txt'
        content = b'bad'
        manifest = {'schema_version': 1, 'directories': [], 'files': {
            name: {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}}}
        buffer = io.BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr(name, content)
            archive.writestr('archive-manifest.json', json.dumps(manifest))
        payload = buffer.getvalue()
        digest = hashlib.sha256(payload).hexdigest()
        key = f'{DEFAULT_PREFIX}/objects/{digest}.zip'
        self.client.objects[('private', key)] = payload
        self.client.objects[('private', f'{DEFAULT_PREFIX}/latest.json')] = json.dumps({
            'schema_version': 1, 'key': key, 'sha256': digest, 'bytes': len(payload),
            'file_count': 1}).encode()
        destination = self.root / 'downloaded'
        with self.assertRaisesRegex(ValueError, 'Unsafe archive path'):
            download(destination, client=self.client, bucket='private')
        self.assertFalse(destination.exists())
