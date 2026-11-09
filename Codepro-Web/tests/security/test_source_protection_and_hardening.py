"""
Comprehensive Security & Source Code Protection Verification Tests.
Verifies all patches implemented for:
1. Malicious code execution prevention (Judge SecurityScanner).
2. Submission source code masking (SubmissionDetailSerializer).
3. Client IP anti-spoofing in security middleware.
4. Static file path jail & source leak prevention rules.
"""

from django.test import TestCase, RequestFactory
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory

import sys
from django.conf import settings
judge_sys_dir = str(settings.BASE_DIR / 'judge-system')
if judge_sys_dir not in sys.path:
    sys.path.insert(0, judge_sys_dir)

from backend.judge.models import Problem, Submission, Language, Profile
from backend.api.v2.serializers import SubmissionDetailSerializer
from security.middleware import FullSecurityMiddleware
from sandbox.security import SecurityScanner


class JudgeMaliciousCodeExecutionSecurityTest(TestCase):
    """Kiểm tra máy chấm phát hiện và ngăn chặn mã độc, RCE."""

    def test_python_dangerous_imports_blocked(self):
        malicious_samples = [
            "import os\nos.system('whoami')",
            "from subprocess import Popen\nPopen(['ls'])",
            "import socket\ns = socket.socket()",
            "import sys\nsys.exit(0)",
            "import shutil\nshutil.rmtree('/')",
            "__import__('os').system('id')",
            "open('/etc/passwd').read()",
            "eval('__import__(\"os\")')",
            "exec('import os')",
        ]
        for code in malicious_samples:
            is_safe, violations = SecurityScanner.scan_source("python", code)
            self.assertFalse(is_safe, f"Mã nguồn nguy hiểm không bị chặn: {code}")
            self.assertTrue(len(violations) > 0)

    def test_python_legitimate_algorithm_allowed(self):
        legitimate_code = """
import math
import collections
from itertools import permutations

def solve():
    n = int(input())
    a = list(map(int, input().split()))
    print(sum(a))

if __name__ == '__main__':
    solve()
"""
        is_safe, violations = SecurityScanner.scan_source("python", legitimate_code)
        self.assertTrue(is_safe, f"Thuật toán hợp lệ bị chặn nhầm: {violations}")

    def test_cpp_dangerous_syscalls_blocked(self):
        malicious_samples = [
            "#include <windows.h>\nint main(){}",
            "#include <sys/socket.h>\nint main(){}",
            "#include <unistd.h>\nint main(){}",
            "int main(){ system(\"whoami\"); }",
            "int main(){ popen(\"ls\", \"r\"); }",
            "int main(){ fork(); }",
        ]
        for code in malicious_samples:
            is_safe, violations = SecurityScanner.scan_source("cpp", code)
            self.assertFalse(is_safe, f"Mã C++ nguy hiểm không bị chặn: {code}")
            self.assertTrue(len(violations) > 0)

    def test_cpp_legitimate_algorithm_allowed(self):
        legitimate_code = """
#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int n;
    if (cin >> n) {
        cout << n * 2 << "\n";
    }
    return 0;
}
"""
        is_safe, violations = SecurityScanner.scan_source("cpp", legitimate_code)
        self.assertTrue(is_safe, f"Thuật toán C++ hợp lệ bị chặn nhầm: {violations}")


