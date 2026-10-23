from collections import Counter, defaultdict

from django.db import connection, transaction
from django.utils import timezone

from backend.judge.models import Submission
from backend.contest_admin.services.audit_service import log_contest_audit
from backend.anti_cheat.models import AntiCheatCase, AntiCheatSettings, ScanJob, SimilarityResult
from .similarity import fingerprint, normalize_tokens, source_digest
from .similarity_client import compare


def enqueue_scan(contest, actor=None, submission=None):
    existing = ScanJob.objects.filter(contest=contest, target_submission=submission,
                                      status__in=['PENDING', 'RUNNING']).first()
    if existing:
        return existing, False
    job = ScanJob.objects.create(contest=contest, target_submission=submission, requested_by=actor)
    return job, True


def claim_scan():
    with transaction.atomic():
        pending = ScanJob.objects.filter(status='PENDING').order_by('created_at', 'pk')
        if connection.features.has_select_for_update_skip_locked:
            pending = pending.select_for_update(skip_locked=True)
        else:
            pending = pending.select_for_update()
        job = pending.first()
        if not job:
            return None
        job.status = 'RUNNING'
        job.started_at = timezone.now()
        job.error = ''
        job.save(update_fields=['status', 'started_at', 'error'])
        return job.pk


def _submission_data(submission, minimum):
    tokens = normalize_tokens(submission.source, submission.language.key or submission.language.name)
    if len(tokens) < minimum:
        return None
    return fingerprint(tokens)


def _record_match(job, first, second, score, algorithm_version, evidence):
    a, b = sorted((first, second), key=lambda item: item.pk)
    result, _ = SimilarityResult.objects.update_or_create(
        submission_a=a, submission_b=b,
        defaults={
            'contest': job.contest, 'problem': a.problem, 'score': score,
            'algorithm_version': algorithm_version,
            'source_a_sha256': source_digest(a.source),
            'source_b_sha256': source_digest(b.source),
            'evidence': evidence,
        },
    )
    AntiCheatCase.objects.get_or_create(result=result, defaults={'contest': job.contest})


def process_scan(job_id):
    job = ScanJob.objects.select_related('contest', 'target_submission').get(pk=job_id)
    config, _ = AntiCheatSettings.objects.get_or_create(contest=job.contest)
    try:
        if not config.enabled:
            raise ValueError('Anti-cheat is disabled for this contest')
        submissions = list(Submission.objects.filter(contest=job.contest)
                           .select_related('language', 'user__user', 'problem')
                           .order_by('date', 'pk'))
        job.total = 1 if job.target_submission_id else len(submissions)
        job.save(update_fields=['total'])
        groups = defaultdict(list)
        for submission in submissions:
            groups[(submission.problem_id, submission.language_id)].append(submission)

        processed = matches = 0
        for entries in groups.values():
            index = defaultdict(list)
            prepared = {}
            for submission in entries:
                try:
                    current = _submission_data(submission, config.min_tokens)
                except ValueError:
                    current = None
                if current:
                    candidate_counts = Counter(
                        prior_id for item in current for prior_id in index[item]
                    )
                    # Common templates can produce many candidates. Prioritize overlap,
                    # and keep the worker's work bounded for large contests.
                    for prior_id, _ in candidate_counts.most_common(100):
                        prior, previous = prepared[prior_id]
                        if prior.user_id == submission.user_id:
                            continue
                        if job.target_submission_id and job.target_submission_id not in (prior_id, submission.pk):
                            continue
                        score, algorithm_version, evidence = compare(
                            prior, submission, previous, current,
                        )
                        if score >= config.similarity_threshold:
                            _record_match(job, prior, submission, score, algorithm_version, evidence)
                            matches += 1
                    prepared[submission.pk] = (submission, current)
                    for item in current:
                        index[item].append(submission.pk)
                if not job.target_submission_id or submission.pk == job.target_submission_id:
                    processed += 1
                if processed and processed % 20 == 0:
                    ScanJob.objects.filter(pk=job_id).update(processed=processed, matches=matches)
        job.status = 'COMPLETED'
        job.processed = processed
        job.matches = matches
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'processed', 'matches', 'finished_at'])
        log_contest_audit(job.contest, job.requested_by, 'ANTI_CHEAT_SCAN_COMPLETE',
                          target_type='scan', target_id=job.pk,
                          details=f'{processed} submissions checked; {matches} matching pairs')
    except Exception as exc:
        job.status = 'FAILED'
        job.error = str(exc)[:1000]
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'error', 'finished_at'])
        raise
