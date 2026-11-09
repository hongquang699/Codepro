import hashlib
import io
import json
import os
import sys
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from testcase.versioned import materialize_version
from testcase.manager import TestcaseManager


class VersionedPackageTests(unittest.TestCase):
    def test_digest_checked_package_loads_expected_cases(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('manifest.json', json.dumps({'groups': [
                {'name': 'main', 'points': 100, 'cases': [{'name': '01'}]}]}))
            archive.writestr('cases/01.in', '1 2\n')
            archive.writestr('cases/01.out', '3\n')
        payload = output.getvalue()
        digest = hashlib.sha256(payload).hexdigest()
        version_id = '11111111-1111-1111-1111-111111111111'
        ref = {'id': version_id, 'sha256': digest,
            'key': f'problems/1/versions/{version_id}/{digest}.zip'}
        with patch.dict(os.environ, {'PROBLEM_STORAGE_ENDPOINT': 'http://minio:9000',
                'PROBLEM_STORAGE_ACCESS_KEY': 'test', 'PROBLEM_STORAGE_SECRET_KEY': 'test'}), \
             patch('testcase.versioned.boto3.client') as client:
            client.return_value.get_object.return_value = {
                'ContentLength': len(payload), 'Body': io.BytesIO(payload)}
            with materialize_version(ref) as directory:
                cases = TestcaseManager(directory).get_testcases('IGNORED', problem_dir=directory)
                self.assertEqual(len(cases), 1)
                self.assertEqual(cases[0].input_data, '1 2\n')
                self.assertEqual(cases[0].expected_output, '3\n')


if __name__ == '__main__':
    unittest.main()
