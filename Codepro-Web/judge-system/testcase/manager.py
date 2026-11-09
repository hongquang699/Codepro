"""
Testcase Manager for Judge System.
Unified coordinator for fetching, caching, and organizing testcases into subtasks.
"""

import os
from typing import List, Dict
from .loader import TestcaseLoader
from .cache import TestcaseCache
from .subtask import TestCaseInfo, SubtaskInfo

class TestcaseManager:
    def __init__(self, problem_base_dir: str):
        self.problem_base_dir = os.path.abspath(problem_base_dir)
        self.cache = TestcaseCache()

    def get_testcases(self, problem_code: str, problem_dir=None) -> List[TestCaseInfo]:
        """
        Returns all testcases for a problem, utilizing caching where possible.
        """
        problem_dir = problem_dir or os.path.join(self.problem_base_dir, problem_code)
        manifest = TestcaseLoader.load_manifest(problem_dir)
        testcases = TestcaseLoader.load_from_directory(problem_dir, manifest)
        
        # Also check storage/testcases/{problem_code} if empty
        if not testcases and problem_dir == os.path.join(self.problem_base_dir, problem_code):
            storage_cases = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "storage", "testcases", problem_code
            )
            if os.path.exists(storage_cases):
                testcases = TestcaseLoader.load_from_directory(storage_cases)

        return testcases

    def get_subtasks(self, problem_code: str, total_points: float = 100.0, problem_dir=None) -> List[SubtaskInfo]:
        """
        Organizes testcases into subtasks with proportional points.
        """
        testcases = self.get_testcases(problem_code, problem_dir=problem_dir)
        if not testcases:
            return []

        # Group by subtask_id
        grouped: Dict[int, List[TestCaseInfo]] = {}
        for tc in testcases:
            grouped.setdefault(tc.subtask_id, []).append(tc)

        subtask_list: List[SubtaskInfo] = []
        problem_dir = problem_dir or os.path.join(self.problem_base_dir, problem_code)
        manifest = TestcaseLoader.load_manifest(problem_dir)
        configured = {int(item['id']): item for item in manifest.get('subtasks', [])
                      if isinstance(item, dict) and str(item.get('id', '')).isdigit()}
        for st_id in sorted(grouped.keys()):
            cases = grouped[st_id]
            settings = configured.get(st_id, {})
            depends_on = settings.get('depends_on', [st_id - 1] if st_id > 1 else [])
            subtask_list.append(SubtaskInfo(
                subtask_id=st_id,
                points=max(0.0, float(settings.get('points', sum(tc.points for tc in cases)))),
                scoring_method=settings.get('scoring_method', 'all_or_nothing'),
                depends_on=[int(value) for value in depends_on],
                testcases=cases
            ))

        return subtask_list
