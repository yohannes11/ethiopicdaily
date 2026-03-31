from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Start the background scheduler only when the app is ready
        # (not during management commands like migrate, shell, etc.)
        import os
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("SCHEDULER_ENABLED") == "true":
            from . import scheduler
            scheduler.start()
