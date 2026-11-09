import http.client
import os
import sys
import threading
import unittest

JUDGE_SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'judge-server'))
if JUDGE_SERVER_DIR not in sys.path:
    sys.path.insert(0, JUDGE_SERVER_DIR)

from main import BoundedJudgeHTTPServer, JudgeHttpHandler, MAX_REQUEST_BYTES


class JudgeManagerHttpLimitsTest(unittest.TestCase):
    def test_oversized_body_is_rejected_before_router(self):
        server = BoundedJudgeHTTPServer(('127.0.0.1', 0), JudgeHttpHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            connection.putrequest('POST', '/api/v1/jobs')
            connection.putheader('Content-Length', str(MAX_REQUEST_BYTES + 1))
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 413)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
