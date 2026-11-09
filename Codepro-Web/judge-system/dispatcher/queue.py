"""
Submission Queue for Judge System Dispatcher.
Thread-safe priority queue supporting memory and optional Redis backends.
"""

import queue
import time
import threading
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass(order=True)
class PrioritizedJob:
    priority: int  # Lower number = higher priority (e.g. 1 for Contest, 10 for Practice)
    timestamp: float
    job_id: str = field(compare=False)
    data: Dict[str, Any] = field(compare=False)

class SubmissionQueue:
    def __init__(self, backend_type: str = "memory", redis_url: Optional[str] = None):
        self.backend_type = backend_type
        self.redis_url = redis_url
        self._mem_queue = queue.PriorityQueue()
        self._jobs: Dict[str, PrioritizedJob] = {}
        self._lock = threading.RLock()
        self.redis = None
        self._paused = False
        if backend_type == 'redis':
            import redis
            self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()

    @property
    def paused(self):
        return bool(self.redis.get('judge:queue:paused')) if self.redis else self._paused

    @paused.setter
    def paused(self, value):
        if self.redis:
            if value:
                self.redis.set('judge:queue:paused', '1')
            else:
                self.redis.delete('judge:queue:paused')
        else:
            self._paused = bool(value)

    def push(self, job_id: str, data: dict, priority: int = 10):
        """Pushes a submission job to the priority queue."""
        job = PrioritizedJob(
            priority=priority,
            timestamp=time.time(),
            job_id=job_id,
            data=data
        )
        if self.redis:
            with self.redis.pipeline(transaction=True) as pipe:
                pipe.hset('judge:queue:jobs', job_id, json.dumps(job.data))
                pipe.zadd('judge:queue:pending', {job_id: priority * 10_000_000_000 + job.timestamp})
                pipe.execute()
            return
        with self._lock:
            self._jobs[job_id] = job
            self._mem_queue.put(job)

    def pop(self, timeout: Optional[float] = 1.0) -> Optional[dict]:
        """Pops the highest priority job from the queue."""
        if self.paused:
            return None
        if self.redis:
            script = """
            local entry = redis.call('ZPOPMIN', KEYS[1], 1)
            if #entry == 0 then return nil end
            local data = redis.call('HGET', KEYS[2], entry[1])
            redis.call('HDEL', KEYS[2], entry[1])
            return data
            """
            data = self.redis.eval(script, 2, 'judge:queue:pending', 'judge:queue:jobs')
            return json.loads(data) if data else None
        try:
            job: PrioritizedJob = self._mem_queue.get(timeout=timeout)
            with self._lock:
                if self.paused:
                    self._mem_queue.put(job)
                    return None
                if self._jobs.pop(job.job_id, None) is None:
                    return None
                return job.data
        except queue.Empty:
            return None

    def size(self) -> int:
        """Returns the number of jobs waiting in queue."""
        if self.redis:
            return self.redis.zcard('judge:queue:pending')
        with self._lock:
            return len(self._jobs)

    def get_job(self, job_id: str) -> Optional[dict]:
        """Looks up job data by ID."""
        if self.redis:
            data = self.redis.hget('judge:queue:jobs', job_id)
            return json.loads(data) if data else None
        with self._lock:
            job = self._jobs.get(job_id)
            return job.data if job else None

    def list_jobs(self) -> list:
        if self.redis:
            result = []
            for job_id, score in self.redis.zrange('judge:queue:pending', 0, -1, withscores=True):
                data = self.get_job(job_id) or {}
                result.append({'job_id': job_id, 'priority': int(score // 10_000_000_000),
                    'submitted_at': score % 10_000_000_000,
                    'submission_id': data.get('submission_id'),
                    'problem_code': data.get('problem_code'), 'language': data.get('language')})
            return result
        with self._lock:
            return [dict(job_id=j.job_id, priority=j.priority, submitted_at=j.timestamp,
                         submission_id=j.data.get('submission_id'),
                         problem_code=j.data.get('problem_code'), language=j.data.get('language'))
                    for j in sorted(self._jobs.values())]

    def cancel(self, job_id: str) -> bool:
        if self.redis:
            removed = self.redis.zrem('judge:queue:pending', job_id)
            self.redis.hdel('judge:queue:jobs', job_id)
            return bool(removed)
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
