"""Authenticated encryption for testcase files shared by the API and judge."""

import base64
import binascii
import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


MAGIC = b'CPOJCASE1\x00'


def _cipher():
    encoded = os.environ.get('TESTCASE_ENCRYPTION_KEY', '')
    if not encoded:
        return None
    try:
        key = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('TESTCASE_ENCRYPTION_KEY must be base64 encoded') from exc
    if len(key) != 32:
        raise ValueError('TESTCASE_ENCRYPTION_KEY must contain 32 random bytes')
    return AESGCM(key)


def is_encrypted(path):
    with open(path, 'rb') as handle:
        return handle.read(len(MAGIC)) == MAGIC


def read_file(path):
    payload = Path(path).read_bytes()
    if not payload.startswith(MAGIC):
        return payload  # Legacy files remain readable until migrated.
    cipher = _cipher()
    if cipher is None:
        raise RuntimeError('TESTCASE_ENCRYPTION_KEY is required to read encrypted testcases')
    nonce_at = len(MAGIC)
    return cipher.decrypt(payload[nonce_at:nonce_at + 12], payload[nonce_at + 12:], Path(path).name.encode())


def write_file(path, data):
    cipher = _cipher()
    if cipher is not None:
        nonce = os.urandom(12)
        data = MAGIC + nonce + cipher.encrypt(nonce, data, Path(path).name.encode())
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=target.parent, prefix='.case-')
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
