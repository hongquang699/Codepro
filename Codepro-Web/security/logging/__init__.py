"""
CODING_OJ Security Logging Subsystem
Centralized structured logger for authentication, admin actions, judge operations,
API requests, security violations, and compliance audit trails.
"""

import os
import json
import logging
from datetime import datetime, timezone

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# Define standard log file targets
LOG_FILES = {
    'security': os.path.join(LOG_DIR, 'security.log'),
    'auth': os.path.join(LOG_DIR, 'auth.log'),
    'admin': os.path.join(LOG_DIR, 'admin.log'),
    'api': os.path.join(LOG_DIR, 'api.log'),
    'judge': os.path.join(LOG_DIR, 'judge.log'),
    'audit': os.path.join(LOG_DIR, 'audit.log'),
}

class JSONFormatter(logging.Formatter):
    """Formats log records as newline-delimited JSON objects."""
    def format(self, record):
        data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            data.update(record.extra_data)
        return json.dumps(data, ensure_ascii=False)

def get_security_logger(channel: str = 'security') -> logging.Logger:
    """Retrieves or configures a dedicated security logger for a specific channel."""
    logger_name = f'security.{channel}'
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_path = LOG_FILES.get(channel, LOG_FILES['security'])
    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger

class SecurityLogger:
    """High-level security logger interface."""
    @staticmethod
    def log_auth(event: str, username: str, ip: str, success: bool, details: dict = None):
        logger = get_security_logger('auth')
        extra = {
            'event': event,
            'username': username,
            'ip': ip,
            'success': success,
            'details': details or {}
        }
        msg = f"Auth event: {event} for user {username} [IP: {ip}] - Success: {success}"
        logger.info(msg, extra={'extra_data': extra})

    @staticmethod
    def log_admin(admin_username: str, action: str, resource: str, resource_id: str, ip: str, outcome: str = 'SUCCESS', details: dict = None):
        logger = get_security_logger('admin')
        extra = {
            'admin': admin_username,
            'action': action,
            'resource': resource,
            'resource_id': str(resource_id),
            'ip': ip,
            'outcome': outcome,
            'details': details or {}
        }
        msg = f"Admin action: {admin_username} performed {action} on {resource}:{resource_id} [Outcome: {outcome}]"
        logger.info(msg, extra={'extra_data': extra})

    @staticmethod
    def log_security_alert(threat_type: str, severity: str, ip: str, details: dict = None):
        logger = get_security_logger('security')
        extra = {
            'threat_type': threat_type,
            'severity': severity.upper(),
            'ip': ip,
            'details': details or {}
        }
        msg = f"SECURITY ALERT [{severity.upper()}]: {threat_type} from {ip}"
        if severity.lower() in ('high', 'critical'):
            logger.error(msg, extra={'extra_data': extra})
        else:
            logger.warning(msg, extra={'extra_data': extra})

    @staticmethod
    def log_judge(worker_id: str, submission_id: int, action: str, status: str, duration_sec: float = 0.0, details: dict = None):
        logger = get_security_logger('judge')
        extra = {
            'worker_id': worker_id,
            'submission_id': submission_id,
            'action': action,
            'status': status,
            'duration_sec': duration_sec,
            'details': details or {}
        }
        msg = f"Judge operation: Worker {worker_id} executed {action} for #{submission_id} -> {status}"
        logger.info(msg, extra={'extra_data': extra})

    @staticmethod
    def log_audit(category: str, actor: str, action: str, target: str, ip: str, details: dict = None):
        logger = get_security_logger('audit')
        extra = {
            'category': category,
            'actor': actor,
            'action': action,
            'target': target,
            'ip': ip,
            'details': details or {}
        }
        msg = f"Audit [{category}]: {actor} -> {action} on {target}"
        logger.info(msg, extra={'extra_data': extra})
