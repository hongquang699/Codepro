"""Small, allowlisted terminal for site content and direct messages."""

import shlex
import time
from datetime import timedelta
from io import StringIO
from pathlib import Path

import psutil
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError, OutputWrapper
from django.db import DatabaseError, close_old_connections, connection, transaction
from django.utils import timezone

from backend.community.models import Conversation, Message, Post
from backend.community.services.notification_service import NotificationService
from backend.judge.models import JudgeJob, JudgeWorker, Profile, Submission
from backend.anti_cheat.models import ScanJob
from backend.community import site_runtime
from backend.community import site_files
from backend.community import site_git
from backend.community.terminal_ui import TerminalUI, command_suggestions


HELP = """HỆ THỐNG
  /status                         Dịch vụ, CPU/RAM và hàng đợi
  /server start [SERVICE|all]     Mở API + web, hoặc dịch vụ được chọn
  /server stop SERVICE            Dừng dịch vụ do terminal khởi chạy
  /server restart [SERVICE|all]   Khởi động lại dịch vụ do terminal quản lý
  /server status                  Kiểm tra dịch vụ và tiến trình
  /server logs SERVICE [LINES]    Xem log đã ghi (tối đa 200 dòng)
  /monitor [SECONDS]              Theo dõi liên tục; Ctrl+C để trở lại
  /activity [COUNT]               Bài nộp và job chấm gần đây

NỘI DUNG
  /posts                          Danh sách bài viết
  /show-post ID                   Xem bài viết
  /edit-post ID title|content FILE  Sửa bài viết từ tệp UTF-8
  /file PATH [LINES]              Xem tệp UTF-8 trong project
  /open PATH                      Mở tệp project bằng VS Code

GIT / GITHUB
  /git status                     Trạng thái nhánh và tệp thay đổi
  /git log [COUNT]                Lịch sử commit
  /git diff [PATH]                Xem thay đổi chưa stage
  /git staged [PATH]              Xem thay đổi đã stage
  /git branch                     Danh sách nhánh
  /git add PATH                   Stage một tệp trong project
  /git commit MESSAGE             Commit các tệp đã stage
  /git pull                       Chỉ cập nhật fast-forward khi cây sạch
  /git push                       Đẩy nhánh hiện tại lên origin

TIN NHẮN
  /chats                          Các cuộc trò chuyện của bạn
  /read ID                        Đọc cuộc trò chuyện
  /send USERNAME TEXT             Gửi tin nhắn

PHIÊN LÀM VIỆC
  /help                           Hiện bảng lệnh
  /suggest TEXT                   Gợi ý lệnh theo câu mô tả
  /clear                          Xóa màn hình
  /quit                           Thoát

Có thể bỏ dấu / khi gõ lệnh. Đây là terminal quản trị, không tự xử lý câu hỏi ngôn ngữ tự nhiên."""


