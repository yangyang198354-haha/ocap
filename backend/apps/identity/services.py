"""身份聚合与账号合并（IFC-030~034 / REQ-FUNC-067）。"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import AccountService
from apps.committee.models import Seat
from apps.committee.services import CommitteeCommands
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.core.masking import PHONE_RE, mask_phone
from apps.core.user_refs import references
from apps.residency.models import Membership
from apps.residency.services import MembershipService


ROLE_LABELS = {"HEAD": "产权业主", "OWNER": "产权业主", "RESIDENT": "同住人"}
ROLE_RANK = {"HEAD": 3, "OWNER": 2, "RESIDENT": 1}


class IdentityService:
    @staticmethod
    def _unit_view(membership) -> dict:
        unit = membership.unit
        area_text = str(unit.area.quantize(Decimal("0.01"))) if unit.area is not None else None
        return {
            "unit_id": membership.unit_id,
            "specific_part": unit.specific_part,
            "role": membership.role,
            "role_label": ROLE_LABELS.get(membership.role, "产权业主"),
            "unit_type": unit.unit_type,
            "unit_type_label": unit.get_unit_type_display() if unit.unit_type else "未登记",
            "area": area_text,
            "area_display": f"{area_text} ㎡" if area_text else "未登记",
        }

    @staticmethod
    def _units(user) -> list[dict]:
        memberships = Membership.objects.filter(user=user, ended_at__isnull=True).select_related("unit")
        picked = {}
        for membership in memberships:
            current = picked.get(membership.unit_id)
            if current is None or ROLE_RANK.get(membership.role, 0) > ROLE_RANK.get(current.role, 0):
                picked[membership.unit_id] = membership
        ordered = sorted(picked.values(), key=lambda m: (m.unit.specific_part, m.unit_id))
        return [IdentityService._unit_view(m) for m in ordered]

    @staticmethod
    def me(user) -> dict:
        from apps.committee.services import CommitteeQuery

        units = IdentityService._units(user)
        committee_seat = CommitteeQuery.active_seat(user.id)
        labels = CommitteeQuery.identity_labels(user.id)
        return {
            "profile": {
                "id": user.id, "account_no": user.account_no, "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "phone": mask_phone(user.phone) if user.phone else None,
                "gender": user.gender, "birthday": user.birthday,
                "email": user.email, "email_state": user.email_state,
            },
            "identities": {
                "is_guest": labels == ["游客"],
                "units": units,
                "committee": ({"position": committee_seat.position,
                               "term_end": committee_seat.term_end}
                              if committee_seat else None),
                "labels": labels,
            },
        }

    @staticmethod
    def bind_phone(user, phone: str, code: str) -> dict:
        if not PHONE_RE.match(phone):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        if user.phone:
            raise ApiError("PHONE_ALREADY_BOUND", "已绑定手机号，请使用换绑", 409)
        AccountService.verify_code(target=phone, purpose="BIND_PHONE", code=code)
        other = User.objects.filter(phone=phone).first()
        if other is not None:
            # REQ-FUNC-026：手机号属于其他账号 → 合并，主账号为手机号原有账号
            return IdentityService._merge_by_phone(current=user, other=other, trigger="WECHAT_BIND")
        user.phone = phone
        user.save(update_fields=["phone"])
        AuditService.record(actor=AuditActor("MEMBER", user.id, user.identity_label),
                            action="PHONE_BOUND", object_type="user", object_id=str(user.id),
                            result="SUCCESS")
        return {"merged": False, "phone": mask_phone(phone), "primary": user}

    @staticmethod
    def change_phone(user, old_phone: str, new_phone: str, old_code: str, new_code: str) -> dict:
        if not user.phone or user.phone != old_phone:
            raise ApiError("PHONE_MISMATCH", "原手机号与当前绑定不一致")
        if not PHONE_RE.match(new_phone):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        if new_phone == old_phone:
            raise ApiError("INVALID_VALUE", "新手机号不能与原手机号相同")
        AccountService.verify_code(target=old_phone, purpose="CHANGE_PHONE", code=old_code)
        AccountService.verify_code(target=new_phone, purpose="CHANGE_PHONE", code=new_code)
        other = User.objects.filter(phone=new_phone).first()
        if other is not None:
            # REQ-FUNC-028：新手机号属于其他账号 → 合并，主账号为新手机号原有账号
            return IdentityService._merge_by_phone(current=user, other=other, trigger="PHONE_CHANGE")
        user.phone = new_phone
        user.save(update_fields=["phone"])
        AuditService.record(actor=AuditActor("MEMBER", user.id, user.identity_label),
                            action="PHONE_CHANGED", object_type="user", object_id=str(user.id),
                            result="SUCCESS", detail={"before": mask_phone(old_phone),
                                                      "after": mask_phone(new_phone)})
        return {"merged": False, "phone": mask_phone(new_phone), "primary": user}

    @staticmethod
    def _merge_by_phone(*, current, other, trigger: str) -> dict:
        """当前登录账号并入手机号原有账号（IFC-075）；按 id 升序加锁，整体一个事务。"""
        if other.id == current.id:
            raise ApiError("INVALID_VALUE", "手机号已绑定在当前账号")
        with transaction.atomic():
            locked = {u.id: u for u in User.objects.select_for_update()
                      .filter(id__in=[current.id, other.id]).order_by("id")}
            primary, secondary = locked.get(other.id), locked.get(current.id)
            if primary is None or secondary is None:
                raise ApiError("NOT_FOUND", "账号不存在", 404)
            report = IdentityService.merge_accounts(
                primary, secondary, actor=AuditActor("MEMBER", current.id, current.identity_label),
                trigger=trigger)
        return {"merged": True, "phone": mask_phone(primary.phone), "primary": primary,
                "report": report}

    @staticmethod
    def cancel(user, phone: str, code: str) -> None:
        if not user.phone or user.phone != phone:
            raise ApiError("PHONE_MISMATCH", "手机号与当前绑定不一致")
        AccountService.verify_code(target=phone, purpose="CANCEL", code=code)
        head_unit_ids = list(Membership.objects.filter(
            user=user, ended_at__isnull=True, role="HEAD"
        ).values_list("unit_id", flat=True))
        with transaction.atomic():
            Membership.objects.filter(user=user, ended_at__isnull=True).update(
                ended_at=timezone.now(), end_reason="CANCELLED", active_slot=None, head_slot=None,
            )
            for seat in Seat.objects.filter(user=user, status="ACTIVE"):
                seat.status = "INVALIDATED"
                seat.active_slot = None
                seat.end_reason = "ACCOUNT_CANCELLED"
                seat.save()
            AccountService.tombstone(user)
            AuditService.record(actor=AuditActor("MEMBER", user.id, f"用户{user.account_no}"),
                                action="ACCOUNT_CANCELLED", object_type="user",
                                object_id=str(user.id), result="SUCCESS")
        for unit_id in head_unit_ids:
            MembershipService.promote_head_if_vacant(unit_id)

    @staticmethod
    def revoke_membership(user_id: int, unit_id: int, admin_id: int) -> dict:
        membership = Membership.objects.filter(user_id=user_id, unit_id=unit_id,
                                               ended_at__isnull=True).first()
        if membership is None:
            raise ApiError("NOT_FOUND", "目标不是该专有部分有效产权业主", 404)
        if membership.role not in {"HEAD", "OWNER"}:
            raise ApiError("INVALID_VALUE", "仅产权业主可撤销认证", 409)
        result = MembershipService.revoke_owner(user_id, unit_id)
        sync = CommitteeCommands.sync_after_ownership_change(user_id)
        seat_invalidated = bool(sync and sync.get("invalidated"))
        AuditService.record(actor=AuditActor("ADMIN", admin_id, f"管理员{admin_id}"),
                            action="CERTIFICATION_REVOKED", object_type="membership",
                            object_id=str(membership.id), result="SUCCESS",
                            detail={"user_id": user_id, "unit_id": unit_id,
                                    "was_head": result["was_head"],
                                    "seat_invalidated": seat_invalidated})
        return {**result, "seat_invalidated": seat_invalidated}

    @staticmethod
    def merge_accounts(primary, secondary, admin_id: int | None = None, *,
                       actor: AuditActor | None = None, trigger: str | None = None) -> dict:
        if primary.id == secondary.id:
            raise ApiError("INVALID_VALUE", "不能合并同一账号")
        if primary.status != "ACTIVE" or secondary.status != "ACTIVE":
            raise ApiError("ACCOUNT_NOT_ACTIVE", "仅正常状态账号可合并", 409)
        moved: list[str] = []
        discarded = 0
        with transaction.atomic():
            for ref in references():
                model, field, on_conflict = ref["model"], ref["field"], ref["on_conflict"]
                if on_conflict == "move_all":
                    count = model.objects.filter(**{field: secondary}).update(**{field: primary})
                    moved.append(f"{model._meta.label}.{field}:{count}")
                elif on_conflict == "delete_secondary":
                    count, _ = model.objects.filter(**{field: secondary}).delete()
                    discarded += count
                elif on_conflict == "custom" and ref["handler"] is not None:
                    moved.extend(ref["handler"](primary.id, secondary.id))
                # keep_primary: 保留旧记录
            AccountService.fill_empty_profile_from(primary, secondary)
            AccountService.tombstone(secondary)
            AuditService.record(actor=actor or (AuditActor("ADMIN", admin_id, f"管理员{admin_id}")
                                                if admin_id else AuditActor("SYSTEM", None, "系统")),
                                action="ACCOUNTS_MERGED", object_type="user",
                                object_id=str(primary.id), result="SUCCESS",
                                detail={"primary": primary.id, "secondary": secondary.id,
                                        "trigger": trigger, "moved": moved,
                                        "discarded": discarded})
        return {"primary_id": primary.id, "secondary_id": secondary.id, "moved": moved,
                "discarded": discarded}


_ = (MembershipService,)
