"""
Tests for Judge System Compiler module.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from judging.compile import Compiler

class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = Compiler()
        self.build_dir = os.path.join(BASE_DIR, "storage", "executables", "test_build")
        os.makedirs(self.build_dir, exist_ok=True)

    def test_python_valid_syntax(self):
        code = "print('Hello, Judge!')\n"
        res = self.compiler.compile("python", code, self.build_dir)
        self.assertTrue(res.success)

    def test_python_syntax_error(self):
        code = "def invalid_syntax(\n"
        res = self.compiler.compile("python", code, self.build_dir)
        self.assertFalse(res.success)
        self.assertIn("Syntax", res.error_message)

    def test_cpp_compilation(self):
        # Check if g++ exists
        import shutil
        if not shutil.which("g++"):
            self.skipTest("g++ compiler not installed on host")

        code = """
        #include <iostream>
        using namespace std;
        int main() {
            int a, b;
            if (cin >> a >> b) {
                cout << (a + b) << endl;
            }
            return 0;
        }
        """
        res = self.compiler.compile("cpp", code, self.build_dir)
        self.assertTrue(res.success, f"Compilation failed: {res.compiler_output}")
        self.assertIsNotNone(res.binary_path)
        self.assertTrue(os.path.exists(res.binary_path))

if __name__ == "__main__":
    unittest.main()
