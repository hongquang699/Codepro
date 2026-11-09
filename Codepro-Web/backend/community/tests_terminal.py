import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from backend.community.models import Conversation, Message, Notification, Post
from backend.judge.models import Profile


class SiteTerminalTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user('operator', password='unused', is_staff=True)
        self.member = user_model.objects.create_user('member', password='unused')
        self.staff_profile = Profile.objects.get_or_create(user=self.staff)[0]
        self.member_profile = Profile.objects.get_or_create(user=self.member)[0]
        self.post = Post.objects.create(
            author=self.member_profile, title='Old title', slug='old-title', content='Old body',
        )

    def test_requires_active_staff_user(self):
        with self.assertRaises(CommandError):
            call_command('site_terminal', '--user', 'member', 'status')

    def test_unique_staff_opens_without_username(self):
        output = StringIO()
        call_command('site_terminal', 'server', 'status', stdout=output)
        self.assertIn('api:', output.getvalue())

    def test_interactive_slash_commands_keep_separate_output_lines(self):
        output = StringIO()
        with patch('builtins.input', side_effect=['/status', '/quit']), \
                patch('backend.community.site_runtime.service_status', side_effect=lambda name: f'{name}: stopped'):
            call_command('site_terminal', '--user', 'operator', stdout=output)
        self.assertIn('CodePro Terminal', output.getvalue())
        self.assertIn('  api: stopped\n  web: stopped', output.getvalue())

    def test_edit_post_from_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'body.txt'
            path.write_text('New body\nwith second line', encoding='utf-8')
            call_command('site_terminal', '--user', 'operator', 'edit-post', str(self.post.pk), 'content', str(path))
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'New body\nwith second line')
        self.assertEqual(LogEntry.objects.get(object_id=str(self.post.pk)).user, self.staff)

    def test_send_message_and_restrict_chat_reads(self):
        call_command('site_terminal', '--user', 'operator', 'send', 'member', 'Hello there')
        chat = Conversation.objects.get()
        self.assertEqual(Message.objects.get(conversation=chat).content, 'Hello there')
        self.assertEqual(Notification.objects.get(recipient=self.member_profile).notification_type, 'message')
        other_staff = get_user_model().objects.create_user('other_staff', password='unused', is_staff=True)
        with self.assertRaisesMessage(CommandError, 'Conversation not found'):
            call_command('site_terminal', '--user', other_staff.username, 'read', str(chat.pk))
