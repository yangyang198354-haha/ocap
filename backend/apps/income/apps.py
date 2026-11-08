from django.apps import AppConfig


class IncomeConfig(AppConfig):
    name = "apps.income"
    verbose_name = "收入记账"

    def ready(self) -> None:
        from apps.approval.services import register_callbacks
        from apps.core.attachments import register_attachment_policy
        from apps.core.user_refs import register_user_reference

        from .models import IncomeSheet
        from .services import IncomeAttachmentPolicy, on_approved, on_rejected, on_withdrawn

        register_callbacks("income_sheet", on_approved=on_approved, on_rejected=on_rejected,
                           on_withdrawn=on_withdrawn)
        register_attachment_policy("income_sheet", IncomeAttachmentPolicy())
        register_user_reference(IncomeSheet, "submitted_by", on_conflict="move_all")
