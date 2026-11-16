"""业委会服务（IFC-062/063）。"""
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService

from .effective import effective_q
from .models import CommitteeConfig, Seat

POSITION_RANK = {"CHAIR": 4, "VICE_CHAIR": 3, "MEMBER": 2, "REPRESENTATIVE": 1}
CAP_FIELDS = {
    "CHAIR": "cap_chair", "VICE_CHAIR": "cap_vice", "MEMBER": "cap_member", "REPRESENTATIVE": "cap_rep",
}
TERM_FIELDS = {
    "CHAIR": "term_months_chair", "VICE_CHAIR": "term_months_vice",
    "MEMBER": "term_months_member", "REPRESENTATIVE": "term_months_rep",
}


def add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    day = min(value.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


class CommitteeQuery:
    @staticmethod
    def active_seat(user_id: int) -> Seat | None:
        today = timezone.localdate()
        return Seat.objects.filter(effective_q(today), user_id=user_id).order_by("-term_end").first()

    @staticmethod
    def is_member(user_id: int) -> bool:
        seat = CommitteeQuery.active_seat(user_id)
        return seat is not None and seat.position in {"CHAIR", "VICE_CHAIR", "MEMBER"}

    @staticmethod
    def is_chair_or_vice(user_id: int) -> bool:
        seat = CommitteeQuery.active_seat(user_id)
        return seat is not None and seat.position in {"CHAIR", "VICE_CHAIR"}

    @staticmethod
    def is_representative(user_id: int) -> bool:
        seat = CommitteeQuery.active_seat(user_id)
        return seat is not None and seat.position == "REPRESENTATIVE"

    @staticmethod
    def active_member_ids() -> list[int]:
        today = timezone.localdate()
        return list(Seat.objects.filter(effective_q(today), position__in=["CHAIR", "VICE_CHAIR", "MEMBER"])
                    .values_list("user_id", flat=True))

    @staticmethod
    def active_representative_ids() -> list[int]:
        today = timezone.localdate()
        return list(Seat.objects.filter(effective_q(today), position="REPRESENTATIVE")
                    .values_list("user_id", flat=True))

    @staticmethod
    def identity_labels(user_id: int) -> list[str]:
        """C-34 / REQ-FUNC-136：用户可见身份只返回单一最高身份。"""
        seat = CommitteeQuery.active_seat(user_id)
        if seat is not None:
            return [seat.get_position_display()]
        from apps.residency.services import MembershipService

        memberships = MembershipService.list_active(user_id)
        if any(membership.role in ("HEAD", "OWNER") for membership in memberships):
            return ["产权业主"]
        if memberships:
            return ["同住人"]
        return ["游客"]

    @staticmethod
    def denominator_for_half_majority(mode: str) -> int:
        config = CommitteeConfig.load()
        if mode == "CONFIGURED_CAP":
            return sum(getattr(config, field) or 0
                       for field in ("cap_chair", "cap_vice", "cap_member"))
        today = timezone.localdate()
        return Seat.objects.filter(effective_q(today), position__in=["CHAIR", "VICE_CHAIR", "MEMBER"]).count()


class CommitteeCommands:
    @staticmethod
    def grant(*, user_id: int, position: str, term_start: date, admin_id: int) -> Seat:
        config = CommitteeConfig.load()
        term_months = getattr(config, TERM_FIELDS[position])
        if not term_months:
            from apps.core.errors import ApiError

            raise ApiError("TERM_NOT_CONFIGURED", "该身份任期未配置", 409)
        cap = getattr(config, CAP_FIELDS[position])
        if cap is None:
            from apps.core.errors import ApiError

            raise ApiError("CAP_NOT_CONFIGURED", "该身份人数上限未配置", 409)
        term_end = add_months(term_start, term_months)
        if term_end <= timezone.localdate():  # IFC-312：结束日须严格晚于今天（AC-205-02/03）
            from apps.core.errors import ApiError

            raise ApiError("INVALID_VALUE", f"按配置任期，该席位已于 {term_end:%Y-%m-%d} 结束，不能授予")
        # 注意：下面两项计数有意含"未生效"席位（Q-OA-28=A），不使用 effective_q
        if Seat.objects.filter(user_id=user_id, status="ACTIVE").exists():
            from apps.core.errors import ApiError

            raise ApiError("ALREADY_SEATED", "该用户已有有效席位", 409)
        with transaction.atomic():
            current = Seat.objects.filter(status="ACTIVE", position=position).count()
            if current >= cap:
                from apps.core.errors import ApiError

                raise ApiError("CAP_REACHED", "该身份在任人数已达上限", 409)
            seat = Seat.objects.create(
                user_id=user_id, position=position, term_start=term_start,
                term_end=term_end, granted_by_admin_id=admin_id,
                active_slot=1,
            )
        AuditService.record(actor=AuditActor("ADMIN", admin_id, f"管理员{admin_id}"),
                            action="SEAT_GRANTED", object_type="seat", object_id=str(seat.id),
                            result="SUCCESS", detail={"user_id": user_id, "position": position})
        return seat

    @staticmethod
    def change(seat: Seat, *, position: str, admin_id: int) -> Seat:
        if seat.position == position:
            return seat
        config = CommitteeConfig.load()
        if not getattr(config, TERM_FIELDS[position]):
            from apps.core.errors import ApiError

            raise ApiError("TERM_NOT_CONFIGURED", "该身份任期未配置", 409)
        today = timezone.localdate()
        # IFC-312：旧席位未生效（开始日在将来）时新席位沿用旧开始日，不让变更提前生效
        new_start = seat.term_start if seat.term_start > today else today
        with transaction.atomic():
            seat.status = "REPLACED"
            seat.active_slot = None
            seat.ended_at = timezone.now()
            seat.end_reason = "CHANGED"
            seat.save()
            new_seat = CommitteeCommands.grant(user_id=seat.user_id, position=position,
                                               term_start=new_start, admin_id=admin_id)
        AuditService.record(actor=AuditActor("ADMIN", admin_id, f"管理员{admin_id}"),
                            action="SEAT_CHANGED", object_type="seat", object_id=str(new_seat.id),
                            result="SUCCESS", detail={"from": seat.position, "to": position})
        return new_seat

    @staticmethod
    def revoke(seat: Seat, *, admin_id: int) -> None:
        seat.status = "REVOKED"
        seat.active_slot = None
        seat.ended_at = timezone.now()
        seat.end_reason = "REVOKED"
        seat.save()
        AuditService.record(actor=AuditActor("ADMIN", admin_id, f"管理员{admin_id}"),
                            action="SEAT_REVOKED", object_type="seat", object_id=str(seat.id),
                            result="SUCCESS")

    @staticmethod
    def sync_after_ownership_change(user_id: int) -> dict | None:
        from apps.residency.services import MembershipService

        if MembershipService.is_owner_of_any(user_id):
            return None
        seats = list(Seat.objects.filter(user_id=user_id, status="ACTIVE"))
        for seat in seats:
            seat.status = "INVALIDATED"
            seat.active_slot = None
            seat.ended_at = timezone.now()
            seat.end_reason = "NOT_OWNER"
            seat.save()
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"),
                                action="SEAT_INVALIDATED", object_type="seat",
                                object_id=str(seat.id), result="SUCCESS")
        return {"invalidated": len(seats)} if seats else None

    @staticmethod
    def _audit_merge_invalidated(seat: Seat) -> None:
        # DEF-018：AC-066-05/AC-064-08 合并使身份失效时写身份失效审计
        AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="SEAT_INVALIDATED",
                            object_type="seat", object_id=str(seat.id), result="SUCCESS",
                            detail={"reason": "ACCOUNT_MERGED", "position": seat.position})

    @staticmethod
    def merge_seats(primary_id: int, secondary_id: int) -> list[str]:
        moved: list[str] = []
        primary = Seat.objects.filter(user_id=primary_id, status="ACTIVE").first()
        for seat in Seat.objects.filter(user_id=secondary_id, status="ACTIVE"):
            if primary is None:
                seat.user_id = primary_id
                seat.save(update_fields=["user"])
                primary = seat
                moved.append(f"move:{seat.id}")
            elif POSITION_RANK[seat.position] > POSITION_RANK[primary.position]:
                seat.status = "MERGED"
                seat.active_slot = None
                seat.save()
                primary.status = "MERGED"
                primary.active_slot = None
                primary.save()
                CommitteeCommands._audit_merge_invalidated(primary)
                seat.user_id = primary_id
                seat.status = "ACTIVE"
                seat.active_slot = 1
                seat.save()
                primary = seat
                moved.append(f"upgrade:{seat.id}")
            else:
                seat.status = "MERGED"
                seat.active_slot = None
                seat.save()
                CommitteeCommands._audit_merge_invalidated(seat)
                moved.append(f"drop:{seat.id}")
        return moved

    @staticmethod
    def expire_due(today: date) -> int:
        rows = list(Seat.objects.filter(status="ACTIVE", term_end__lt=today))
        for seat in rows:
            seat.status = "EXPIRED"
            seat.active_slot = None
            seat.ended_at = timezone.now()
            seat.end_reason = "EXPIRED"
            seat.save()
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="SEAT_EXPIRED",
                                object_type="seat", object_id=str(seat.id), result="SUCCESS")
        return len(rows)


_ = POSITION_RANK
