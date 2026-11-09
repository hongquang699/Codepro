"""
Unified Checker Engine for Judge System.
Selects and executes the appropriate checker strategy (standard, float, custom).
"""

from typing import Tuple, Optional
from .standard import StandardChecker
from .float import FloatChecker
from .custom import CustomChecker

class Checker:
    @staticmethod
    def evaluate(
        user_output: str,
        expected_output: str,
        input_data: str = "",
        checker_type: str = "standard", # "standard", "float", "custom"
        checker_binary_or_script: Optional[str] = None,
        float_epsilon: float = 1e-6
    ) -> Tuple[bool, str]:
        """
        Evaluates participant output against expected output or custom judge.
        Returns: (is_correct: bool, message: str)
        """
        if checker_type == "custom" and checker_binary_or_script:
            return CustomChecker.run_custom(
                checker_path=checker_binary_or_script,
                input_data=input_data,
                user_output=user_output,
                expected_output=expected_output
            )
        elif checker_type == "float":
            return FloatChecker.check_float(
                user_output=user_output,
                expected_output=expected_output,
                eps=float_epsilon
            )
        elif checker_type == "line":
            return StandardChecker.check_lines(
                user_output=user_output,
                expected_output=expected_output
            )
        else: # default to standard token comparison
            return StandardChecker.check_tokens(
                user_output=user_output,
                expected_output=expected_output
            )
