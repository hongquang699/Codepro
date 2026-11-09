"""
Bridge between Django Backend and the CodeProOJ Judge System.
Routes grading jobs to the external Judge Server (port 9999).
Never executes contestant code inside Django.
"""
import time
import json
import uuid
from urllib import request
from django.conf import settings
from .models import Submission, SubmissionTestCase, JudgeWorker, JudgeJob, JudgeResult, JudgeLog
from django.utils import timezone

# ── Judge Server Settings ────────────────────────────────────────────────────
JUDGE_SERVER_URL = getattr(settings, 'JUDGE_SERVER_URL', 'http://127.0.0.1:9999')
JUDGE_AUTH_TOKEN = getattr(settings, 'JUDGE_AUTH_TOKEN', '')
JUDGE_POLL_TIMEOUT = getattr(settings, 'JUDGE_POLL_TIMEOUT', 30)   # max seconds to wait for result
JUDGE_POLL_INTERVAL = getattr(settings, 'JUDGE_POLL_INTERVAL', 0.5)  # seconds between polls


def _judge_headers():
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {JUDGE_AUTH_TOKEN}'
    }


def _judge_server_online() -> bool:
    """Quick health check to see if judge server is up."""
    try:
        req = request.Request(f'{JUDGE_SERVER_URL}/api/v1/health')
        with request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('status') == 'healthy'
    except Exception:
        return False


def _submit_to_judge_server(job_id: str, problem_code: str, language: str,
                              source: str, time_limit: float, memory_limit: int,
                              checker_type: str = 'standard', subtask_mode: bool = False,
                              problem_version: dict | None = None) -> bool:
    """Enqueues a grading job to the external judge server."""
    payload = json.dumps({
        'submission_id': job_id,
        'problem_code': problem_code,
        'language': language,
        'source_code': source,
        'time_limit': time_limit,
        'memory_limit': memory_limit,
        'checker_type': checker_type,
        'subtask_mode': subtask_mode,
        'priority': 1,
        'problem_version': problem_version,
    }).encode('utf-8')

    try:
        req = request.Request(
            f'{JUDGE_SERVER_URL}/api/v1/submissions',
            data=payload,
            headers=_judge_headers()
        )
        with request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 201, 202)
    except Exception:
        return False


def _poll_judge_result(job_id: str) -> dict | None:
    """Polls judge server until result is ready or timeout."""
    deadline = time.time() + JUDGE_POLL_TIMEOUT
    while time.time() < deadline:
        try:
            req = request.Request(
                f'{JUDGE_SERVER_URL}/api/v1/submissions/{job_id}',
                headers=_judge_headers()
            )
            with request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                sub_data = data.get('submission', {})
                status = sub_data.get('status', '')
                if status == 'Judging':
                    JudgeJob.objects.filter(remote_id=job_id, status='WAITING').update(
                        status='RUNNING', started_at=timezone.now())
                if status in ('Completed', 'Failed'):
                    return sub_data
                if status == 'Cancelled':
                    return sub_data
        except Exception:
            pass
        time.sleep(JUDGE_POLL_INTERVAL)
    return None


def _map_language_key(lang_key: str) -> str:
    """Maps Django language keys to judge-system language identifiers."""
    mapping = {
        'PY3': 'python',   'PYTHON3': 'python', 'PY': 'python',
        'PYPY': 'pypy',    'PYPY3': 'pypy',
        'CPP': 'cpp',      'CPP17': 'cpp',       'CPP14': 'cpp',
        'CPP20': 'cpp',    'GCC': 'cpp',
        'C': 'c',          'C11': 'c',
        'JAVA': 'java',    'JAVA17': 'java',
        'RUST': 'rust',
        'GO': 'go',
        'JS': 'javascript', 'NODEJS': 'javascript',
        'TS': 'typescript',
        'KT': 'kotlin',    'KOTLIN': 'kotlin',
        'CS': 'csharp',    'CSHARP': 'csharp',
        'PAS': 'pascal',   'PASCAL': 'pascal',
    }
    return mapping.get(lang_key.upper())


