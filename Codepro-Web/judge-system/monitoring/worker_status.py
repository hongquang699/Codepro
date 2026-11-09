"""
Worker Status Monitor for Judge System.
Aggregates worker availability, capacity, and active load factors.
"""

from typing import List, Dict, Any

class WorkerStatusMonitor:
    @staticmethod
    def evaluate_status(workers_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a list of worker health records.
        """
        total = len(workers_list)
        online = sum(1 for w in workers_list if w.get("status") == "online")
        offline = total - online
        active_jobs = sum(w.get("active_jobs", 0) for w in workers_list)

        return {
            "total_workers": total,
            "online_workers": online,
            "offline_workers": offline,
            "current_active_jobs": active_jobs,
            "availability_ratio": round(online / max(1, total), 2)
        }
