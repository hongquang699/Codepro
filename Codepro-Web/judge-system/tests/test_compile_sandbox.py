import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from judging import compile as compile_module  # noqa: E402


class CompileSandboxTest(unittest.TestCase):
    def test_compiler_runs_with_privilege_drop(self):
        """`#include "/proc/1/environ"` must not run as the judge's own user."""
        compiler = compile_module.Compiler()
        compiler.languages = {'CPP17': {'is_compiled': True, 'source_file': 'a.cpp', 'binary_file': 'a',
                                        'compile_cmd': ['g++', '{source}', '-o', '{binary}']}}
        sentinel = object()
        helper = mock.Mock()
        helper.get_preexec_fn.return_value = sentinel
        with tempfile.TemporaryDirectory() as build_dir, \
                mock.patch.object(compile_module, 'IsolatedRunnerHelper', helper), \
                mock.patch.object(compile_module.os, 'name', 'posix'), \
                mock.patch.object(compile_module.os, 'getuid', create=True, return_value=1000), \
                mock.patch.object(compile_module.subprocess, 'run') as run:
            run.return_value = mock.Mock(returncode=1, stdout='', stderr='err')
            compiler.compile('CPP17', 'int main(){}', build_dir)
        self.assertIs(run.call_args.kwargs['preexec_fn'], sentinel)
        self.assertEqual(helper.get_preexec_fn.call_args.kwargs['target_uid'], compile_module.SANDBOX_UID)
        self.assertFalse(helper.get_preexec_fn.call_args.kwargs['enable_seccomp'])


if __name__ == '__main__':
    unittest.main()
