"""
Judge Job definition for Judge System Workers.
Encapsulates all metadata required to execute and evaluate a submission.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class JudgeJob:
    job_id: str
    problem_code: str
    language: str
    source_code: str
    time_limit_sec: float = 1.0
    memory_limit_mb: int = 256
    checker_type: str = "standard"  # "standard", "float", "custom", "line"
    checker_path: Optional[str] = None
    float_epsilon: float = 1e-6
    subtask_mode: bool = False
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    problem_version: Optional[Dict[str, str]] = None
