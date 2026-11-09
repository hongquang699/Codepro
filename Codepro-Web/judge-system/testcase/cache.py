"""
Testcase in-memory and disk cache for Judge System.
Implements an LRU cache to speed up repeated testcase lookups for active problems.
"""

import time
from typing import Dict, Any, Optional

class TestcaseCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TestcaseCache, cls).__new__(cls)
            cls._instance._cache: Dict[str, Dict[str, Any]] = {}
            cls._instance._max_entries = 100
            cls._instance._ttl_sec = 1800  # 30 minutes
        return cls._instance

    def get(self, problem_code: str) -> Optional[list]:
        """Retrieves cached testcases for a given problem code."""
        entry = self._cache.get(problem_code)
        if not entry:
            return None
        
        # Check TTL
        if time.time() - entry["timestamp"] > self._ttl_sec:
            del self._cache[problem_code]
            return None

        entry["last_accessed"] = time.time()
        return entry["testcases"]

    def put(self, problem_code: str, testcases: list):
        """Stores testcases in the cache."""
        if len(self._cache) >= self._max_entries:
            # Evict least recently accessed entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get("last_accessed", 0))
            del self._cache[oldest_key]

        now = time.time()
        self._cache[problem_code] = {
            "testcases": testcases,
            "timestamp": now,
            "last_accessed": now
        }

    def invalidate(self, problem_code: str):
        """Removes a problem from cache when testcases are updated."""
        if problem_code in self._cache:
            del self._cache[problem_code]

    def clear(self):
        """Clears all entries in the cache."""
        self._cache.clear()
