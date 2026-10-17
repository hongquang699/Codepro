from datetime import timedelta
import ipaddress
import re
import uuid
from pathlib import Path
from django.middleware.csrf import get_token
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.judge.models import Language, Problem, Submission, JudgeWorker, JudgeJob, JudgeLog
from backend.judge.permissions.judge_manager import IsJudgeManager
from backend.judge.permissions.authentication import JudgeCookieAuthentication
from backend.judge.services.manager import call_manager, ManagerError


class JudgeAdminView(APIView):
    authentication_classes = [TokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsJudgeManager]

    def finalize_response(self, request, response, *args, **kwargs):
        if request.method == 'GET':
            get_token(request._request)
        return super().finalize_response(request, response, *args, **kwargs)

    def manager(self, path, method='GET'):
        try:
            return None, call_manager(path, method)
        except ManagerError as exc:
            return Response({'error': str(exc)}, status=exc.status), None

    def audit(self, request, action, target='', worker=None, job=None):
        remote = request.META.get('REMOTE_ADDR') or ''
        candidate = request.META.get('HTTP_X_REAL_IP') if remote in ('127.0.0.1', '::1') else remote
        try:
            address = str(ipaddress.ip_address(candidate))
        except ValueError:
            address = None
        return JudgeLog.objects.create(
            actor=request.user, action=action, message=str(target), worker=worker,
            job=job, ip_address=address,
        )


def worker_payload(w):
    meta = w.get('metadata') or {}
    worker_id = w['worker_id']
    mode = w.get('mode', 'enabled')
    raw_status = w.get('status', 'offline').lower()
    if mode == 'maintenance':
        label = 'MAINTENANCE'
    elif mode == 'restart':
        label = 'RESTARTING'
    elif mode == 'disable':
        label = 'DISABLED'
    elif raw_status == 'error':
        label = 'ERROR'
    elif raw_status != 'online':
        label = 'OFFLINE'
    elif w.get('active_jobs', 0):
        label = 'BUSY'
    else:
        label = 'ONLINE'
    return {
        'id': worker_id, 'name': meta.get('name') or worker_id,
        'hostname': meta.get('hostname') or worker_id,
        'ip_address': meta.get('ip_address'), 'os': meta.get('os'),
        'cpu': meta.get('cpu_percent'), 'ram': meta.get('memory_percent'),
        'disk': meta.get('disk_percent'), 'cpu_count': meta.get('cpu_count'),
        'network_tx_kbps': meta.get('network_tx_kbps'), 'network_rx_kbps': meta.get('network_rx_kbps'),
        'memory_limit': meta.get('max_memory_mb'),
        'supported_languages': meta.get('supported_languages') or [],
        'error': meta.get('error'),
        'current_job': meta.get('current_job'), 'active_jobs': w.get('active_jobs', 0),
        'status': label, 'mode': mode, 'last_seen_sec_ago': w.get('last_seen_sec_ago'),
    }


def submission_payload(sub, detail=False):
    data = {
        'id': sub.id, 'user': sub.user.user.username, 'problem': sub.problem.code,
        'contest': sub.contest.key if sub.contest else None,
        'language': sub.language.name, 'status': sub.get_status_display(),
        'verdict': sub.result, 'score': sub.points, 'time_ms': round((sub.time or 0) * 1000, 2),
        'memory_kb': sub.memory, 'submitted_at': sub.date.isoformat(),
    }
    if detail:
        data['source'] = sub.source
        data['error'] = sub.error
        data['testcases'] = [
            {'case': tc.case, 'verdict': tc.status, 'time_ms': round(tc.time * 1000, 2),
             'memory_kb': tc.memory, 'points': tc.points, 'feedback': tc.feedback}
            for tc in sub.test_cases.all()
        ]
        data['jobs'] = [
            {'id': job.remote_id, 'worker': job.worker.name if job.worker else None,
             'status': job.status, 'attempts': job.attempts}
            for job in sub.judge_jobs.select_related('worker').all().order_by('-created_at')[:10]
        ]
    return data


class AccessView(JudgeAdminView):
    def get(self, request):
        role = 'Admin' if request.user.is_staff or request.user.is_superuser else 'Judge Manager'
        return Response({'username': request.user.username, 'role': role})


