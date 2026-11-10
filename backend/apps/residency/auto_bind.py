"""MOD-034：按已验证手机号自动绑定产权业主（IFC-163）。"""
import logging
from dataclasses import dataclass

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


class AutoBindService:
    @staticmethod
    def bind_by_phone(user) -> list[AutoBound]:
        """前置：调用方保证 user.phone 刚通过验证码校验（C-25）；不向外抛异常。"""
        phone = getattr(user, "phone", None)
        if not phone:
            return []

        bound: list[AutoBound] = []
        for unit in RegistryService.units_by_phone(phone):
            if MembershipService.is_owner_of(user.id, unit.id):
                continue
            try:
                role = MembershipService.certify_owner(
                    user.id, unit.id, "REGISTRY", origin="REGISTRY_AUTO"
                )
            except ApiError as exc:
                if exc.code == "ALREADY_CERTIFIED":
                    continue
                logger.warning("清册自动绑定失败 user=%s unit=%s code=%s", user.id, unit.id, exc.code)
                break
            except Exception:  # noqa: BLE001 - 自动绑定不得影响注册/绑定主流程
                logger.exception("清册自动绑定异常 user=%s unit=%s", user.id, unit.id)
                break
            bound.append(AutoBound(unit_id=unit.id, specific_part=unit.specific_part, role=role))
        return bound
