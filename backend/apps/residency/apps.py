from django.apps import AppConfig


class ResidencyConfig(AppConfig):
    name = "apps.residency"
    verbose_name = "房屋关系与认证"

    def ready(self) -> None:
        from apps.core.attachments import register_attachment_policy
        from apps.core.user_refs import register_user_reference

        from .models import Appeal, Membership, ResidentApplication
        from .services import MembershipService

        register_attachment_policy("appeal", AppealAttachmentPolicy())
        register_user_reference(Membership, "user", on_conflict="custom",
                                handler=MembershipService.merge_memberships)
        register_user_reference(Appeal, "user", on_conflict="move_all")
        register_user_reference(ResidentApplication, "applicant", on_conflict="move_all")
        register_user_reference(ResidentApplication, "decided_by", on_conflict="move_all")


class AppealAttachmentPolicy:
    def can_open(self, linked_id: str, principal) -> bool:
        from .models import Appeal

        appeal = Appeal.objects.filter(id=linked_id).first()
        if appeal is None or principal is None:
            return False
        if getattr(principal, "is_admin_principal", False):
            return True
        return appeal.user_id == getattr(principal, "id", None)
