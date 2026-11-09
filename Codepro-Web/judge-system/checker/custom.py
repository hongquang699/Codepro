"""
Custom / Special Judge Runner for Judge System.
Supports testlib-compatible checkers or custom Python checker scripts.
"""

import os
import subprocess
import tempfile
from typing import Tuple

class CustomChecker:
    @staticmethod
    def run_custom(
        checker_path: str,
        input_data: str,
        user_output: str,
        expected_output: str,
        time_limit_sec: float = 5.0
    ) -> Tuple[bool, str]:
        """
        Executes a custom checker.
        Supports both testlib binary and .py custom checker scripts.
        Command line convention: checker <input_file> <output_file> <answer_file>
        """
        if not os.path.exists(checker_path):
            return False, f"Checker file not found: {checker_path}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            inp_file = os.path.join(tmp_dir, "input.txt")
            out_file = os.path.join(tmp_dir, "user.out")
            ans_file = os.path.join(tmp_dir, "answer.ans")

            with open(inp_file, "w", encoding="utf-8") as f:
                f.write(input_data)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(user_output)
            with open(ans_file, "w", encoding="utf-8") as f:
                f.write(expected_output)

            # Determine command
            if checker_path.endswith(".py"):
                cmd = ["python", checker_path, inp_file, out_file, ans_file]
            else:
                cmd = [checker_path, inp_file, out_file, ans_file]

            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=time_limit_sec
                )

                # Testlib exit codes:
                # 0 = _ok
                # 1 = _wa
                # 2 = _pe
                # 3 = _fail
                msg = (proc.stderr.strip() or proc.stdout.strip())
                if proc.returncode == 0:
                    return True, msg or "Custom checker: OK"
                elif proc.returncode == 1:
                    return False, f"Custom checker: WA - {msg}"
                elif proc.returncode == 2:
                    return False, f"Custom checker: PE - {msg}"
                else:
                    return False, f"Custom checker failure (exit {proc.returncode}): {msg}"

            except subprocess.TimeoutExpired:
                return False, "Custom checker timed out"
            except Exception as e:
                return False, f"Custom checker execution error: {str(e)}"
