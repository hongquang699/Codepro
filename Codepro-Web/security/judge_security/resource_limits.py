"""
Resource limits configuration and POSIX rlimit enforcer for Judge Sandboxes.
Provides safe containment boundaries for process execution.
"""

import os
from typing import Dict, Any, Optional

try:
    import resource
except ImportError:
    resource = None

class ResourceLimiter:
    @staticmethod
    def get_default_limits(time_limit_sec: float = 1.0, memory_limit_mb: int = 256) -> Dict[str, Any]:
        """Calculates containment boundaries for student executable."""
        return {
            'cpu_time_limit_sec': float(time_limit_sec),
            'real_time_limit_sec': float(time_limit_sec * 2.5 + 1.0),
            'memory_limit_bytes': int(memory_limit_mb * 1024 * 1024),
            'stack_limit_bytes': 64 * 1024 * 1024,      # 64MB stack
            'max_processes': 1,                         # Prevent fork bombs
            'max_file_size_bytes': 32 * 1024 * 1024,    # 32MB max stdout/stderr
            'target_uid': 65534,                        # 'nobody' user
            'target_gid': 65534
        }

    @staticmethod
    def apply_child_limits(
        cpu_time_limit_sec: float,
        memory_limit_mb: int,
        stack_limit_mb: int = 64,
        max_output_bytes: int = 33554432,
        max_processes: int = 1
    ):
        """
        Executed inside the child process (preexec_fn) right after fork and before execve.
        Applies hard kernel rlimits on POSIX systems.
        """
        if resource is None or os.name == 'nt':
            return  # Windows does not have POSIX resource limits; handled by runner watchdog

        # 1. CPU Time (Soft limit sends SIGXCPU, hard limit terminates)
        cpu_sec = max(1, int(cpu_time_limit_sec))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_sec, cpu_sec + 1))

        # 2. Virtual Memory / Address Space (RLIMIT_AS)
        mem_bytes = int(memory_limit_mb * 1024 * 1024)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            pass

        # 3. Stack Size
        stack_bytes = int(stack_limit_mb * 1024 * 1024)
        try:
            resource.setrlimit(resource.RLIMIT_STACK, (stack_bytes, stack_bytes))
        except (ValueError, OSError):
            pass

        # 4. Maximum output file size (protect against filling disk)
        try:
            resource.setrlimit(resource.RLIMIT_FSIZE, (max_output_bytes, max_output_bytes))
        except (ValueError, OSError):
            pass

        # 5. Maximum number of processes (Fork bomb protection)
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (max_processes, max_processes))
        except (ValueError, OSError):
            pass

        # 6. Disable core dumps
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (ValueError, OSError):
            pass
