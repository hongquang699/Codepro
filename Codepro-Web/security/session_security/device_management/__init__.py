"""Device fingerprinting and anomaly detector."""
import hashlib
from typing import Dict, Any

class DeviceManager:
    @staticmethod
    def compute_fingerprint(user_agent: str, accept_lang: str, client_ip: str) -> str:
        data = f"{user_agent}|{accept_lang}|{client_ip.split('.')[0]}.*.*.*"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]

    @staticmethod
    def is_suspicious_change(original_fp: str, current_fp: str) -> bool:
        return original_fp and original_fp != current_fp