class DashboardView(JudgeAdminView):
    def get(self, request):
        err, health = self.manager('health')
        if err: return err
        err, worker_data = self.manager('workers')
        if err: return err
        err, queue_data = self.manager('admin/queue')
        if err: return err
        workers = [worker_payload(w) for w in worker_data.get('workers', [])]
        today_start = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        remote_errors = sum(1 for r in queue_data.get('results', [])
                            if r.get('verdict') in ('SE', 'IE') and (r.get('completed_at') or 0) >= today_start)
        return Response({
            'health': health, 'workers': workers, 'queue': queue_data.get('jobs', []),
            'paused': queue_data.get('paused', False),
            'running': sum(w['active_jobs'] for w in workers),
            'errors_today': JudgeLog.objects.filter(level='ERROR', created_at__date=timezone.localdate()).count() + remote_errors,
        })


class WorkersView(JudgeAdminView):
    def get(self, request):
        err, data = self.manager('workers')
        if err: return err
        workers = [worker_payload(w) for w in data.get('workers', [])]
        for w in workers:
            JudgeWorker.objects.update_or_create(name=w['id'], defaults={
                'hostname': w['hostname'], 'status': w['status'],
                'cpu_count': w['cpu_count'] or 0, 'memory_limit': w['memory_limit'] or 0,
                'supported_languages': w['supported_languages'],
                'enabled': w['mode'] == 'enabled', 'maintenance': w['mode'] == 'maintenance',
                'last_heartbeat': timezone.now() - timedelta(seconds=w['last_seen_sec_ago'] or 0),
            })
        return Response({'workers': workers})


class WorkerView(JudgeAdminView):
    def get(self, request, worker_id):
        response = WorkersView().get(request)
        if response.status_code != 200: return response
        worker = next((w for w in response.data['workers'] if w['id'] == worker_id), None)
        if not worker: return Response({'error': 'Worker not found'}, status=404)
        worker['logs'] = list(JudgeLog.objects.filter(worker__name=worker_id).values('level', 'action', 'message', 'created_at')[:30])
        return Response(worker)


class WorkerActionView(JudgeAdminView):
    def post(self, request, worker_id, action):
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', worker_id):
            return Response({'error': 'Invalid worker ID'}, status=400)
        if action not in ('enable', 'disable', 'maintenance', 'restart'):
            return Response({'error': 'Invalid action'}, status=400)
        worker = JudgeWorker.objects.filter(name=worker_id).first()
        log = self.audit(request, f'worker.{action}', worker_id, worker=worker)
        err, data = self.manager(f'admin/workers/{worker_id}/{action}', 'POST')
        if err:
            log.level, log.message = 'ERROR', f'{worker_id}: {err.data.get("error", "Manager error")}'
            log.save(update_fields=['level', 'message'])
            return err
        return Response(data)


class QueueView(JudgeAdminView):
    def get(self, request):
        err, data = self.manager('admin/queue')
        if err: return err
        waiting = data.get('jobs', [])
        results = data.get('results', [])
        jobs = [dict(j, status='WAITING') for j in waiting]
        jobs += [dict(j) for j in results if j.get('status') != 'Queued']
        remote_ids = [j.get('job_id') for j in jobs]
        local = {j.remote_id: j for j in JudgeJob.objects.filter(remote_id__in=remote_ids).select_related('submission__user__user', 'submission__contest', 'worker')}
        now = timezone.now().timestamp()
        for job in jobs:
            record = local.get(job['job_id'])
            sub = record.submission if record else None
            raw_date = job.get('submitted_at')
            job.update({
                'user': sub.user.user.username if sub else None,
                'contest': sub.contest.key if sub and sub.contest else None,
                'problem_code': sub.problem.code if sub else job.get('problem_code'),
                'language': sub.language.name if sub else job.get('language'),
                'submission_id': sub.id if sub else job.get('submission_id'),
                'priority': record.priority if record else job.get('priority'),
                'waiting_seconds': round(max(0, now - raw_date)) if raw_date else None,
                'assigned_worker': job.get('assigned_worker') or (record.worker.name if record and record.worker else None),
            })
        return Response({'paused': data.get('paused', False), 'jobs': jobs})


