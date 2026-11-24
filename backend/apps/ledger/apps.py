from django.apps import AppConfig


class LedgerConfig(AppConfig):
    name = "apps.ledger"
    verbose_name = "收支台账"

    def ready(self) -> None:
        from apps.approval.services import register_callbacks
        from apps.core.user_refs import register_user_reference

        from . import historical
        from .models import HistoricalExpenseBatch

        for field in ("imported_by", "voided_by"):
            register_user_reference(HistoricalExpenseBatch, field, on_conflict="move_all")

        register_callbacks("historical_expense_batch", on_approved=historical.on_approved,
                           on_rejected=historical.on_rejected,
                           on_withdrawn=historical.on_withdrawn)
