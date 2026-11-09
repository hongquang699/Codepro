"""
Execution Engine for Judge System.
Executes participant binary/script on a testcase inside the sandbox.
"""

import os
from dataclasses import dataclass
from typing import Optional, List
import yaml
from sandbox.sandbox import Sandbox, SandboxResult

@dataclass
class TestcaseExecutionResult:
    verdict: str
    time_ms: int
    memory_kb: int
    user_output: str
    stderr: str
    message: str

class Executor:
    def __init__(self, languages_config_path: Optional[str] = None):
        if not languages_config_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            languages_config_path = os.path.join(current_dir, "..", "config", "languages.yml")
            
        self.languages = {}
        if os.path.exists(languages_config_path):
            with open(languages_config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.languages = data.get("languages", {})

        self.sandbox = Sandbox()

    def run_testcase(
        self,
        language: str,
        target_path: str,
        input_data: str,
        time_limit_sec: float = 1.0,
        memory_limit_mb: int = 256,
        working_dir: Optional[str] = None
    ) -> TestcaseExecutionResult:
        """
        Executes a testcase against the target binary or script.
        """
        lang_info = self.languages.get(language, {})
        time_mult = float(lang_info.get("time_multiplier", 1.0))
        mem_mult = float(lang_info.get("memory_multiplier", 1.0))

        effective_time_limit = time_limit_sec * time_mult
        effective_mem_limit = int(memory_limit_mb * mem_mult)

        # Build execution command
        run_cmd_template = lang_info.get("run_cmd")
        if not run_cmd_template:
            # Fallback
            if target_path.endswith(".py"):
                cmd = ["python", "-u", target_path]
            elif target_path.endswith(".js"):
                cmd = ["node", target_path]
            else:
                cmd = [target_path]
        else:
            cmd = []
            for arg in run_cmd_template:
                cmd.append(
                    arg.replace("{binary}", target_path)
                       .replace("{source}", target_path)
                       .replace("{memory_limit_mb}", str(effective_mem_limit))
                )

        cwd = working_dir or os.path.dirname(target_path)

        res: SandboxResult = self.sandbox.execute(
            cmd=cmd,
            stdin_data=input_data,
            time_limit_sec=effective_time_limit,
            memory_limit_mb=effective_mem_limit,
            cwd=cwd
        )

        return TestcaseExecutionResult(
            verdict=res.verdict,
            time_ms=res.time_ms,
            memory_kb=res.memory_kb,
            user_output=res.stdout,
            stderr=res.stderr,
            message=res.message
        )
