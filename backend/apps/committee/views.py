"""业委会视图（IFC-060/061）。"""
import re
from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.errors import ApiError, NotFound
from apps.core.masking import mask_phone
from apps.core.permissions import IsAdmin
from apps.core.serializers import page_response
from apps.registry.models import RegistryPhone
from apps.residency.models import Membership
from apps.residency.services import MembershipService

from .effective import is_effective
from .binding import SeatBinding
from .models import CommitteeConfig, Seat
from .services import CAP_FIELDS, CommitteeCommands, CommitteeQuery

from django.utils.dateparse import parse_date

TERM_START_MAX_DAYS = 5 * 366  # 开始日上界：今天起约 5 年（OQ-04，待用户确认）

ENDED_STATUSES = ("REVOKED", "EXPIRED", "INVALIDATED", "REPLACED", "MERGED")


def seat_view(seat: Seat, holder_detail: dict | None = None) -> dict:
    user = seat.user
    is_registry_holder = bool(seat.holder_owner_id or seat.holder_name)
    if user is None:
        bind_state = "CONFLICT" if seat.bind_conflict_at else "PENDING_BIND"
    else:
        bind_state = "BOUND"
    detail = holder_detail if holder_detail is not None else _holder_detail_single(seat)
    return {
        "id": seat.id, "position": seat.position,
        "user": ({"id": user.id, "account_no": user.account_no, "nickname": user.nickname,
                  "phone": mask_phone(user.phone) if user.phone else None} if user is not None else None),
        "term_start": seat.term_start, "term_end": seat.term_end, "status": seat.status,
        "end_reason": seat.end_reason,
        "effective": is_effective(seat, timezone.localdate()),
        # IFC-349：持有人信息；不含手机号
        "holder": {"kind": "REGISTRY_OWNER" if is_registry_holder else "USER",
                   "unit_text": seat.holder_unit_text or None, "owner_name": seat.holder_name or None},
        "holder_detail": detail,
        "bind_state": bind_state,
    }


def _holder_detail_single(seat: Seat) -> dict:
    """MOD-157：单个席位的持有人分列信息（详情/新建响应使用）。"""
    membership = None
    if seat.user_id:
        membership = (Membership.objects.filter(
            user_id=seat.user_id, ended_at__isnull=True, role__in=("HEAD", "OWNER"),
        ).select_related("unit", "registry_owner").order_by("-id").first())
    owner = seat.holder_owner if seat.holder_owner_id else None
    return _build_holder_detail(seat, membership, owner)


def _holder_details(seats: list) -> dict[int, dict]:
    """MOD-157：批量构造持有人明细，避免列表 N+1（M-SA-010）。"""
    user_ids = [s.user_id for s in seats if s.user_id]
    memberships = {}
    if user_ids:
        for m in (Membership.objects.filter(
                user_id__in=user_ids, ended_at__isnull=True, role__in=("HEAD", "OWNER"),
        ).select_related("unit", "registry_owner").order_by("-id")):
            memberships.setdefault(m.user_id, m)
    owner_ids = [s.holder_owner_id for s in seats if s.holder_owner_id]
    owner_phones = {}
    if owner_ids:
        for row in RegistryPhone.objects.filter(owner_id__in=owner_ids).values("owner_id", "phone"):
            owner_phones.setdefault(row["owner_id"], row["phone"])
    return {s.id: _build_holder_detail(s, memberships.get(s.user_id), s.holder_owner,
                                       owner_phones.get(s.holder_owner_id))
            for s in seats}


