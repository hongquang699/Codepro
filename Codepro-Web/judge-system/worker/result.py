"""
Judge Result definition for Judge System Workers.
Formats verdict, scores, diagnostic logs, and per-testcase performance.
"""

from dataclasses import dataclass, field
import time
from typing import List, Dict, Any, Optional

@dataclass
class JudgeResult:
    job_id: str
    verdict: str  # AC, WA, TLE, MLE, OLE, RE, CE, SE
    score: float  # Percentage 0.0 - 100.0
    points_earned: float = 0.0
    max_points: float = 100.0
    time_ms: int = 0
    memory_kb: int = 0
    compiler_output: str = ""
    error_message: str = ""
    passed_count: int = 0
    total_count: int = 0
    testcases: List[Dict[str, Any]] = field(default_factory=list)
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "verdict": self.verdict,
            "score": self.score,
            "points_earned": self.points_earned,
            "max_points": self.max_points,
            "time_ms": self.time_ms,
            "memory_kb": self.memory_kb,
            "compiler_output": self.compiler_output,
            "error_message": self.error_message,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "testcases": self.testcases,
            "subtasks": self.subtasks,
            "completed_at": self.completed_at
        }
