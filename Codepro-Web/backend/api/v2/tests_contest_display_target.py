from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.judge.models import Contest


class ContestDisplayTargetTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        start = timezone.now() + timedelta(days=1)
        for target in ('both', 'web', 'client'):
            Contest.objects.create(
                key=f'VIS_{target.upper()}',
                name=f'Contest {target}',
                start_time=start,
                end_time=start + timedelta(hours=2),
                display_target=target,
            )

    def test_web_and_client_lists_use_their_display_target(self):
        web_v2 = self.api.get('/api/v2/contests')
        client_v2 = self.api.get('/api/v2/contests', HTTP_X_CODEPROOJ_SURFACE='client')
        web_v1 = self.api.get('/api/v1/contests/')

        self.assertEqual({c['key'] for c in web_v2.data['data']['objects']}, {'VIS_BOTH', 'VIS_WEB'})
        self.assertEqual({c['key'] for c in client_v2.data['data']['objects']}, {'VIS_BOTH', 'VIS_CLIENT'})
        self.assertEqual({c['key'] for c in web_v1.data['data']}, {'VIS_BOTH', 'VIS_WEB'})

    def test_detail_is_hidden_on_the_other_surface(self):
        self.assertEqual(self.api.get('/api/v2/contest/VIS_CLIENT').status_code, 403)
        self.assertEqual(self.api.get('/api/v2/contest/VIS_CLIENT', HTTP_X_CODEPROOJ_SURFACE='client').status_code, 200)
        self.assertEqual(self.api.get('/api/v2/contest/VIS_WEB', HTTP_X_CODEPROOJ_SURFACE='client').status_code, 403)
        self.assertEqual(self.api.get('/api/v1/contests/VIS_CLIENT/').status_code, 404)

    def test_admin_can_update_target_and_invalid_values_are_rejected(self):
        admin = User.objects.create_user('target_admin', is_staff=True)
        self.api.force_authenticate(user=admin)
        invalid = self.api.put('/api/v2/contest/VIS_BOTH', {'display_target': 'unknown'}, format='json')
        self.assertEqual(invalid.status_code, 400)
        saved = self.api.put('/api/v2/contest/VIS_BOTH', {'display_target': 'client'}, format='json')
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data['data']['object']['display_target'], 'client')
