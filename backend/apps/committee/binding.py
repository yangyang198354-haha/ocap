# MOD-140 / implements IFC-352 / depends registry.models、registry.ownership、residency.models（只读）、core.audit
"""待绑定席位与已认证用户的绑定服务（ADR-138、ADR-139）：永不向外抛异常。"""
import logging
from typing import Literal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.registry.models import RegistryOwner, RegistryPhone
from apps.registry.ownership import normalize_owner_name
from apps.residency.models import Membership

from .models import Seat

logger = logging.getLogger(__name__)

Outcome = Literal["NOOP", "BOUND", "CONFLICT"]
_SYSTEM = AuditActor("SYSTEM", None, "系统")


def _holder_detail(seat: Seat) -> dict:
    return {"owner_id": seat.holder_owner_id, "unit": seat.holder_unit_text, "owner_name": seat.holder_name}


class SeatBinding:
    @staticmethod
    def try_bind(user_id: int, owner_id: int, *, via: str) -> Outcome:
        """永不向外抛异常（内部 savepoint + try/except，失败记日志返回 "NOOP"）。"""
        try:
            with transaction.atomic():
                return SeatBinding._bind(user_id, owner_id, via)
        except Exception:  # noqa: BLE001 - 绑定不得影响认证主流程
            logger.exception("席位绑定异常 user=%s owner=%s", user_id, owner_id)
            return "NOOP"

    @staticmethod
    def _bind(user_id: int, owner_id: int, via: str) -> Outcome:
        today = timezone.localdate()
        seat = (Seat.objects.select_for_update()
                .filter(holder_owner_id=owner_id, user__isnull=True, status="ACTIVE", term_end__gte=today)
                .first())
        if seat is None:
            return "NOOP"
        owner = RegistryOwner.objects.filter(id=owner_id).first()
        if owner is None or normalize_owner_name(owner.name) != seat.holder_name:
            return "NOOP"  # 清册已变化，交由 reconcile_registry_seats 失效
        now = timezone.now()
        if Seat.objects.filter(user_id=user_id, status="ACTIVE").exists():
            return SeatBinding._conflict(seat, user_id, via, now)
        try:
            with transaction.atomic():
                seat.user_id = user_id
                seat.bound_at = now
                seat.bind_conflict_at = None
                seat.save(update_fields=["user", "bound_at", "bind_conflict_at"])
        except IntegrityError:
            seat.user_id = None
            seat.bound_at = None
            return SeatBinding._conflict(seat, user_id, via, now)
        AuditService.record(actor=_SYSTEM, action="SEAT_BOUND", object_type="seat", object_id=str(seat.id),
                            result="SUCCESS",
                            detail={"user_id": user_id, "via": via, "position": seat.position,
                                    "holder": _holder_detail(seat)})
        return "BOUND"

    @staticmethod
    def _conflict(seat: Seat, user_id: int, via: str, now) -> Outcome:
        seat.bind_conflict_at = now
        seat.save(update_fields=["bind_conflict_at"])
        AuditService.record(actor=_SYSTEM, action="SEAT_BIND_CONFLICT", object_type="seat",
                            object_id=str(seat.id), result="FAILURE",
                            detail={"seat_id": seat.id, "user_id": user_id, "via": via})
        return "CONFLICT"

    @staticmethod
    def certified_user_of(owner: RegistryOwner) -> int | None:
        """已认证该清册业主的用户：先查 Membership.registry_owner；无则按已验证手机号回退（ADR-138）。"""
        roles = ["HEAD", "OWNER"]
        row = (Membership.objects.filter(registry_owner_id=owner.id, ended_at__isnull=True, role__in=roles)
               .order_by("certified_at", "id").values_list("user_id", flat=True).first())
        if row is not None:
            return row
        phones = list(RegistryPhone.objects.filter(owner_id=owner.id).values_list("phone", flat=True))
        if not phones:
            return None
        return (Membership.objects.filter(unit_id=owner.unit_id, ended_at__isnull=True, role__in=roles,
                                          user__phone__in=phones)
                .order_by("certified_at", "id").values_list("user_id", flat=True).first())
