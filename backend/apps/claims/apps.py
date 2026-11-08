from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    name = "apps.claims"
    verbose_name = "报销与借款"

    def ready(self) -> None:
        from apps.approval.services import register_callbacks
        from apps.core.attachments import register_attachment_policy
        from apps.core.user_refs import register_user_reference

        from .models import Claim
        from .services import ClaimAttachmentPolicy, on_approved, on_rejected, on_withdrawn

        register_callbacks("claim", on_approved=on_approved, on_rejected=on_rejected,
                           on_withdrawn=on_withdrawn)
        register_attachment_policy("claim", ClaimAttachmentPolicy())
        register_user_reference(Claim, "submitter", on_conflict="move_all")