class QueueActionView(JudgeAdminView):
    def post(self, request, action):
        if action not in ('pause', 'resume'):
            return Response({'error': 'Invalid action'}, status=400)
        err, data = self.manager(f'admin/queue/{action}', 'POST')
        if err: return err
        self.audit(request, f'queue.{action}')
        return Response(data)


class JobActionView(JudgeAdminView):
    def post(self, request, job_id, action):
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', job_id):
            return Response({'error': 'Invalid job ID'}, status=400)
        if action not in ('cancel', 'retry'):
            return Response({'error': 'Invalid action'}, status=400)
        job = JudgeJob.objects.filter(remote_id=job_id).first()
        if action == 'retry':
            if not job or job.status not in ('FAILED', 'CANCELLED'):
                return Response({'error': 'Only failed or cancelled jobs can be retried'}, status=409)
            self.audit(request, 'job.retry', job_id, job=job)
            return RejudgeView().post(request, job.submission_id)
        err, data = self.manager(f'admin/queue/{job_id}/cancel', 'POST')
        if err: return err
        if job:
            job.status = 'CANCELLED'
            job.finished_at = timezone.now()
            job.save(update_fields=['status', 'finished_at'])
        self.audit(request, 'job.cancel', job_id, job=job)
        return Response(data)


class SubmissionsView(JudgeAdminView):
    def get(self, request):
        qs = Submission.objects.select_related('user__user', 'problem', 'language', 'contest').order_by('-date')
        return Response({'submissions': [submission_payload(s) for s in qs[:100]]})


class SubmissionView(JudgeAdminView):
    def get(self, request, submission_id):
        sub = Submission.objects.filter(pk=submission_id).select_related('user__user', 'problem', 'language', 'contest').first()
        if not sub: return Response({'error': 'Submission not found'}, status=404)
        return Response(submission_payload(sub, detail=True))


class RejudgeView(JudgeAdminView):
    def post(self, request, submission_id):
        sub = Submission.objects.filter(pk=submission_id).first()
        if not sub: return Response({'error': 'Submission not found'}, status=404)
        if sub.status in ('QU', 'P', 'G') or JudgeJob.objects.filter(submission=sub, status__in=('WAITING', 'RUNNING')).exists():
            return Response({'error': 'Submission is already waiting or running'}, status=409)
        sub.status, sub.result, sub.is_rejudged = 'QU', None, True
        sub.save(update_fields=['status', 'result', 'is_rejudged'])
        self.audit(request, 'submission.rejudge', submission_id)
        from backend.submissions.services.judge_submission import JudgeSubmissionService
        import threading
        threading.Thread(target=JudgeSubmissionService.dispatch, args=(sub.id,), daemon=True).start()
        return Response({'submission_id': sub.id, 'status': 'QUEUED'}, status=202)


class LanguagesView(JudgeAdminView):
    def get(self, request):
        return Response({'languages': list(Language.objects.values('id', 'key', 'name', 'short_name', 'is_active').order_by('name'))})

    def post(self, request):
        raw_key, raw_name = request.data.get('key'), request.data.get('name')
        short_name, common_name = request.data.get('short_name'), request.data.get('common_name')
        if not isinstance(raw_key, str) or not isinstance(raw_name, str):
            return Response({'error': 'Valid key and name are required'}, status=400)
        key, name = raw_key.strip().upper(), raw_name.strip()
        if (not re.fullmatch(r'[A-Z0-9_]{1,20}', key) or not name or len(name) > 50
                or (short_name is not None and not isinstance(short_name, str))
                or (common_name is not None and not isinstance(common_name, str))):
            return Response({'error': 'Valid key and name are required'}, status=400)
        if Language.objects.filter(key=key).exists():
            return Response({'error': 'Language key already exists'}, status=409)
        lang = Language.objects.create(key=key, name=name, short_name=(short_name or name)[:20],
                                       common_name=(common_name or name)[:20], is_active=False)
        self.audit(request, 'language.create', lang.key)
        return Response({'id': lang.id, 'key': lang.key}, status=201)


