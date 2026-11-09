"""Django talks only to the judge coordinator; the coordinator owns its queue."""
import json
from urllib import request, error
from django.conf import settings


class ManagerError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def call_manager(path, method='GET', payload=None):
    base = settings.JUDGE_SERVER_URL.rstrip('/')
    token = settings.JUDGE_AUTH_TOKEN
    req = request.Request(
        f'{base}/api/v1/{path.lstrip("/")}',
        data=json.dumps(payload if payload is not None else {}).encode('utf-8') if method == 'POST' else None,
        method=method,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            return json.load(response)
    except error.HTTPError as exc:
        try:
            message = json.load(exc).get('error', 'Judge Manager rejected request')
        except (ValueError, OSError):
            message = 'Judge Manager rejected request'
        raise ManagerError(message, exc.code) from exc
    except (error.URLError, TimeoutError, ValueError) as exc:
        raise ManagerError('Judge Manager is unavailable') from exc
