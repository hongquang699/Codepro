"""Migrate existing plaintext testcase files after making a backup.

Usage: python scripts/encrypt_testcases.py PATH [--apply]
Without --apply, only counts files that would be encrypted.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security.encryption import file_cipher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='problem-data/problems directory')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('root must be an existing directory')
    if file_cipher._cipher() is None:
        parser.error('TESTCASE_ENCRYPTION_KEY is required')
    paths = sorted(path for pattern in ('*.in', '*.out', '*.ans')
                   for path in args.root.rglob(pattern)
                   if path.is_file() and path.parent.name in ('cases', 'tests'))
    pending = [path for path in paths if not file_cipher.is_encrypted(path)]
    if args.apply:
        for path in pending:
            file_cipher.write_file(path, file_cipher.read_file(path))
    print(f'{len(pending)} plaintext testcase files ' + ('encrypted' if args.apply else 'would be encrypted'))


if __name__ == '__main__':
    main()
