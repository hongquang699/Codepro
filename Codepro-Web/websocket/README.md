# WebSocket routes

- `/ws/submissions/<id>/` is a read-only Django Channels stream for public grading status. The Node gateway forwards upgrades to Django ASGI. The backend publishes changes after a submission save commits, using Redis as the shared channel layer in deployment.
- `/ws/live` is the public invalidation stream in `apps/web/live-sync.js`. Contest, problem, submission, account, and share writes trigger it; clients reload data through the normal API.

The old empty contest, notification, scoreboard, submission, and system handler files and the unused in-process ranking socket registry were removed. They never registered routes or received events. New streams should have a defined consumer, publisher, access policy, and deployment route before being added here.
