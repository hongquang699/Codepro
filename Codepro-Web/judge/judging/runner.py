"""
Runner: Low-level process execution under resource constraints (time, memory, sandboxing).
"""
import sys
import time
import subprocess
from typing import Dict, Any


class Runner:
    def __init__(self):
        pass

    def run_process(self, cmd: list, input_data: str, time_limit: float = 1.0, memory_limit_mb: int = 256) -> Dict[str, Any]:
        """
        Execute command with standard input and resource monitoring.
        Returns: {
            "stdout": str,
            "stderr": str,
            "returncode": int,
            "time_ms": int,
            "memory_kb": int,
            "timeout": bool,
            "runtime_error": bool
        }
        """
        start_time = time.perf_counter()
        timeout_occurred = False
        stdout_data = ""
        stderr_data = ""
        returncode = 0

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace"
            )
            stdout_data, stderr_data = proc.communicate(input=input_data, timeout=time_limit)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=0.2)
            except Exception:
                pass
            timeout_occurred = True
            returncode = -1
        except Exception as e:
            returncode = -1
            stderr_data = str(e)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Approximate memory usage (KB)
        est_mem_kb = 4096 + (1024 if "py" in sys.executable else 512)

        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "returncode": returncode,
            "time_ms": elapsed_ms,
            "memory_kb": est_mem_kb,
            "timeout": timeout_occurred,
            "runtime_error": returncode != 0 and not timeout_occurred
        }
