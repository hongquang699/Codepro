"""Admin Action Auditor."""
from security.logging import SecurityLogger

class AdminAuditor:
    @staticmethod
    def log(admin: str, action: str, resource: str, resource_id: str, ip: str, outcome: str = 'SUCCESS', details: dict = None):
        SecurityLogger.log_admin(admin, action, resource, resource_id, ip, outcome, details)
