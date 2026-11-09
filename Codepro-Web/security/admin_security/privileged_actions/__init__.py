"""Guard for destructive operations."""
import time
from typing import Dict, Tuple
from security.logging import SecurityLogger

class PrivilegedActionGuard:
    _rate_limits: Dict[str, float] = {}

    CRITICAL_ACTIONS = {
        'DELETE_PROBLEM', 'BULK_REJUDGE', 'PURGE_SUBMISSIONS', 'BAN_USER'
    }

    @classmethod
    def can_perform(cls, admin: str, action: str, resource_id: str, ip: str) -> Tuple[bool, str]:
        key = f"{admin}:{action}"
        now = time.time()
        last = cls._rate_limits.get(key, 0)
        # 3 seconds throttle between consecutive critical actions
        if now - last < 3.0:
            return False, "Thao tác quá nhanh. Vui lòng đợi vài giây."

        cls._rate_limits[key] = now
        SecurityLogger.log_admin(admin, action, 'RESOURCE', resource_id, ip, 'APPROVED')
        return True, "Thao tác được phê duyệt."
