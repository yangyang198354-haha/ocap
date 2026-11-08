from django.apps import AppConfig


class ResolutionsConfig(AppConfig):
    name = "apps.resolutions"
    verbose_name = "业委会决议"

    def ready(self) -> None:
        from apps.approval.services import register_callbacks
        from apps.core.attachments import register_attachment_policy
        from apps.core.user_refs import register_user_reference

        from .models import Resolution, Vote
        from .services import merge_votes, on_approved, on_rejected, on_withdrawn

        register_callbacks("resolution", on_approved=on_approved, on_rejected=on_rejected,
                           on_withdrawn=on_withdrawn)
        register_attachment_policy("resolution", ResolutionAttachmentPolicy())
        register_user_reference(Resolution, "initiator", on_conflict="move_all")
        register_user_reference(Vote, "voter", on_conflict="custom", handler=merge_votes)


class ResolutionAttachmentPolicy:
    def can_open(self, linked_id: str, principal) -> bool:
        from .models import Resolution

        resolution = Resolution.objects.filter(id=linked_id).first()
        if resolution is None or principal is None:
            return False
        if getattr(principal, "is_admin_principal", False):
            return True
        user_id = getattr(principal, "id", None)
        if resolution.status in {"APPROVED", "REJECTED"}:
            return True
        if resolution.status == "PENDING":
            from apps.committee.services import CommitteeQuery

            return resolution.initiator_id == user_id or CommitteeQuery.is_member(user_id)
        return resolution.initiator_id == user_id
