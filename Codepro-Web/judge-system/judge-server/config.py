"""
Configuration Loader for Judge Server.
Parses YAML configurations for server, workers, limits, and paths.
"""

import os
import yaml
from typing import Dict, Any

def _load_project_env(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

class ServerConfig:
    def __init__(self, config_dir: str = None):
        if not config_dir:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(current_dir, "..", "config")
        
        self.config_dir = os.path.abspath(config_dir)
        _load_project_env(os.path.abspath(os.path.join(self.config_dir, '..', '..', '.env')))
        self.judge_cfg = self._load_yaml("judge.yml")
        self.workers_cfg = self._load_yaml("workers.yml")
        self.limits_cfg = self._load_yaml("limits.yml")

        # Server Settings
        server_info = self.judge_cfg.get("server", {})
        self.host = server_info.get("host", "0.0.0.0")
        self.port = int(server_info.get("port", 9999))
        self.auth_token = os.getenv('JUDGE_AUTH_TOKEN', server_info.get("auth_token", ""))
        if not self.auth_token:
            raise ValueError('JUDGE_AUTH_TOKEN must be set in the environment or project .env file')
        self.heartbeat_interval = int(server_info.get("heartbeat_interval", 10))

        # Paths
        paths = self.judge_cfg.get("paths", {})
        root_dir = os.path.abspath(os.path.join(self.config_dir, ".."))
        self.storage_dir = os.path.abspath(os.getenv('JUDGE_STORAGE_DIR', os.path.join(root_dir, paths.get("storage", "./storage"))))
        default_data_root = os.path.abspath(os.path.join(root_dir, '..', '..', '..', 'Codepro-Data'))
        data_root = os.getenv('CODEPRO_DATA_ROOT') or default_data_root
        self.problem_data_dir = os.path.abspath(os.getenv(
            'JUDGE_PROBLEM_DATA_DIR', os.path.join(data_root, 'problem-data', 'problems')))
        self.logs_dir = os.path.abspath(os.path.join(root_dir, paths.get("logs", "./logs")))
        self.tmp_dir = os.path.abspath(os.getenv('JUDGE_TMP_DIR', os.path.join(self.storage_dir, 'executables')))

        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
