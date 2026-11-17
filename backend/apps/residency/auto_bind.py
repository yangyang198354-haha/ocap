"""MOD-034：按已验证手机号自动绑定产权业主（IFC-163）。"""
import logging
from dataclasses import dataclass

from django.db import transaction

from apps.core.errors import ApiError
from apps.registry.services import RegistryService

from .services import MembershipService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutoBound:
    unit_id: int
    specific_part: str
    role: str

    def as_dict(self) -> dict:
        return {"unit_id": self.unit_id, "specific_part": self.specific_part, "role": self.role}


def certify_one(user, unit, origin: str, detail_extra: dict | None = None) -> tuple[str | None, str | None]:
    """逐套认证（共享 savepoint 写法，DEF-009）：返回 (role, None) 或 (None, 错误码)；不向外抛异常。"""
    extra = {"detail_extra": detail_extra} if detail_extra else {}  # 旧调用形态（无该参数）保持不变
    try:
        with transaction.atomic():
            role = MembershipService.certify_owner(user.id, unit.id, "REGISTRY", origin=origin, **extra)
    except ApiError as exc:
        if exc.code != "ALREADY_CERTIFIED":
            logger.warning("清册绑定失败 user=%s unit=%s code=%s", user.id, unit.id, exc.code)
        return None, exc.code
    except Exception:  # noqa: BLE001 - 绑定不得影响主流程
        logger.exception("清册绑定异常 user=%s unit=%s", user.id, unit.id)
        return None, "FAILED"
    return role, None


def certify_units(user, units, origin: str) -> list[AutoBound]:
    bound: list[AutoBound] = []
    for unit in units:
        if MembershipService.is_owner_of(user.id, unit.id):
            continue
        role, _code = certify_one(user, unit, origin)
        if role is not None:
            bound.append(AutoBound(unit_id=unit.id, specific_part=unit.specific_part, role=role))
    return bound


class AutoBindService:
    @staticmethod
    def bind_by_phone(user) -> list[AutoBound]:
        """前置：调用方保证 user.phone 刚通过验证码校验（C-25）；不向外抛异常。
        ADR-130：已不再被注册/绑定手机号视图调用（改为 PhoneMatchService 引导确认），仅保留供既有测试与复用。"""
        phone = getattr(user, "phone", None)
        if not phone:
            return []
        return certify_units(user, RegistryService.units_by_phone(phone), "REGISTRY_AUTO")
