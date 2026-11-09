"""
Regex-based Input Validator for Judge System.
Validates input structure against expected regular expression patterns.
"""

import re
from typing import Tuple

class RegexValidator:
    @staticmethod
    def validate(input_data: str, pattern: str) -> Tuple[bool, str]:
        """
        Validates input against a given regex pattern.
        """
        try:
            match = re.search(pattern, input_data, re.MULTILINE)
            if match:
                return True, "Input matches regular expression pattern"
            return False, "Input failed regex validation"
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"
