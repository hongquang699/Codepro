"""
Tests for Judge System Checker module.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from checker.standard import StandardChecker
from checker.float import FloatChecker
from checker.checker import Checker

class TestChecker(unittest.TestCase):
    def test_standard_tokens_match(self):
        ok, _ = StandardChecker.check_tokens("10 20\n30", "10   20 30\n")
        self.assertTrue(ok)

    def test_standard_tokens_mismatch(self):
        ok, msg = StandardChecker.check_tokens("10 20 40", "10 20 30")
        self.assertFalse(ok)
        self.assertIn("Mismatch", msg)

    def test_float_tolerance(self):
        ok, _ = FloatChecker.check_float("3.14159265", "3.14159270", eps=1e-6)
        self.assertTrue(ok)

    def test_float_exceed_tolerance(self):
        ok, msg = FloatChecker.check_float("3.14", "3.141592", eps=1e-4)
        self.assertFalse(ok)

    def test_unified_checker(self):
        ok, _ = Checker.evaluate("42", "42\n", checker_type="standard")
        self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()
