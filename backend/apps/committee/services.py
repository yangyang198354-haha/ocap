"""业委会服务（IFC-062/063）。"""
from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService

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
        return Seat.objects.filter(user_id=user_id, status="ACTIVE",
                                   term_end__gte=today).order_by("-term_end").first()

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
        return list(Seat.objects.filter(status="ACTIVE", term_end__gte=today,
                                        position__in=["CHAIR", "VICE_CHAIR", "MEMBER"])
                    .values_list("user_id", flat=True))

    @staticmethod
    def active_representative_ids() -> list[int]:
        today = timezone.localdate()
        return list(Seat.objects.filter(status="ACTIVE", term_end__gte=today,
                                        position="REPRESENTATIVE").values_list("user_id", flat=True))

    @staticmethod
    def identity_labels(user_id: int) -> list[str]:
        labels = []
        seat = CommitteeQuery.active_seat(user_id)
        if seat is not None:
            labels.append(seat.get_position_display())
        from apps.residency.services import MembershipService

        for membership in MembershipService.list_active(user_id):
            labels.append(membership.get_role_display())
            break
        if not labels:
            labels.append("游客")
        return labels

    @staticmethod
    def denominator_for_half_majority(mode: str) -> int:
        config = CommitteeConfig.load()
        if mode == "CONFIGURED_CAP":
            return sum(getattr(config, field) or 0
                       for field in ("cap_chair", "cap_vice", "cap_member"))
        today = timezone.localdate()
        return Seat.objects.filter(status="ACTIVE", term_end__gte=today,
                                   position__in=["CHAIR", "VICE_CHAIR", "MEMBER"]).count()


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
                term_end=add_months(term_start, term_months), granted_by_admin_id=admin_id,
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
        with transaction.atomic():
            seat.status = "REPLACED"
            seat.active_slot = None
            seat.ended_at = timezone.now()
            seat.end_reason = "CHANGED"
            seat.save()
            new_seat = CommitteeCommands.grant(user_id=seat.user_id, position=position,
                                               term_start=timezone.localdate(), admin_id=admin_id)
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
