"""Bot defense mechanisms for registration forms."""
import time
from typing import Tuple

class BotDefense:
    MIN_SUBMISSION_TIME_SEC = 2.0  # humans take > 2s to fill form

    @classmethod
    def verify(cls, honeypot_value: str, form_loaded_timestamp: float) -> Tuple[bool, str]:
        # Honeypot check
        if honeypot_value and str(honeypot_value).strip():
            return False, "Phát hiện spam bot (honeypot triggered)."
        
        # Timing check
        now = time.time()
        if form_loaded_timestamp and (now - form_loaded_timestamp < cls.MIN_SUBMISSION_TIME_SEC):
            return False, "Thao tác quá nhanh. Vui lòng thử lại."
            
        return True, "OK"
