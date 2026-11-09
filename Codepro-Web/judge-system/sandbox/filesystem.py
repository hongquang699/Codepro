"""
Filesystem isolation manager for Judge Sandbox.
Manages isolated execution folders, workspace sandboxing, and safe cleanup.
"""

import os
import shutil
import uuid
from pathlib import Path

class FilesystemSandbox:
    def __init__(self, base_dir: str = None):
        if base_dir:
            self.base_dir = os.path.abspath(base_dir)
        else:
            # Use the mounted writable storage when the container root is read-only.
            current_dir = os.path.dirname(os.path.abspath(__file__))
            storage_dir = os.getenv('JUDGE_STORAGE_DIR', os.path.join(current_dir, '..', 'storage'))
            self.base_dir = os.path.abspath(os.path.join(storage_dir, 'executables'))
        os.makedirs(self.base_dir, exist_ok=True)

    def create_sandbox_dir(self, prefix: str = "run_") -> str:
        """Creates a unique temporary folder for an execution run."""
        unique_name = f"{prefix}{uuid.uuid4().hex[:12]}"
        sandbox_path = os.path.join(self.base_dir, unique_name)
        os.makedirs(sandbox_path, exist_ok=True)
        return sandbox_path

    def clean_sandbox_dir(self, path: str):
        """Safely removes the sandbox folder."""
        if not path or not os.path.exists(path):
            return
        
        # Security check: must reside inside base_dir
        abs_path = os.path.realpath(path)
        if os.path.commonpath([os.path.realpath(self.base_dir), abs_path]) != os.path.realpath(self.base_dir):
            raise PermissionError(f"Attempted to clean path outside sandbox base: {path}")

        try:
            shutil.rmtree(abs_path, ignore_errors=True)
        except Exception:
            pass

    @staticmethod
    def sanitize_path(path: str, root_dir: str) -> str:
        """Prevents path traversal outside of root directory."""
        resolved = os.path.realpath(os.path.join(root_dir, path))
        if os.path.commonpath([os.path.realpath(root_dir), resolved]) != os.path.realpath(root_dir):
            raise ValueError(f"Path traversal detected: {path}")
        return resolved
