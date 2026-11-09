"""
System Health Monitoring for Judge System.
Monitors CPU load, memory utilization, and storage disk space.
"""

import shutil
import psutil
from typing import Dict, Any

class SystemHealth:
    @staticmethod
    def get_system_stats(storage_path: str = "./storage") -> Dict[str, Any]:
        """Returns host machine metrics and disk free space."""
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        disk_usage = shutil.disk_usage(storage_path)
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 2)
        disk_total_gb = round(disk_usage.total / (1024 ** 3), 2)

        return {
            "cpu_usage_percent": cpu_pct,
            "memory_usage_percent": mem.percent,
            "memory_available_mb": round(mem.available / (1024 ** 2), 1),
            "disk_free_gb": disk_free_gb,
            "disk_total_gb": disk_total_gb,
            "is_healthy": (cpu_pct < 95.0 and mem.percent < 95.0 and disk_free_gb > 0.5)
        }
