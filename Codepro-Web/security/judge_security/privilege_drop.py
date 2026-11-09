"""
Privilege dropping and privilege escalation protection for Judge Sandbox.
Sets PR_SET_NO_NEW_PRIVS and demotes execution to an unprivileged user (UID/GID 65534).
"""

import os
import ctypes
from typing import Optional

PR_SET_NO_NEW_PRIVS = 38

class PrivilegeDropper:
    @staticmethod
    def drop(target_uid: int = 65534, target_gid: int = 65534):
        """
        Executed in child preexec_fn on POSIX systems.
        Prevents privilege escalation and drops root permissions if present.
        """
        if os.name == 'nt':
            return  # Windows: handled via job object or low-integrity token if needed

        # 1. Enable PR_SET_NO_NEW_PRIVS
        # Ensures that execve will never grant child processes additional privileges (e.g. via setuid)
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        if not hasattr(libc, "prctl") or libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "Could not set no_new_privs")

        # 2. Drop user privileges if running as root
        if hasattr(os, "getuid") and os.getuid() == 0:
            if hasattr(os, "setgroups"):
                os.setgroups([])
            os.setgid(target_gid)
            os.setuid(target_uid)
            if os.getuid() != target_uid or os.getgid() != target_gid:
                raise RuntimeError("Could not drop judge process privileges")
