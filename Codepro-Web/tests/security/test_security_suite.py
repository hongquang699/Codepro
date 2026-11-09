import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.template import Context, Template
from django.db import connection

from security.api_security.input_validation import InputSanitizer
from security.api_security.csrf import CSRFGuard
from backend.auth.security.brute_force import (
    record_login_attempt,
    is_ip_or_user_locked,
    MAX_FAILED_ATTEMPTS
)


class SQLInjectionDefenseTest(TestCase):
    """Kiểm tra cơ chế phòng thủ SQL Injection (Parameterized query & Detection)."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')

    def test_orm_parameterization_neutralizes_sqli(self):
        """Django ORM an toàn trước payload SQLi kinh điển."""
        malicious_input = "alice' OR '1'='1"
        # Truy vấn an toàn qua ORM không trả về tất cả users
        matched_user = User.objects.filter(username=malicious_input).first()
        self.assertIsNone(matched_user)

    def test_raw_parameterized_query_neutralizes_sqli(self):
        """Sử dụng connection.cursor với parameterized argument (%s)."""
        malicious_input = "alice' OR '1'='1"
        with connection.cursor() as cursor:
            # An toàn: truyền tham số riêng biệt qua tuple
            cursor.execute("SELECT id, username FROM auth_user WHERE username = %s", [malicious_input])
            row = cursor.fetchone()
            self.assertIsNone(row)

    def test_input_sanitizer_detects_real_sqli_payloads(self):
        """Phát hiện chính xác payload SQL Injection thực sự."""
        real_attacks = [
            "1' OR '1'='1",
            "1' UNION SELECT null, username, password FROM users--",
            "admin'; DROP TABLE auth_user--",
            "1' AND SLEEP(5)--",
            "1 /*!50000UNION*/ SELECT 1,2",
        ]
        for payload in real_attacks:
            self.assertTrue(
                InputSanitizer.check_sqli(payload),
                f"Payload độc hại không bị phát hiện: {payload}"
            )

    def test_input_sanitizer_does_not_false_positive_on_legitimate_queries(self):
        """Không chặn nhầm các từ khóa lập trình hợp lệ (selection sort, union find, update)."""
        legitimate_inputs = [
            "selection sort algorithm",
            "disjoint set union find",
            "please update the problem description",
            "select an option from the menu",
            "drop by drop water filling problem",
        ]
        for text in legitimate_inputs:
            self.assertFalse(
                InputSanitizer.check_sqli(text),
                f"Đầu vào hợp lệ bị chặn nhầm: {text}"
            )


class XSSDefenseTest(TestCase):
    """Kiểm tra cơ chế phòng thủ XSS (Template auto-escaping & Content-Type)."""

    def test_template_auto_escaping_neutralizes_script_tags(self):
        """Template của Django tự động escape thẻ script độc hại."""
        dirty_input = '<script>alert("XSS")</script>'
        template = Template("<div>{{ user_input }}</div>")
        rendered = template.render(Context({'user_input': dirty_input}))

        # Thẻ <script> phải được chuyển thành &lt;script&gt;
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;', rendered)


class CSRFDefenseTest(TestCase):
    """Kiểm tra cơ chế phòng thủ CSRF."""

    def test_csrf_guard_verification(self):
        """Mã CSRF token phải khớp giữa cookie và header."""
        cookie_token = "abc123securetoken"
        valid_header = "abc123securetoken"
        invalid_header = "forged_token_from_attacker"

        self.assertTrue(CSRFGuard.verify(cookie_token, valid_header))
        self.assertFalse(CSRFGuard.verify(cookie_token, invalid_header))
        self.assertFalse(CSRFGuard.verify(cookie_token, None))


class BruteForceDefenseTest(TestCase):
    """Kiểm tra cơ chế phòng thủ Brute Force đăng nhập."""

    def setUp(self):
        self.test_ip = "198.51.100.42"
        self.test_username = "victim_account"

    def test_lockout_after_max_failed_attempts(self):
        """Khóa sau 5 lần nhập sai mật khẩu liên tiếp."""
        # 4 lần đầu chưa bị khóa
        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            record_login_attempt(self.test_ip, self.test_username, is_success=False)
            locked, _ = is_ip_or_user_locked(self.test_ip, self.test_username)
            self.assertFalse(locked)

        # Lần thứ 5 sai -> Phải bị khóa
        record_login_attempt(self.test_ip, self.test_username, is_success=False)
        locked, remaining = is_ip_or_user_locked(self.test_ip, self.test_username)
        self.assertTrue(locked)
        self.assertGreater(remaining, 0)
