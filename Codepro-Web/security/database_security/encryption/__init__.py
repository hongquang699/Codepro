"""Column-level Field Encryption."""
import base64
import os
import hashlib
import hmac

KEY = os.environ.get('DB_FIELD_ENCRYPTION_KEY', 'oj_field_encryption_master_key_2026').encode('utf-8')

class FieldCipher:
    @staticmethod
    def encrypt(plaintext: str) -> str:
        if not plaintext:
            return ""
        salt = os.urandom(16)
        stream_key = hashlib.sha256(KEY + salt).digest()
        data = plaintext.encode('utf-8')
        encrypted = bytes(b ^ stream_key[i % len(stream_key)] for i, b in enumerate(data))
        mac = hmac.new(KEY, salt + encrypted, hashlib.sha256).digest()[:16]
        return base64.b64encode(salt + mac + encrypted).decode('utf-8')

    @staticmethod
    def decrypt(cipher_b64: str) -> str:
        if not cipher_b64:
            return ""
        try:
            raw = base64.b64decode(cipher_b64.encode('utf-8'))
            salt = raw[:16]
            mac = raw[16:32]
            encrypted = raw[32:]
            expected_mac = hmac.new(KEY, salt + encrypted, hashlib.sha256).digest()[:16]
            if not hmac.compare_digest(mac, expected_mac):
                return ""  # Tampered
            stream_key = hashlib.sha256(KEY + salt).digest()
            data = bytes(b ^ stream_key[i % len(stream_key)] for i, b in enumerate(encrypted))
            return data.decode('utf-8')
        except Exception:
            return ""
