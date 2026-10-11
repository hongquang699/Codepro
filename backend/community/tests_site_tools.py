import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase

from backend.community import site_files, site_git
from backend.community.management.commands.site_terminal import Command
from backend.community.terminal_ui import command_suggestions


class SiteFileTests(SimpleTestCase):
    def test_preview_and_restrict_to_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sample.txt').write_text('first\nsecond\nthird', encoding='utf-8')
            (root / 'binary.dat').write_bytes(b'abc\x00def')
            with patch.object(site_files, 'ROOT', root):
                self.assertIn('   2  second', site_files.preview('sample.txt', 2))
                self.assertIn('more lines available', site_files.preview('sample.txt', 2))
                with self.assertRaises(CommandError):
                    site_files.resolve_file('../outside.txt')
                with self.assertRaisesMessage(CommandError, 'Binary files'):
                    site_files.preview('binary.dat')

    def test_open_uses_argument_list_for_vscode(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / 'sample file.txt'
            target.write_text('hello', encoding='utf-8')
            with patch.object(site_files, 'ROOT', root), \
                    patch.object(site_files.shutil, 'which', return_value='/usr/bin/code'), \
                    patch.object(site_files.os, 'name', 'posix'), \
                    patch.object(site_files.subprocess, 'Popen') as launch:
                self.assertIn('Opening', site_files.open_in_editor('sample file.txt'))
            self.assertEqual(launch.call_args.args[0], ['/usr/bin/code', '--reuse-window', str(target)])


class SiteGitTests(SimpleTestCase):
    def test_git_workflow_and_command_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Test'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'test@example.invalid'], check=True)
            (root / 'test.txt').write_text('hello\n', encoding='utf-8')
            with patch.object(site_git, 'ROOT', root), patch.object(site_files, 'ROOT', root):
                self.assertIn('Staged test.txt', site_git.run_git(['add', 'test.txt']))
                self.assertIn('test.txt', site_git.run_git(['staged']))
                self.assertIn('initial', site_git.run_git(['commit', 'initial']))
                (root / 'test.txt').write_text('changed\n', encoding='utf-8')
                self.assertIn('changed', site_git.run_git(['diff', 'test.txt']))
                self.assertIn('test.txt', site_git.run_git(['status']))
                self.assertIn('initial', site_git.run_git(['log', '1']))
                with self.assertRaises(CommandError):
                    site_git.run_git(['reset', '--hard'])
                with self.assertRaisesMessage(CommandError, 'not clean'):
                    site_git.run_git(['pull'])

    def test_windows_paths_and_suggestions(self):
        self.assertEqual(Command.split_input('/open "C:\\work folder\\file.txt"'),
                         ['/open', 'C:\\work folder\\file.txt'])
        self.assertIn('/server restart', command_suggestions('khởi động lại server'))
        self.assertIn('/git status', command_suggestions('github'))
