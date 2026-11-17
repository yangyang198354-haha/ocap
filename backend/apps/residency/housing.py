# MOD-074 / implements IFC-273 / depends accounts.directory, residency.models, committee.models
"""我的房屋聚合（只读，不写库）。"""
from datetime import datetime
from typing import TypedDict

from django.db.models import Count

from apps.accounts.directory import ROLE_LABELS, IdentityView, identity_view
from apps.committee.models import Seat
from apps.registry import display
from apps.registry.ordering import unit_sort_key

from .models import Membership, ResidentApplication

OWNER_ROLES = ("HEAD", "OWNER")


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


class HousingPayload(TypedDict):
    summary: IdentityView
    units: list[HousingUnit]
    pending_review_count: int


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
        })
    return {"summary": summary, "units": units,
            "pending_review_count": sum(u["pending_application_count"] for u in units)}
