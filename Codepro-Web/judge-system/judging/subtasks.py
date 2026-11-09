"""
Subtask Judge Orchestrator for Judge System.
Evaluates submissions across grouped subtasks and dependency graphs.
"""

from typing import List, Dict, Any
from testcase.subtask import SubtaskInfo, SubtaskEvaluator
from .verdict import Verdict

class SubtaskJudge:
    @staticmethod
    def evaluate_subtasks(
        subtasks: List[SubtaskInfo],
        testcase_results: Dict[int, dict] # tc_id -> { verdict, score, ... }
    ) -> Dict[str, Any]:
        """
        Calculates scores and verdicts for all subtasks taking dependencies into account.
        """
        subtask_scores = {}
        subtask_verdicts = {}
        subtask_details = []

        total_points = sum(st.points for st in subtasks)
        total_earned = 0.0

        for st in subtasks:
            # Check dependencies
            dep_failed = any(subtask_scores.get(dep_id, 0.0) <= 0.0 for dep_id in st.depends_on)
            
            st_cases = [testcase_results.get(tc.id, {}) for tc in st.testcases]
            st_verdicts = [c.get("verdict", Verdict.SE) for c in st_cases]

            if dep_failed:
                earned = 0.0
                st_verdict = Verdict.WA
                comment = f"Skipped due to failed dependency on subtask {st.depends_on}"
            else:
                earned = SubtaskEvaluator.calculate_subtask_score(
                    subtask=st,
                    testcase_results=testcase_results,
                    parent_subtask_scores=subtask_scores
                )
                st_verdict = Verdict.AC if earned >= st.points else Verdict.get_worst(st_verdicts)
                comment = "Evaluated"

            subtask_scores[st.subtask_id] = earned
            subtask_verdicts[st.subtask_id] = st_verdict
            total_earned += earned

            subtask_details.append({
                "subtask_id": st.subtask_id,
                "points": st.points,
                "earned": earned,
                "verdict": st_verdict,
                "status": comment,
                "testcase_count": len(st.testcases)
            })

        overall_verdict = Verdict.AC if total_earned >= total_points else Verdict.get_worst(list(subtask_verdicts.values()))

        return {
            "verdict": overall_verdict,
            "total_earned": round(total_earned, 2),
            "max_points": total_points,
            "score": round((total_earned / max(1.0, total_points)) * 100.0, 1),
            "subtasks": subtask_details
        }
