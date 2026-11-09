"""
Compiler: Compiles source code in various languages with time and output limits.
"""
import os
import subprocess
import tempfile
import time
from typing import Tuple


class Compiler:
    def __init__(self, work_dir: str = None):
        self.work_dir = work_dir or tempfile.gettempdir()

    def compile(self, language: str, source_code: str, submission_id: int = 0) -> Tuple[bool, str, str]:
        """
        Compile code. Returns: (success, executable_or_entry_path, compiler_output)
        For interpreted languages (Python, JS), syntax is checked or returned as-is.
        """
        lang = language.lower()
        sub_dir = os.path.join(self.work_dir, f"sub_{submission_id}_{int(time.time()*1000)}")
        os.makedirs(sub_dir, exist_ok=True)

        if "cpp" in lang or "c++" in lang:
            src_file = os.path.join(sub_dir, "solution.cpp")
            exe_file = os.path.join(sub_dir, "solution.exe" if os.name == "nt" else "solution")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source_code)
            
            cmd = ["g++", "-O3", "-std=c++17", src_file, "-o", exe_file]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if proc.returncode != 0:
                    return False, "", proc.stderr or proc.stdout
                return True, exe_file, proc.stderr or "Compilation successful"
            except FileNotFoundError:
                # Fallback if g++ not found on local path
                return False, "", "g++ compiler not found on system PATH"
            except subprocess.TimeoutExpired:
                return False, "", "Compilation timed out (>15s)"

        elif "c" == lang:
            src_file = os.path.join(sub_dir, "solution.c")
            exe_file = os.path.join(sub_dir, "solution.exe" if os.name == "nt" else "solution")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source_code)
            
            cmd = ["gcc", "-O3", src_file, "-o", exe_file]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if proc.returncode != 0:
                    return False, "", proc.stderr or proc.stdout
                return True, exe_file, proc.stderr or "Compilation successful"
            except Exception as e:
                return False, "", str(e)

        elif "py" in lang:
            src_file = os.path.join(sub_dir, "solution.py")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source_code)
            
            # Syntax validation
            try:
                compile(source_code, "solution.py", "exec")
                return True, src_file, "Python syntax verified"
            except SyntaxError as se:
                return False, "", f"SyntaxError: {se}"

        elif "java" in lang:
            src_file = os.path.join(sub_dir, "Main.java")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(source_code)
            try:
                proc = subprocess.run(["javac", src_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if proc.returncode != 0:
                    return False, "", proc.stderr
                return True, os.path.join(sub_dir, "Main.class"), "Java compilation successful"
            except Exception as e:
                return False, "", str(e)

        # Default fallback
        src_file = os.path.join(sub_dir, f"solution.{lang}")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write(source_code)
        return True, src_file, "Ready"