def _verdict_from_testcases(testcases: list) -> str:
    """Derives overall verdict from testcase results (worst-first priority)."""
    priority = {'CE': 100, 'SE': 90, 'RE': 80, 'RTE': 80,
                'MLE': 70, 'TLE': 60, 'OLE': 50, 'WA': 40, 'AC': 10}
    worst = 'AC'
    for tc in testcases:
        v = tc.get('verdict', 'AC')
        if priority.get(v, 0) > priority.get(worst, 0):
            worst = v
    return worst


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point called by views
# ─────────────────────────────────────────────────────────────────────────────
def grade_submission(submission_id):
    """
    Grades a submission by routing to the external judge server (port 9999).
    Falls back to legacy in-process judging if server is offline.
    """
    try:
        sub = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return

    sub.status = 'G'  # Grading
    sub.save(update_fields=['status'])

    prob = sub.problem
    from backend.problem_storage.models import SubmissionVersion
    pin = SubmissionVersion.objects.select_related('version').filter(submission=sub).first()
    version_ref = None
    if pin:
        v = pin.version
        version_ref = {'id': str(v.id), 'key': v.private_key, 'sha256': v.sha256}
    lang_key = sub.language.key.upper()
    judge_lang = _map_language_key(lang_key)
    if not judge_lang:
        sub.status, sub.result = 'D', 'IE'
        sub.error = f'Language {lang_key} is not configured on Judge Manager.'
        sub.save(update_fields=['status', 'result', 'error'])
        JudgeLog.objects.create(level='ERROR', action='job.unsupported_language', message=sub.error)
        return sub
    job_id = f'sub_{submission_id}_{uuid.uuid4().hex[:6]}'
    job = JudgeJob.objects.create(remote_id=job_id, submission=sub, status='WAITING', attempts=1,
                                  priority=1 if sub.contest_id else 10)

    # ── Try external judge server ─────────────────────────────────────────
    if _judge_server_online():
        time_limit = float(getattr(prob, 'time_limit', 1.0) or 1.0)
        memory_limit = min(1024, max(16, (int(getattr(prob, 'memory_limit', 262144) or 262144) + 1023) // 1024))
        checker_type = getattr(prob, 'checker_type', 'standard') or 'standard'
        from . import problem_package

        queued = _submit_to_judge_server(
            job_id=job_id,
            problem_code=prob.code,
            language=judge_lang,
            source=sub.source,
            time_limit=time_limit,
            memory_limit=memory_limit,
            checker_type=checker_type,
            subtask_mode=bool(pin and v.groups.count() > 1) if pin else problem_package.has_subtasks(prob.code),
            problem_version=version_ref
        )

        if queued:
            result = _poll_judge_result(job_id)
            if result:
                if JudgeJob.objects.filter(submission=sub, created_at__gt=job.created_at).exists():
                    job.status = 'SUPERSEDED'
                    job.finished_at = timezone.now()
                    job.save(update_fields=['status', 'finished_at'])
                    return sub
                if result.get('status') == 'Cancelled':
                    job.status = 'CANCELLED'
                    job.finished_at = timezone.now()
                    job.save(update_fields=['status', 'finished_at'])
                    sub.status, sub.result, sub.error = 'D', 'AB', 'Cancelled by Judge Admin.'
                    sub.save(update_fields=['status', 'result', 'error'])
                    return sub
                graded = _apply_judge_result(sub, prob, result)
                job.status = 'FAILED' if graded.result in ('SE', 'IE') else 'COMPLETED'
                job.finished_at = timezone.now()
                assigned = result.get('assigned_worker')
                if assigned:
                    job.worker, _ = JudgeWorker.objects.get_or_create(name=assigned)
                job.save(update_fields=['status', 'finished_at', 'worker'])
                JudgeResult.objects.create(job=job, submission=sub, worker=job.worker,
                    verdict=graded.result or 'IE', score=graded.points or 0,
                    execution_time=(graded.time or 0) * 1000, memory_used=result.get('memory_kb', 0),
                    output_size=result.get('output_size', 0), compile_time=result.get('compile_time_ms', 0))
                return graded

    # Web/API processes must never compile or execute contestant source.
    job.refresh_from_db(fields=['status'])
    if JudgeJob.objects.filter(submission=sub, created_at__gt=job.created_at).exists():
        job.status = 'SUPERSEDED'
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'finished_at'])
        return sub
    if job.status == 'CANCELLED':
        sub.status, sub.result, sub.error = 'D', 'AB', 'Cancelled by Judge Admin.'
        sub.save(update_fields=['status', 'result', 'error'])
        return sub
    job.status = 'FAILED'
    job.finished_at = timezone.now()
    job.save(update_fields=['status', 'finished_at'])
    sub.status = 'D'
    sub.result = 'IE'
    sub.error = 'Judge Manager unavailable or timed out. Rejudge when it is healthy.'
    sub.save(update_fields=['status', 'result', 'error'])
    JudgeLog.objects.create(job=job, level='ERROR', action='job.failed', message=sub.error)
    return sub


