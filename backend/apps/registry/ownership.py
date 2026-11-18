# MOD-114 / implements IFC-304, IFC-305 / depends registry.models（不依赖 residency、core.audit）
"""清册核对与追加：姓名归一、"同一业主"比对、申诉通过后追加产权人（C-58、C-61）。"""
from dataclasses import dataclass
from typing import Literal

from apps.core.masking import mask_phone

from .models import RegistryOwner, RegistryPhone, RegistryUnit

OWNER_NAME_MAX: int = 64


def normalize_owner_name(text: str | None) -> str:
    """全角空格转半角空格后去首尾空白；不做中间空格、大小写、繁简、模糊处理（IFC-304）。"""
    if not isinstance(text, str):
        return ""
    return text.replace("　", " ").strip()


def matched_owner(unit_id: int, name: str, phone: str | None) -> RegistryOwner | None:
    """IFC-355：与 owner_matches 同一判定，返回命中的清册业主行（比较在 Python 内进行，ADR-113）。"""
    wanted = normalize_owner_name(name)
    if not wanted or not phone:
        return None
    row = (RegistryPhone.objects.filter(unit_id=unit_id, phone=phone)
           .select_related("owner").order_by("id").first())
    if row is None or not row.owner.name:
        return None
    return row.owner if normalize_owner_name(row.owner.name) == wanted else None


def owner_matches(unit_id: int, name: str, phone: str | None) -> bool:
    """用户姓名与手机号是否对应该专有部分清册中的同一位业主。"""
    return matched_owner(unit_id, name, phone) is not None


@dataclass(frozen=True)
class AppendResult:
    result: Literal["OWNER_ADDED", "PHONE_ADDED", "UNCHANGED"]
    owner_id: int
    owner_phone_written: bool
    names_before: tuple[str, ...]
    names_after: tuple[str, ...]
    phone_masked: str | None


class PhoneOwnedByOtherOwner(Exception):
    """号码已登记在该专有部分另一位业主名下（视图翻译为 409）。"""


def _names(unit_id: int) -> tuple[str, ...]:
    return tuple(n for n in RegistryOwner.objects.filter(unit_id=unit_id).order_by("id")
                 .values_list("name", flat=True) if n)


def append_owner_from_appeal(unit_id: int, name: str, phone: str | None) -> AppendResult:
    """申诉通过后追加产权人：同名复用并追加号码，同号属他人则拒绝；不动原业主与认证（IFC-305）。

    调用方须已处于 transaction.atomic()；IntegrityError 由调用方回滚并转 409。
    """
    list(RegistryUnit.objects.select_for_update().filter(id=unit_id).values_list("id", flat=True))
    wanted = normalize_owner_name(name)
    names_before = _names(unit_id)
    owner = next((o for o in RegistryOwner.objects.filter(unit_id=unit_id).order_by("id")
                  if o.name and normalize_owner_name(o.name) == wanted), None)
    created = False
    if owner is None:
        owner = RegistryOwner.objects.create(unit_id=unit_id, name=wanted)
        created = True
    if not phone:
        return AppendResult("OWNER_ADDED" if created else "UNCHANGED", owner.id, False,
                            names_before, _names(unit_id), None)
    existing = RegistryPhone.objects.filter(unit_id=unit_id, phone=phone).first()
    if existing is not None and existing.owner_id != owner.id:
        raise PhoneOwnedByOtherOwner()
    if existing is not None:
        return AppendResult("OWNER_ADDED" if created else "UNCHANGED", owner.id, False,
                            names_before, _names(unit_id), mask_phone(phone))
    RegistryPhone.objects.create(unit_id=unit_id, owner=owner, phone=phone)
    return AppendResult("OWNER_ADDED" if created else "PHONE_ADDED", owner.id, True,
                        names_before, _names(unit_id), mask_phone(phone))
