"""
Memory measurement and limit enforcement utilities for Judge Sandbox.
Tracks peak resident set size (RSS) and peak working set.
"""

import os
import psutil

class MemoryTracker:
    @staticmethod
    def get_memory_usage_kb(proc: psutil.Process) -> int:
        """Returns current resident memory (RSS) in kilobytes."""
        try:
            mem = proc.memory_info()
            # On Windows, mem.peak_wset or mem.rss
            peak = getattr(mem, 'peak_wset', mem.rss)
            return int(peak / 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    @staticmethod
    def get_tree_memory_usage_kb(pid: int) -> int:
        """Returns aggregate resident memory across process and its children in kilobytes."""
        try:
            parent = psutil.Process(pid)
            total = MemoryTracker.get_memory_usage_kb(parent)
            for child in parent.children(recursive=True):
                total += MemoryTracker.get_memory_usage_kb(child)
            return total
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0
