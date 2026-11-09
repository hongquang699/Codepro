"""Contest Anti-cheat engine."""
import time
from typing import Dict, List, Tuple

class AntiCheatEngine:
    # {user: [(ip, timestamp)]}
    _user_activity: Dict[str, List[Tuple[str, float]]] = {}

    @classmethod
    def record_activity(cls, user: str, ip: str) -> List[str]:
        """Detects anomalies such as multiple IPs simultaneously active on same account."""
        warnings = []
        now = time.time()
        history = cls._user_activity.get(user, [])
        # Keep activity within last 5 minutes
        recent = [(prev_ip, t) for prev_ip, t in history if now - t < 300]
        
        distinct_ips = {prev_ip for prev_ip, t in recent if prev_ip != ip}
        if distinct_ips:
            warnings.append(f"Cảnh báo gian lận: Tài khoản {user} đang hoạt động đồng thời từ 2 IP khác nhau: {distinct_ips} và {ip}")

        recent.append((ip, now))
        cls._user_activity[user] = recent
        return warnings
