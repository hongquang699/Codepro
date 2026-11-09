"""
Central Job Dispatcher for Judge System.
Pulls submissions from the queue, balances load, routes to workers, and monitors execution.
"""

import time
import threading
import logging
from typing import Optional, Callable
from .queue import SubmissionQueue
from .scheduler import WorkerScheduler, WorkerNode
from .retry import RetryManager

logger = logging.getLogger("JudgeDispatcher")

class Dispatcher:
    def __init__(
        self,
        queue: SubmissionQueue,
        scheduler: WorkerScheduler,
        retry_mgr: RetryManager,
        dispatch_handler: Optional[Callable[[str, dict, WorkerNode], None]] = None
    ):
        self.queue = queue
        self.scheduler = scheduler
        self.retry_mgr = retry_mgr
        self.dispatch_handler = dispatch_handler
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the background dispatcher loop."""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Judge Dispatcher started.")

    def stop(self):
        """Stops the dispatcher loop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Judge Dispatcher stopped.")

    def _run_loop(self):
        while self._running:
            job_data = self.queue.pop(timeout=0.5)
            if not job_data:
                continue

            job_id = str(job_data.get("job_id") or job_data.get("submission_id"))
            language = job_data.get("language", "cpp")

            # Find worker
            worker = self.scheduler.select_worker(language=language)
            if not worker:
                # No worker available right now, requeue or retry
                logger.warning(f"No available workers for job {job_id}. Requeueing...")
                can_retry = self.retry_mgr.record_failure(job_id, job_data, "No available worker")
                if can_retry:
                    self.queue.push(job_id, job_data, priority=job_data.get("priority", 10))
                time.sleep(1.0)
                continue

            # Assign and dispatch
            worker.active_jobs += 1
            logger.info(f"Dispatched job {job_id} to worker {worker.id} ({worker.name})")

            try:
                if self.dispatch_handler:
                    # Run async or pass to worker callback
                    threading.Thread(
                        target=self._safe_dispatch,
                        args=(job_id, job_data, worker),
                        daemon=True
                    ).start()
                else:
                    logger.warning(f"No dispatch handler configured for job {job_id}")
            except Exception as e:
                logger.error(f"Dispatch failed for {job_id}: {str(e)}")
                worker.active_jobs = max(0, worker.active_jobs - 1)
                if self.retry_mgr.record_failure(job_id, job_data, str(e)):
                    self.queue.push(job_id, job_data, priority=job_data.get("priority", 10))

    def _safe_dispatch(self, job_id: str, job_data: dict, worker: WorkerNode):
        try:
            self.dispatch_handler(job_id, job_data, worker)
            self.retry_mgr.mark_success(job_id)
        except Exception as e:
            logger.error(f"Execution error on worker {worker.id} for job {job_id}: {str(e)}")
            if self.retry_mgr.record_failure(job_id, job_data, str(e)):
                self.queue.push(job_id, job_data, priority=job_data.get("priority", 10))
        finally:
            worker.active_jobs = max(0, worker.active_jobs - 1)