def _apply_judge_result(sub: Submission, prob, result: dict):
    """Applies the grading result from judge-server into database."""
    sub.test_cases.all().delete()

    testcases = result.get('testcases', [])
    fallback_weight = prob.points / max(1, len(testcases)) if testcases else 0.0

    for tc in testcases:
        raw_verdict = tc.get('verdict', 'AC')
        # Map judge-system verdicts → Django submission status codes
        verdict_map = {
            'AC': 'AC', 'WA': 'WA', 'TLE': 'TLE', 'MLE': 'MLE',
            'OLE': 'OLE', 'RE': 'RTE', 'CE': 'CE', 'SE': 'IE', 'OK': 'AC'
        }
        db_verdict = verdict_map.get(raw_verdict, 'WA')
        case_weight = float(tc.get('max_points', fallback_weight) or 0.0)

        SubmissionTestCase.objects.create(
            submission=sub,
            case=tc.get('id', 1),
            status=db_verdict,
            time=round(tc.get('time_ms', 0) / 1000.0, 4),
            memory=round(tc.get('memory_kb', 0) / 1024.0, 2),
            points=float(tc.get('score', case_weight if db_verdict == 'AC' else 0.0) or 0.0),
            total_points=case_weight,
            feedback=tc.get('message', '')[:250]
        )

    # Summary fields
    final_verdict = result.get('verdict', 'WA')
    if final_verdict == 'OK':
        final_verdict = 'AC'

    sub.status = 'D'
    sub.result = final_verdict
    sub.error = result.get('compiler_output') or result.get('error_message', '')
    sub.time = round(result.get('time_ms', 0) / 1000.0, 4)
    sub.memory = round(result.get('memory_kb', 0), 1)
    has_subtask_scores = bool(result.get('subtasks'))
    sub.points = round(result.get('points_earned', 0.0), 1) if final_verdict == 'AC' or has_subtask_scores or getattr(prob, 'partial', False) else 0.0
    sub.save()

    # Update author profile stats
    _update_profile_stats(sub)
    return sub


def _update_profile_stats(sub: Submission):
    """Updates user profile points and problem count on AC."""
    if sub.result == 'AC':
        prof = sub.user
        ac_count = Submission.objects.filter(user=prof, result='AC').values('problem').distinct().count()
        prof.problem_count = ac_count
        prof.points = ac_count * 100.0
        prof.save(update_fields=['problem_count', 'points'])

    if sub.contest:
        _update_contest_stats(sub)


def _update_contest_stats(sub: Submission):
    """Updates ContestParticipation scores, tries, and penalty time for ICPC/IOI."""
    try:
        from .models import ContestParticipation, ContestProblem
        part, _ = ContestParticipation.objects.get_or_create(contest=sub.contest, user=sub.user)
        subs = Submission.objects.filter(contest=sub.contest, user=sub.user).order_by('date')
        c_probs = list(ContestProblem.objects.filter(contest=sub.contest).select_related('problem'))

        prob_stats = {}
        for cp in c_probs:
            prob_stats[cp.problem.code] = {
                'solved': False,
                'points': 0.0,
                'tries': 0,
                'time': 0,
                'prefix': cp.output_prefix
            }

        for s in subs:
            pcode = s.problem.code
            if pcode not in prob_stats:
                continue
            st = prob_stats[pcode]
            if st['solved']:
                continue
            st['tries'] += 1
            if s.result == 'AC':
                st['solved'] = True
                st['points'] = 100.0
                mins = max(0, int((s.date - sub.contest.start_time).total_seconds() / 60))
                st['time'] = mins
            elif getattr(s.problem, 'partial', False) and s.points and s.points > st['points']:
                st['points'] = s.points

        if sub.contest.format_name == 'ioi':
            part.score = sum(st['points'] for st in prob_stats.values())
            part.cumulative_time = sum(st['time'] for st in prob_stats.values() if st['solved'])
        else: # ICPC
            part.score = sum(1 for st in prob_stats.values() if st['solved'])
            part.cumulative_time = sum(st['time'] + (st['tries'] - 1) * 20 for st in prob_stats.values() if st['solved'])

        part.format_data = prob_stats
        part.save()
    except Exception as e:
        pass

