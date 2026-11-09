"""Staff-only downloads of private contest archives."""
import tempfile
from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from backend.judge.models import Contest
from backend.judge.services.contest_archive import export_contest
from .views import IsPlatformAdmin, V2APIView


class ContestArchiveDownload(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, contest):
        obj = get_object_or_404(Contest, key=contest)
        temporary = tempfile.TemporaryDirectory(prefix='hq-contest-')
        try:
            path = Path(temporary.name) / 'archive.zip'
            manifest = export_contest(obj.key, path)
            if manifest['missing_packages']:
                temporary.cleanup()
                return Response({'error': 'Chưa thể tạo bản lưu đầy đủ: thiếu gói bài toán.',
                                 'missing_packages': manifest['missing_packages']}, status=409)
            response = FileResponse(path.open('rb'), as_attachment=True,
                                    filename=f'contest-{obj.pk}.zip', content_type='application/zip')
            response['Cache-Control'] = 'no-store, private'
            response['X-Content-Type-Options'] = 'nosniff'
            original_close = response.close

            def close():
                try:
                    original_close()
                finally:
                    temporary.cleanup()

            response.close = close
            return response
        except ValueError as exc:
            temporary.cleanup()
            return Response({'error': str(exc)}, status=400)
        except BaseException:
            temporary.cleanup()
            raise
