# MOD-132 / implements IFC-335 / depends MOD-134(registry.display), registry.services, residency.services/auto_bind, core.masking
"""手机号匹配清册后的引导确认服务（ADR-128、ADR-129）。

匹配集合永远由"当前账号手机号 + 清册"实时计算；前端传来的 unit_ids 只被视为"用户勾选"，必须是匹配集合子集。
"""
import logging
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.core.errors import ApiError
from apps.core.masking import mask_phone
from apps.registry import display
from apps.registry.ordering import unit_sort_key
from apps.registry.services import RegistryService

from .auto_bind import certify_one
from .models import PhoneMatchPrompt
from .services import MembershipService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchUnit:
    unit_id: int
    specific_part: str
    unit_type_label: str  # 未登记为"未登记"

    def as_dict(self) -> dict:
        return {"unit_id": self.unit_id, "specific_part": self.specific_part,
                "unit_type_label": self.unit_type_label}


@dataclass(frozen=True)
class ConfirmItem:
    unit_id: int
    specific_part: str
    ok: bool
    role: str | None  # ok 时 "HEAD" | "OWNER"
    code: str | None  # 未成功时的错误码

    def as_dict(self) -> dict:
        return {"unit_id": self.unit_id, "specific_part": self.specific_part, "ok": self.ok,
                "role": self.role, "code": self.code}


def _unowned_matches(user) -> list:
    """该手机号登记且 user 尚非产权业主的专有部分，按数字自然顺序。"""
    phone = getattr(user, "phone", None)
    if not phone:
        return []
    units = [u for u in RegistryService.units_by_phone(phone) if not MembershipService.is_owner_of(user.id, u.id)]
    return sorted(units, key=lambda u: unit_sort_key(u.building, u.unit_no, u.floor, u.room, u.id))


class PhoneMatchService:
    @staticmethod
    def open_prompt(user) -> int:
        """触发点调用：user.phone 刚通过验证码校验。n>0 → 建立/重置为 PENDING；n=0 → 不建行（已有行不改）。
        不向外抛异常，不得影响注册/绑定主流程。"""
        try:
            count = len(_unowned_matches(user))
            if count > 0:
                with transaction.atomic():
                    PhoneMatchPrompt.objects.update_or_create(
                        user=user, defaults={"status": "PENDING", "resolved_at": None})
            return count
        except Exception:  # noqa: BLE001
            logger.exception("手机号匹配引导开启失败 user=%s", getattr(user, "id", None))
            return 0

    @staticmethod
    def _is_pending(user) -> bool:
        return PhoneMatchPrompt.objects.filter(user=user, status="PENDING").exists()

    @staticmethod
    def pending_matches(user) -> list[MatchUnit]:
        if not PhoneMatchService._is_pending(user):
            return []
        return [MatchUnit(u.id, u.specific_part, display.unit_type_label(u)) for u in _unowned_matches(user)]

    @staticmethod
    def confirm(user, unit_ids: list[int]) -> list[ConfirmItem]:
        """前置：已通过限频、unit_ids 已做形状校验。"""
        with transaction.atomic():
            prompt = PhoneMatchPrompt.objects.select_for_update().filter(user=user).first()
            if prompt is None or prompt.status != "PENDING":
                raise ApiError("MATCH_NOT_PENDING", "当前没有待确认的清册匹配", 409)
            phone = getattr(user, "phone", None)
            allowed = {u.id: u for u in RegistryService.units_by_phone(phone)} if phone else {}
            # 任一不在匹配集合内 → 整批拒绝，与手动认证同一错误出口（REQ-NFUNC-037），不含清册信息
            if any(uid not in allowed for uid in unit_ids):
                raise ApiError("OWNER_NOT_MATCHED", "未能通过清册核对", 422)
            extra = {"phone_masked": mask_phone(phone)}
            items: list[ConfirmItem] = []
            for uid in unit_ids:
                unit = allowed[uid]
                if MembershipService.is_owner_of(user.id, uid):
                    items.append(ConfirmItem(uid, unit.specific_part, False, None, "ALREADY_CERTIFIED"))
                    continue
                role, code = certify_one(user, unit, "REGISTRY_AUTO", detail_extra=extra)
                items.append(ConfirmItem(uid, unit.specific_part, role is not None, role, code))
            prompt.status = "DONE"
            prompt.resolved_at = timezone.now()
            prompt.save(update_fields=["status", "resolved_at"])
            return items

    @staticmethod
    def dismiss(user) -> None:
        PhoneMatchPrompt.objects.filter(user=user, status="PENDING").update(
            status="DISMISSED", resolved_at=timezone.now())

    @staticmethod
    def expire(user) -> None:
        PhoneMatchPrompt.objects.filter(user=user, status="PENDING").update(
            status="EXPIRED", resolved_at=timezone.now())
