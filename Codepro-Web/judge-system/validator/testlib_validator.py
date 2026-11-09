"""
Testlib-compatible Input Validator for Judge System.
Runs compiled validator executable or Python script to verify input bounds and formats.
"""

import subprocess
import os
import tempfile
from typing import Tuple

class TestlibValidator:
    @staticmethod
    def validate(validator_path: str, input_data: str, timeout_sec: float = 5.0) -> Tuple[bool, str]:
        """
        Runs the testlib validator binary or python script on testcase input.
        """
        if not os.path.exists(validator_path):
            return False, f"Validator file not found: {validator_path}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = os.path.join(tmp_dir, "input.in")
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(input_data)

            if validator_path.endswith(".py"):
                cmd = ["python", validator_path, input_file]
            else:
                cmd = [validator_path, input_file]

            try:
                proc = subprocess.run(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_sec
                )

                if proc.returncode == 0:
                    return True, "Input testcase is valid"
                else:
                    err_msg = proc.stderr.strip() or proc.stdout.strip()
                    return False, f"Validation error (code {proc.returncode}): {err_msg}"
            except subprocess.TimeoutExpired:
                return False, "Validator timed out"
            except Exception as e:
                return False, f"Validator error: {str(e)}"
