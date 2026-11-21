"""业委会服务（IFC-062/063）。"""
from datetime import date

from django.db import IntegrityError, transaction
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
        # IFC-367：排除待绑定席位（user 为空），其无表决资格
        return list(Seat.objects.filter(effective_q(today), position__in=["CHAIR", "VICE_CHAIR", "MEMBER"])
                    .exclude(user__isnull=True).values_list("user_id", flat=True))

    @staticmethod
    def active_representative_ids() -> list[int]:
        today = timezone.localdate()
        return list(Seat.objects.filter(effective_q(today), position="REPRESENTATIVE")
                    .exclude(user__isnull=True).values_list("user_id", flat=True))

    @staticmethod
    def pending_bind_count(positions: tuple[str, ...] = ("CHAIR", "VICE_CHAIR", "MEMBER")) -> int:
        """IFC-367：生效且尚未绑定用户（user 为空）的席位数，用于席位页提示（IFC-356）。"""
        today = timezone.localdate()
        return Seat.objects.filter(effective_q(today), position__in=list(positions), user__isnull=True).count()

    @staticmethod
    def identity_labels(user_id: int) -> list[str]:
        """C-34 / REQ-FUNC-136：用户可见身份只返回单一最高身份；REQ-FUNC-277 用业务全称。"""
        from apps.accounts.directory import identity_label

        seat = CommitteeQuery.active_seat(user_id)
        if seat is not None:
            return [identity_label(seat.position)]
        from apps.residency.services import MembershipService

        memberships = MembershipService.list_active(user_id)
        if any(membership.role in ("HEAD", "OWNER") for membership in memberships):
            return ["产权业主"]
        if memberships:
            return ["同住人"]
        return ["游客"]

    @staticmethod
    def denominator_for_half_majority(mode: str) -> int:
        """半数同意决议的应投总数：ACTIVE 口径含待绑定席位（Q-B18-21=B，REQ-FUNC-254），业主代表不计入。"""
        config = CommitteeConfig.load()
        if mode == "CONFIGURED_CAP":
            return sum(getattr(config, field) or 0
                       for field in ("cap_chair", "cap_vice", "cap_member"))
        today = timezone.localdate()
        return Seat.objects.filter(effective_q(today), position__in=["CHAIR", "VICE_CHAIR", "MEMBER"]).count()


