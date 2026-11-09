from django.apps import AppConfig


class JudgeAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.judge'
    verbose_name = 'CodeProOJ Judge System'

    def ready(self):
        from . import signals  # noqa: F401
