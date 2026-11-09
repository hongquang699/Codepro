"""
Unit tests for Judge Security and Sandbox Isolation integration.
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
for p in (BASE_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from security.judge_security.resource_limits import ResourceLimiter
from security.judge_security.privilege_drop import PrivilegeDropper
from security.judge_security.syscall_policy import SyscallPolicy
from security.judge_security.syscall_policy.seccomp_filter import SeccompFilter
from security.judge_security.isolated_runner import IsolatedRunnerHelper
from sandbox.security import SecurityScanner
from sandbox.process import ProcessRunner
from sandbox.filesystem import FilesystemSandbox
from worker.compiler import WorkerCompiler
from judging.compile import Compiler

class TestJudgeSecurity(unittest.TestCase):
    def test_resource_limits_calculation(self):
        limits = ResourceLimiter.get_default_limits(time_limit_sec=2.0, memory_limit_mb=512)
        self.assertEqual(limits['cpu_time_limit_sec'], 2.0)
        self.assertEqual(limits['memory_limit_bytes'], 512 * 1024 * 1024)
        self.assertEqual(limits['max_processes'], 1)
        self.assertEqual(limits['target_uid'], 65534)
        self.assertEqual(limits['target_gid'], 65534)

    def test_syscall_policy_whitelist_and_blacklist(self):
        # Whitelisted I/O and memory
        self.assertTrue(SyscallPolicy.is_syscall_allowed('read'))
        self.assertTrue(SyscallPolicy.is_syscall_allowed('write'))
        self.assertTrue(SyscallPolicy.is_syscall_allowed('mmap'))
        self.assertTrue(SyscallPolicy.is_syscall_allowed('exit_group'))

        # Prohibited dangerous system calls
        self.assertFalse(SyscallPolicy.is_syscall_allowed('socket'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('connect'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('clone'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('fork'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('execve'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('ptrace'))
        self.assertFalse(SyscallPolicy.is_syscall_allowed('kill'))

    def test_security_scanner_detects_malicious_cpp(self):
        malicious_cpp = """
        #include <iostream>
        #include <sys/socket.h>
        int main() {
            system("rm -rf /");
            return 0;
        }
        """
        is_safe, violations = SecurityScanner.scan_source("cpp", malicious_cpp)
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)

    def test_security_scanner_detects_malicious_python(self):
        malicious_py = "import os\nos.system('whoami')"
        is_safe, violations = SecurityScanner.scan_source("python", malicious_py)
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)

    def test_security_scanner_allows_clean_algorithm_code(self):
        clean_cpp = """
        #include <iostream>
        #include <vector>
        #include <algorithm>
        using namespace std;
        int main() {
            int a, b;
            if (cin >> a >> b) {
                cout << a + b << endl;
            }
            return 0;
        }
        """
        is_safe, violations = SecurityScanner.scan_source("cpp", clean_cpp)
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)

    def test_isolated_runner_helper(self):
        preexec = IsolatedRunnerHelper.get_preexec_fn(
            time_limit_sec=1.0,
            memory_limit_mb=256
        )
        # On Windows, preexec must be None; on Linux, it must be a callable
        if os.name == 'nt':
            self.assertIsNone(preexec)
        else:
            self.assertTrue(callable(preexec))

    def test_contestant_process_does_not_inherit_manager_token(self):
        with patch.dict(os.environ, {'JUDGE_AUTH_TOKEN': 'private-test-token'}):
            result = ProcessRunner.run_process(
                [sys.executable, '-c', 'import os; print(os.getenv("JUDGE_AUTH_TOKEN", "missing"))'],
                time_limit_sec=3,
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), 'missing')

    def test_compiler_does_not_inherit_manager_token(self):
        with patch.dict(os.environ, {'JUDGE_AUTH_TOKEN': 'private-test-token'}):
            self.assertNotIn('JUDGE_AUTH_TOKEN', Compiler._compiler_env())

    def test_job_id_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as workdir:
            result = WorkerCompiler(workdir).compile_job('../outside', 'PY3', 'print(1)')
            self.assertFalse(result.success)
            self.assertEqual(result.error_message, 'Invalid job ID')

    def test_excessive_output_is_stopped_without_buffering_it_all(self):
        result = ProcessRunner.run_process(
            [sys.executable, '-c', 'import sys; sys.stdout.write("x" * 8192)'],
            time_limit_sec=3,
            output_limit_bytes=1024,
        )
        self.assertTrue(result.is_ole)
        self.assertLess(len(result.stdout), 2000)

    def test_sandbox_paths_stay_inside_mounted_storage(self):
        with tempfile.TemporaryDirectory() as workdir:
            with patch.dict(os.environ, {'JUDGE_STORAGE_DIR': workdir}):
                filesystem = FilesystemSandbox()
            self.assertEqual(filesystem.base_dir, os.path.join(workdir, 'executables'))
            with self.assertRaises(ValueError):
                FilesystemSandbox.sanitize_path('../executables-other/file', filesystem.base_dir)

if __name__ == '__main__':
    unittest.main()
