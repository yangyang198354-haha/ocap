from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "平台基础"

    def ready(self) -> None:
        from . import checks  # noqa: F401
