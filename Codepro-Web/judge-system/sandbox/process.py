"""
Process execution controller for Judge Sandbox.
Manages low-level process creation, input/output piping, timeout handling,
and real-time memory monitoring.
"""

import subprocess
import time
import os
import tempfile
import psutil
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class ProcessExecutionResult:
    exit_code: int
    time_ms: int
    memory_kb: int
    stdout: str
    stderr: str
    is_tle: bool
    is_mle: bool
    is_ole: bool
    is_sec: bool = False

try:
    from security.judge_security.isolated_runner import IsolatedRunnerHelper
except ImportError:
    import sys
    sys_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if sys_parent not in sys.path:
        sys.path.insert(0, sys_parent)
    try:
        from security.judge_security.isolated_runner import IsolatedRunnerHelper
    except ImportError:
        IsolatedRunnerHelper = None

class ProcessRunner:
    @staticmethod
    def kill_process_tree(pid: int):
        """Recursively terminates a process and all its children."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    @classmethod
    def run_process(
        cls,
        cmd: list,
        stdin_data: str = "",
        time_limit_sec: float = 1.0,
        memory_limit_mb: int = 256,
        output_limit_bytes: int = 33554432, # 32 MB
        cwd: Optional[str] = None,
        env: Optional[dict] = None
    ) -> ProcessExecutionResult:
        """
        Executes a process with strict resource monitoring.
        """
        # Contestant processes receive only runtime settings, never manager
        # credentials such as JUDGE_AUTH_TOKEN or database connection secrets.
        run_env = {
            key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TZ', 'SYSTEMROOT', 'WINDIR', 'TMP', 'TEMP', 'TMPDIR', 'HOME', 'USERPROFILE')
            if key in os.environ
        }
        if env:
            allowed_overrides = {'LANG', 'LC_ALL', 'TZ', 'PYTHONPATH', 'JAVA_TOOL_OPTIONS'}
            run_env.update({key: value for key, value in env.items() if key in allowed_overrides})

        start_wall_time = time.time()
        start_cpu_time = 0.0
        peak_memory_kb = 0
        is_tle = False
        is_mle = False
        is_ole = False
        is_sec = False

        memory_limit_kb = memory_limit_mb * 1024

        preexec = None
        if IsolatedRunnerHelper and os.name != "nt":
            try:
                preexec = IsolatedRunnerHelper.get_preexec_fn(
                    time_limit_sec=time_limit_sec,
                    memory_limit_mb=memory_limit_mb,
                    max_output_bytes=output_limit_bytes
                )
            except Exception:
                preexec = None

        stdout_file = tempfile.TemporaryFile(mode='w+b')
        stderr_file = tempfile.TemporaryFile(mode='w+b')
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                env=run_env,
                preexec_fn=preexec
            )
        except Exception as e:
            stdout_file.close()
            stderr_file.close()
            return ProcessExecutionResult(
                exit_code=-1,
                time_ms=0,
                memory_kb=0,
                stdout="",
                stderr=str(e),
                is_tle=False,
                is_mle=False,
                is_ole=False,
                is_sec=False
            )

        ps_proc = None
        try:
            ps_proc = psutil.Process(proc.pid)
            start_cpu_time = ps_proc.cpu_times().user + ps_proc.cpu_times().system
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # Communicate writes stdin while stdout and stderr go to bounded files.
        import threading

        result_container = {"exc": None}

        def comm_worker():
            try:
                proc.communicate(input=stdin_data)
            except Exception as ex:
                result_container["exc"] = ex

        comm_thread = threading.Thread(target=comm_worker, daemon=True)
        comm_thread.start()

        # Polling loop
        poll_interval = 0.015  # 15 ms
        cpu_time_spent = 0.0

        while comm_thread.is_alive():
            elapsed_wall = time.time() - start_wall_time

            if os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size > output_limit_bytes:
                is_ole = True
                cls.kill_process_tree(proc.pid)
                break

            # Check TLE by wall time (with 2x safety margin) or cpu time
            if elapsed_wall > (time_limit_sec + 0.5):
                is_tle = True
                cls.kill_process_tree(proc.pid)
                break

            # Poll memory and CPU
            if ps_proc and ps_proc.is_running():
                try:
                    # Current process + children memory
                    cur_mem_kb = int(ps_proc.memory_info().rss / 1024)
                    for child in ps_proc.children(recursive=True):
                        cur_mem_kb += int(child.memory_info().rss / 1024)
                    
                    if cur_mem_kb > peak_memory_kb:
                        peak_memory_kb = cur_mem_kb

                    if peak_memory_kb > memory_limit_kb:
                        is_mle = True
                        cls.kill_process_tree(proc.pid)
                        break

                    # CPU time
                    c_times = ps_proc.cpu_times()
                    cpu_time_spent = (c_times.user + c_times.system) - start_cpu_time
                    if cpu_time_spent > time_limit_sec:
                        is_tle = True
                        cls.kill_process_tree(proc.pid)
                        break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            time.sleep(poll_interval)

        comm_thread.join(timeout=0.5)

        # Finalize
        stdout_file.seek(0)
        stderr_file.seek(0)
        total_output_bytes = os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size
        stdout_bytes = stdout_file.read(output_limit_bytes + 1)
        stderr_bytes = stderr_file.read(max(0, output_limit_bytes - len(stdout_bytes)) + 1)
        raw_stdout = stdout_bytes.decode('utf-8', errors='replace')
        raw_stderr = stderr_bytes.decode('utf-8', errors='replace')
        stdout_file.close()
        stderr_file.close()

        if total_output_bytes > output_limit_bytes:
            is_ole = True
            raw_stdout = raw_stdout[:1000] + "\n...[OUTPUT TRUNCATED - OLE]..."
            raw_stderr = raw_stderr[:1000]

        # Calculate final execution time in ms
        time_ms = int(max(cpu_time_spent, time.time() - start_wall_time) * 1000)

        # Baseline memory floor for process runtime
        if peak_memory_kb < 1024:
            peak_memory_kb = 1024

        # Check signals on POSIX systems (e.g. SIGXCPU, SIGSYS, SIGSEGV)
        if IsolatedRunnerHelper and proc.returncode is not None:
            sig_verdict = IsolatedRunnerHelper.interpret_signal_exit(proc.returncode)
            if sig_verdict == "TLE":
                is_tle = True
            elif sig_verdict == "SEC":
                is_sec = True
            elif sig_verdict == "OLE":
                is_ole = True
            elif sig_verdict == "MLE/RE" and peak_memory_kb >= (memory_limit_kb * 0.9):
                is_mle = True

        return ProcessExecutionResult(
            exit_code=proc.returncode if proc.returncode is not None else -1,
            time_ms=time_ms,
            memory_kb=peak_memory_kb,
            stdout=raw_stdout,
            stderr=raw_stderr,
            is_tle=is_tle,
            is_mle=is_mle,
            is_ole=is_ole,
            is_sec=is_sec
        )
