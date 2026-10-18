"""
Job Executor for Judge System Workers.
Coordinates the entire lifecycle of compiling, testcase execution, and score computation.
"""

import os
import shutil
import logging
from contextlib import nullcontext
from typing import Optional
from .job import JudgeJob
from .result import JudgeResult
from .compiler import WorkerCompiler
from .runner import WorkerRunner
from testcase.manager import TestcaseManager
from testcase.versioned import materialize_version
from judging.score import Scorer
from judging.subtasks import SubtaskJudge
from judging.verdict import Verdict
from sandbox.security import SecurityScanner

logger = logging.getLogger("JobExecutor")

class JobExecutor:
    def __init__(self, problem_base_dir: str, storage_base_dir: str):
        self.problem_base_dir = os.path.abspath(problem_base_dir)
        self.storage_base_dir = os.path.abspath(storage_base_dir)
        self.executables_dir = os.path.join(self.storage_base_dir, "executables")
        
        self.compiler = WorkerCompiler(self.executables_dir)
        self.runner = WorkerRunner()
        self.testcase_mgr = TestcaseManager(self.problem_base_dir)

    def execute_job(self, job: JudgeJob) -> JudgeResult:
        """
        Executes a JudgeJob and generates the final JudgeResult.
        """
        logger.info(f"Starting execution of job {job.job_id} (Problem: {job.problem_code}, Lang: {job.language})")

        # 0. Pre-Execution Security Scanning
        is_safe, violations = SecurityScanner.scan_source(job.language, job.source_code)
        if not is_safe:
            violation_msg = "\n".join(violations)
            logger.warning(f"Job {job.job_id} failed security validation: {violation_msg}")
            return JudgeResult(
                job_id=job.job_id,
                verdict=Verdict.CE,
                score=0.0,
                points_earned=0.0,
                max_points=100.0,
                compiler_output=f"Lỗi bảo mật (Security Restriction): Phát hiện mã nguồn chứa lệnh cấm hoặc hàm hệ thống nguy hiểm.\n{violation_msg}",
                error_message=f"Bị từ chối do vi phạm chính sách an ninh hệ thống chấm: {violations[0]}"
            )

        # 1. Compilation
        compile_res = self.compiler.compile_job(
            job_id=job.job_id,
            language=job.language,
            source_code=job.source_code
        )

        if not compile_res.success:
            logger.info(f"Job {job.job_id} failed compilation: {compile_res.error_message}")
            return JudgeResult(
                job_id=job.job_id,
                verdict=Verdict.CE,
                score=0.0,
                points_earned=0.0,
                max_points=100.0,
                compiler_output=compile_res.compiler_output,
                error_message=compile_res.error_message
            )

        binary_path = compile_res.binary_path

        # 2. Load testcases
        version_context = materialize_version(job.problem_version) if job.problem_version else nullcontext(None)
        with version_context as version_dir:
            testcases = self.testcase_mgr.get_testcases(job.problem_code, problem_dir=version_dir)
            subtasks = self.testcase_mgr.get_subtasks(job.problem_code, problem_dir=version_dir) if job.subtask_mode else []
        if not testcases:
            logger.error(f"No testcases found for problem {job.problem_code}")
            return JudgeResult(
                job_id=job.job_id,
                verdict=Verdict.SE,
                score=0.0,
                compiler_output=compile_res.compiler_output,
                error_message=f"No testcases available for problem '{job.problem_code}'."
            )

        # Apply job-level time/memory limit overrides if specified
        for tc in testcases:
            if job.time_limit_sec:
                tc.time_limit_sec = job.time_limit_sec
            if job.memory_limit_mb:
                tc.memory_limit_mb = job.memory_limit_mb

        # 3. Execution
        tc_results = []
        tc_results_dict = {}

        for tc in testcases:
            res = self.runner.run_case(
                language=job.language,
                binary_or_script=binary_path,
                testcase=tc,
                checker_type=job.checker_type,
                checker_path=job.checker_path,
                float_epsilon=job.float_epsilon
            )
            tc_results.append(res)
            tc_results_dict[tc.id] = res

        # 4. Subtasks vs Standard Scoring
        if job.subtask_mode:
            eval_res = SubtaskJudge.evaluate_subtasks(subtasks, tc_results_dict)
            
            max_time = max(r.get("time_ms", 0) for r in tc_results)
            max_mem = max(r.get("memory_kb", 0) for r in tc_results)
            passed_cnt = sum(1 for r in tc_results if r.get("verdict") == Verdict.AC)

            final_result = JudgeResult(
                job_id=job.job_id,
                verdict=eval_res["verdict"],
                score=eval_res["score"],
                points_earned=eval_res["total_earned"],
                max_points=eval_res["max_points"],
                time_ms=max_time,
                memory_kb=max_mem,
                compiler_output=compile_res.compiler_output,
                passed_count=passed_cnt,
                total_count=len(tc_results),
                testcases=tc_results,
                subtasks=eval_res["subtasks"]
            )
        else:
            agg = Scorer.calculate_submission_result(tc_results, total_problem_points=100.0)
            final_result = JudgeResult(
                job_id=job.job_id,
                verdict=agg["verdict"],
                score=agg["score"],
                points_earned=agg["points_earned"],
                max_points=agg["max_points"],
                time_ms=agg["time_ms"],
                memory_kb=agg["memory_kb"],
                compiler_output=compile_res.compiler_output,
                passed_count=agg["passed_count"],
                total_count=agg["total_count"],
                testcases=tc_results
            )

        logger.info(f"Job {job.job_id} completed with verdict: {final_result.verdict} ({final_result.score}%)")
        return final_result
