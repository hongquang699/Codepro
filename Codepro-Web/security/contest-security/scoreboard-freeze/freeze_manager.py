"""Contest scoreboard freeze manager."""
import time
from typing import Tuple

class ScoreboardFreezeManager:
    @staticmethod
    def is_scoreboard_frozen(start_timestamp: float, duration_seconds: int, freeze_seconds_before_end: int = 3600) -> Tuple[bool, float]:
        """Calculates if the scoreboard is currently frozen. Returns (is_frozen, time_remaining)."""
        now = time.time()
        end_timestamp = start_timestamp + duration_seconds
        freeze_start = end_timestamp - freeze_seconds_before_end

        if now < start_timestamp:
            return False, duration_seconds
        if now >= end_timestamp:
            return False, 0.0  # Contest ended, scoreboard unfrozen
        
        is_frozen = (now >= freeze_start)
        remaining = max(0.0, end_timestamp - now)
        return is_frozen, remaining
