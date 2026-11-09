"""
Comparison Engine for Judge System.
Evaluates program output against expected output using configured checkers.
"""

from typing import Tuple, Optional
from checker.checker import Checker

class Comparator:
    @staticmethod
    def compare(
        user_output: str,
        expected_output: str,
        input_data: str = "",
        checker_type: str = "standard",
        checker_path: Optional[str] = None,
        float_epsilon: float = 1e-6
    ) -> Tuple[bool, str]:
        """
        Runs checker evaluation.
        Returns: (is_correct: bool, message: str)
        """
        return Checker.evaluate(
            user_output=user_output,
            expected_output=expected_output,
            input_data=input_data,
            checker_type=checker_type,
            checker_binary_or_script=checker_path,
            float_epsilon=float_epsilon
        )
