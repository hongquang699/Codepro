from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from security.middleware import FullSecurityMiddleware, is_internal_ip


class SecurityMiddlewareRegressionTests(SimpleTestCase):
    def test_login_page_get_does_not_consume_login_rate_limit(self):
        middleware = FullSecurityMiddleware(lambda request: HttpResponse('ok'))
        factory = RequestFactory()
        with patch('security.middleware.RateLimiter.check_limit', return_value=(True, 9)) as limiter:
            self.assertEqual(middleware(factory.get('/admin/login/')).status_code, 200)
            limiter.assert_not_called()
            self.assertEqual(middleware(factory.post('/admin/login/')).status_code, 200)
            limiter.assert_called_once_with('login:127.0.0.1', max_requests=10, window_seconds=60)

    def test_private_network_range_is_complete(self):
        for address in ('127.0.0.1', '10.1.2.3', '172.16.0.1',
                        '172.25.0.7', '172.31.255.254', '192.168.1.5', '::1'):
            with self.subTest(address=address):
                self.assertTrue(is_internal_ip(address))
        for address in ('172.15.255.255', '172.32.0.1', '203.0.113.1', 'not-an-ip'):
            with self.subTest(address=address):
                self.assertFalse(is_internal_ip(address))

    def test_internal_endpoint_allows_full_lan_range_only(self):
        middleware = FullSecurityMiddleware(lambda request: HttpResponse('ok'))
        factory = RequestFactory()
        with patch('security.middleware.SecurityLogger.log_security_alert'):
            allowed = factory.get('/api/v1/internal/health', REMOTE_ADDR='172.25.0.7')
            denied = factory.get('/api/v1/internal/health', REMOTE_ADDR='203.0.113.1')
            self.assertEqual(middleware(allowed).status_code, 200)
            self.assertEqual(middleware(denied).status_code, 403)
