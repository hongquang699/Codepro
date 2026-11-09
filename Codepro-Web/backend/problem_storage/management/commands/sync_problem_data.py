from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from backend.problem_storage.archive_sync import DEFAULT_PREFIX, download, upload


class Command(BaseCommand):
    help = 'Upload or download private problem-data snapshots from S3/MinIO.'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=('upload', 'download'))
        parser.add_argument('--source', default=str(settings.CODEPRO_DATA_ROOT),
                            help='Directory containing problem-data, contest-data and storage/contests')
        parser.add_argument('--destination',
                            help='New external directory for the downloaded snapshot')
        parser.add_argument('--bucket', default=settings.PROBLEM_STORAGE_PRIVATE_BUCKET)
        parser.add_argument('--prefix', default=DEFAULT_PREFIX)

    def handle(self, *args, **options):
        try:
            if options['action'] == 'upload':
                result = upload(options['source'], bucket=options['bucket'],
                                prefix=options['prefix'])
            else:
                if not options['destination']:
                    raise ValueError('--destination is required for download')
                result = download(options['destination'], bucket=options['bucket'],
                                  prefix=options['prefix'])
        except (ValueError, OSError, RuntimeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"{options['action']}: {result['file_count']} files, "
            f"{result['bytes']} archive bytes, SHA-256 {result['sha256']}"))
