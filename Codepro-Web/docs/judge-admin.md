# Judge Admin

Judge Admin lives at `/admin/judge`. The Node gateway asks Django to authorize
the page on every navigation. Django API endpoints live under
`/api/v1/admin/judge/` and accept authenticated staff, superusers, or members of
the `judge_admin` / `judge_manager` groups (profile roles `admin`,
`judge_admin`, and `judge_manager` also work).
Write requests made with the `cp_session` cookie require a CSRF token. DRF token
authentication is also supported.

## Data flow

Browser → Django Judge Admin API → Judge Manager (`judge-system/judge-server`)
→ queue → worker → sandbox. The Django web process never compiles or executes a
submission. If Judge Manager is unavailable or times out, grading records a
system error for later rejudge. Set `JUDGE_SERVER_URL` and `JUDGE_AUTH_TOKEN`
consistently on Django and Judge Manager. Run migrations before opening the
dashboard.

The Judge Manager currently keeps its queue and result cache in memory. A
manager restart loses those pending jobs. Workers are discovered through
heartbeats. `workers.yml` configures their capabilities; adding a worker
requires starting it under an external supervisor. Restart requests are
delivered to the worker on its next poll, after its current job finishes. The
worker recreates its executor and heartbeat state without a shell command.
No browser action runs a shell command on a worker.

## Pages and operations

- Dashboard: live worker, running job, queue and error counts.
- Workers: heartbeat, resources, languages, current job, enable, disable and
  maintenance controls. Worker detail includes recent audit entries.
- Queue: pending/running/completed/failed views; pause, resume, cancel waiting
  jobs, and retry failed jobs through rejudge.
- Submissions: details, source, testcase results, rejudge and errors.
- Languages: Django language metadata. New languages start disabled; a compiler
  mapping and worker configuration are required before activation.
- Test: sends a bounded sample submission to Judge Manager for sandbox grading.
- Monitoring and logs: heartbeat telemetry, audit entries and a bounded tail
  of Judge Manager log files.
- Sandbox and settings: show where deployment configuration is managed.

Administrative writes create `judge_logs` audit records. The tables
`judge_workers`, `judge_jobs`, and `judge_results` persist local management
state and completed grading data. Live queue state comes from Judge Manager.
