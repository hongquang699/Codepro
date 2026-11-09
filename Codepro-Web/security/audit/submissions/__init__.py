"""Submission Action Auditor (Rejudge, Score override)."""
from security.logging import SecurityLogger

class SubmissionAuditor:
    @staticmethod
    def log_rejudge(actor: str, submission_id: int, old_verdict: str, new_verdict: str, ip: str):
        details = {'old_verdict': old_verdict, 'new_verdict': new_verdict}
        SecurityLogger.log_audit('SUBMISSION_REJUDGE', actor, 'REJUDGE', f"#{submission_id}", ip, details)
