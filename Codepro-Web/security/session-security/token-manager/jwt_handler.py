"""Lightweight, zero-dependency JWT implementation with HMAC-SHA256."""
import json
import base64
import hmac
import hashlib
import time
import os
from typing import Dict, Any, Optional

SECRET_KEY = os.environ.get('JWT_SECRET', '')

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64url_decode(s: str) -> bytes:
    padding = '=' * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + padding)

class JWTHandler:
    @classmethod
    def encode(cls, payload: Dict[str, Any], expires_in_seconds: int = 3600) -> str:
        if not SECRET_KEY:
            raise RuntimeError('JWT_SECRET is required')
        header = {'alg': 'HS256', 'typ': 'JWT'}
        full_payload = dict(payload)
        now = int(time.time())
        full_payload['iat'] = now
        full_payload['exp'] = now + expires_in_seconds

        h_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        p_b64 = _b64url_encode(json.dumps(full_payload, separators=(',', ':')).encode('utf-8'))
        signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
        sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        sig_b64 = _b64url_encode(sig)

        return f"{h_b64}.{p_b64}.{sig_b64}"

    @classmethod
    def decode(cls, token: str) -> Optional[Dict[str, Any]]:
        if not SECRET_KEY:
            return None
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            h_b64, p_b64, sig_b64 = parts
            signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
            expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
            actual_sig = _b64url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(_b64url_decode(p_b64).decode('utf-8'))
            if payload.get('exp', 0) < time.time():
                return None  # Expired

            return payload
        except Exception:
            return None
