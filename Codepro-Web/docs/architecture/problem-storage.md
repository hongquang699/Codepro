# Problem Storage (PostgreSQL, MinIO, BullMQ, Judge)

The existing `judge.Problem`, `judge.Submission`, `judge.JudgeJob`, and
`judge.JudgeResult` tables remain the canonical application records. The
`problem_storage` migration adds immutable package versions, test groups,
testcase metadata, a published release pointer, and one version pin per
submission. Existing filesystem problem packages and authoring endpoints keep
working for problems without a published storage release.

## Package format

The private ZIP contains `statement.md`, `manifest.json`, and flat testcase
pairs under `cases/`. Example:

```text
statement.md
manifest.json
cases/01.in
cases/01.out
cases/02.in
cases/02.out
```

```json
{"groups":[{"name":"samples","points":20,"cases":[{"name":"01","sample":true}]},{"name":"main","points":80,"cases":[{"name":"02"}]}]}
```

Group points must total 100. Names use ASCII letters, digits, `_`, `.`, and
`-`; nested paths and unreferenced files are rejected. Limits: 20 MiB ZIP,
100 MiB expanded, 1000 entries, 20 MiB per file, and compression ratio 100:1.
Encrypted members, symlinks, duplicate paths, and invalid UTF-8 metadata are
rejected. Testcases stay private; the public bucket holds statements only.

## API and lifecycle

All paths start with `/api/v1/problem-storage/`. Authenticated staff,
superusers, members of `problem_editor`, and a problem's authors can use the
version endpoints. Existing problem creation and publication APIs retain their
current permissions. The internal validation endpoint uses a separate shared
token and is reachable only on the Compose network.

1. `POST problems/{code}/versions` creates a pending version and returns a
   presigned **POST** URL plus form fields. Upload the ZIP with those fields and
   the `file` field; the policy limits size and expires after 15 minutes.
2. `POST problems/{code}/versions/{uuid}/complete` verifies the staged object
   and queues validation in BullMQ. Poll `GET .../versions/{uuid}`.
3. Validation checks the archive, calculates SHA-256, copies it to the immutable
   `problems/{problem_id}/versions/{uuid}/{sha256}.zip` key, writes the public
   statement, and records test groups/cases in PostgreSQL.
4. `POST problems/{code}/versions/{uuid}/publish` updates the active release
   pointer and `Problem.description`. A new submission pins that release at
   creation. Rejudging retains the original pin. The Django to Judge protocol
   sends `{id,key,sha256}` as `problem_version`; Judge downloads from the
   private bucket, verifies the digest, and loads testcases in a temporary
   directory. Legacy submissions without a pin use the old filesystem path.

Publication does not change `Problem.is_public`, organization visibility, or
contest access. Use the existing access workflow for those settings. The
published version supplies the statement returned by the existing statement
API. Editing the legacy statement after publication does not change that
version; upload and publish a new ZIP instead.

## Deployment

Set `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, and
`PROBLEM_STORAGE_INTERNAL_TOKEN` to independent random secrets. Set
`PROBLEM_STORAGE_PUBLIC_ENDPOINT` to an HTTPS MinIO/S3 endpoint reachable by
editors' browsers. Restrict the MinIO API listener to the intended network and
configure browser CORS for the authoring origin. The Compose example binds its
API to loopback for local development. The initialization service creates
private and public buckets, enables private bucket versioning, and permits
anonymous downloads from the public statement bucket only. In production,
replace root credentials in backend and Judge with separate least-privilege
service accounts: backend needs staged read/copy/delete and public statement
write, Judge needs private version read only. Preserve MinIO data and the
PostgreSQL volume in backups; test restore as a pair.

Run `python manage.py migrate`, then start the updated Compose services.
Roll out the Judge image before publishing the first MinIO-backed version.
Inspect `problem-storage-queue` logs for failed validation jobs and version
`error` fields for rejected packages. BullMQ handles validation. Judge Manager
uses Redis database 2 for queued jobs and results; its existing authenticated
HTTP polling protocol remains in place. A job already handed to a worker when
Judge Manager restarts may need rejudge. Existing authoring endpoints can still
change legacy package files; migrate an individual problem only after its ZIP
is ready.