class Command(BaseCommand):
    help = 'Admin terminal for editing community posts and chatting with users.'

    def add_arguments(self, parser):
        parser.add_argument('--user', help='Active staff username (required when there is more than one)')
        parser.add_argument('action', nargs='?', help='Command to run once; omit for interactive mode')
        parser.add_argument('arguments', nargs='*', help='Arguments for the command')

    def handle(self, *args, **options):
        username = options['user']
        if not username:
            staff = list(get_user_model().objects.filter(is_active=True, is_staff=True).order_by('pk')[:2])
            if len(staff) == 1:
                username = staff[0].username
            elif options['action']:
                raise CommandError('Specify --user when there are zero or multiple active staff accounts.')
            else:
                username = input('Tên tài khoản quản trị › ').strip()
        user = get_user_model().objects.filter(username=username, is_active=True, is_staff=True).first()
        if user is None:
            raise CommandError('An active staff user is required.')
        self.profile, _ = Profile.objects.get_or_create(user=user)
        self.user = user
        if options['action']:
            self.run_command([options['action'], *options['arguments']])
            return
        ui = TerminalUI(self.stdout, self.stderr, user.username)
        self.interactive = True
        ui.banner()
        while True:
            try:
                line = input(ui.prompt())
            except (EOFError, KeyboardInterrupt):
                self.stdout.write('')
                break
            try:
                parts = self.split_input(line)
                if not parts:
                    continue
                action = parts[0].lstrip('/')
                if action in ('quit', 'exit'):
                    break
                if action == 'clear':
                    ui.clear()
                    ui.banner()
                    continue
                if action == 'monitor':
                    ui.response('Đang theo dõi. Nhấn Ctrl+C để trở lại.')
                    self.run_command(parts)
                    continue
                captured = StringIO()
                original = self.stdout
                try:
                    self.stdout = OutputWrapper(captured)
                    self.run_command(parts)
                finally:
                    self.stdout = original
                ui.response(captured.getvalue())
                ui.followup('git' if action in ('git', 'github', 'gh') else action)
            except (CommandError, ValueError) as exc:
                ui.error(exc)

    def run_command(self, parts):
        if not parts:
            return
        action, *arguments = parts
        action = action.lstrip('/')
        if action in ('help', '?') and not arguments:
            self.stdout.write(HELP)
        elif action == 'status' and not arguments:
            self.show_status()
        elif action == 'server':
            self.server(arguments)
        elif action == 'monitor' and len(arguments) <= 1:
            interval = self.bounded_number(arguments[0], 1, 60) if arguments else 3
            try:
                while True:
                    self.stdout.write(f'\n[{timezone.localtime():%Y-%m-%d %H:%M:%S}]')
                    self.show_status()
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write('\nMonitoring stopped.')
        elif action == 'activity' and len(arguments) <= 1:
            count = self.bounded_number(arguments[0], 1, 50) if arguments else 10
            self.show_activity(count)
        elif action == 'open' and len(arguments) == 1:
            self.stdout.write(site_files.open_in_editor(arguments[0]))
        elif action == 'file' and 1 <= len(arguments) <= 2:
            lines = self.bounded_number(arguments[1], 1, 200) if len(arguments) == 2 else 60
            self.stdout.write(site_files.preview(arguments[0], lines))
        elif action == 'suggest':
            for suggestion in command_suggestions(' '.join(arguments)):
                self.stdout.write(suggestion)
        elif action in ('git', 'github', 'gh'):
            self.stdout.write(site_git.run_git(arguments))
        elif action == 'posts' and not arguments:
            for post in Post.objects.select_related('author__user').order_by('-created_at')[:20]:
                self.stdout.write(f'{post.pk}\t{post.title}\t{post.author.user.username}')
        elif action == 'show-post' and len(arguments) == 1:
            post = self.get_post(arguments[0])
            self.stdout.write(f'{post.pk}: {post.title}\n{post.content}')
        elif action == 'edit-post' and len(arguments) == 3:
            self.edit_post(*arguments)
        elif action == 'chats' and not arguments:
            chats = Conversation.objects.filter(participant_1=self.profile) | Conversation.objects.filter(participant_2=self.profile)
            for chat in chats.select_related('participant_1__user', 'participant_2__user').order_by('-updated_at')[:20]:
                other = chat.participant_2 if chat.participant_1_id == self.profile.pk else chat.participant_1
                self.stdout.write(f'{chat.pk}\t{other.user.username}\t{chat.updated_at:%Y-%m-%d %H:%M}')
        elif action == 'read' and len(arguments) == 1:
            chat = self.get_chat(arguments[0])
            for message in chat.messages.select_related('sender__user').order_by('-created_at')[:100]:
                self.stdout.write(f'{message.created_at:%Y-%m-%d %H:%M} {message.sender.user.username}: {message.content}')
        elif action == 'send' and len(arguments) >= 2:
            self.send(arguments[0], ' '.join(arguments[1:]))
        else:
            if getattr(self, 'interactive', False):
                self.stdout.write('Mình chưa nhận ra lệnh này. Bạn có thể thử:')
                for suggestion in command_suggestions(' '.join(parts)):
                    self.stdout.write(f'  {suggestion}')
            else:
                raise CommandError('Invalid command or arguments. Type help for usage.')

    @staticmethod
    def split_input(line):
        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        lexer.escape = ''  # Windows paths must keep backslashes.
        lexer.commenters = ''
        return list(lexer)

    @staticmethod
    def parse_id(value):
        if not value.isdecimal() or int(value) < 1:
            raise CommandError('ID must be a positive integer.')
        return int(value)

    @staticmethod
    def bounded_number(value, minimum, maximum):
        if not value.isdecimal() or not minimum <= int(value) <= maximum:
            raise CommandError(f'Number must be between {minimum} and {maximum}.')
        return int(value)

    def show_status(self):
        for name in site_runtime.SERVICES:
            self.stdout.write(site_runtime.service_status(name))
        memory = psutil.virtual_memory()
        self.stdout.write(f'Host: CPU {psutil.cpu_percent(interval=None):.0f}% | RAM {memory.percent:.0f}%')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            self.stdout.write(f'Database: connected ({connection.vendor})')
            self.stdout.write(
                f'Data: posts {Post.objects.count()} | chats {Conversation.objects.count()} | '
                f'messages {Message.objects.count()} | submissions queued {Submission.objects.filter(status="QU").count()} | '
                f'grading {Submission.objects.filter(status__in=["P", "G"]).count()}'
            )
            self.stdout.write(
                f'Judge: jobs waiting {JudgeJob.objects.filter(status="WAITING").count()} | '
                f'workers online {JudgeWorker.objects.filter(status="ONLINE", enabled=True, last_heartbeat__gte=timezone.now() - timedelta(minutes=2)).count()} | '
                f'anti-cheat pending {ScanJob.objects.filter(status="PENDING").count()}'
            )
        except DatabaseError:
            close_old_connections()
            self.stdout.write('Database: unavailable')

    def show_activity(self, count):
        self.stdout.write('Recent submissions:')
        for item in Submission.objects.select_related('user__user', 'problem').order_by('-date')[:count]:
            self.stdout.write(f'#{item.pk} {item.date:%Y-%m-%d %H:%M} {item.user.user.username} {item.problem.code} {item.status}/{item.result or "-"}')
        self.stdout.write('Recent judge jobs:')
        for job in JudgeJob.objects.order_by('-created_at')[:count]:
            self.stdout.write(f'#{job.pk} submission {job.submission_id} {job.status}')

    def server(self, arguments):
        if arguments == ['status']:
            for name in site_runtime.SERVICES:
                self.stdout.write(site_runtime.service_status(name))
            return
        if arguments and arguments[0] == 'start' and len(arguments) <= 2:
            target = arguments[1] if len(arguments) == 2 else 'default'
            names = ('api', 'web') if target == 'default' else tuple(site_runtime.SERVICES) if target == 'all' else (target,)
            for name in names:
                self.stdout.write(site_runtime.start(name))
            return
        if len(arguments) == 2 and arguments[0] == 'stop':
            self.stdout.write(site_runtime.stop(arguments[1]))
            return
        if arguments and arguments[0] == 'restart' and len(arguments) <= 2:
            target = arguments[1] if len(arguments) == 2 else 'default'
            names = ('api', 'web') if target == 'default' else tuple(site_runtime.SERVICES) if target == 'all' else (target,)
            for result in site_runtime.restart(names):
                self.stdout.write(result)
            return
        if 2 <= len(arguments) <= 3 and arguments[0] == 'logs':
            lines = self.bounded_number(arguments[2], 1, 200) if len(arguments) == 3 else 30
            self.stdout.write(site_runtime.log_tail(arguments[1], lines))
            return
        raise CommandError('Usage: server start|restart [SERVICE|all], server stop SERVICE, server status, or server logs SERVICE [LINES].')

    def get_post(self, value):
        post = Post.objects.filter(pk=self.parse_id(value)).first()
        if post is None:
            raise CommandError('Post not found.')
        return post

    def get_chat(self, value):
        chat = Conversation.objects.filter(pk=self.parse_id(value)).first()
        if chat is None or self.profile.pk not in (chat.participant_1_id, chat.participant_2_id):
            raise CommandError('Conversation not found for this user.')
        return chat

    def edit_post(self, value, field, filename):
        if field not in ('title', 'content'):
            raise CommandError('Editable fields: title, content.')
        path = Path(filename)
        try:
            if path.stat().st_size > 1_000_000:
                raise CommandError('File exceeds 1 MB.')
            content = path.read_text(encoding='utf-8').strip()
        except (OSError, UnicodeError) as exc:
            raise CommandError(f'Cannot read UTF-8 file: {exc}') from exc
        if not content or (field == 'title' and len(content) > 255):
            raise CommandError('Field is empty or title exceeds 255 characters.')
        with transaction.atomic():
            post = self.get_post(value)
            setattr(post, field, content)
            post.save(update_fields=[field, 'updated_at'])
            LogEntry.objects.create(
                user=self.user,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=str(post.pk),
                object_repr=str(post)[:200],
                action_flag=CHANGE,
                change_message=f'Site terminal changed {field}',
            )
        self.stdout.write(f'Updated post {post.pk} ({field}).')

    def send(self, username, content):
        content = content.strip()
        if not content or len(content) > 5000:
            raise CommandError('Message must contain 1 to 5000 characters.')
        target = Profile.objects.select_related('user').filter(user__username=username, user__is_active=True).first()
        if target is None or target.pk == self.profile.pk:
            raise CommandError('Recipient not found or is the current user.')
        p1, p2 = sorted((self.profile, target), key=lambda p: p.pk)
        with transaction.atomic():
            chat, _ = Conversation.objects.get_or_create(participant_1=p1, participant_2=p2)
            message = Message.objects.create(conversation=chat, sender=self.profile, content=content)
            chat.updated_at = timezone.now()
            chat.save(update_fields=['updated_at'])
            NotificationService.notify(
                recipient=target, sender=self.profile, ntype='message', title='Tin nhắn mới',
                message=f'{self.profile.user.username}: {content[:60]}',
                link=f'/community/messages/conversation.html?id={chat.pk}',
            )
        self.stdout.write(f'Sent message {message.pk} in conversation {chat.pk}.')
