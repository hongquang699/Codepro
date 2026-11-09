"""
Linux Seccomp-BPF Syscall Filter for Judge Sandbox.
Enforces whitelist policy: any non-whitelisted syscall is terminated immediately.
"""

import os
from typing import List, Optional
from . import ALLOWED_SYSCALLS, BLOCKED_DANGEROUS_SYSCALLS

try:
    import seccomp
except ImportError:
    seccomp = None

class SeccompFilter:
    @classmethod
    def is_available(cls) -> bool:
        """Checks if seccomp python module is available in current environment."""
        return seccomp is not None and os.name != 'nt'

    @classmethod
    def apply_filter(cls, extra_allowed: Optional[List[str]] = None) -> bool:
        """
        Installs seccomp BPF filter on current thread/process.
        Must be called in child preexec_fn before executing untrusted code.
        """
        if not cls.is_available():
            return False

        try:
            # Default action: kill process if it attempts an unauthorized syscall
            f = seccomp.SyscallFilter(defaction=seccomp.KILL_PROCESS)

            allowed = set(ALLOWED_SYSCALLS)
            if extra_allowed:
                allowed.update(extra_allowed)

            # Ensure dangerous syscalls are explicitly prohibited
            allowed.difference_update(BLOCKED_DANGEROUS_SYSCALLS)

            for sc_name in allowed:
                try:
                    f.add_rule(seccomp.ALLOW, sc_name)
                except (ValueError, OSError):
                    # Syscall may not exist on this specific architecture/kernel version
                    continue

            f.load()
            return True
        except Exception:
            return False
