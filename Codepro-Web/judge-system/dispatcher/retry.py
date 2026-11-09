"""
Retry Policy and Dead-Letter handler for Judge System Dispatcher.
Controls automatic requeueing on transient failures and node crashes.
"""

import time
from typing import Dict, Optional

class RetryManager:
    def __init__(self, max_retries: int = 3, base_backoff_sec: float = 2.0):
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self._retry_counts: Dict[str, int] = {}
        self._dead_letters: Dict[str, dict] = {}

    def can_retry(self, job_id: str) -> bool:
        """Determines whether a failed job is eligible for another attempt."""
        current_attempts = self._retry_counts.get(job_id, 0)
        return current_attempts < self.max_retries

    def record_failure(self, job_id: str, job_data: dict, error_reason: str) -> bool:
        """
        Increments retry count. If max retries reached, moves to dead-letter storage.
        Returns: True if job can be retried, False if moved to dead letters.
        """
        self._retry_counts[job_id] = self._retry_counts.get(job_id, 0) + 1
        
        if self._retry_counts[job_id] > self.max_retries:
            self._dead_letters[job_id] = {
                "job_data": job_data,
                "reason": error_reason,
                "failed_at": time.time(),
                "attempts": self._retry_counts[job_id]
            }
            return False

        # Exponential backoff sleep
        backoff = self.base_backoff_sec * (2 ** (self._retry_counts[job_id] - 1))
        time.sleep(min(backoff, 10.0))
        return True

    def mark_success(self, job_id: str):
        """Cleans up retry tracking once a job finishes successfully."""
        if job_id in self._retry_counts:
            del self._retry_counts[job_id]

    def get_dead_letters(self) -> Dict[str, dict]:
        """Returns all unrecoverable jobs."""
        return self._dead_letters
