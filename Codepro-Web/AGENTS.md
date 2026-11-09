# Repository Guidelines

## Project Structure & Module Organization

`backend/` contains the Django API, models, services, and migrations. `apps/web/` is the Node web gateway; `apps/worker/` and `judge-system/` handle background and judging work. Pages, JavaScript, CSS, and assets live under `frontend/`. Cross-cutting tests are in `tests/`, while some Django apps keep tests beside their code. Operational files are in `infrastructure/`, `scripts/`, and `docs/`.

## Build, Test, and Development Commands

- `npm ci` and `pip install -r requirements.txt` install the Node and Python dependencies.
- `start-dev.bat` starts the Django API, judge server, web gateway, and anti-cheat worker on Windows. Open pages through `http://localhost:8888`, not directly as files.
- `python manage.py migrate` applies database migrations after schema changes.
- `docker compose up --build -d` builds and starts the containerized services; `docker compose logs -f` follows their logs.
- `npm run lint` runs ESLint; `npm test` runs Jest tests under `tests/`.
- `python manage.py test tests` (or `make test`) runs the top-level Python tests. Run relevant app-local Django tests with `python manage.py test backend.<app>.tests`.

## Coding Style & Naming Conventions

Follow nearby code conventions: four-space indentation and `snake_case` for Python; two-space indentation and `camelCase` for JavaScript. Name Python test files `test_*.py` and Jest files `*.test.js`. Keep API authorization and validation in the backend, even when the frontend also hides unavailable actions. Use existing CSS variables in `frontend/css/global/theme.css` for theme-aware colors. Run `npm run lint` for JavaScript changes; the ESLint configuration is in `.eslintrc.cjs`.

## Testing Guidelines

Add focused tests for changed behavior, especially permissions, submissions, judging, and gateway routes. Python tests use pytest and Django's test runner; JavaScript tests use Jest. Place integration and security coverage in `tests/integration/` and `tests/security/`. No repository-wide coverage threshold is configured. CI runs Node lint and Jest, so run relevant Python tests locally for backend changes.

## Commit & Pull Request Guidelines

Recent commits use short, imperative subjects such as `Fix submission WebSocket routing and status broadcasts`. Keep commits scoped to one change. In pull requests, explain the behavior changed, affected services, any migration or configuration steps, and the commands used to verify it. Link related issues when available; include screenshots for visible UI changes.

## Security & Configuration

Copy required settings from `.env.example` into a local `.env`; never commit secrets or use example values in production. Review authentication, CSRF, and role checks when changing API routes. Keep user-submitted code execution in the judge path, outside the web process.
