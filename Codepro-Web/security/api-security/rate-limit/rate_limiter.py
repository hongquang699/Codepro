"""Sliding Window Rate Limiter."""
import time
from typing import Dict, List, Tuple

class RateLimiter:
    # {key: [timestamps]}
    _requests: Dict[str, List[float]] = {}

    @classmethod
    def check_limit(cls, key: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
        """Returns (allowed: bool, remaining_requests: int)."""
        now = time.time()
        cutoff = now - window_seconds
        
        # Clean older entries
        cls._requests[key] = [t for t in cls._requests.get(key, []) if t > cutoff]
        
        current_count = len(cls._requests[key])
        if current_count >= max_requests:
            return False, 0
        
        cls._requests[key].append(now)
        return True, max_requests - current_count - 1
