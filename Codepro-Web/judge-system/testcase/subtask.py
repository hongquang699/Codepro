"""
Subtask Management and Scoring models for Judge System.
Supports IOI-style subtask points, dependencies, and grouping.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TestCaseInfo:
    id: int
    name: str
    input_data: str
    expected_output: str
    subtask_id: int = 1
    points: float = 10.0
    time_limit_sec: float = 1.0
    memory_limit_mb: int = 256

@dataclass
class SubtaskInfo:
    subtask_id: int
    points: float
    scoring_method: str = "all_or_nothing" # "all_or_nothing", "sum", "min"
    depends_on: List[int] = field(default_factory=list)
    testcases: List[TestCaseInfo] = field(default_factory=list)

class SubtaskEvaluator:
    @staticmethod
    def calculate_subtask_score(
        subtask: SubtaskInfo,
        testcase_results: Dict[int, dict], # testcase_id -> { "verdict": "AC", "score": float, ... }
        parent_subtask_scores: Dict[int, float] # parent_id -> score
    ) -> float:
        """
        Calculates score earned for a subtask based on scoring method and dependencies.
        """
        # If dependency fails, subtask earns 0
        for dep_id in subtask.depends_on:
            if parent_subtask_scores.get(dep_id, 0.0) <= 0.0:
                return 0.0

        if not subtask.testcases:
            return 0.0

        if subtask.scoring_method == "all_or_nothing":
            all_ac = all(
                testcase_results.get(tc.id, {}).get("verdict") == "AC"
                for tc in subtask.testcases
            )
            return float(subtask.points) if all_ac else 0.0

        elif subtask.scoring_method == "sum":
            earned = sum(
                testcase_results.get(tc.id, {}).get("score", 0.0)
                for tc in subtask.testcases
            )
            return min(float(subtask.points), earned)

        elif subtask.scoring_method == "min":
            min_ratio = min(
                (testcase_results.get(tc.id, {}).get("score", 0.0) / max(tc.points, 1.0))
                for tc in subtask.testcases
            )
            return float(subtask.points) * max(0.0, min_ratio)

        return 0.0
