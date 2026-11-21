"""MOD-062 / IFC-244~246：注册用户目录信息的只读聚合。"""
from typing import Sequence, TypedDict

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.committee.effective import is_effective
from apps.committee.models import Seat
from apps.residency.models import Membership

POSITION_RANK = {"CHAIR": 4, "VICE_CHAIR": 3, "MEMBER": 2, "REPRESENTATIVE": 1}
ROLE_RANK = {"HEAD": 3, "OWNER": 2, "RESIDENT": 1}
ROLE_LABELS = {"HEAD": "产权业主", "OWNER": "产权业主", "RESIDENT": "同住人"}  # C-34：用户可见文案
# REQ-FUNC-277 / D-01：身份展示用业务全称；席位页"职位"列仍用 Seat.POSITIONS 短名
IDENTITY_LABELS = {
    "CHAIR": "业委会主任",
    "VICE_CHAIR": "业委会副主任",
    "MEMBER": "业委会委员",
    "REPRESENTATIVE": "业主代表",
    "HEAD": "产权业主",
    "OWNER": "产权业主",
    "RESIDENT": "同住人",
    "GUEST": "游客",
}


def identity_label(code: str) -> str:
    """身份 code → 用户可见全称；未知 code 原样返回（AC-282-04）。"""
    return IDENTITY_LABELS.get(code, code)


class IdentityView(TypedDict):
    identity_code: str
    identity_label: str


def identity_view(*, memberships: Sequence[Membership], seats: Sequence[Seat]) -> IdentityView:
    """最高身份：业委会职务 > 产权业主 > 同住人 > 游客（REQ-FUNC-136 / C-34：户主不作为身份文案，HEAD 与 OWNER 同为产权业主）。"""
    today = timezone.localdate()
    active_seats = [s for s in seats if is_effective(s, today)]
    if active_seats:
        seat = max(active_seats, key=lambda s: (POSITION_RANK.get(s.position, 0), s.term_end, s.id or 0))
        return {"identity_code": seat.position, "identity_label": identity_label(seat.position)}
    active_memberships = [m for m in memberships if m.ended_at is None]
    if active_memberships:
        membership = max(active_memberships,
                         key=lambda m: (ROLE_RANK.get(m.role, 0), m.certified_at, m.id or 0))
        code = "RESIDENT" if membership.role == "RESIDENT" else "OWNER"
        return {"identity_code": code, "identity_label": ROLE_LABELS.get(membership.role, "产权业主")}
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
