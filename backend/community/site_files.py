"""Project-scoped file viewing and editor launch for the terminal."""

import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError


ROOT = Path(settings.BASE_DIR).resolve()


def resolve_file(raw_path):
    if not raw_path or raw_path.startswith('-'):
        raise CommandError('Provide a project file path.')
    try:
        candidate = Path(raw_path)
        path = (candidate if candidate.is_absolute() else ROOT / candidate).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CommandError(f'File not found: {raw_path}') from exc
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise CommandError('Only files inside this project can be opened.')
    return path


def preview(raw_path, lines=60):
    path = resolve_file(raw_path)
    if path.stat().st_size > 1_000_000:
        raise CommandError('File exceeds the 1 MB preview limit. Use /open to edit it.')
    try:
        data = path.read_bytes()
        if b'\x00' in data:
            raise CommandError('Binary files cannot be previewed in the terminal.')
        content = data.decode('utf-8')
    except UnicodeError as exc:
        raise CommandError('File is not UTF-8 text. Use /open to view it in the editor.') from exc
    content_lines = content.splitlines()
    numbered = [f'{index:>4}  {line}' for index, line in enumerate(content_lines[:lines], 1)]
    suffix = '\n… (more lines available)' if len(content_lines) > lines else ''
    return f'{path.relative_to(ROOT)}\n' + '\n'.join(numbered) + suffix


def open_in_editor(raw_path):
    path = resolve_file(raw_path)
    executable = shutil.which('code')
    if os.name == 'nt':
        if executable:
            command = Path(executable).resolve()
            executable = str(command.parent.parent / 'Code.exe') if command.suffix.lower() in ('.cmd', '.bat') else str(command)
        if not executable or not Path(executable).is_file():
            raise CommandError('VS Code was not found. Install VS Code or add its code command to PATH.')
    elif not executable:
        raise CommandError('VS Code was not found. Install it or add code to PATH.')
    try:
        subprocess.Popen(
            [executable, '--reuse-window', str(path)], cwd=ROOT,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise CommandError(f'Cannot open VS Code: {exc}') from exc
    return f'Opening {path.relative_to(ROOT)} in VS Code.'
