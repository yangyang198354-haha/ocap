"""房屋关系服务（IFC-050/055）。"""
from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService

from .models import Membership

ROLE_RANK = {"HEAD": 3, "OWNER": 2, "RESIDENT": 1}


class MembershipService:
    @staticmethod
    def certify_owner(user_id: int, unit_id: int, source: str, origin: str | None = None) -> str:
        with transaction.atomic():
            from apps.registry.models import RegistryUnit

            RegistryUnit.objects.select_for_update().filter(id=unit_id).first()
            active = Membership.objects.filter(user_id=user_id, unit_id=unit_id, ended_at__isnull=True)
            existing = active.filter(role__in=["HEAD", "OWNER"]).first()
            if existing is not None:
                from apps.core.errors import ApiError

                raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
            resident = active.filter(role="RESIDENT").first()
            if resident is not None:
                MembershipService.end_membership(resident.id, "UPGRADED")
            head_exists = Membership.objects.filter(unit_id=unit_id, head_slot=1,
                                                    ended_at__isnull=True).exists()
            role = "OWNER" if head_exists else "HEAD"
            Membership.objects.create(user_id=user_id, unit_id=unit_id, role=role, source=source,
                                      active_slot=1, head_slot=1 if role == "HEAD" else None)
            detail = {"role": role, "source": source}
            if origin == "REGISTRY_AUTO":
                detail.update({"origin": origin, "origin_label": "清册自动绑定"})
            AuditService.record(
                actor=AuditActor("MEMBER", user_id, f"用户{user_id}"), action="CERTIFY_BY_REGISTRY",
                object_type="membership", object_id=f"{user_id}:{unit_id}", result="SUCCESS",
                detail=detail,
            )
            if role == "HEAD":
                AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="HEAD_ASSIGNED",
                                    object_type="unit", object_id=str(unit_id), result="SUCCESS",
                                    detail={"user_id": user_id})
            return role

    @staticmethod
    def end_membership(membership_id: int, reason: str) -> None:
        Membership.objects.filter(id=membership_id).update(
            ended_at=timezone.now(), end_reason=reason, active_slot=None, head_slot=None,
        )

    @staticmethod
    def promote_head_if_vacant(unit_id: int) -> int | None:
        with transaction.atomic():
            if Membership.objects.filter(unit_id=unit_id, head_slot=1, ended_at__isnull=True).exists():
                return None
            candidate = (Membership.objects
                         .filter(unit_id=unit_id, role="OWNER", ended_at__isnull=True)
                         .order_by("certified_at", "id").first())
            if candidate is None:
                return None
            candidate.role = "HEAD"
            candidate.head_slot = 1
            candidate.save(update_fields=["role", "head_slot"])
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="HEAD_SUCCEEDED",
                                object_type="unit", object_id=str(unit_id), result="SUCCESS",
                                detail={"user_id": candidate.user_id})
            return candidate.user_id

    @staticmethod
    def list_active(user_id: int) -> list[Membership]:
        return list(Membership.objects.filter(user_id=user_id, ended_at__isnull=True).select_related("unit"))

    @staticmethod
    def is_owner_of_any(user_id: int) -> bool:
        return Membership.objects.filter(user_id=user_id, ended_at__isnull=True,
                                         role__in=["HEAD", "OWNER"]).exists()

    @staticmethod
    def is_owner_of(user_id: int, unit_id: int) -> bool:
        return Membership.objects.filter(user_id=user_id, unit_id=unit_id, ended_at__isnull=True,
                                         role__in=["HEAD", "OWNER"]).exists()

    @staticmethod
    def is_owner_or_resident_of_any(user_id: int, *, include_residents: bool) -> bool:
        roles = ["HEAD", "OWNER"] + (["RESIDENT"] if include_residents else [])
        return Membership.objects.filter(user_id=user_id, ended_at__isnull=True, role__in=roles).exists()

    @staticmethod
    def is_head_or_owner_of(user_id: int, unit_id: int) -> bool:
        return MembershipService.is_owner_of(user_id, unit_id)

    @staticmethod
    def revoke_owner(user_id: int, unit_id: int) -> dict:
        with transaction.atomic():
            membership = Membership.objects.filter(user_id=user_id, unit_id=unit_id,
                                                   ended_at__isnull=True,
                                                   role__in=["HEAD", "OWNER"]).first()
            if membership is None:
                from apps.core.errors import NotFound

                raise NotFound("目标不是该专有部分有效产权业主")
            was_head = membership.role == "HEAD"
            MembershipService.end_membership(membership.id, "REVOKED")
            new_head = MembershipService.promote_head_if_vacant(unit_id) if was_head else None
            return {"was_head": was_head, "new_head_id": new_head}

    @staticmethod
    def merge_memberships(primary_id: int, secondary_id: int) -> list[str]:
        """同房取高、跨房保留（REQ-FUNC-030）。"""
        moved: list[str] = []
        secondaries = list(Membership.objects.filter(user_id=secondary_id, ended_at__isnull=True))
        for member in secondaries:
            primary = Membership.objects.filter(user_id=primary_id, unit_id=member.unit_id,
                                                ended_at__isnull=True).first()
            if primary is None:
                member.user_id = primary_id
                member.save(update_fields=["user"])
                moved.append(f"move:{member.unit_id}")
                continue
            if ROLE_RANK[member.role] > ROLE_RANK[primary.role]:
                if primary.role == "HEAD":
                    MembershipService.end_membership(primary.id, "MERGED")
                else:
                    MembershipService.end_membership(primary.id, "MERGED")
                member.user_id = primary_id
                member.save(update_fields=["user"])
                moved.append(f"upgrade:{member.unit_id}")
            else:
                MembershipService.end_membership(member.id, "MERGED")
                moved.append(f"drop:{member.unit_id}")
        return moved
