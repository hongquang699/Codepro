"""Small dependency-free chat-style interface for the interactive site terminal."""

import os
import shutil
import sys
import unicodedata
from difflib import get_close_matches


EXAMPLES = {
    'status': '/status',
    'server': '/server status',
    'restart': '/server restart',
    'monitor': '/monitor 3',
    'git': '/git status',
    'diff': '/git diff',
    'commit': '/git commit "Mô tả thay đổi"',
    'push': '/git push',
    'open': '/open docs/development/site-terminal.md',
    'file': '/file README.md',
    'chats': '/chats',
    'posts': '/posts',
    'help': '/help',
}


def command_suggestions(query):
    normalized = ''.join(
        character for character in unicodedata.normalize('NFD', query.lower())
        if unicodedata.category(character) != 'Mn'
    ).replace('đ', 'd')
    matches = []
    keywords = (
        (('khoi dong lai', 'restart'), 'restart'),
        (('may chu', 'server', 'chay web', 'chay api'), 'server'),
        (('theo doi', 'quan sat', 'monitor'), 'monitor'),
        (('github', 'git', 'nhanh', 'branch'), 'git'),
        (('thay doi', 'diff'), 'diff'),
        (('commit', 'luu ma'), 'commit'),
        (('push', 'day len'), 'push'),
        (('mo file', 'mo tep', 'open'), 'open'),
        (('xem file', 'doc file', 'file'), 'file'),
        (('tin nhan', 'chat'), 'chats'),
        (('bai viet', 'post'), 'posts'),
    )
    for words, command in keywords:
        if any(word in normalized for word in words):
            matches.append(EXAMPLES[command])
    first = normalized.split(' ', 1)[0].lstrip('/')
    for command in get_close_matches(first, EXAMPLES, n=2, cutoff=0.5):
        matches.append(EXAMPLES[command])
    return list(dict.fromkeys(matches))[:3] or [EXAMPLES['help'], EXAMPLES['status']]


def _enable_color(stream):
    if not getattr(stream, 'isatty', lambda: False)() or os.getenv('NO_COLOR') is not None:
        return False
    if os.name != 'nt':
        return os.getenv('TERM', '') != 'dumb'
    try:
        import ctypes
        import msvcrt

        kernel = ctypes.windll.kernel32
        handle = msvcrt.get_osfhandle(stream.fileno())
        mode = ctypes.c_uint()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError, ValueError):
        return False


class TerminalUI:
    def __init__(self, output, errors, username, project_name='HQ'):
        self.output = output
        self.errors = errors
        self.username = username
        self.project_name = project_name
        self.color = _enable_color(sys.stdout) and getattr(output, 'isatty', lambda: False)()
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        try:
            '╭─╮│╰╯›●'.encode(encoding)
            self.unicode = True
        except UnicodeError:
            self.unicode = False

    def tint(self, value, color):
        return f'\x1b[{color}m{value}\x1b[0m' if self.color else value

    def banner(self):
        width = min(68, max(38, shutil.get_terminal_size((76, 24)).columns - 2))
        if self.unicode:
            top, side, bottom, fill = '╭', '│', '╰', '─'
            right_top, right_bottom = '╮', '╯'
        else:
            top, side, bottom, fill = '+', '|', '+', '-'
            right_top = right_bottom = '+'
        lines = [
            'CodePro Terminal',
            f'Project {self.project_name}  ·  Admin {self.username}',
            'Quản trị, chat và theo dõi hệ thống',
        ]
        inner = width - 4
        frame = [top + fill * (width - 2) + right_top]
        for line in lines:
            frame.append(f'{side}  {line[:inner].ljust(inner)}{side}')
        frame.append(bottom + fill * (width - 2) + right_bottom)
        self.output.write('\n' + self.tint('\n'.join(frame), '36'))
        self.output.write('  /help  /status  /server status  /chats  /quit\n')
        self.output.write('  Thử: /server status  ·  /git status  ·  /open README.md\n')

    def prompt(self):
        marker = '›' if self.unicode else '>'
        return '\n' + self.tint(f'{marker} ', '36')

    def response(self, value):
        value = value.rstrip()
        if not value:
            return
        marker = '●' if self.unicode else '*'
        self.output.write('\n' + self.tint(f'{marker} CodePro', '32'))
        for line in value.splitlines():
            self.output.write('  ' + line)

    def error(self, value):
        marker = '!' if not self.unicode else '●'
        self.errors.write('\n' + self.tint(f'{marker} Lỗi', '31'))
        self.errors.write('  ' + str(value))

    def followup(self, action):
        next_steps = {
            'server': '/status  ·  /monitor 3  ·  /server logs api',
            'git': '/git diff  ·  /git log 5',
            'open': '/file README.md  ·  /git diff',
            'file': '/open README.md',
        }
        if action in next_steps:
            self.output.write(self.tint('  Gợi ý tiếp: ', '90') + next_steps[action])

    def clear(self):
        if self.color:
            sys.stdout.write('\x1b[2J\x1b[H')
            sys.stdout.flush()
        else:
            self.output.write('\n' * 12)
