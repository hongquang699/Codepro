"""
Worker Scheduler and Load Balancer for Judge System Dispatcher.
Selects optimal worker node according to current load and health metrics.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class WorkerNode:
    id: str
    name: str
    host: str
    port: int = 9999
    capacity: int = 2
    active_jobs: int = 0
    max_memory_mb: int = 2048
    supported_languages: List[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time.time)
    is_alive: bool = True

class WorkerScheduler:
    def __init__(self, heartbeat_timeout_sec: float = 30.0, strategy: str = "least_busy"):
        self.workers: Dict[str, WorkerNode] = {}
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.strategy = strategy
        self._round_robin_idx = 0

    def register_worker(self, worker: WorkerNode):
        """Registers or updates a worker node."""
        self.workers[worker.id] = worker

    def update_heartbeat(self, worker_id: str, active_jobs: int = 0):
        """Updates last heartbeat timestamp and active jobs count."""
        if worker_id in self.workers:
            w = self.workers[worker_id]
            w.last_heartbeat = time.time()
            w.active_jobs = active_jobs
            w.is_alive = True

    def get_healthy_workers(self, language: Optional[str] = None) -> List[WorkerNode]:
        """Filters active and healthy workers that have spare capacity."""
        now = time.time()
        healthy = []
        for w in self.workers.values():
            if not w.is_alive:
                continue
            if (now - w.last_heartbeat) > self.heartbeat_timeout_sec:
                w.is_alive = False
                continue
            if w.active_jobs >= w.capacity:
                continue
            if language and w.supported_languages and language not in w.supported_languages:
                continue
            healthy.append(w)
        return healthy

    def select_worker(self, language: Optional[str] = None) -> Optional[WorkerNode]:
        """Selects the best worker based on scheduling strategy."""
        candidates = self.get_healthy_workers(language)
        if not candidates:
            return None

        if self.strategy == "least_busy":
            # Pick worker with smallest active_jobs / capacity ratio
            return min(candidates, key=lambda w: (w.active_jobs / max(1, w.capacity)))

        elif self.strategy == "round_robin":
            self._round_robin_idx = (self._round_robin_idx + 1) % len(candidates)
            return candidates[self._round_robin_idx]

        return candidates[0]
