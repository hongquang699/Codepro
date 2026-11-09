"""Resolve the external problem-data root for standalone maintenance scripts."""

import os
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent


def data_root():
    configured = os.getenv('CODEPRO_DATA_ROOT')
    if not configured:
        env_file = PROJECT / '.env'
        if env_file.is_file():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                if line.startswith('CODEPRO_DATA_ROOT='):
                    configured = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    return Path(configured or PROJECT.parent.parent / 'Codepro-Data').expanduser().resolve()
