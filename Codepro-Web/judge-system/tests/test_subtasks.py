"""
Tests for Judge System Subtask Evaluation.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from testcase.subtask import TestCaseInfo, SubtaskInfo, SubtaskEvaluator
from judging.subtasks import SubtaskJudge

class TestSubtasks(unittest.TestCase):
    def test_all_or_nothing_success(self):
        tc1 = TestCaseInfo(id=1, name="case1", input_data="", expected_output="")
        tc2 = TestCaseInfo(id=2, name="case2", input_data="", expected_output="")
        st = SubtaskInfo(subtask_id=1, points=40.0, scoring_method="all_or_nothing", testcases=[tc1, tc2])

        results = {
            1: {"verdict": "AC", "score": 10.0},
            2: {"verdict": "AC", "score": 10.0}
        }
        score = SubtaskEvaluator.calculate_subtask_score(st, results, {})
        self.assertEqual(score, 40.0)

    def test_all_or_nothing_failure(self):
        tc1 = TestCaseInfo(id=1, name="case1", input_data="", expected_output="")
        tc2 = TestCaseInfo(id=2, name="case2", input_data="", expected_output="")
        st = SubtaskInfo(subtask_id=1, points=40.0, scoring_method="all_or_nothing", testcases=[tc1, tc2])

        results = {
            1: {"verdict": "AC", "score": 10.0},
            2: {"verdict": "WA", "score": 0.0}
        }
        score = SubtaskEvaluator.calculate_subtask_score(st, results, {})
        self.assertEqual(score, 0.0)

    def test_subtask_dependencies(self):
        tc1 = TestCaseInfo(id=1, name="c1", input_data="", expected_output="")
        tc2 = TestCaseInfo(id=2, name="c2", input_data="", expected_output="")
        st1 = SubtaskInfo(subtask_id=1, points=30.0, testcases=[tc1])
        st2 = SubtaskInfo(subtask_id=2, points=70.0, depends_on=[1], testcases=[tc2])

        # If subtask 1 failed, subtask 2 should get 0 despite passing tc2
        results = {
            1: {"verdict": "WA", "score": 0.0},
            2: {"verdict": "AC", "score": 10.0}
        }
        judge_res = SubtaskJudge.evaluate_subtasks([st1, st2], results)
        self.assertEqual(judge_res["total_earned"], 0.0)
        self.assertEqual(judge_res["verdict"], "WA")

if __name__ == "__main__":
    unittest.main()
