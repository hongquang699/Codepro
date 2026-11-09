"""
Tests for Judge System Sandbox and Runner module.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sandbox.sandbox import Sandbox
from judging.execute import Executor

class TestRunner(unittest.TestCase):
    def setUp(self):
        self.sandbox = Sandbox()
        self.executor = Executor()
        self.test_dir = os.path.join(BASE_DIR, "storage", "executables", "test_run")
        os.makedirs(self.test_dir, exist_ok=True)

    def test_python_normal_execution(self):
        script = os.path.join(self.test_dir, "sum.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write("import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n")

        res = self.executor.run_testcase(
            language="python",
            target_path=script,
            input_data="15 25\n",
            time_limit_sec=2.0
        )
        self.assertEqual(res.verdict, "OK")
        self.assertEqual(res.user_output.strip(), "40")
        self.assertGreater(res.time_ms, 0)
        self.assertGreater(res.memory_kb, 0)

    def test_python_tle_detection(self):
        script = os.path.join(self.test_dir, "infinite.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write("while True:\n    pass\n")

        res = self.executor.run_testcase(
            language="python",
            target_path=script,
            input_data="",
            time_limit_sec=0.5
        )
        self.assertEqual(res.verdict, "TLE")

    def test_python_runtime_error(self):
        script = os.path.join(self.test_dir, "re.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write("x = 1 / 0\n")

        res = self.executor.run_testcase(
            language="python",
            target_path=script,
            input_data="",
            time_limit_sec=1.0
        )
        self.assertEqual(res.verdict, "RE")

if __name__ == "__main__":
    unittest.main()
