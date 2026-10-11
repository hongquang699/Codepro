"""Small dependency-free chat-style interface for the interactive site terminal."""

import os
import shutil
import sys


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

    def clear(self):
        if self.color:
            sys.stdout.write('\x1b[2J\x1b[H')
            sys.stdout.flush()
        else:
            self.output.write('\n' * 12)
