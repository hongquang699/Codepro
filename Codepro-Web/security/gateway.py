"""
CODING_OJ Master Security Gateway
Unified entry point coordinating all security subsystem capabilities:
Authentication, RBAC Authorization, Session Management, Sandbox Protection,
Injection Defense, Content Sanitization, and Audit Logging.
"""

from typing import Dict, Any, Tuple, Optional, List

from security.authentication import Authenticator, BruteForceProtector, TwoFactorAuthenticator
from security.authorization import SystemRole, Permissions, RBACChecker, OwnershipGuard
from security.session_security import JWTHandler, SecureCookieBuilder, DeviceManager
from security.password import PasswordHasher, PasswordPolicyValidator, BreachChecker
from security.submission_security import SourceProtectionGuard, SubmissionValidator, PlagiarismDetector
from security.judge_security import SandboxSecurityManager, SyscallPolicy, WorkerAuthenticator
from security.problem_security import TestcaseGuard, ProblemAccessControl
from security.admin_security import AdminAuthenticator, PrivilegedActionGuard
from security.api_security import RateLimiter, InputSanitizer, CSRFGuard, SecurityHeaders, APIKeyManager
from security.content_security import HTMLSanitizer, XSSFilter, UploadValidator
from security.contest_security import ScoreboardFreezeManager, ContestAccessGuard, AntiCheatEngine
from security.database_security import DatabaseVault, FieldCipher
from security.infrastructure_security import SecretLoader, FirewallTopology
from security.monitoring import IntrusionDetector, AlertDispatcher
from security.audit import AdminAuditor, SubmissionAuditor
from security.incident_response import EmergencyContainment
from security.logging import SecurityLogger

class SecurityGateway:
    """Master Security Interface for Django API and Judge Microservices."""

    @staticmethod
    def verify_request_safety(ip: str, path: str, query_params: Dict[str, str], body_text: str = '') -> Tuple[bool, str]:
        """Checks IP bans, maintenance mode, and intrusion signatures."""
        if EmergencyContainment.is_ip_banned(ip):
            return False, "Địa chỉ IP của bạn đã bị chặn do nghi vấn bảo mật."

        if EmergencyContainment.is_maintenance_mode() and not path.startswith('/admin'):
            return False, "Hệ thống đang bảo trì định kỳ. Vui lòng quay lại sau."

        has_threat, threats = IntrusionDetector.inspect_request(ip, path, query_params, body_text)
        if has_threat:
            return False, f"Yêu cầu bị từ chối do vi phạm quy tắc an toàn: {threats[0]}"

        return True, "Safe"

    @staticmethod
    def check_rate_limit(client_id: str, max_req: int = 60, window_sec: int = 60) -> Tuple[bool, int]:
        return RateLimiter.check_limit(client_id, max_req, window_sec)

    @staticmethod
    def authenticate_user(username: str, password: str, stored_hash: str, ip: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return Authenticator.authenticate(username, password, stored_hash, ip)

    @staticmethod
    def generate_access_token(user_id: int, username: str, role: str) -> str:
        return JWTHandler.encode({'sub': username, 'uid': user_id, 'role': role}, expires_in_seconds=3600)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        return JWTHandler.decode(token)

    @staticmethod
    def check_permission(user_role: str, permission: str) -> bool:
        return RBACChecker.has_permission(user_role, permission)

    @staticmethod
    def sanitize_html(raw_html: str) -> str:
        return HTMLSanitizer.sanitize(raw_html)

    @staticmethod
    def validate_submission(code: str, language: str) -> Tuple[bool, str]:
        return SubmissionValidator.validate(code, language)

    @staticmethod
    def get_judge_sandbox_limits(time_limit: float, memory_limit: int) -> Dict[str, Any]:
        return SandboxSecurityManager.get_sandbox_limits(time_limit, memory_limit)
