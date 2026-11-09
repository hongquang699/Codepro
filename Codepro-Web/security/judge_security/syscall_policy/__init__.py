"""Seccomp system call whitelist policy."""
from typing import Set

ALLOWED_SYSCALLS: Set[str] = {
    'read', 'write', 'open', 'openat', 'close', 'fstat', 'lstat', 'poll',
    'lseek', 'mmap', 'mprotect', 'munmap', 'brk', 'rt_sigaction', 'rt_sigprocmask',
    'rt_sigreturn', 'ioctl', 'access', 'faccessat', 'pipe', 'pipe2', 'select',
    'sched_yield', 'nanosleep', 'getpid', 'gettid', 'exit', 'exit_group', 'futex',
    'set_robust_list', 'get_robust_list', 'clock_gettime', 'arch_prctl'
}

BLOCKED_DANGEROUS_SYSCALLS: Set[str] = {
    'socket', 'connect', 'bind', 'listen', 'accept', 'sendto', 'recvfrom',
    'clone', 'clone3', 'fork', 'vfork', 'execve', 'execveat', 'ptrace',
    'kill', 'tkill', 'tgkill', 'reboot', 'setuid', 'setgid', 'chroot'
}

class SyscallPolicy:
    @staticmethod
    def is_syscall_allowed(name: str) -> bool:
        return name in ALLOWED_SYSCALLS and name not in BLOCKED_DANGEROUS_SYSCALLS
