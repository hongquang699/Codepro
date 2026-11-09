"""
CPU measurement utilities for Judge Sandbox.
Measures process user and system CPU times.
"""

import time
import os
import psutil

class CpuTracker:
    @staticmethod
    def get_cpu_time(proc: psutil.Process) -> float:
        """Returns total user + system CPU time consumed by the process in seconds."""
        try:
            times = proc.cpu_times()
            return times.user + times.system
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    @staticmethod
    def get_total_tree_cpu(pid: int) -> float:
        """Calculates total CPU time across process and all its children."""
        try:
            parent = psutil.Process(pid)
            total = CpuTracker.get_cpu_time(parent)
            for child in parent.children(recursive=True):
                total += CpuTracker.get_cpu_time(child)
            return total
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0
