from django.apps import AppConfig


class CommitteeConfig(AppConfig):
    name = "apps.committee"
    verbose_name = "业委会与业主代表"

    def ready(self) -> None:
        from apps.core.user_refs import register_user_reference

        from .models import Seat
        from .services import CommitteeCommands

        register_user_reference(Seat, "user", on_conflict="custom", handler=CommitteeCommands.merge_seats)
