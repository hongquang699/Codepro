"""
Result Sender: Transmits submission results to Django database, Redis, or WebSocket bus.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger("judge.result_sender")


class ResultSender:
    def __init__(self):
        pass

    def send_status_update(self, submission_id: int, status: str, progress: float = 0.0):
        """
        Notify that submission status has changed (e.g., QUEUED -> COMPILING -> RUNNING).
        """
        logger.info(f"[Submission #{submission_id}] Status update: {status} ({progress*100:.0f}%)")
        # In a distributed setup, broadcast to Redis / WebSocket channel
        try:
            from websocket.submission.consumer import broadcast_submission_update
            broadcast_submission_update(submission_id, {"status": status, "progress": progress})
        except Exception:
            logger.exception("Unable to publish submission %s status", submission_id)

    def send_final_result(self, submission_id: int, verdict: str, score: float, time_ms: int, memory_kb: int, testcases: List[Dict[str, Any]] = None):
        """
        Notify that grading completed.
        """
        logger.info(f"[Submission #{submission_id}] Finished: verdict={verdict}, score={score}, time={time_ms}ms, mem={memory_kb}KB")
        try:
            from websocket.submission.consumer import broadcast_submission_update
            broadcast_submission_update(submission_id, {
                "status": "FINISHED",
                "verdict": verdict,
                "score": score,
                "time_ms": time_ms,
                "memory_kb": memory_kb,
                "testcases": testcases or []
            })
        except Exception:
            logger.exception("Unable to publish submission %s result", submission_id)