class CommitteeCommands:
    @staticmethod
    def grant(*, user_id: int | None = None, registry_owner_id: int | None = None, position: str,
              term_start: date, admin_id: int) -> Seat:
        """恰好一个 user_id / registry_owner_id（IFC-347/348）。registry_owner_id：授予给清册业主，
        已认证用户存在则直接绑定，否则为待绑定席位（user 为空，占名额、计入分母）。"""
        from apps.core.errors import ApiError

        if (user_id is None) == (registry_owner_id is None):
            raise ApiError("INVALID_VALUE", "user_id 与 registry_owner_id 须恰好给一个")
        owner = None
        holder = None
        if registry_owner_id is not None:
            from apps.registry.models import RegistryOwner
            from apps.registry.ownership import normalize_owner_name

            owner = RegistryOwner.objects.select_related("unit").filter(id=registry_owner_id).first()
            if owner is None:
                raise ApiError("NOT_FOUND", "清册业主不存在", 404)
            holder_name = normalize_owner_name(owner.name)
            if not holder_name:
                raise ApiError("OWNER_NAME_REQUIRED", "该业主姓名为空，不能授予席位", 422)
            holder = {"owner_id": owner.id, "unit_text": owner.unit.specific_part, "name": holder_name}
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
        bound_user_id = user_id
        if owner is not None:
            from .binding import SeatBinding

            if Seat.objects.filter(holder_owner_id=owner.id, status="ACTIVE").exists():
                raise ApiError("ALREADY_SEATED", "该业主已有有效席位", 409)
            bound_user_id = SeatBinding.certified_user_of(owner)  # AC-256-05：已认证则直接对应注册用户
        # 注意：下面两项计数有意含"未生效"席位（Q-OA-28=A），不使用 effective_q
        if bound_user_id is not None and Seat.objects.filter(user_id=bound_user_id, status="ACTIVE").exists():
            raise ApiError("ALREADY_SEATED", "该用户已有有效席位", 409)
        extra: dict = {}
        if holder is not None:
            extra = {"holder_owner_id": holder.get("owner_id"), "holder_unit_text": holder.get("unit_text") or "",
                     "holder_name": holder.get("name") or ""}
            if bound_user_id is not None:
                extra["bound_at"] = timezone.now()
        try:
            with transaction.atomic():
                current = Seat.objects.filter(status="ACTIVE", position=position).count()
                if current >= cap:
                    raise ApiError("CAP_REACHED", "该身份在任人数已达上限", 409)
                seat = Seat.objects.create(
                    user_id=bound_user_id, position=position, term_start=term_start,
                    term_end=term_end, granted_by_admin_id=admin_id,
                    active_slot=1, **extra,
                )
        except IntegrityError as exc:  # 并发下唯一约束兜底（每人/每清册业主至多一个有效席位）
            raise ApiError("ALREADY_SEATED", "该业主或用户已有有效席位", 409) from exc
        detail: dict = {"user_id": bound_user_id, "position": position}
        if owner is not None:  # 用户 ID 授予路径的审计内容保持不变（TC-INT-708）；本字段不含手机号
            detail["holder"] = {"owner_id": owner.id, "unit": holder["unit_text"], "owner_name": holder["name"]}
        AuditService.record(actor=AuditActor("ADMIN", admin_id, f"管理员{admin_id}"),
                            action="SEAT_GRANTED", object_type="seat", object_id=str(seat.id),
                            result="SUCCESS", detail=detail)
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
            if seat.user_id is not None:
                new_seat = CommitteeCommands.grant(user_id=seat.user_id, position=position,
                                                   term_start=new_start, admin_id=admin_id)
                if seat.holder_owner_id or seat.holder_name:  # 保留清册业主记录（IFC-347 change 语义）
                    Seat.objects.filter(id=new_seat.id).update(
                        holder_owner_id=seat.holder_owner_id, holder_unit_text=seat.holder_unit_text,
                        holder_name=seat.holder_name, bound_at=seat.bound_at)
                    new_seat.refresh_from_db()
            else:  # 待绑定席位可变更职位，仍待绑定（或授予时已有认证用户则直接绑定）
                new_seat = CommitteeCommands.grant(registry_owner_id=seat.holder_owner_id, position=position,
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
    def reconcile_registry_seats() -> int:
        """IFC-353：待绑定席位的清册业主已被删除或改名（姓名与快照不一致）→ 置资格失效并审计；只扫描待绑定席位，幂等。"""
        from apps.registry.models import RegistryOwner
        from apps.registry.ownership import normalize_owner_name

        count = 0
        for seat in list(Seat.objects.filter(status="ACTIVE", user__isnull=True)):
            owner = RegistryOwner.objects.filter(id=seat.holder_owner_id).first() if seat.holder_owner_id else None
            if owner is not None and normalize_owner_name(owner.name) == seat.holder_name:
                continue
            seat.status = "INVALIDATED"
            seat.active_slot = None
            seat.ended_at = timezone.now()
            seat.end_reason = "REGISTRY_CHANGED"
            seat.save()
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="SEAT_INVALIDATED",
                                object_type="seat", object_id=str(seat.id), result="SUCCESS",
                                detail={"reason": "REGISTRY_CHANGED", "reason_label": "清册变化",
                                        "position": seat.position,
                                        "holder": {"owner_id": seat.holder_owner_id, "unit": seat.holder_unit_text,
                                                   "owner_name": seat.holder_name}})
            count += 1
        return count

    @staticmethod
    def expire_due(today: date) -> int:
        CommitteeCommands.reconcile_registry_seats()  # IFC-353：兜底
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
