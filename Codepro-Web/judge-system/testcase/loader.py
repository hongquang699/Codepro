"""
Testcase Loader for Judge System.
Loads input and expected output testcases from disk or problem package directory.
"""

import os
import glob
import re
import json
from typing import List
from .subtask import TestCaseInfo
from security.encryption import file_cipher

class TestcaseLoader:
    @staticmethod
    def load_manifest(problem_dir: str) -> dict:
        try:
            with open(os.path.join(problem_dir, 'testcases.json'), 'r', encoding='utf-8') as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @staticmethod
    def load_from_directory(problem_dir: str, manifest: dict = None) -> List[TestCaseInfo]:
        """
        Loads testcases from a directory containing .in and .out / .ans files.
        Looks in 'cases/', 'testcases/', or directly in problem_dir.
        """
        cases_dir = problem_dir
        for sub in ["cases", "testcases", "tests"]:
            candidate = os.path.join(problem_dir, sub)
            if os.path.isdir(candidate):
                cases_dir = candidate
                break

        if not os.path.exists(cases_dir):
            return []

        # Find all .in files
        in_files = glob.glob(os.path.join(cases_dir, "*.in"))
        
        # Natural sort
        def natural_keys(text):
            return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]

        in_files.sort(key=natural_keys)
        configured = {str(item.get('id')): item for item in (manifest or {}).get('cases', [])
                      if isinstance(item, dict) and item.get('id') is not None}
        in_files_by_name = {os.path.splitext(os.path.basename(path))[0]: path for path in in_files}
        configured_order = [str(item.get('id')) for item in (manifest or {}).get('cases', [])
                            if isinstance(item, dict) and str(item.get('id')) in in_files_by_name]
        ordered_names = configured_order + [name for name in in_files_by_name if name not in configured_order]

        testcases: List[TestCaseInfo] = []
        for idx, case_name in enumerate(ordered_names, start=1):
            in_path = in_files_by_name[case_name]
            base_name = os.path.splitext(in_path)[0]
            
            # Check for matching .out or .ans
            out_path = base_name + ".out"
            if not os.path.exists(out_path):
                out_path = base_name + ".ans"
            
            if not os.path.exists(out_path):
                continue

            try:
                in_data = file_cipher.read_file(in_path).decode('utf-8', errors='replace')
                out_data = file_cipher.read_file(out_path).decode('utf-8', errors='replace')
            except OSError:
                continue

            case_name = os.path.basename(base_name)
            
            # Detect subtask from name if patterned: subtask1_case01 or s1_01
            subtask_id = 1
            m = re.search(r'(?:subtask|s|st)[_-]?(\d+)', case_name, re.IGNORECASE)
            if m:
                subtask_id = int(m.group(1))
            case_meta = configured.get(case_name, {})
            try:
                subtask_id = int(case_meta.get('subtask', subtask_id))
            except (TypeError, ValueError):
                subtask_id = 1
            try:
                points = float(case_meta.get('points', 10.0))
                if points < 0 or points != points or points == float('inf'):
                    points = 10.0
            except (TypeError, ValueError):
                points = 10.0

            testcases.append(TestCaseInfo(
                id=idx,
                name=case_name,
                input_data=in_data,
                expected_output=out_data,
                subtask_id=subtask_id,
                points=points
            ))

        return testcases
