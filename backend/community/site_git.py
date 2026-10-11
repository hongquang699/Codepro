"""Allowlisted Git operations for the local CodePro terminal."""

import os
import re
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError

from backend.community.site_files import resolve_file


ROOT = Path(settings.BASE_DIR).resolve()
MAX_OUTPUT = 30_000


def _run(arguments, timeout=30):
    environment = os.environ.copy()
    environment['GIT_TERMINAL_PROMPT'] = '0'
    try:
        result = subprocess.run(
            ['git', *arguments], cwd=ROOT, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace', timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CommandError(f'Git command failed: {type(exc).__name__}') from exc
    output = re.sub(r'(https?://)[^/@\s]+@', r'\1***@', result.stdout).strip()
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + '\n… (output truncated)'
    if result.returncode:
        raise CommandError(output or f'Git exited with code {result.returncode}.')
    return output or '(no changes)'


def run_git(arguments):
    if not arguments:
        raise CommandError('Usage: git status|log|diff|staged|branch|add|commit|pull|push')
    action, *rest = arguments
    if action == 'status' and not rest:
        return _run(['status', '--short', '--branch'])
    if action == 'branch' and not rest:
        return _run(['branch', '--list'])
    if action == 'log' and len(rest) <= 1:
        count = rest[0] if rest else '10'
        if not count.isdecimal() or not 1 <= int(count) <= 50:
            raise CommandError('Commit count must be between 1 and 50.')
        return _run(['log', '--oneline', '--decorate', '-n', count])
    if action in ('diff', 'staged') and len(rest) <= 1:
        command = ['diff'] + (['--cached'] if action == 'staged' else [])
        if rest:
            path = resolve_file(rest[0])
            command += ['--', str(path.relative_to(ROOT))]
        return _run(command)
    if action == 'add' and len(rest) == 1:
        path = resolve_file(rest[0])
        relative = str(path.relative_to(ROOT))
        _run(['add', '--', relative])
        return f'Staged {relative}.'
    if action == 'commit' and rest:
        message = ' '.join(rest).strip()
        if not 3 <= len(message) <= 200:
            raise CommandError('Commit message must contain 3 to 200 characters.')
        staged = _run(['diff', '--cached', '--name-only'])
        if staged == '(no changes)':
            raise CommandError('Nothing is staged. Use /git add PATH first.')
        return _run(['commit', '-m', message], timeout=120)
    if action == 'pull' and not rest:
        if _run(['status', '--porcelain']) != '(no changes)':
            raise CommandError('Working tree is not clean; commit or resolve changes before pull.')
        return _run(['pull', '--ff-only'], timeout=120)
    if action == 'push' and not rest:
        branch = _run(['branch', '--show-current'])
        if branch == '(no changes)':
            raise CommandError('Cannot push from a detached HEAD.')
        return _run(['push', 'origin', 'HEAD'], timeout=120)
    raise CommandError('Usage: git status|log [N]|diff [PATH]|staged [PATH]|branch|add PATH|commit MESSAGE|pull|push')
