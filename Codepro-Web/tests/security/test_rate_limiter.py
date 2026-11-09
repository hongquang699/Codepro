from django.test import SimpleTestCase
from collections import OrderedDict

from security.api_security.rate_limit import RateLimiter


class RateLimiterTest(SimpleTestCase):
    def setUp(self):
        self.original = (RateLimiter._requests, RateLimiter._max_keys, RateLimiter._last_sweep)
        RateLimiter._requests = OrderedDict()
        RateLimiter._max_keys = 2
        RateLimiter._last_sweep = 0

    def tearDown(self):
        RateLimiter._requests, RateLimiter._max_keys, RateLimiter._last_sweep = self.original

    def test_repeated_requests_are_blocked(self):
        self.assertTrue(RateLimiter.check_limit('same-ip', max_requests=2)[0])
        self.assertTrue(RateLimiter.check_limit('same-ip', max_requests=2)[0])
        self.assertFalse(RateLimiter.check_limit('same-ip', max_requests=2)[0])

    def test_unique_clients_cannot_grow_state_without_bound(self):
        for key in ('first', 'second', 'third'):
            RateLimiter.check_limit(key)
        self.assertLessEqual(len(RateLimiter._requests), 2)
