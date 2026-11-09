"""
Testcase Runner: Runs executable against problem testcases and tracks verdicts.
"""
import sys
import os
from typing import Dict, Any
from .runner import Runner
from .checker import Checker


class TestcaseRunner:
    def __init__(self, runner: Runner = None, checker: Checker = None):
        self.runner = runner or Runner()
        self.checker = checker or Checker()

    def run_testcase(self, executable_path: str, language: str, testcase: Dict[str, Any], time_limit: float = 1.0, memory_limit_mb: int = 256) -> Dict[str, Any]:
        """
        Executes a single testcase and determines individual verdict.
        """
        test_id = testcase.get("id", 1)
        inp = testcase.get("input", "")
        expected = testcase.get("expected_output", "")
        points = testcase.get("points", 10)
        is_hidden = testcase.get("is_hidden", False)

        lang = language.lower()
        if "py" in lang:
            cmd = [sys.executable, executable_path]
        elif "java" in lang:
            work_dir = os.path.dirname(executable_path)
            cmd = ["java", "-cp", work_dir, "Main"]
        else:
            cmd = [executable_path]

        exec_res = self.runner.run_process(cmd, inp, time_limit=time_limit, memory_limit_mb=memory_limit_mb)

        verdict = "AC"
        score = 0
        message = ""

        if exec_res["timeout"]:
            verdict = "TLE"
            message = f"Time Limit Exceeded (> {time_limit}s)"
        elif exec_res["runtime_error"]:
            verdict = "RTE"
            message = f"Runtime Error (exit code {exec_res['returncode']})"
            if exec_res["stderr"]:
                message += f": {exec_res['stderr'][:100]}"
        elif exec_res["memory_kb"] > memory_limit_mb * 1024:
            verdict = "MLE"
            message = f"Memory Limit Exceeded (> {memory_limit_mb} MB)"
        else:
            is_ok, check_msg = self.checker.check(exec_res["stdout"], expected)
            if is_ok:
                verdict = "AC"
                score = points
                message = check_msg
            else:
                verdict = "WA"
                message = check_msg

        return {
            "test_number": test_id,
            "verdict": verdict,
            "time_ms": exec_res["time_ms"],
            "memory_kb": exec_res["memory_kb"],
            "score": score,
            "message": message,
            "is_hidden": is_hidden,
            "input": "" if is_hidden else inp[:500],
            "output": exec_res["stdout"][:500] if not is_hidden else "",
            "expected": expected[:500] if not is_hidden else ""
        }
