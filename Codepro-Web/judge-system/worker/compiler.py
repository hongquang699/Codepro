"""
Worker-level Compiler wrapper for Judge System.
Manages isolated workspace and artifact generation for each submission.
"""

import os
import re
from judging.compile import Compiler, CompileResult

class WorkerCompiler:
    def __init__(self, base_executables_dir: str):
        self.base_dir = os.path.abspath(base_executables_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self.compiler = Compiler()

    def compile_job(self, job_id: str, language: str, source_code: str) -> CompileResult:
        """
        Compiles the submission inside an isolated directory storage/executables/{job_id}.
        """
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', str(job_id)):
            return CompileResult(False, None, '', 'Invalid job ID')
        job_dir = os.path.join(self.base_dir, f"job_{job_id}")
        os.makedirs(job_dir, exist_ok=True)
        return self.compiler.compile(
            language=language,
            source_code=source_code,
            build_dir=job_dir
        )
