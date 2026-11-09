"""
Verdicts and Evaluation Priority for Judge System.
Standard competitive programming verdicts: AC, WA, TLE, MLE, OLE, RE, CE, SE.
"""

from typing import List

class Verdict:
    AC = "AC"    # Accepted
    WA = "WA"    # Wrong Answer
    TLE = "TLE"  # Time Limit Exceeded
    MLE = "MLE"  # Memory Limit Exceeded
    OLE = "OLE"  # Output Limit Exceeded
    RE = "RE"    # Runtime Error
    CE = "CE"    # Compilation Error
    SE = "SE"    # System Error

    # Priority of verdicts when aggregating testcase results (worst verdict wins)
    PRIORITY = {
        CE: 100,
        SE: 90,
        RE: 80,
        MLE: 70,
        TLE: 60,
        OLE: 50,
        WA: 40,
        AC: 10,
    }

    @classmethod
    def get_worst(cls, verdicts: List[str]) -> str:
        """Returns the most severe verdict from a list of testcase verdicts."""
        if not verdicts:
            return cls.SE
        return max(verdicts, key=lambda v: cls.PRIORITY.get(v, 0))

    @classmethod
    def is_passing(cls, verdict: str) -> bool:
        """Returns True if the verdict is Accepted."""
        return verdict == cls.AC
