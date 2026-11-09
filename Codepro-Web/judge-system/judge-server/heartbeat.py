"""
Heartbeat Service for Judge Server.
Tracks worker node liveness, load, and health status.
"""

import time
from typing import Dict, List, Any

class HeartbeatManager:
    def __init__(self, timeout_sec: float = 30.0):
        self.timeout_sec = timeout_sec
        self._workers: Dict[str, Dict[str, Any]] = {}

    def record_heartbeat(self, worker_id: str, active_jobs: int = 0, metadata: dict = None, status: str = 'online'):
        """Records a heartbeat from a worker."""
        now = time.time()
        self._workers[worker_id] = {
            "worker_id": worker_id,
            "last_seen": now,
            "active_jobs": active_jobs,
            "status": 'error' if status == 'error' else 'online',
            "metadata": metadata or {}
        }

    def get_all_workers(self) -> List[Dict[str, Any]]:
        """Returns health status of all known workers."""
        now = time.time()
        results = []
        for wid, info in self._workers.items():
            is_alive = (now - info["last_seen"]) <= self.timeout_sec
            results.append({
                "worker_id": wid,
                "status": info['status'] if is_alive else "offline",
                "last_seen_sec_ago": round(now - info["last_seen"], 1),
                "active_jobs": info["active_jobs"],
                "metadata": info["metadata"]
            })
        return results

    def is_worker_alive(self, worker_id: str) -> bool:
        """Checks if a worker is currently online."""
        info = self._workers.get(worker_id)
        if not info:
            return False
        return (time.time() - info["last_seen"]) <= self.timeout_sec
