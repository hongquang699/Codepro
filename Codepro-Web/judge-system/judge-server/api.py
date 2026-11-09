"""
REST API Router and Handlers for Judge Server.
Provides endpoints for submissions, status polling, worker heartbeats, and metrics.
"""

import json
import uuid
import time
import re
from typing import Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
try:
    from .authentication import Authenticator
    from .heartbeat import HeartbeatManager
except ImportError:
    from authentication import Authenticator
    from heartbeat import HeartbeatManager
from dispatcher.queue import SubmissionQueue

class JudgeApiRouter:
    def __init__(
        self,
        authenticator: Authenticator,
        heartbeat_mgr: HeartbeatManager,
        queue: SubmissionQueue,
        results_store: Dict[str, dict],
        limits: dict = None,
    ):
        self.auth = authenticator
        self.heartbeat = heartbeat_mgr
        self.queue = queue
        self.results = results_store
        self.limits = (limits or {}).get('limits', {})
        self.worker_modes = {}  # Manager-owned dispatch policy; never launches processes.

    def handle(self, method: str, path: str, headers: dict, body: bytes) -> Tuple[int, dict]:
        """
        Routes incoming HTTP request and returns (status_code, response_dict).
        """
        parsed_url = urlparse(path)
        clean_path = parsed_url.path.rstrip("/")
        query_params = parse_qs(parsed_url.query)

        # Health endpoint doesn't require auth
        if clean_path == "/api/v1/health" and method == "GET":
            return 200, {
                "status": "healthy",
                "timestamp": time.time(),
                "queue_size": self.queue.size(),
                "completed_results": len(self.results)
            }

        # Check Authentication
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if not self.auth.verify_auth_header(auth_header):
            return 401, {"error": "Unauthorized: Invalid or missing authentication token"}

        # Route POST /api/v1/heartbeat
        if clean_path == "/api/v1/heartbeat" and method == "POST":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                worker_id = data.get("worker_id", "unknown")
                active_jobs = data.get("active_jobs", 0)
                self.heartbeat.record_heartbeat(worker_id, active_jobs, data.get("metadata"), data.get('status', 'online'))
                return 200, {"status": "ok", "worker_id": worker_id}
            except Exception as e:
                return 400, {"error": str(e)}

        # Route GET /api/v1/workers
        if clean_path == "/api/v1/workers" and method == "GET":
            return 200, {"workers": [dict(w, mode=self.worker_modes.get(w['worker_id'], 'enabled')) for w in self.heartbeat.get_all_workers()]}

        if clean_path == "/api/v1/admin/limits" and method == "GET":
            return 200, {"limits": self.limits}

        if clean_path == "/api/v1/admin/queue" and method == "GET":
            return 200, {"paused": self.queue.paused, "jobs": self.queue.list_jobs(), "results": list(self.results.values())[-100:]}
        if clean_path in ("/api/v1/admin/queue/pause", "/api/v1/admin/queue/resume") and method == "POST":
            self.queue.paused = clean_path.endswith('pause')
            return 200, {"paused": self.queue.paused}
        if clean_path.startswith("/api/v1/admin/queue/") and method == "POST":
            parts = clean_path.split('/')
            if len(parts) == 7 and parts[-1] == 'cancel':
                job_id = parts[-2]
                if not self.queue.cancel(job_id):
                    return 409, {"error": "Only waiting jobs can be cancelled"}
                self.results[job_id] = {"job_id": job_id, "status": "Cancelled", "verdict": "CANCELLED"}
                return 200, {"job_id": job_id, "status": "Cancelled"}
            if len(parts) == 7 and parts[-1] == 'retry':
                job_id = parts[-2]
                old = self.results.get(job_id)
                if not old or old.get('status') not in ('Failed', 'Cancelled'):
                    return 409, {"error": "Only failed or cancelled jobs can be retried"}
                return 409, {"error": "Retry requires the submission source from Django; use rejudge"}
        if clean_path.startswith("/api/v1/admin/workers/") and method == "POST":
            parts = clean_path.split('/')
            if len(parts) == 7 and parts[-1] in ('enable', 'disable', 'maintenance', 'restart'):
                worker_id, action = parts[-2], parts[-1]
                if not any(w['worker_id'] == worker_id for w in self.heartbeat.get_all_workers()):
                    return 404, {"error": "Worker not found"}
                if action == 'restart':
                    if not self.heartbeat.is_worker_alive(worker_id):
                        return 409, {"error": "Offline worker cannot receive a restart request"}
                    self.worker_modes[worker_id] = 'restart'
                    return 202, {"worker_id": worker_id, "status": "restart scheduled after current job"}
                self.worker_modes[worker_id] = 'enabled' if action == 'enable' else action
                return 200, {"worker_id": worker_id, "mode": self.worker_modes[worker_id]}

        # Route POST /api/v1/submissions or /api/v1/jobs
        if (clean_path in ["/api/v1/submissions", "/api/v1/jobs"]) and method == "POST":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                execution = self.limits.get('execution', {})
                storage = self.limits.get('storage', {})
                source_code = data.get('source_code', '')
                if not isinstance(source_code, str) or len(source_code.encode('utf-8')) > storage.get('max_source_size_bytes', 262144):
                    return 400, {"error": "Source size exceeds judge policy"}
                data['time_limit'] = min(max(float(data.get('time_limit', 1)),
                    execution.get('min_time_limit_sec', 0.1)), execution.get('max_time_limit_sec', 10.0))
                data['memory_limit'] = min(max(int(data.get('memory_limit', 256)),
                    execution.get('min_memory_limit_mb', 16)), execution.get('max_memory_limit_mb', 1024))
                job_id = str(data.get("job_id") or data.get("submission_id") or uuid.uuid4().hex[:12])
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', job_id):
                    return 400, {"error": "Invalid job ID"}
                data["job_id"] = job_id
                priority = int(data.get("priority", 10))

                self.queue.push(job_id, data, priority=priority)
                self.results[job_id] = {
                    "job_id": job_id,
                    "verdict": "PENDING",
                    "status": "Queued",
                    "submitted_at": time.time()
                }

                return 202, {
                    "status": "queued",
                    "job_id": job_id,
                    "message": "Submission enqueued successfully"
                }
            except Exception as e:
                return 400, {"error": str(e)}

        # Route GET /api/v1/jobs/poll (for workers)
        if clean_path == "/api/v1/jobs/poll" and method == "GET":
            worker_id = (query_params.get('worker_id') or [''])[0]
            if self.worker_modes.get(worker_id) == 'restart':
                self.worker_modes[worker_id] = 'enabled'
                return 200, {"job": None, "command": "restart"}
            if not worker_id or self.worker_modes.get(worker_id, 'enabled') != 'enabled':
                return 200, {"job": None}
            job = self.queue.pop(timeout=0.1)
            if job:
                job_id = job.get("job_id")
                job['assigned_worker'] = worker_id
                if job_id in self.results:
                    active = self.results[job_id]
                    active["status"] = "Judging"
                    active["verdict"] = "RUNNING"
                    active["assigned_worker"] = worker_id
                    self.results[job_id] = active
                return 200, {"job": job}
            return 200, {"job": None}

        # Route POST /api/v1/results (worker reports results)
        if clean_path == "/api/v1/results" and method == "POST":
            try:
                result_data = json.loads(body.decode("utf-8")) if body else {}
                job_id = str(result_data.get("job_id"))
                old = self.results.get(job_id, {})
                result_data['submitted_at'] = old.get('submitted_at')
                result_data['assigned_worker'] = old.get('assigned_worker')
                result_data["status"] = "Failed" if result_data.get('verdict') in ('SE', 'IE') else "Completed"
                self.results[job_id] = result_data
                return 200, {"status": "recorded", "job_id": job_id}
            except Exception as e:
                return 400, {"error": str(e)}

        # Route GET /api/v1/submissions/{id}
        if clean_path.startswith("/api/v1/submissions/") and method == "GET":
            sub_id = clean_path.split("/")[-1]
            result = self.results.get(sub_id)
            if result:
                return 200, {"submission": result}
            return 404, {"error": f"Submission '{sub_id}' not found"}

        return 404, {"error": f"Endpoint not found: {method} {clean_path}"}
