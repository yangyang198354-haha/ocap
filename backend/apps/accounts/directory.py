"""MOD-062 / IFC-244~246：注册用户目录信息的只读聚合。"""
from typing import Sequence, TypedDict

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.committee.models import Seat
from apps.residency.models import Membership

POSITION_RANK = {"CHAIR": 4, "VICE_CHAIR": 3, "MEMBER": 2, "REPRESENTATIVE": 1}
ROLE_RANK = {"HEAD": 3, "OWNER": 2, "RESIDENT": 1}


class IdentityView(TypedDict):
    identity_code: str
    identity_label: str


def identity_view(*, memberships: Sequence[Membership], seats: Sequence[Seat]) -> IdentityView:
    """按 IFC-244 取最高身份：业委会职务 > 户主 > 产权业主 > 同住人 > 游客。"""
    today = timezone.localdate()
    active_seats = [s for s in seats if s.status == "ACTIVE" and s.term_end >= today]
    if active_seats:
        seat = max(active_seats, key=lambda s: (POSITION_RANK.get(s.position, 0), s.term_end, s.id or 0))
        return {"identity_code": seat.position, "identity_label": seat.get_position_display()}
    active_memberships = [m for m in memberships if m.ended_at is None]
    if active_memberships:
        membership = max(active_memberships,
                         key=lambda m: (ROLE_RANK.get(m.role, 0), m.certified_at, m.id or 0))
        return {"identity_code": membership.role, "identity_label": membership.get_role_display()}
    return {"identity_code": "GUEST", "identity_label": "游客"}


def certified_units(*, memberships: Sequence[Membership]) -> int:
    """IFC-245：当前有效认证的专有部分去重数量。"""
    return len({m.unit_id for m in memberships if m.ended_at is None})


def real_names(*, user, memberships: Sequence[Membership]) -> list[str]:
    """IFC-245：产权业主在已认证专有部分清册中的实名，去重保序。"""
    if not user.phone:
        return []
    names: list[str] = []
    for membership in memberships:
        if membership.ended_at is not None or membership.role not in ("HEAD", "OWNER"):
            continue
        for owner in membership.unit.owners.all():
            if not owner.name or owner.name in names:
                continue
            if any(phone.phone == user.phone for phone in owner.phones.all()):
                names.append(owner.name)
    return names


def real_name_q(q: str) -> Q:
    """IFC-246：实名搜索条件；同一 RegistryPhone 记录同时约束手机号与业主姓名。"""
    matched = Membership.objects.filter(
        user=OuterRef("pk"),
        role__in=("HEAD", "OWNER"),
        ended_at__isnull=True,
        unit__phones__phone=OuterRef("phone"),
        unit__phones__owner__name__icontains=q,
    )
    return Q(Exists(matched))
