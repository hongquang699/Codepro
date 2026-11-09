"""Sliding Window Rate Limiter."""
import time
from collections import OrderedDict
from threading import Lock
from typing import Dict, List, Tuple

class RateLimiter:
    # {key: [timestamps]}
    _requests: Dict[str, List[float]] = OrderedDict()
    _lock = Lock()
    _last_sweep = 0.0
    _max_keys = 10000

    @classmethod
    def check_limit(cls, key: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
        """Returns (allowed: bool, remaining_requests: int)."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with cls._lock:
            if now - cls._last_sweep > 60 or len(cls._requests) >= cls._max_keys:
                for old_key, timestamps in list(cls._requests.items()):
                    if not timestamps or timestamps[-1] <= now - 3600:
                        del cls._requests[old_key]
                cls._last_sweep = now
            if key not in cls._requests and len(cls._requests) >= cls._max_keys:
                cls._requests.popitem(last=False)
            timestamps = [t for t in cls._requests.get(key, []) if t > cutoff]
            cls._requests[key] = timestamps
            cls._requests.move_to_end(key)
            if len(timestamps) >= max_requests:
                return False, 0
            timestamps.append(now)
            return True, max_requests - len(timestamps)
