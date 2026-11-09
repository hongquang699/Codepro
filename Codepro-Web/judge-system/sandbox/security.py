"""
Security Scanner and policy enforcer for Judge submissions.
Detects malicious patterns, banned system headers, and dangerous keywords.
"""

import re
from typing import Tuple, List

class SecurityScanner:
    BANNED_PATTERNS = {
        "cpp": [
            r'#include\s*<windows\.h>',
            r'#include\s*<winsock2?\.h>',
            r'#include\s*<sys/socket\.h>',
            r'#include\s*<sys/ptrace\.h>',
            r'#include\s*<sys/stat\.h>',
            r'#include\s*<sys/mman\.h>',
            r'#include\s*<unistd\.h>',
            r'#include\s*<fcntl\.h>',
            r'#include\s*<dlfcn\.h>',
            r'\bsystem\s*\(',
            r'\bpopen\s*\(',
            r'\bfork\s*\(',
            r'\bexec[lvep]+\s*\(',
            r'\bkill\s*\(',
            r'\bunlink\s*\(',
            r'\bremove\s*\(',
            r'\brename\s*\(',
            r'\bsocket\s*\(',
            r'\bconnect\s*\(',
            r'\bptrace\s*\(',
        ],
        "c": [
            r'#include\s*<windows\.h>',
            r'#include\s*<winsock2?\.h>',
            r'#include\s*<sys/socket\.h>',
            r'#include\s*<sys/ptrace\.h>',
            r'#include\s*<sys/stat\.h>',
            r'#include\s*<sys/mman\.h>',
            r'#include\s*<unistd\.h>',
            r'#include\s*<fcntl\.h>',
            r'#include\s*<dlfcn\.h>',
            r'\bsystem\s*\(',
            r'\bpopen\s*\(',
            r'\bfork\s*\(',
            r'\bexec[lvep]+\s*\(',
            r'\bkill\s*\(',
            r'\bunlink\s*\(',
            r'\bremove\s*\(',
            r'\brename\s*\(',
            r'\bsocket\s*\(',
            r'\bconnect\s*\(',
            r'\bptrace\s*\(',
        ],
        "python": [
            r'(?:import|from)\s+(?:os|subprocess|socket|pty|shutil|ctypes|sys|signal|multiprocessing|threading|importlib|commands|urllib|requests|http|ftplib|telnetlib|webbrowser)\b',
            r'\b__import__\s*\(',
            r'\b(?:os|subprocess|pty)\s*\.',
            r'\b(?:eval|exec|compile)\s*\(',
            r'\bopen\s*\(',
            r'\bgetattr\s*\(\s*(?:__builtins__|builtins)',
            r'\b__subclasses__\b',
            r'\b__globals__\b',
        ],
        "javascript": [
            r'\brequire\s*\(\s*[\'"](?:child_process|net|fs|dgram|cluster|http|https)[\'"]\s*\)',
            r'\bimport\s+.*[\'"](?:child_process|net|fs|dgram|cluster)[\'"]',
            r'\bprocess\.(?:kill|exit|binding|dlopen)\b',
            r'\beval\s*\(',
            r'\bnew\s+Function\s*\(',
        ],
        "java": [
            r'Runtime\.getRuntime\(',
            r'ProcessBuilder',
            r'java\.net\.',
            r'java\.lang\.reflect\.',
            r'System\.exit',
            r'ClassLoader',
        ]
    }

    @classmethod
    def scan_source(cls, language: str, source_code: str) -> Tuple[bool, List[str]]:
        """
        Inspects source code for dangerous keywords or system sabotage.
        Returns: (is_safe, list_of_violations)
        """
        violations = []
        patterns = cls.BANNED_PATTERNS.get('python' if language == 'pypy' else language, [])
        for pat in patterns:
            if re.search(pat, source_code, re.IGNORECASE):
                violations.append(f"Security restriction violated: pattern '{pat}' is prohibited.")

        return (len(violations) == 0, violations)
