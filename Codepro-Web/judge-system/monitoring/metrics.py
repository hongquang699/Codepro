"""
Metrics Collector for Judge System.
Tracks verdict distributions, evaluation latency, and judge throughput.
"""

import time
from typing import Dict, Any

class JudgeMetrics:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(JudgeMetrics, cls).__new__(cls)
            cls._instance.total_judged = 0
            cls._instance.verdict_counts = {
                "AC": 0, "WA": 0, "TLE": 0, "MLE": 0,
                "OLE": 0, "RE": 0, "CE": 0, "SE": 0
            }
            cls._instance.total_execution_time_ms = 0
            cls._instance.start_time = time.time()
        return cls._instance

    def record_job(self, verdict: str, time_ms: int):
        """Records metrics for a completed judging task."""
        self.total_judged += 1
        self.verdict_counts[verdict] = self.verdict_counts.get(verdict, 0) + 1
        self.total_execution_time_ms += time_ms

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistical overview of judging performance."""
        uptime = round(time.time() - self.start_time, 1)
        avg_time = (
            round(self.total_execution_time_ms / self.total_judged, 1)
            if self.total_judged > 0 else 0.0
        )
        ac_count = self.verdict_counts.get("AC", 0)
        ac_rate = (
            round((ac_count / self.total_judged) * 100.0, 1)
            if self.total_judged > 0 else 0.0
        )

        return {
            "uptime_seconds": uptime,
            "total_judged": self.total_judged,
            "ac_rate_percent": ac_rate,
            "average_time_ms": avg_time,
            "verdicts": self.verdict_counts
        }