class LanguageView(JudgeAdminView):
    def patch(self, request, language_id):
        lang = Language.objects.filter(pk=language_id).first()
        if not lang: return Response({'error': 'Language not found'}, status=404)
        from backend.judge.bridge import _map_language_key
        if request.data.get('is_active') is True and not _map_language_key(lang.key):
            return Response({'error': 'Configure the language on Judge Manager before enabling it'}, status=400)
        for field in ('name', 'short_name', 'common_name', 'is_active'):
            if field in request.data:
                if field == 'is_active' and not isinstance(request.data[field], bool):
                    return Response({'error': 'is_active must be a boolean'}, status=400)
                if field != 'is_active' and (not isinstance(request.data[field], str) or len(request.data[field]) > (50 if field == 'name' else 20)):
                    return Response({'error': f'Invalid {field}'}, status=400)
                setattr(lang, field, request.data[field])
        lang.save()
        self.audit(request, 'language.update', lang.key)
        return Response({'id': lang.id, 'key': lang.key, 'is_active': lang.is_active})


class MonitoringView(JudgeAdminView):
    def get(self, request):
        err, data = self.manager('workers')
        if err: return err
        return Response({'workers': [worker_payload(w) for w in data.get('workers', [])]})


class LogsView(JudgeAdminView):
    def get(self, request):
        qs = JudgeLog.objects.select_related('actor', 'worker', 'job')
        level = request.query_params.get('level')
        if level: qs = qs.filter(level=level.upper())
        source = request.query_params.get('source', 'judge')
        worker_id = request.query_params.get('worker_id', 'worker-1')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', worker_id):
            return Response({'error': 'Invalid worker ID'}, status=400)
        filenames = {'judge': 'judge-server.log', 'worker': f'{worker_id}.log', 'dispatcher': 'dispatcher.log'}
        if source not in filenames:
            return Response({'error': 'Invalid log source'}, status=400)
        path = Path(__file__).resolve().parents[3] / 'judge-system' / 'logs' / filenames[source]
        lines = []
        try:
            with path.open('rb') as handle:
                handle.seek(0, 2)
                handle.seek(max(0, handle.tell() - 65536))
                lines = handle.read().decode('utf-8', errors='replace').splitlines()[-100:]
        except OSError:
            pass
        return Response({'source': source, 'system_logs': lines, 'logs': [
            {'id': x.id, 'level': x.level, 'action': x.action, 'message': x.message,
             'actor': x.actor.username if x.actor else None, 'worker': x.worker.name if x.worker else None,
             'job': x.job.remote_id if x.job else None, 'created_at': x.created_at.isoformat()}
            for x in qs[:200]
        ]})


class HealthView(JudgeAdminView):
    def get(self, request):
        err, data = self.manager('health')
        if err: return err
        return Response(data)


class TestRunView(JudgeAdminView):
    def post(self, request):
        code = request.data.get('problem', '')
        language_key = request.data.get('language', '')
        source = request.data.get('source', '')
        if not all(isinstance(x, str) for x in (code, language_key, source)):
            return Response({'error': 'Invalid test run input'}, status=400)
        code, language_key = code.strip().upper(), language_key.strip().upper()
        problem = Problem.objects.filter(code=code).first()
        language = Language.objects.filter(key=language_key, is_active=True).first()
        if not problem or not language or not source or len(source.encode('utf-8')) > 65536:
            return Response({'error': 'Valid problem, active language and source (max 64 KB) are required'}, status=400)
        from backend.judge.bridge import _map_language_key
        if not _map_language_key(language.key):
            return Response({'error': 'Language is not configured on Judge Manager'}, status=400)
        job_id = f'admin_test_{uuid.uuid4().hex[:12]}'
        payload = {
            'job_id': job_id, 'problem_code': problem.code,
            'language': _map_language_key(language.key), 'source_code': source,
            'time_limit': problem.time_limit,
            'memory_limit': min(1024, max(16, (int(problem.memory_limit) + 1023) // 1024)),
            'checker_type': 'standard', 'priority': 5,
        }
        try:
            data = call_manager('submissions', 'POST', payload)
        except ManagerError as exc:
            return Response({'error': str(exc)}, status=exc.status)
        self.audit(request, 'test.run', f'{job_id} on {code}')
        return Response({'job_id': data.get('job_id', job_id), 'status': 'QUEUED'}, status=202)


class LimitsView(JudgeAdminView):
    def get(self, request):
        err, data = self.manager('admin/limits')
        if err: return err
        return Response(data)
