"""Brute force prevention and account lockout tracker."""
import time
from typing import Dict, Tuple

class BruteForceProtector:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes

    # In-memory store: {identifier: [timestamp, count]}
    _attempts: Dict[str, Tuple[float, int]] = {}

    @classmethod
    def record_failure(cls, key: str) -> int:
        now = time.time()
        last_time, count = cls._attempts.get(key, (now, 0))
        if now - last_time > cls.LOCKOUT_DURATION:
            count = 0
        count += 1
        cls._attempts[key] = (now, count)
        return count

    @classmethod
    def is_locked(cls, key: str) -> Tuple[bool, int]:
        now = time.time()
        if key not in cls._attempts:
            return False, 0
        last_time, count = cls._attempts[key]
        if count >= cls.MAX_ATTEMPTS:
            remaining = int(cls.LOCKOUT_DURATION - (now - last_time))
            if remaining > 0:
                return True, remaining
            else:
                # Lock expired
                del cls._attempts[key]
                return False, 0
        return False, 0

    @classmethod
    def record_success(cls, key: str):
        if key in cls._attempts:
            del cls._attempts[key]