def _build_holder_detail(seat: Seat, membership, owner, owner_phone=None) -> dict:
    from apps.registry import display as registry_display

    unit = membership.unit if membership is not None else (owner.unit if owner is not None else None)
    name = None
    if owner is not None:
        name = owner.name or None
    if name is None and seat.holder_name:
        name = seat.holder_name
    nickname = None
    if seat.user is not None:
        nickname = seat.user.nickname or seat.user.account_no
    phone = None
    if seat.user_id and seat.user.phone:
        phone = mask_phone(seat.user.phone)
    elif owner is not None:
        if owner_phone is None and hasattr(owner, "phones"):
            first_phone = owner.phones.first()
            owner_phone = first_phone.phone if first_phone is not None else None
        if owner_phone:
            phone = mask_phone(owner_phone)
    return {
        "nickname": nickname,
        "name": name,
        "phone_masked": phone,
        "unit_text": (unit.specific_part if unit is not None else None) or (seat.holder_unit_text or None),
        "unit_type": registry_display.unit_type_label(unit) if unit is not None else None,
        "building": unit.building if unit is not None else None,
        "unit_no": unit.unit_no if unit is not None else None,
        "floor": unit.floor if unit is not None else None,
        # REQ-FUNC-287：席位表拆列展示房号与面积
        "room": unit.room if unit is not None else None,
        "area": registry_display.area_text(unit) if unit is not None else None,
    }


class SeatSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = list(rows) if many else [rows]
        details = _holder_details(rows)
        self.data = [seat_view(r, details.get(r.id)) for r in rows]


class AdminSeatListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Seat.objects.select_related("user", "holder_owner__unit").order_by("-id")
        position = request.query_params.get("position")
        status_param = request.query_params.get("status")
        if position:
            qs = qs.filter(position=position)
        if status_param:
            qs = qs.filter(status=status_param)
        # MOD-157 / IFC-372：分桶与楼栋/单元/楼层过滤（ADR-152）
        bucket = request.query_params.get("bucket", "active")
        ended_count = None
        if bucket == "active":
            ended_count = qs.filter(status__in=ENDED_STATUSES).count()  # AC-265-01：折叠区标题条数
            qs = qs.filter(status="ACTIVE")
        elif bucket == "ended":
            qs = qs.filter(status__in=ENDED_STATUSES)
        else:
            raise ApiError("INVALID_QUERY", "bucket 取值不合法")
        for param, field in (("building", "building"), ("unit_no", "unit_no"), ("floor", "floor")):
            value = request.query_params.get(param)
            if not value:
                continue
            member_units = Membership.objects.filter(
                user_id=OuterRef("user_id"), ended_at__isnull=True,
                **{f"unit__{field}": value},
            ).values("user_id")
            qs = qs.filter(
                Q(**{f"holder_owner__unit__{field}": value}) | Q(Exists(member_units))
            )
        # REQ-FUNC-291：与业主清册一致的昵称/姓名/电话/专有部分搜索（作用于在任与失效两个分桶）
        nickname = (request.query_params.get("nickname") or "").strip()
        if nickname:
            qs = qs.filter(Q(user__nickname__icontains=nickname) | Q(user__account_no__icontains=nickname))
        name_keyword = (request.query_params.get("name") or "").strip()
        if name_keyword:
            qs = qs.filter(Q(holder_owner__name__icontains=name_keyword) | Q(holder_name__icontains=name_keyword))
        phone = re.sub(r"\D", "", request.query_params.get("phone") or "")
        if phone:
            owner_phones = RegistryPhone.objects.filter(
                owner_id=OuterRef("holder_owner_id"), phone__icontains=phone,
            ).values("owner_id")
            qs = qs.filter(Q(user__phone__icontains=phone) | Q(Exists(owner_phones)))
        unit_keyword = (request.query_params.get("unit_keyword") or "").strip()
        if unit_keyword:
            member_units = Membership.objects.filter(
                user_id=OuterRef("user_id"), ended_at__isnull=True,
            ).filter(Q(unit__specific_part__icontains=unit_keyword) | Q(unit__room__icontains=unit_keyword)
                     ).values("user_id")
            qs = qs.filter(
                Q(holder_owner__unit__specific_part__icontains=unit_keyword)
                | Q(holder_owner__unit__room__icontains=unit_keyword)
                | Q(holder_unit_text__icontains=unit_keyword)
                | Q(Exists(member_units))
            )
        response = page_response(qs, request, SeatSerializer)
        if ended_count is not None:
            response.data["ended_count"] = ended_count
        return response

    def post(self, request):
        data = request.data or {}
        position = data.get("position")
        if position not in {"CHAIR", "VICE_CHAIR", "MEMBER", "REPRESENTATIVE"}:
            raise ApiError("INVALID_VALUE", "position 不合法")
        has_user, has_owner = data.get("user_id") is not None, data.get("registry_owner_id") is not None
        if has_user == has_owner:  # IFC-348：恰好给一个
            raise ApiError("INVALID_VALUE", "user_id 与 registry_owner_id 须恰好给一个")
        user_id = None
        registry_owner_id = None
        if has_owner:
            raw = data.get("registry_owner_id")
            if isinstance(raw, bool) or not isinstance(raw, int):
                raise ApiError("INVALID_VALUE", "registry_owner_id 不合法")
            registry_owner_id = raw
        else:
            try:
                user_id = int(data.get("user_id"))
            except (TypeError, ValueError) as exc:
                raise ApiError("INVALID_VALUE", "user_id 不合法") from exc
            from apps.accounts.models import User

            if not User.objects.filter(id=user_id).exists():
                raise ApiError("NOT_FOUND", "用户不存在", 404)
            if not MembershipService.is_owner_of_any(user_id):
                raise ApiError("NOT_AN_OWNER", "目标须是有效产权业主", 422)
        try:
            term_start = parse_date(str(data.get("term_start"))) if data.get("term_start") else timezone.localdate()
        except ValueError:  # DEF-024：格式合法但日期不存在（如 2026-02-30）
            term_start = None
        if term_start is None:
            raise ApiError("INVALID_VALUE", "term_start 格式不正确")
        # IFC-312：不再限制开始日早于今天；上界防止 add_months 对极大日期抛 ValueError [ASSUMPTION] OQ-04
        if term_start > timezone.localdate() + timedelta(days=TERM_START_MAX_DAYS):
            raise ApiError("INVALID_VALUE", "任期开始日过远")
        seat = CommitteeCommands.grant(user_id=user_id, registry_owner_id=registry_owner_id,
                                       position=position, term_start=term_start, admin_id=request.user.id)
        return Response(seat_view(seat), status=status.HTTP_201_CREATED)


class AdminSeatDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, seat_id: int):
        seat = Seat.objects.select_related("user").filter(id=seat_id).first()
        if seat is None:
            raise ApiError("NOT_FOUND", "席位不存在", 404)
        if seat.status != "ACTIVE":
            raise ApiError("ALREADY_ENDED", "席位已结束", 409)
        position = (request.data or {}).get("position")
        if position not in {"CHAIR", "VICE_CHAIR", "MEMBER", "REPRESENTATIVE"}:
            raise ApiError("INVALID_VALUE", "position 不合法")
        seat = CommitteeCommands.change(seat, position=position, admin_id=request.user.id)
        return Response(seat_view(seat))

    def delete(self, request, seat_id: int):
        seat = Seat.objects.select_related("user").filter(id=seat_id).first()
        if seat is None:
            raise ApiError("NOT_FOUND", "席位不存在", 404)
        if seat.status != "ACTIVE":
            raise ApiError("ALREADY_ENDED", "席位已结束", 409)
        CommitteeCommands.revoke(seat, admin_id=request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminOwnerCandidatesView(APIView):
    """IFC-350：某专有部分的清册业主候选（姓名 + 脱敏手机号），仅管理员；不返回完整手机号。"""
    permission_classes = [IsAdmin]

    def get(self, request):
        raw = request.query_params.get("unit_id")
        try:
            unit_id = int(raw)
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_QUERY", "unit_id 不合法") from exc
        if unit_id <= 0:
            raise ApiError("INVALID_QUERY", "unit_id 不合法")
        from apps.registry.models import RegistryUnit

        unit = RegistryUnit.objects.prefetch_related("owners__phones").filter(id=unit_id).first()
        if unit is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        owners = [o for o in unit.owners.all() if (o.name or "").strip()]
        seated_owner_ids = set(Seat.objects.filter(holder_owner_id__in=[o.id for o in owners], status="ACTIVE")
                               .values_list("holder_owner_id", flat=True))
        certified = {o.id: SeatBinding.certified_user_of(o) for o in owners}
        seated_user_ids = set(Seat.objects.filter(user_id__in=[u for u in certified.values() if u is not None],
                                                  status="ACTIVE").values_list("user_id", flat=True))
        results = []
        for owner in owners:
            phones = [p.phone for p in owner.phones.all()]
            user_id = certified[owner.id]
            results.append({
                "owner_id": owner.id, "name": owner.name,
                "phone_masked": mask_phone(phones[0]) if phones else None,
                "seated": owner.id in seated_owner_ids or (user_id is not None and user_id in seated_user_ids),
                "registered": user_id is not None,
            })
        return Response({"unit_id": unit.id, "specific_part": unit.specific_part, "owners": results})


class AdminCommitteeConfigView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(config_view(CommitteeConfig.load()))

    def put(self, request):
        config = CommitteeConfig.load()
        data = request.data or {}
        limits = {
            "cap_chair": (0, 50), "cap_vice": (0, 50), "cap_member": (0, 50), "cap_rep": (0, 500),
            "term_months_chair": (1, 120), "term_months_vice": (1, 120),
            "term_months_member": (1, 120), "term_months_rep": (1, 120),
        }
        for field, (low, high) in limits.items():
            if field in data and data[field] is not None:
                value = data[field]
                if not isinstance(value, int) or isinstance(value, bool) or not (low <= value <= high):
                    from apps.core.audit import AuditActor, AuditService

                    # DEF-017：AC-040-08/AC-064-06 保存失败也写"结果为失败"的审计
                    AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                                        action="COMMITTEE_CONFIG_CHANGED", object_type="committee_config",
                                        object_id="1", result="FAILURE", detail={"field": field})
                    raise ApiError("INVALID_VALUE", f"{field} 取值须在 {low}~{high}")
                setattr(config, field, value)
        config.updated_by_admin_id = request.user.id
        config.save()
        from apps.core.audit import AuditActor, AuditService

        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="COMMITTEE_CONFIG_CHANGED", object_type="committee_config",
                            object_id="1", result="SUCCESS", detail={"fields": list(data)})
        return Response(config_view(config))


def config_view(config: CommitteeConfig) -> dict:
    result = {field: getattr(config, field) for field in
              ["cap_chair", "cap_vice", "cap_member", "cap_rep", "term_months_chair",
               "term_months_vice", "term_months_member", "term_months_rep"]}
    over_cap = []
    for position, field in CAP_FIELDS.items():
        cap = getattr(config, field)
        current = Seat.objects.filter(status="ACTIVE", position=position).count()
        if cap is not None and current > cap:
            over_cap.append({"position": position, "current": current, "cap": cap})
    result["over_cap"] = over_cap
    # IFC-356：半数同意通过性提示（仅提示、不拦截，Q-B18-33=A）
    from apps.core.config import SystemConfig

    mode = SystemConfig.get("vote.denominator_mode")
    denominator = CommitteeQuery.denominator_for_half_majority(mode)
    pending_bind = CommitteeQuery.pending_bind_count()
    need_agree = denominator // 2 + 1
    result["half_majority_hint"] = {
        "mode": mode, "denominator": denominator, "pending_bind": pending_bind,
        "need_agree": need_agree, "can_pass": (denominator - pending_bind) >= need_agree,
    }
    return result


_ = NotFound
