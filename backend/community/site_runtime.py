"""Local development service control for the staff management terminal."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import psutil
from django.conf import settings
from django.core.management.base import CommandError


ROOT = Path(settings.BASE_DIR)
RUNTIME = ROOT / 'storage' / 'temp' / 'site-terminal'
STATE = RUNTIME / 'processes.json'
SERVICES = {
    'api': {'port': 8000, 'path': '/api/v2/problems', 'marker': 'manage.py',
            'args': lambda: [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload']},
    'web': {'port': 8888, 'path': '/', 'marker': 'apps/web/server.js',
            'args': lambda: [shutil.which('node') or 'node', 'apps/web/server.js']},
    'judge': {'port': 9999, 'path': '/api/v1/health', 'marker': 'judge-system/judge-server/main.py',
              'args': lambda: [sys.executable, 'judge-system/judge-server/main.py']},
    'worker': {'port': None, 'path': None, 'marker': 'run_anticheat_worker',
               'args': lambda: [sys.executable, 'manage.py', 'run_anticheat_worker']},
}
HTTP = build_opener(ProxyHandler({}))


def _state():
    try:
        data = json.loads(STATE.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data), encoding='utf-8')
    temporary.replace(STATE)


def _matches(process, name):
    try:
        args = ' '.join(process.cmdline()).replace('\\', '/').lower()
        cwd = Path(process.cwd()).resolve()
        return SERVICES[name]['marker'] in args and cwd == ROOT.resolve()
    except (psutil.Error, OSError):
        return False


def _owned(name):
    entry = _state().get(name)
    if not isinstance(entry, dict):
        return None
    try:
        process = psutil.Process(int(entry['pid']))
        if abs(process.create_time() - float(entry['created'])) < 1 and _matches(process, name):
            return process
    except (KeyError, ValueError, TypeError, psutil.Error):
        pass
    return None


def _find(name):
    port = SERVICES[name]['port']
    if port:
        try:
            connections = psutil.net_connections(kind='tcp')
        except psutil.Error:
            connections = []
        for connection in connections:
            if connection.status == psutil.CONN_LISTEN and connection.laddr.port == port and connection.pid:
                try:
                    process = psutil.Process(connection.pid)
                    if _matches(process, name):
                        return process
                except psutil.Error:
                    continue
    else:
        for process in psutil.process_iter(['pid', 'cmdline']):
            if _matches(process, name):
                return process
    return None


def _http_ok(name):
    config = SERVICES[name]
    if not config['port']:
        return None
    url = f"http://127.0.0.1:{config['port']}{config['path']}"
    try:
        with HTTP.open(url, timeout=1.5) as response:
            return response.status == 200
    except (OSError, URLError, ValueError):
        return False


def service_status(name):
    process = _find(name)
    if process is None:
        return f'{name}: stopped'
    try:
        memory = process.memory_info().rss / 1024 / 1024
        managed = _owned(name)
        owner = 'managed' if managed and managed.pid == process.pid else 'external'
        health = _http_ok(name)
        state = 'healthy' if health else ('unhealthy' if health is False else 'running')
        return f'{name}: {state} | pid {process.pid} | {memory:.0f} MB | {owner}'
    except psutil.Error:
        return f'{name}: stopped'


def start(name):
    if name not in SERVICES:
        raise CommandError('Unknown service. Choose api, web, judge, or worker.')
    existing = _find(name)
    if existing:
        return f'{name}: already running (pid {existing.pid}).'
    if name == 'web' and not shutil.which('node'):
        raise CommandError('Node.js is not installed or missing from PATH.')
    RUNTIME.mkdir(parents=True, exist_ok=True)
    log_path = RUNTIME / f'{name}.log'
    flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    environment = os.environ.copy()
    environment['PYTHONUNBUFFERED'] = '1'
    try:
        with log_path.open('ab') as log:
            process = subprocess.Popen(
                SERVICES[name]['args'](), cwd=ROOT, env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                creationflags=flags, start_new_session=os.name != 'nt',
            )
    except OSError as exc:
        raise CommandError(f'Cannot start {name}: {exc}') from exc
    state = _state()
    state[name] = {'pid': process.pid, 'created': psutil.Process(process.pid).create_time()}
    _save(state)
    for _ in range(15):
        if process.poll() is not None:
            state = _state()
            state.pop(name, None)
            _save(state)
            raise CommandError(f'{name} exited with code {process.returncode}. See: {log_path}')
        if _find(name):
            return f'{name}: started (pid {process.pid}). Log: {log_path}'
        time.sleep(0.2)
    return f'{name}: starting (pid {process.pid}). Log: {log_path}'


def stop(name):
    if name not in SERVICES:
        raise CommandError('Unknown service. Choose api, web, judge, or worker.')
    process = _owned(name)
    if process is None:
        raise CommandError(f'{name} was not started by site terminal; refusing to stop it.')
    try:
        process.terminate()
        process.wait(timeout=5)
    except psutil.TimeoutExpired:
        raise CommandError(f'{name} did not stop within 5 seconds; inspect pid {process.pid}.')
    except psutil.Error as exc:
        raise CommandError(f'Cannot stop {name}: {exc}') from exc
    state = _state()
    state.pop(name, None)
    _save(state)
    return f'{name}: stopped.'


def restart(names):
    """Restart only services managed by this terminal; check all first."""
    for name in names:
        if name not in SERVICES:
            raise CommandError('Unknown service. Choose api, web, judge, or worker.')
        if _find(name) and _owned(name) is None:
            raise CommandError(f'{name} was started outside site terminal; refusing to restart it.')
    results = []
    for name in names:
        if _owned(name):
            results.append(stop(name))
        results.append(start(name))
    return results


def log_tail(name, lines=30):
    if name not in SERVICES:
        raise CommandError('Unknown service. Choose api, web, judge, or worker.')
    path = RUNTIME / f'{name}.log'
    if not path.is_file():
        raise CommandError(f'No captured log for {name}; it may have been started outside site terminal.')
    with path.open('rb') as log:
        log.seek(max(0, path.stat().st_size - 65536))
        return '\n'.join(log.read().decode('utf-8', errors='replace').splitlines()[-lines:])
