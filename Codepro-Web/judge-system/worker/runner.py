"""
Worker Testcase Runner for Judge System.
Executes testcases and performs comparison checks.
"""

from typing import Dict, Any
from judging.execute import Executor, TestcaseExecutionResult
from judging.compare import Comparator
from judging.verdict import Verdict
from testcase.subtask import TestCaseInfo

class WorkerRunner:
    def __init__(self):
        self.executor = Executor()

    def run_case(
        self,
        language: str,
        binary_or_script: str,
        testcase: TestCaseInfo,
        checker_type: str = "standard",
        checker_path: str = None,
        float_epsilon: float = 1e-6
    ) -> Dict[str, Any]:
        """
        Runs a single testcase and compares results.
        """
        # Execute in sandbox
        exec_res: TestcaseExecutionResult = self.executor.run_testcase(
            language=language,
            target_path=binary_or_script,
            input_data=testcase.input_data,
            time_limit_sec=testcase.time_limit_sec,
            memory_limit_mb=testcase.memory_limit_mb
        )

        # If sandbox caught a non-OK verdict (TLE, MLE, OLE, RE)
        if exec_res.verdict != "OK":
            return {
                "id": testcase.id,
                "name": testcase.name,
                "verdict": exec_res.verdict,
                "time_ms": exec_res.time_ms,
                "memory_kb": exec_res.memory_kb,
                "score": 0.0,
                "max_points": testcase.points,
                "message": exec_res.message,
                "output_preview": exec_res.user_output[:200]
            }

        # Sandbox completed normally -> run checker
        is_ok, check_msg = Comparator.compare(
            user_output=exec_res.user_output,
            expected_output=testcase.expected_output,
            input_data=testcase.input_data,
            checker_type=checker_type,
            checker_path=checker_path,
            float_epsilon=float_epsilon
        )

        verdict = Verdict.AC if is_ok else Verdict.WA
        score = testcase.points if is_ok else 0.0

        return {
            "id": testcase.id,
            "name": testcase.name,
            "verdict": verdict,
            "time_ms": exec_res.time_ms,
            "memory_kb": exec_res.memory_kb,
            "score": score,
            "max_points": testcase.points,
            "message": check_msg,
            "output_preview": exec_res.user_output[:200]
        }
