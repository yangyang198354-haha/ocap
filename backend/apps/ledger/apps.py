from django.apps import AppConfig


class LedgerConfig(AppConfig):
    name = "apps.ledger"
    verbose_name = "收支台账"

    def ready(self) -> None:
        from apps.core.user_refs import register_user_reference

        from .models import HistoricalExpenseBatch

        for field in ("imported_by", "voided_by"):
            register_user_reference(HistoricalExpenseBatch, field, on_conflict="move_all")
