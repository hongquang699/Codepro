from django.apps import AppConfig


class AntiCheatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.anti_cheat'
    verbose_name = 'Contest anti-cheat review'

    def ready(self):
        from . import signals  # noqa: F401
