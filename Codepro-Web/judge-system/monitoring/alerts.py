"""
Alert Manager for Judge System.
Triggers warnings when resources, workers, or queues exceed safety thresholds.
"""

from typing import List, Dict, Any

class AlertManager:
    @staticmethod
    def check_system_alerts(health_stats: dict, worker_stats: dict, queue_size: int) -> List[Dict[str, str]]:
        """
        Evaluates system indicators and generates warnings.
        """
        alerts = []

        # Worker alerts
        if worker_stats.get("online_workers", 0) == 0:
            alerts.append({
                "severity": "CRITICAL",
                "message": "All judge workers are currently OFFLINE! Submissions will stall."
            })

        # Memory alert
        if health_stats.get("memory_usage_percent", 0) > 90.0:
            alerts.append({
                "severity": "WARNING",
                "message": f"High memory usage: {health_stats.get('memory_usage_percent')}%"
            })

        # Disk alert
        if health_stats.get("disk_free_gb", 10.0) < 1.0:
            alerts.append({
                "severity": "CRITICAL",
                "message": f"Low disk space remaining: {health_stats.get('disk_free_gb')} GB"
            })

        # Queue backlog alert
        if queue_size > 50:
            alerts.append({
                "severity": "WARNING",
                "message": f"Queue backlog high: {queue_size} pending submissions."
            })

        return alerts
