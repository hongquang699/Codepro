"""
Unified Validator Engine for Judge System.
Coordinates input verification using regex or testlib validators.
"""

from typing import Tuple, Optional
from .regex_validator import RegexValidator
from .testlib_validator import TestlibValidator

class Validator:
    @staticmethod
    def validate_testcase(
        input_data: str,
        validator_type: str = "none", # "none", "regex", "testlib"
        pattern: Optional[str] = None,
        validator_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validates input testcase structure and constraints.
        Returns: (is_valid: bool, message: str)
        """
        if validator_type == "regex" and pattern:
            return RegexValidator.validate(input_data, pattern)
        elif validator_type == "testlib" and validator_path:
            return TestlibValidator.validate(validator_path, input_data)
        elif validator_type == "none":
            return True, "No validation required"
        else:
            return True, "Validator skipped (no configuration provided)"
