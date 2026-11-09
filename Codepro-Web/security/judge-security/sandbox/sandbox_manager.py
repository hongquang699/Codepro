"""Judge Sandbox security coordinator."""
from typing import Dict, Any

class SandboxSecurityManager:
    @staticmethod
    def get_sandbox_limits(time_limit_sec: float = 1.0, memory_limit_mb: int = 256) -> Dict[str, Any]:
        """Calculates hard containment boundaries for student executable."""
        return {
            'cpu_time_limit_sec': float(time_limit_sec),
            'real_time_limit_sec': float(time_limit_sec * 2.5 + 1.0),
            'memory_limit_bytes': int(memory_limit_mb * 1024 * 1024),
            'stack_limit_bytes': 64 * 1024 * 1024,   # 64MB stack
            'max_processes': 1,                     # Fork bomb prevention
            'max_file_size_bytes': 32 * 1024 * 1024, # 32MB max stdout/stderr
            'network_disabled': True,
            'drop_privileges': True,
            'target_uid': 10001,
            'target_gid': 10001
        }
