"""Intrusion Detection System (IDS) analyzing HTTP requests."""
from typing import Dict, List, Tuple
from security.api_security.input_validation import InputSanitizer
from security.logging import SecurityLogger

class IntrusionDetector:
    @classmethod
    def inspect_request(cls, ip: str, path: str, query_params: Dict[str, str], body_text: str = '') -> Tuple[bool, List[str]]:
        threats = []
        
        # Check path
        if InputSanitizer.check_cmd_injection(path) or '..' in path:
            threats.append(f"Path traversal or command injection in URL: {path}")

        # Check query params
        for k, v in query_params.items():
            if InputSanitizer.check_sqli(v):
                threats.append(f"SQL Injection attempt in param '{k}': {v}")
            if InputSanitizer.check_cmd_injection(v):
                threats.append(f"Command injection attempt in param '{k}': {v}")

        # Check body text
        if body_text and len(body_text) < 50000:
            if InputSanitizer.check_sqli(body_text):
                threats.append("SQL Injection detected in request payload")

        if threats:
            SecurityLogger.log_security_alert('IDS_SIGNATURE_MATCH', 'HIGH', ip, {'threats': threats, 'path': path})
            return True, threats

        return False, []
