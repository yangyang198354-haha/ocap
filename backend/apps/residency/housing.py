# MOD-074 / implements IFC-273 / depends accounts.directory, residency.models, committee.models
"""我的房屋聚合（只读，不写库）。"""
from datetime import datetime
from typing import TypedDict

from django.db.models import Count

from apps.accounts.directory import ROLE_LABELS, IdentityView, identity_view
from apps.committee.models import Seat
from apps.registry import display
from apps.registry.ordering import unit_sort_key

from apps.registry.models import RegistryOwner

from .models import Membership, ResidentApplication

OWNER_ROLES = ("HEAD", "OWNER")


def _is_mine(owner: RegistryOwner, linked_owner_ids: dict[int, set[int]],
             phone: str | None) -> bool:
    """IFC-357：清册业主与本人的对应关系——认证时记录关联，或该专有部分内手机号一致。"""
    if owner.id in linked_owner_ids.get(owner.unit_id, ()):
        return True
    return bool(phone) and any(p.phone == phone for p in owner.phones.all())


def _owner_names(memberships, owners_by_unit: dict[int, list[RegistryOwner]],
                 linked_owner_ids: dict[int, set[int]], phone: str | None) -> list[str]:
    names: list[str] = []
    for m in memberships:
        if m.role not in OWNER_ROLES:
            continue
        for owner in owners_by_unit.get(m.unit_id, []):
            if owner.name and _is_mine(owner, linked_owner_ids, phone) and owner.name not in names:
                names.append(owner.name)
    return names


def verified_owner_names(user) -> list[str]:
    """MOD-153 / AC-271-03：与“我的身份与房屋”同一口径的有效产权业主清册姓名。"""
    memberships = list(Membership.objects.filter(user=user, ended_at__isnull=True))
    owner_memberships = [m for m in memberships if m.role in OWNER_ROLES]
    if not owner_memberships:
        return []
    unit_ids = {m.unit_id for m in owner_memberships}
    owners_by_unit: dict[int, list[RegistryOwner]] = {}
    for owner in (RegistryOwner.objects.filter(unit_id__in=unit_ids)
                  .prefetch_related("phones").order_by("id")):
        owners_by_unit.setdefault(owner.unit_id, []).append(owner)
    linked_owner_ids: dict[int, set[int]] = {}
    for m in owner_memberships:
        if m.registry_owner_id is not None:
            linked_owner_ids.setdefault(m.unit_id, set()).add(m.registry_owner_id)
    return _owner_names(owner_memberships, owners_by_unit, linked_owner_ids,
                        getattr(user, "phone", None))


class HousingResident(TypedDict):
    user_id: int
    nickname: str | None
    account_no: str
    joined_at: datetime


class HousingUnit(TypedDict):
    unit_id: int
    specific_part: str
    role: str
    role_label: str
    unit_type_label: str
    area_display: str
    certified_at: datetime
    residents: list[HousingResident]
    pending_application_count: int
    co_owners: list[str]  # IFC-357：该专有部分其余清册业主姓名（不含本人对应的业主行；无手机号、无注册状态）


class HousingPayload(TypedDict):
    summary: IdentityView
    units: list[HousingUnit]
    pending_review_count: int
    real_names: list[str]  # IFC-357：本人作为产权业主对应的清册姓名，去重保序


def housing_view(user) -> HousingPayload:
    memberships = list(Membership.objects.filter(user=user, ended_at__isnull=True)
                       .select_related("unit").order_by("certified_at", "id"))
    seats = list(Seat.objects.filter(user=user, status="ACTIVE"))
    summary = identity_view(memberships=memberships, seats=seats)

    owner_unit_ids = [m.unit_id for m in memberships if m.role in OWNER_ROLES]
    residents_by_unit: dict[int, list[HousingResident]] = {}
    pending_by_unit: dict[int, int] = {}
    if owner_unit_ids:
        rows = (Membership.objects.filter(unit_id__in=owner_unit_ids, role="RESIDENT",
                                          ended_at__isnull=True)
                .select_related("user").order_by("certified_at", "id"))
        for row in rows:
            residents_by_unit.setdefault(row.unit_id, []).append({
                "user_id": row.user_id, "nickname": row.user.nickname,
                "account_no": row.user.account_no, "joined_at": row.certified_at,
            })
        counts = (ResidentApplication.objects.filter(unit_id__in=owner_unit_ids, status="PENDING")
                  .values("unit_id").annotate(n=Count("id")))
        pending_by_unit = {row["unit_id"]: row["n"] for row in counts}

    # IFC-357：本人全部房屋的清册业主一次取出（含号码），查询数不随房屋数增长
    my_unit_ids = list({m.unit_id for m in memberships})
    owners_by_unit: dict[int, list[RegistryOwner]] = {}
    if my_unit_ids:
        for owner in (RegistryOwner.objects.filter(unit_id__in=my_unit_ids)
                      .prefetch_related("phones").order_by("id")):
            owners_by_unit.setdefault(owner.unit_id, []).append(owner)
    linked_owner_ids: dict[int, set[int]] = {}
    for m in memberships:
        if m.registry_owner_id is not None:
            linked_owner_ids.setdefault(m.unit_id, set()).add(m.registry_owner_id)

    def is_mine(owner: RegistryOwner) -> bool:
        return _is_mine(owner, linked_owner_ids, getattr(user, "phone", None))

    real_names = _owner_names(memberships, owners_by_unit, linked_owner_ids,
                              getattr(user, "phone", None))

    def co_owner_names(unit_id: int) -> list[str]:
        names: list[str] = []
        for owner in owners_by_unit.get(unit_id, []):
            if owner.name and not is_mine(owner) and owner.name not in names:
                names.append(owner.name)
        return names

    units: list[HousingUnit] = []
    # IFC-290：房屋行按数字自然顺序（与 /me 同口径）；summary/residents 仍用上面的原顺序
    ordered = sorted(memberships, key=lambda m: (
        unit_sort_key(m.unit.building, m.unit.unit_no, m.unit.floor, m.unit.room, m.unit_id), m.id))
    for m in ordered:
        is_owner = m.role in OWNER_ROLES
        units.append({
            "unit_id": m.unit_id, "specific_part": m.unit.specific_part, "role": m.role,
            "role_label": ROLE_LABELS.get(m.role, "产权业主"),
            "unit_type_label": display.unit_type_label(m.unit), "area_display": display.area_display(m.unit),
            "certified_at": m.certified_at,
            "residents": residents_by_unit.get(m.unit_id, []) if is_owner else [],
            "pending_application_count": pending_by_unit.get(m.unit_id, 0) if is_owner else 0,
            "co_owners": co_owner_names(m.unit_id),
        })
    return {"summary": summary, "units": units,
            "pending_review_count": sum(u["pending_application_count"] for u in units),
            "real_names": real_names}
