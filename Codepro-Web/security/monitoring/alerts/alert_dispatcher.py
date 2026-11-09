"""Security Alert Dispatcher."""
import json
from typing import Dict, Any
from security.logging import SecurityLogger

class AlertDispatcher:
    @staticmethod
    def dispatch(title: str, severity: str, details: Dict[str, Any], ip: str = '127.0.0.1'):
        SecurityLogger.log_security_alert(title, severity, ip, details)