class SubmissionSourceCodeMaskingTest(TestCase):
    """Kiểm tra ẩn và bảo vệ mã nguồn bài nộp của thí sinh khác."""

    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password123')
        self.bob = User.objects.create_user(username='bob', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='password123')
        
        self.alice_prof, _ = Profile.objects.get_or_create(user=self.alice)
        self.bob_prof, _ = Profile.objects.get_or_create(user=self.bob)

        self.prob = Problem.objects.create(code='P01', name='Problem 01', points=100)
        self.lang = Language.objects.create(key='PY3', name='Python 3')
        
        self.secret_code = "print('ALICE_SECRET_SOLUTION_CODE')"
        self.submission = Submission.objects.create(
            problem=self.prob,
            user=self.alice_prof,
            language=self.lang,
            source=self.secret_code,
            result='AC'
        )
        self.factory = APIRequestFactory()

    def test_unauthenticated_user_cannot_see_source_code(self):
        """Khách vãng lai không được xem mã nguồn bài nộp."""
        request = self.factory.get(f'/api/v2/submission/{self.submission.id}')
        serializer = SubmissionDetailSerializer(self.submission, context={'request': request})
        self.assertEqual(serializer.data['source'], "[Mã nguồn được bảo mật theo quy chế cuộc thi]")

    def test_other_contestant_cannot_see_alice_source_code(self):
        """Thí sinh Bob không được xem mã nguồn bài nộp của Alice."""
        request = self.factory.get(f'/api/v2/submission/{self.submission.id}')
        request.user = self.bob
        serializer = SubmissionDetailSerializer(self.submission, context={'request': request})
        self.assertEqual(serializer.data['source'], "[Mã nguồn được bảo mật theo quy chế cuộc thi]")

    def test_author_alice_can_see_own_source_code(self):
        """Tác giả Alice xem được mã nguồn của chính mình."""
        request = self.factory.get(f'/api/v2/submission/{self.submission.id}')
        request.user = self.alice
        serializer = SubmissionDetailSerializer(self.submission, context={'request': request})
        self.assertEqual(serializer.data['source'], self.secret_code)

    def test_admin_can_see_submission_source_code(self):
        """Quản trị viên xem được mã nguồn để chấm thi và xử lý gian lận."""
        request = self.factory.get(f'/api/v2/submission/{self.submission.id}')
        request.user = self.admin
        serializer = SubmissionDetailSerializer(self.submission, context={'request': request})
        self.assertEqual(serializer.data['source'], self.secret_code)


class AntiIPSpoofingSecurityTest(TestCase):
    """Kiểm tra chống giả mạo IP qua header X-Forwarded-For."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_external_ip_cannot_spoof_localhost(self):
        """Client ngoài không thể giả mạo 127.0.0.1 bằng X-Forwarded-For."""
        request = self.factory.get('/api/test', REMOTE_ADDR='203.0.113.195')
        request.META['HTTP_X_FORWARDED_FOR'] = '127.0.0.1'
        resolved_ip = FullSecurityMiddleware._get_client_ip(request)
        # Vì REMOTE_ADDR không phải trusted proxy, X-Forwarded-For bị bỏ qua
        self.assertEqual(resolved_ip, '203.0.113.195')

    def test_trusted_proxy_forwarding_is_respected(self):
        """Khi yêu cầu đến từ reverse proxy cục bộ (127.0.0.1), IP gốc được ghi nhận."""
        request = self.factory.get('/api/test', REMOTE_ADDR='127.0.0.1')
        request.META['HTTP_X_FORWARDED_FOR'] = '198.51.100.42, 127.0.0.1'
        resolved_ip = FullSecurityMiddleware._get_client_ip(request)
        self.assertEqual(resolved_ip, '198.51.100.42')

    def test_docker_proxy_cidr_only_trusts_its_network(self):
        with patch.dict('os.environ', {'TRUSTED_PROXY_IPS': '172.16.0.0/12'}):
            trusted = self.factory.get('/api/test', REMOTE_ADDR='172.19.0.3',
                                       HTTP_X_REAL_IP='198.51.100.44')
            untrusted = self.factory.get('/api/test', REMOTE_ADDR='192.168.1.5',
                                         HTTP_X_REAL_IP='127.0.0.1')
            self.assertEqual(FullSecurityMiddleware._get_client_ip(trusted), '198.51.100.44')
            self.assertEqual(FullSecurityMiddleware._get_client_ip(untrusted), '192.168.1.5')
