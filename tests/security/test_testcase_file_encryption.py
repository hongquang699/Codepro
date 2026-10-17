import base64
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from security.encryption import file_cipher


class TestTestcaseFileEncryption(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        key_patch = patch.dict(os.environ, {
            'TESTCASE_ENCRYPTION_KEY': base64.b64encode(os.urandom(32)).decode('ascii')
        })
        key_patch.start()
        self.addCleanup(key_patch.stop)

    def test_roundtrip_and_tamper_detection(self):
        path = self.root / '01.in'
        original = b'private testcase\n'
        file_cipher.write_file(path, original)
        self.assertTrue(file_cipher.is_encrypted(path))
        self.assertNotIn(original, path.read_bytes())
        self.assertEqual(file_cipher.read_file(path), original)

        renamed = self.root / '02.in'
        renamed.write_bytes(path.read_bytes())
        with self.assertRaises(InvalidTag):
            file_cipher.read_file(renamed)

        damaged = bytearray(path.read_bytes())
        damaged[-1] ^= 1
        path.write_bytes(damaged)
        with self.assertRaises(InvalidTag):
            file_cipher.read_file(path)

    def test_encrypted_file_requires_key(self):
        path = self.root / '01.out'
        file_cipher.write_file(path, b'42\n')
        with patch.dict(os.environ, {'TESTCASE_ENCRYPTION_KEY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'TESTCASE_ENCRYPTION_KEY'):
                file_cipher.read_file(path)

    def test_existing_plaintext_migration(self):
        cases = self.root / 'PROBLEM' / 'cases'
        cases.mkdir(parents=True)
        path = cases / '01.in'
        path.write_bytes(b'old testcase\n')
        command = [sys.executable, 'scripts/encrypt_testcases.py', str(self.root)]
        dry_run = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertIn('1 plaintext', dry_run.stdout)
        self.assertFalse(file_cipher.is_encrypted(path))
        subprocess.run([*command, '--apply'], capture_output=True, text=True, check=True)
        self.assertTrue(file_cipher.is_encrypted(path))
        self.assertEqual(file_cipher.read_file(path), b'old testcase\n')

    def test_judge_loader_reads_encrypted_cases(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'judge-system'))
        from testcase.loader import TestcaseLoader

        problem = self.root / 'PROBLEM'
        cases = problem / 'cases'
        cases.mkdir(parents=True)
        file_cipher.write_file(cases / '01.in', b'1 2\n')
        file_cipher.write_file(cases / '01.out', b'3\n')
        loaded = TestcaseLoader.load_from_directory(str(problem))
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].input_data, '1 2\n')
        self.assertEqual(loaded[0].expected_output, '3\n')


if __name__ == '__main__':
    unittest.main()
