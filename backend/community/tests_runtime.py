import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import psutil
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from backend.community import site_runtime


class SiteRuntimeTests(SimpleTestCase):
    def test_restart_refuses_external_service_before_touching_others(self):
        with patch.object(site_runtime, 'SERVICES', {'api': {}, 'web': {}}), \
                patch.object(site_runtime, '_find', side_effect=[None, object()]), \
                patch.object(site_runtime, '_owned', return_value=None), \
                patch.object(site_runtime, 'start') as start:
            with self.assertRaisesMessage(CommandError, 'outside site terminal'):
                site_runtime.restart(('api', 'web'))
            start.assert_not_called()

    def test_restart_managed_service(self):
        with patch.object(site_runtime, 'SERVICES', {'api': {}}), \
                patch.object(site_runtime, '_find', return_value=object()), \
                patch.object(site_runtime, '_owned', return_value=object()), \
                patch.object(site_runtime, 'stop', return_value='api: stopped.') as stop, \
                patch.object(site_runtime, 'start', return_value='api: started.') as start:
            self.assertEqual(site_runtime.restart(('api',)), ['api: stopped.', 'api: started.'])
            stop.assert_called_once_with('api')
            start.assert_called_once_with('api')

    def test_start_status_and_stop_only_owned_process(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            services = {
                'probe': {
                    'port': port, 'path': '/', 'marker': 'http.server',
                    'args': lambda: [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
                }
            }
            runtime = root / 'runtime'
            with patch.object(site_runtime, 'ROOT', root), \
                    patch.object(site_runtime, 'RUNTIME', runtime), \
                    patch.object(site_runtime, 'STATE', runtime / 'processes.json'), \
                    patch.object(site_runtime, 'SERVICES', services):
                pid = None
                try:
                    self.assertIn('started', site_runtime.start('probe'))
                    state = site_runtime._state()
                    pid = state['probe']['pid']
                    self.assertIn('healthy', site_runtime.service_status('probe'))
                    self.assertIn('already running', site_runtime.start('probe'))
                    site_runtime._save({})
                    with self.assertRaisesMessage(CommandError, 'refusing to stop'):
                        site_runtime.stop('probe')
                    site_runtime._save(state)
                    self.assertIn('stopped', site_runtime.stop('probe'))
                    self.assertEqual(site_runtime.service_status('probe'), 'probe: stopped')
                finally:
                    if pid and psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        if 'http.server' in ' '.join(process.cmdline()):
                            process.terminate()
                            process.wait(timeout=5)
