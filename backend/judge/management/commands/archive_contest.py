from django.core.management.base import BaseCommand, CommandError
from backend.judge.models import Contest
from backend.judge.services.contest_archive import export_contest, verify_archive


class Command(BaseCommand):
    help = 'Lưu cuộc thi đã kết thúc vào ZIP riêng tư, hoặc kiểm tra bản lưu.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Đường dẫn ZIP riêng tư, ngoài thư mục web công khai')
        parser.add_argument('--contest', help='Mã cuộc thi cần lưu')
        parser.add_argument('--verify', action='store_true')

    def handle(self, *args, **options):
        if bool(options['contest']) == bool(options['verify']):
            raise CommandError('Chọn --contest KEY hoặc --verify.')
        try:
            if options['verify']:
                manifest = verify_archive(options['path'])
            else:
                manifest = export_contest(options['contest'], options['path'])
        except (ValueError, OSError, KeyError, Contest.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"{manifest['contest_key']}: {len(manifest['files'])} tệp hợp lệ"))
        if manifest['missing_packages']:
            self.stderr.write('Thiếu gói bài toán: ' + ', '.join(manifest['missing_packages']))
