"""
Checker: Evaluates participant output against expected output.
Supports: Exact, Token/Whitespace-insensitive, Float tolerance, and Custom checker.
"""
from typing import Tuple


class Checker:
    def __init__(self, mode: str = "token", float_tolerance: float = 1e-6):
        self.mode = mode
        self.float_tolerance = float_tolerance

    def check(self, user_output: str, expected_output: str) -> Tuple[bool, str]:
        """
        Returns: (is_correct, feedback_message)
        """
        if user_output is None:
            user_output = ""
        if expected_output is None:
            expected_output = ""

        # Normalize line breaks
        u_out = user_output.replace("\r\n", "\n").rstrip()
        e_out = expected_output.replace("\r\n", "\n").rstrip()

        if u_out == e_out:
            return True, "Correct answer"

        if self.mode == "token":
            # Token-by-token comparison (whitespace insensitive)
            u_tokens = u_out.split()
            e_tokens = e_out.split()

            if len(u_tokens) != len(e_tokens):
                return False, f"Output token count mismatch: expected {len(e_tokens)}, got {len(u_tokens)}"

            for idx, (ut, et) in enumerate(zip(u_tokens, e_tokens), 1):
                if ut == et:
                    continue
                # Try floating point comparison
                try:
                    uf = float(ut)
                    ef = float(et)
                    if abs(uf - ef) <= self.float_tolerance or abs(uf - ef) / max(abs(ef), 1.0) <= self.float_tolerance:
                        continue
                except ValueError:
                    pass

                return False, f"Mismatch at token {idx}: expected '{et}', got '{ut}'"

            return True, "Correct answer (tokens match)"

        return False, "Wrong answer"
