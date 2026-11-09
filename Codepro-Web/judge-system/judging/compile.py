"""
Compiler Manager for Judge System.
Compiles submissions for compiled languages and verifies syntax for interpreted ones.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional, List
import yaml

try:
    from sandbox.process import IsolatedRunnerHelper
except ImportError:  # pragma: no cover - judge imported outside its package root
    IsolatedRunnerHelper = None

SANDBOX_UID = 65534

@dataclass
class CompileResult:
    success: bool
    binary_path: Optional[str]
    compiler_output: str
    error_message: str = ""

class Compiler:
    @staticmethod
    def _compiler_env():
        return {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TZ', 'SYSTEMROOT', 'WINDIR', 'TMP', 'TEMP', 'TMPDIR', 'HOME', 'USERPROFILE')
                if key in os.environ}

    @staticmethod
    def _sandbox_preexec(build_dir: str, time_limit_sec: float):
        """Compile as nobody: `#include "/proc/1/environ"` or a test file must not leak through diagnostics."""
        if os.name == "nt" or IsolatedRunnerHelper is None:
            return None
        if os.getuid() == 0:
            for root, dirs, files in os.walk(build_dir):
                for name in [root, *(os.path.join(root, f) for f in dirs + files)]:
                    os.chown(name, SANDBOX_UID, SANDBOX_UID)
        return IsolatedRunnerHelper.get_preexec_fn(
            time_limit_sec=time_limit_sec, memory_limit_mb=1024, max_processes=64,
            max_output_bytes=256 * 1024 * 1024, enable_seccomp=False,
            target_uid=SANDBOX_UID, target_gid=SANDBOX_UID)

    def __init__(self, languages_config_path: Optional[str] = None):
        if not languages_config_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            languages_config_path = os.path.join(current_dir, "..", "config", "languages.yml")
        
        self.languages = {}
        if os.path.exists(languages_config_path):
            with open(languages_config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.languages = data.get("languages", {})

    def compile(
        self,
        language: str,
        source_code: str,
        build_dir: str,
        time_limit_sec: float = 15.0
    ) -> CompileResult:
        """
        Compiles the source code inside build_dir.
        """
        os.makedirs(build_dir, exist_ok=True)
        lang_info = self.languages.get(language)
        if not lang_info:
            return CompileResult(
                success=False,
                binary_path=None,
                compiler_output="",
                error_message=f"Unsupported language: {language}"
            )

        source_file_name = lang_info.get("source_file", "solution.txt")
        source_path = os.path.join(build_dir, source_file_name)

        # Write source code
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        # For non-compiled languages (Python, JS)
        is_compiled = lang_info.get("is_compiled", False)
        if not is_compiled:
            # Syntax validation if compile_cmd exists
            compile_cmd_template = lang_info.get("compile_cmd")
            if compile_cmd_template:
                cmd = [arg.replace("{source}", source_path) for arg in compile_cmd_template]
                try:
                    proc = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=time_limit_sec,
                        env=self._compiler_env(),
                        preexec_fn=self._sandbox_preexec(build_dir, time_limit_sec),
                    )
                    if proc.returncode != 0:
                        return CompileResult(
                            success=False,
                            binary_path=None,
                            compiler_output=proc.stderr or proc.stdout,
                            error_message="Syntax check failed"
                        )
                except Exception as e:
                    return CompileResult(
                        success=False,
                        binary_path=None,
                        compiler_output=str(e),
                        error_message="Compiler process error"
                    )

            return CompileResult(
                success=True,
                binary_path=source_path,
                compiler_output="Syntax check passed"
            )

        # For compiled languages
        binary_file_name = lang_info.get("binary_file", "solution.exe")
        binary_path = os.path.join(build_dir, binary_file_name)

        compile_cmd_template = lang_info.get("compile_cmd", [])
        if not compile_cmd_template:
            return CompileResult(
                success=False,
                binary_path=None,
                compiler_output="",
                error_message="No compile command configured for this language"
            )

        cmd = [
            arg.replace("{source}", source_path).replace("{binary}", binary_path)
            for arg in compile_cmd_template
        ]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=time_limit_sec,
                cwd=build_dir,
                env=self._compiler_env(),
                preexec_fn=self._sandbox_preexec(build_dir, time_limit_sec),
            )

            output = (proc.stdout + "\n" + proc.stderr).strip()

            if proc.returncode != 0 or not os.path.exists(binary_path):
                return CompileResult(
                    success=False,
                    binary_path=None,
                    compiler_output=output,
                    error_message=f"Compilation failed with exit code {proc.returncode}"
                )

            return CompileResult(
                success=True,
                binary_path=os.path.abspath(binary_path),
                compiler_output=output
            )

        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                binary_path=None,
                compiler_output="Compilation timed out",
                error_message="Compilation Time Limit Exceeded"
            )
        except Exception as e:
            return CompileResult(
                success=False,
                binary_path=None,
                compiler_output=str(e),
                error_message=f"Compiler exception: {str(e)}"
            )
