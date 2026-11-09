"""
Secure process launcher and execution boundary coordinator for Judge Sandbox.
Binds Linux rlimit, privilege dropping, and Seccomp filtering into preexec_fn.
"""

import os
import signal
from typing import Callable, Optional, Dict, Any

from .resource_limits import ResourceLimiter
from .privilege_drop import PrivilegeDropper
from .syscall_policy.seccomp_filter import SeccompFilter

class IsolatedRunnerHelper:
    @staticmethod
    def get_preexec_fn(
        time_limit_sec: float,
        memory_limit_mb: int,
        stack_limit_mb: int = 64,
        max_output_bytes: int = 33554432,
        max_processes: int = 32,
        enable_seccomp: bool = True,
        target_uid: int = 65534,
        target_gid: int = 65534
    ) -> Optional[Callable[[], None]]:
        """
        Returns a callable for subprocess.Popen preexec_fn.
        Executed in the child process immediately after fork() and prior to execve().
        Only applicable on POSIX systems (Linux). Returns None on Windows.
        """
        if os.name == 'nt':
            return None

        def _child_setup():
            # 1. Apply hard POSIX rlimits
            ResourceLimiter.apply_child_limits(
                cpu_time_limit_sec=time_limit_sec,
                memory_limit_mb=memory_limit_mb,
                stack_limit_mb=stack_limit_mb,
                max_output_bytes=max_output_bytes,
                max_processes=max_processes
            )

            # 2. Prevent privilege escalation & drop root privileges
            PrivilegeDropper.drop(target_uid=target_uid, target_gid=target_gid)

            # 3. Apply Seccomp-BPF filter if enabled
            if enable_seccomp:
                SeccompFilter.apply_filter()

        return _child_setup

    @staticmethod
    def interpret_signal_exit(exit_code: int) -> Optional[str]:
        """
        Maps negative exit codes (signals on Unix) to standard Judge verdicts.
        """
        if os.name == 'nt':
            return None

        # Process terminated by signal
        if exit_code < 0:
            sig = -exit_code
            if sig == signal.SIGXCPU:
                return "TLE"
            elif sig == signal.SIGSEGV:
                return "MLE/RE"
            elif hasattr(signal, "SIGXFSZ") and sig == signal.SIGXFSZ:
                return "OLE"
            elif hasattr(signal, "SIGSYS") and sig == signal.SIGSYS:
                return "SEC"  # Terminated by Seccomp BPF due to illegal syscall
            elif sig == signal.SIGFPE:
                return "RE"   # Floating point exception (divide by zero)
            elif sig == signal.SIGKILL:
                return "TLE"  # Killed by timeout watchdog

        return None
