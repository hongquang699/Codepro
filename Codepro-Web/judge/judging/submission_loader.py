"""
Submission Loader: loads submission code, language settings, testcases, and execution limits.
"""
import os
from typing import Dict, Any, List


class SubmissionLoader:
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir

    def load_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw submission payload.
        """
        submission_id = data.get("id") or data.get("submission_id", 0)
        source_code = data.get("source_code") or data.get("source", "")
        language = (data.get("language") or "cpp17").lower()
        problem_id = str(data.get("problem_id") or data.get("problem", "SUMA"))
        
        time_limit = float(data.get("time_limit", 1.0))
        memory_limit = int(data.get("memory_limit", 256))
        
        testcases = data.get("testcases", [])
        if not testcases:
            testcases = self.load_problem_testcases(problem_id)
            
        return {
            "id": submission_id,
            "problem_id": problem_id,
            "language": language,
            "source_code": source_code,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
            "testcases": testcases,
        }

    def load_problem_testcases(self, problem_id: str) -> List[Dict[str, Any]]:
        """
        Load testcases from local problem storage if available.
        """
        tc_path = os.path.join(self.storage_dir, "testcases", problem_id)
        testcases = []
        if os.path.exists(tc_path):
            in_files = sorted([f for f in os.listdir(tc_path) if f.endswith(".in")])
            for i, in_file in enumerate(in_files, 1):
                base_name = os.path.splitext(in_file)[0]
                out_file = f"{base_name}.out"
                in_full = os.path.join(tc_path, in_file)
                out_full = os.path.join(tc_path, out_file)
                
                inp = ""
                outp = ""
                if os.path.exists(in_full):
                    with open(in_full, "r", encoding="utf-8", errors="ignore") as f:
                        inp = f.read()
                if os.path.exists(out_full):
                    with open(out_full, "r", encoding="utf-8", errors="ignore") as f:
                        outp = f.read()
                        
                testcases.append({
                    "id": i,
                    "input": inp,
                    "expected_output": outp,
                    "points": 10,
                    "is_hidden": i > 2
                })
        return testcases
