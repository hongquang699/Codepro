"""
Standard Token and Line Checker for Judge System.
Compares participant output with jury answer using token or line normalization.
"""

from typing import Tuple

class StandardChecker:
    @staticmethod
    def check_tokens(user_output: str, expected_output: str) -> Tuple[bool, str]:
        """
        Token-by-token comparison ignoring whitespace differences.
        """
        user_tokens = user_output.split()
        expected_tokens = expected_output.split()

        if len(user_tokens) != len(expected_tokens):
            return False, f"Token count mismatch: expected {len(expected_tokens)}, got {len(user_tokens)}"

        for i, (u_tok, e_tok) in enumerate(zip(user_tokens, expected_tokens), start=1):
            if u_tok != e_tok:
                return False, f"Mismatch at token #{i}: expected '{e_tok[:50]}', got '{u_tok[:50]}'"

        return True, "Correct answer"

    @staticmethod
    def check_lines(user_output: str, expected_output: str) -> Tuple[bool, str]:
        """
        Line-by-line comparison stripping trailing whitespace.
        """
        u_lines = [line.rstrip() for line in user_output.strip().splitlines()]
        e_lines = [line.rstrip() for line in expected_output.strip().splitlines()]

        if len(u_lines) != len(e_lines):
            return False, f"Line count mismatch: expected {len(e_lines)}, got {len(u_lines)}"

        for i, (u_line, e_line) in enumerate(zip(u_lines, e_lines), start=1):
            if u_line != e_line:
                return False, f"Mismatch at line #{i}: expected '{e_line[:50]}', got '{u_line[:50]}'"

        return True, "Correct answer"
