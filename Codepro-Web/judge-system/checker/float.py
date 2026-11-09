"""
Floating-point Checker for Judge System.
Compares numerical tokens allowing absolute or relative error tolerances.
"""

from typing import Tuple

class FloatChecker:
    @staticmethod
    def check_float(user_output: str, expected_output: str, eps: float = 1e-6) -> Tuple[bool, str]:
        """
        Validates output tokens with absolute or relative error <= eps.
        """
        user_tokens = user_output.split()
        expected_tokens = expected_output.split()

        if len(user_tokens) != len(expected_tokens):
            return False, f"Token count mismatch: expected {len(expected_tokens)}, got {len(user_tokens)}"

        for i, (u_tok, e_tok) in enumerate(zip(user_tokens, expected_tokens), start=1):
            try:
                u_val = float(u_tok)
                e_val = float(e_tok)
            except ValueError:
                # Fallback to string equality if not a number
                if u_tok != e_tok:
                    return False, f"Non-numerical mismatch at token #{i}: expected '{e_tok}', got '{u_tok}'"
                continue

            abs_diff = abs(u_val - e_val)
            rel_diff = abs_diff / max(abs(e_val), 1.0)

            if abs_diff > eps and rel_diff > eps:
                return False, f"Precision mismatch at token #{i}: expected {e_val:.9g}, got {u_val:.9g} (diff: {abs_diff:.4e} > {eps})"

        return True, f"Correct answer within tolerance {eps}"
