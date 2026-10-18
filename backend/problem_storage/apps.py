from django.apps import AppConfig


class ProblemStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.problem_storage'

    def ready(self):
        from . import signals  # noqa: F401
