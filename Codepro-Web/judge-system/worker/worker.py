"""
Worker Daemon for Judge System.
Listens for tasks, invokes JobExecutor, maintains heartbeat, and reports results.
"""

import time
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import shutil
import socket
import re
from urllib import request, error
from typing import Optional
try:
    from .job import JudgeJob
    from .result import JudgeResult
    from .executor import JobExecutor
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from worker.job import JudgeJob
    from worker.result import JudgeResult
    from worker.executor import JobExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s"
)
class JudgeWorkerDaemon:
    def __init__(
        self,
        worker_id: str = "worker-1",
        judge_server_url: str = "http://127.0.0.1:9999",
        auth_token: str = "",
        problem_data_dir: Optional[str] = None,
        storage_dir: str = "./storage",
        metadata: Optional[dict] = None
    ):
        self.worker_id = worker_id
        self.judge_server_url = judge_server_url.rstrip("/")
        self.auth_token = auth_token
        self.metadata = metadata or {}
        self.running = False
        self.current_job = None
        self._network_sample = None
        self.last_error = None
        self.logger = logging.getLogger(f'JudgeWorker.{worker_id}')
        if not self.logger.handlers:
            log_dir = os.getenv('JUDGE_LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'))
            os.makedirs(log_dir, exist_ok=True)
            safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', worker_id)
            handler = RotatingFileHandler(os.path.join(log_dir, f'{safe_id}.log'), maxBytes=2_000_000,
                                          backupCount=3, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
            self.logger.addHandler(handler)

        default_data_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 'Codepro-Data'))
        data_root = os.getenv('CODEPRO_DATA_ROOT') or default_data_root
        problem_data_dir = (problem_data_dir or os.getenv('JUDGE_PROBLEM_DATA_DIR')
                            or os.path.join(data_root, 'problem-data', 'problems'))
        self.executor = JobExecutor(
            problem_base_dir=problem_data_dir,
            storage_base_dir=storage_dir
        )

    def send_heartbeat(self, active_jobs: int = 0):
        """Sends heartbeat to judge-server."""
        url = f"{self.judge_server_url}/api/v1/heartbeat"
        metadata = dict(self.metadata)
        metadata.update({
            'hostname': socket.gethostname(), 'os': platform.system(),
            'cpu_count': os.cpu_count() or 0, 'current_job': self.current_job,
            'error': self.last_error,
        })
        try:
            metadata['ip_address'] = socket.gethostbyname(socket.gethostname())
        except OSError:
            pass
        try:
            usage = shutil.disk_usage(self.executor.storage_base_dir)
            metadata['disk_percent'] = round((usage.used / usage.total) * 100, 1)
        except (OSError, AttributeError):
            pass
        try:
            import psutil
            metadata['cpu_percent'] = psutil.cpu_percent(interval=None)
            metadata['memory_percent'] = psutil.virtual_memory().percent
            counters = psutil.net_io_counters()
            sample = (time.time(), counters.bytes_sent, counters.bytes_recv)
            if self._network_sample:
                elapsed = max(0.001, sample[0] - self._network_sample[0])
                metadata['network_tx_kbps'] = round((sample[1] - self._network_sample[1]) / elapsed / 1024, 1)
                metadata['network_rx_kbps'] = round((sample[2] - self._network_sample[2]) / elapsed / 1024, 1)
            self._network_sample = sample
        except ImportError:
            pass
        payload = json.dumps({
            "worker_id": self.worker_id,
            "active_jobs": active_jobs,
            "status": "error" if self.last_error else "online",
            "metadata": metadata
        }).encode("utf-8")

        req = request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}"
            }
        )
        try:
            with request.urlopen(req, timeout=3) as resp:
                pass
        except Exception as e:
            self.logger.debug(f"Heartbeat failed: {e}")

    def report_result(self, result: JudgeResult):
        """Posts completed job result to judge server."""
        url = f"{self.judge_server_url}/api/v1/results"
        payload = json.dumps(result.to_dict()).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}"
            }
        )
        try:
            with request.urlopen(req, timeout=5) as resp:
                self.logger.info(f"Reported result for job {result.job_id}")
        except Exception as e:
            self.logger.error(f"Failed to report result for job {result.job_id}: {e}")

    def execute_job(self, job_dict: dict) -> JudgeResult:
        """Processes a single judging task."""
        job = JudgeJob(
            job_id=str(job_dict.get("job_id") or job_dict.get("id")),
            problem_code=str(job_dict.get("problem_code")),
            language=str(job_dict.get("language")),
            source_code=str(job_dict.get("source_code", "")),
            time_limit_sec=float(job_dict.get("time_limit", 1.0)),
            memory_limit_mb=int(job_dict.get("memory_limit", 256)),
            checker_type=job_dict.get("checker_type", "standard"),
            checker_path=job_dict.get("checker_path"),
            float_epsilon=float(job_dict.get("float_epsilon", 1e-6)),
            subtask_mode=bool(job_dict.get("subtask_mode", False)),
            problem_version=job_dict.get("problem_version"),
        )
        result = self.executor.execute_job(job)
        return result

    def run_standalone(self, poll_interval: float = 2.0):
        """Main loop for pulling jobs from judge server."""
        self.running = True
        self.logger.info(f"Worker {self.worker_id} started. Connecting to {self.judge_server_url}")

        # Send immediate initial heartbeat
        self.send_heartbeat(active_jobs=0)
        last_hb = time.time()

        while self.running:
            now = time.time()
            if now - last_hb >= 10.0:
                self.send_heartbeat(active_jobs=0)
                last_hb = now

            # Poll for job
            url = f"{self.judge_server_url}/api/v1/jobs/poll?worker_id={self.worker_id}"
            req = request.Request(
                url,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            try:
                with request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get('command') == 'restart':
                        self.logger.info(f"Worker {self.worker_id} restarting after manager request")
                        self.running = False
                        return 'restart'
                    job_data = data.get("job")
                    if job_data:
                        self.logger.info(f"Worker {self.worker_id} received job: {job_data.get('job_id')}")
                        self.current_job = job_data.get('job_id')
                        self.send_heartbeat(active_jobs=1)
                        try:
                            try:
                                result = self.execute_job(job_data)
                            except Exception as exc:
                                self.last_error = str(exc)[:250]
                                self.logger.exception('Job execution failed')
                                result = JudgeResult(job_id=str(job_data.get('job_id')),
                                                     verdict='SE', score=0, error_message=self.last_error)
                            self.report_result(result)
                            if result.verdict != 'SE':
                                self.last_error = None
                        finally:
                            self.current_job = None
                            self.send_heartbeat(active_jobs=0)
            except error.URLError:
                pass
            except Exception as e:
                self.logger.error(f"Polling error: {e}")
                self.last_error = str(e)[:250]
                self.send_heartbeat(active_jobs=0)

            time.sleep(poll_interval)

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9999"
    auth_token = os.getenv('JUDGE_AUTH_TOKEN', '')
    if not auth_token:
        raise RuntimeError('JUDGE_AUTH_TOKEN must be set for standalone workers')
    while True:
        daemon = JudgeWorkerDaemon(worker_id=worker_id, judge_server_url=server_url,
                                   auth_token=auth_token)
        if daemon.run_standalone() != 'restart':
            break
