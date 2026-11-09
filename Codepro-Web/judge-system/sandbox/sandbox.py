"""
Unified Sandbox Interface for Judge System.
Combines process isolation, resource caps, filesystem sandboxing, and security validation.
"""

import os
from dataclasses import dataclass
from typing import Optional, List

from .process import ProcessRunner, ProcessExecutionResult
from .filesystem import FilesystemSandbox
from .security import SecurityScanner

@dataclass
class SandboxResult:
    verdict: str         # "AC", "TLE", "MLE", "OLE", "RE", "SE", "SEC"
    time_ms: int
    memory_kb: int
    stdout: str
    stderr: str
    exit_code: int
    message: str = ""

class Sandbox:
    def __init__(self, base_storage_dir: Optional[str] = None):
        self.fs = FilesystemSandbox(base_storage_dir)

    def create_environment(self, prefix: str = "run_") -> str:
        """Sets up an isolated directory for code execution."""
        return self.fs.create_sandbox_dir(prefix)

    def cleanup_environment(self, env_path: str):
        """Cleans up the isolated directory."""
        self.fs.clean_sandbox_dir(env_path)

    def execute(
        self,
        cmd: List[str],
        stdin_data: str = "",
        time_limit_sec: float = 1.0,
        memory_limit_mb: int = 256,
        output_limit_bytes: int = 33554432,
        cwd: Optional[str] = None,
        env: Optional[dict] = None
    ) -> SandboxResult:
        """
        Runs the command in a sandbox and returns the verdict and resource usage.
        """
        proc_res: ProcessExecutionResult = ProcessRunner.run_process(
            cmd=cmd,
            stdin_data=stdin_data,
            time_limit_sec=time_limit_sec,
            memory_limit_mb=memory_limit_mb,
            output_limit_bytes=output_limit_bytes,
            cwd=cwd,
            env=env
        )

        # Classify verdict
        if proc_res.is_sec:
            return SandboxResult(
                verdict="SEC",
                time_ms=proc_res.time_ms,
                memory_kb=proc_res.memory_kb,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                exit_code=proc_res.exit_code,
                message="Security Violation: Prohibited system call or resource limit breach"
            )

        if proc_res.is_tle:
            return SandboxResult(
                verdict="TLE",
                time_ms=proc_res.time_ms,
                memory_kb=proc_res.memory_kb,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                exit_code=proc_res.exit_code,
                message="Time Limit Exceeded"
            )

        if proc_res.is_mle:
            return SandboxResult(
                verdict="MLE",
                time_ms=proc_res.time_ms,
                memory_kb=proc_res.memory_kb,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                exit_code=proc_res.exit_code,
                message="Memory Limit Exceeded"
            )

        if proc_res.is_ole:
            return SandboxResult(
                verdict="OLE",
                time_ms=proc_res.time_ms,
                memory_kb=proc_res.memory_kb,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                exit_code=proc_res.exit_code,
                message="Output Limit Exceeded"
            )

        if proc_res.exit_code != 0:
            return SandboxResult(
                verdict="RE",
                time_ms=proc_res.time_ms,
                memory_kb=proc_res.memory_kb,
                stdout=proc_res.stdout,
                stderr=proc_res.stderr,
                exit_code=proc_res.exit_code,
                message=f"Runtime Error (Exit code {proc_res.exit_code})"
            )

        # Executed normally, verdict will be determined by checker
        return SandboxResult(
            verdict="OK",
            time_ms=proc_res.time_ms,
            memory_kb=proc_res.memory_kb,
            stdout=proc_res.stdout,
            stderr=proc_res.stderr,
            exit_code=0,
            message="Execution completed successfully"
        )
