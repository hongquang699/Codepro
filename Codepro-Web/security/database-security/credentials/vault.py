"""Database credentials loader."""
import os
from typing import Dict

class DatabaseVault:
    @staticmethod
    def get_credentials() -> Dict[str, str]:
        return {
            'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.environ.get('DB_NAME', 'db.sqlite3'),
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432')
        }
