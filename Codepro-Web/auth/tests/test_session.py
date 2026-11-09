from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from backend.auth.services.session import (
    create_auth_session,
    validate_auth_session,
    revoke_auth_session,
    revoke_all_user_sessions,
    get_user_active_sessions,
)


class SessionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='sessionuser',
            email='sessionuser@example.com',
            password='Password123!'
        )

    def test_session_lifecycle(self):
        request = self.factory.get('/')
        token, session = create_auth_session(self.user, request, remember_me=False)

        self.assertIsNotNone(token)
        self.assertTrue(session.is_active)

        # Validate
        validated_user = validate_auth_session(token)
        self.assertEqual(validated_user, self.user)

        # Revoke
        revoked = revoke_auth_session(token)
        self.assertTrue(revoked)

        # Validate after revoke
        self.assertIsNone(validate_auth_session(token))

    def test_revoke_all_user_sessions(self):
        req1 = self.factory.get('/')
        token1, s1 = create_auth_session(self.user, req1)
        token2, s2 = create_auth_session(self.user, req1)

        sessions = get_user_active_sessions(self.user)
        self.assertEqual(len(sessions), 2)

        # Revoke all except token2
        revoke_all_user_sessions(self.user, except_raw_token=token2)

        self.assertIsNone(validate_auth_session(token1))
        self.assertIsNotNone(validate_auth_session(token2))
