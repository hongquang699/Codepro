"""
Judge Server Main Application.
Runs the HTTP Master Judge Server listening on port 9999.
"""

import sys
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_ACTIVE_REQUESTS = 32
request_slots = threading.BoundedSemaphore(MAX_ACTIVE_REQUESTS)


class BoundedJudgeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 64

    def __init__(self, *args, **kwargs):
        self.connection_slots = threading.BoundedSemaphore(64)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connection_slots.release()

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import ServerConfig
from authentication import Authenticator
from heartbeat import HeartbeatManager
from api import JudgeApiRouter
from dispatcher.queue import SubmissionQueue
from dispatcher.scheduler import WorkerScheduler, WorkerNode
from dispatcher.retry import RetryManager
from dispatcher.dispatcher import Dispatcher
from worker.worker import JudgeWorkerDaemon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [JudgeServer] %(message)s"
)
logger = logging.getLogger("JudgeServer")

class JudgeHttpHandler(BaseHTTPRequestHandler):
    router: JudgeApiRouter = None

    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def do_OPTIONS(self):
        self._send_json(405, {"error": "Method not allowed"})

    def do_GET(self):
        if not request_slots.acquire(blocking=False):
            return self._send_json(503, {"error": "Judge manager busy"})
        try:
            code, resp = self.router.handle("GET", self.path, dict(self.headers), b"")
            self._send_json(code, resp)
        finally:
            request_slots.release()

    def do_POST(self):
        if not request_slots.acquire(blocking=False):
            return self._send_json(503, {"error": "Judge manager busy"})
        try:
            try:
                content_length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                return self._send_json(400, {"error": "Invalid Content-Length"})
            if content_length < 0:
                return self._send_json(400, {"error": "Invalid Content-Length"})
            if content_length > MAX_REQUEST_BYTES:
                return self._send_json(413, {"error": "Request too large"})
            if self.headers.get("Transfer-Encoding"):
                return self._send_json(400, {"error": "Transfer-Encoding is not supported"})
            body = self.rfile.read(content_length) if content_length > 0 else b""
            code, resp = self.router.handle("POST", self.path, dict(self.headers), body)
            self._send_json(code, resp)
        finally:
            request_slots.release()

    def log_message(self, format, *args):
        # Silence default standard logger noise for clean logs
        pass

def start_embedded_worker(worker_id: str, server_url: str, auth_token: str, problem_data_dir: str, storage_dir: str, metadata: dict = None):
    """Spawns an embedded worker daemon in a background thread."""
    import time
    time.sleep(0.5)
    while True:
        worker = JudgeWorkerDaemon(
            worker_id=worker_id,
            judge_server_url=server_url,
            auth_token=auth_token,
            problem_data_dir=problem_data_dir,
            storage_dir=storage_dir,
            metadata=metadata or {}
        )
        if worker.run_standalone() != 'restart':
            break

def run_server():
    config = ServerConfig()
    if not logger.handlers:
        file_handler = RotatingFileHandler(os.path.join(config.logs_dir, 'judge-server.log'),
                                           maxBytes=5_000_000, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(file_handler)
    auth = Authenticator(config.auth_token)
    heartbeat_mgr = HeartbeatManager(timeout_sec=config.heartbeat_interval * 3)
    judge_redis_url = os.getenv('JUDGE_QUEUE_REDIS_URL', '')
    queue = SubmissionQueue(backend_type='redis' if judge_redis_url else 'memory',
                            redis_url=judge_redis_url or None)
    if queue.redis:
        from dispatcher.result_store import ResultStore
        results_store = ResultStore(queue.redis)
    else:
        results_store = {}

    # Initialize router
    router = JudgeApiRouter(
        authenticator=auth,
        heartbeat_mgr=heartbeat_mgr,
        queue=queue,
        results_store=results_store,
        limits=config.limits_cfg,
    )
    JudgeHttpHandler.router = router

    server_address = (config.host, config.port)
    httpd = BoundedJudgeHTTPServer(server_address, JudgeHttpHandler)

    logger.info("=" * 60)
    logger.info(f"CodeProOJ Judge Server listening at http://{config.host}:{config.port}")
    logger.info(f"Problem base dir: {config.problem_data_dir}")
    logger.info(f"Storage dir: {config.storage_dir}")
    logger.info("=" * 60)

    # Load all configured workers from workers.yml (defaulting to 7 worker nodes)
    configured_workers = config.workers_cfg.get("workers", [])
    if not configured_workers:
        configured_workers = [
            {"id": f"worker-{i}", "name": f"Judge Worker Node 0{i}", "capacity": 2, "max_memory_mb": 2048}
            for i in range(1, 8)
        ]

    worker_url = f"http://127.0.0.1:{config.port}"
    logger.info(f"Starting {len(configured_workers)} Judge Worker Daemons...")
    for w_cfg in configured_workers:
        w_id = w_cfg.get("id")
        w_name = w_cfg.get("name", w_id)
        t = threading.Thread(
            target=start_embedded_worker,
            args=(w_id, worker_url, config.auth_token, config.problem_data_dir, config.storage_dir, w_cfg),
            daemon=True
        )
        t.start()
        logger.info(f"  [+] Spawned {w_id} ({w_name}) [Capacity: {w_cfg.get('capacity', 2)} jobs, Max RAM: {w_cfg.get('max_memory_mb', 2048)}MB]")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Judge Server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
