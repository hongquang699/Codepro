"""
Verdict Calculator: Synthesizes individual testcase results into an overall submission verdict,
total score, peak time, and peak memory.
"""
from typing import List, Dict, Any, Tuple


class VerdictCalculator:
    # Priority for dominant overall verdict
    VERDICT_PRIORITY = {
        "IE": 1,
        "CE": 2,
        "RTE": 3,
        "TLE": 4,
        "MLE": 5,
        "OLE": 6,
        "WA": 7,
        "AC": 8,
    }

    @classmethod
    def calculate(cls, testcase_results: List[Dict[str, Any]], total_testcases: int = None) -> Tuple[str, float, int, int]:
        """
        Returns: (final_verdict, total_score, max_time_ms, max_memory_kb)
        """
        if not testcase_results:
            return "IE", 0.0, 0, 0

        total_score = 0.0
        max_time_ms = 0
        max_memory_kb = 0
        dominant_verdict = "AC"
        lowest_priority = 999

        for res in testcase_results:
            v = res.get("verdict", "IE")
            score = float(res.get("score", 0))
            t_ms = int(res.get("time_ms", 0))
            m_kb = int(res.get("memory_kb", 0))

            total_score += score
            if t_ms > max_time_ms:
                max_time_ms = t_ms
            if m_kb > max_memory_kb:
                max_memory_kb = m_kb

            prio = cls.VERDICT_PRIORITY.get(v, 99)
            if prio < lowest_priority:
                lowest_priority = prio
                dominant_verdict = v

        # If any test failed, overall verdict is the worst error (e.g. WA or TLE)
        # If all AC, verdict is AC
        all_ac = all(r.get("verdict") == "AC" for r in testcase_results)
        if all_ac:
            dominant_verdict = "AC"

        return dominant_verdict, total_score, max_time_ms, max_memory_kb
