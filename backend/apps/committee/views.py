"""业委会视图（IFC-060/061）。"""
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.errors import ApiError, NotFound
from apps.core.masking import mask_phone
from apps.core.permissions import IsAdmin
from apps.core.serializers import page_response
from apps.residency.services import MembershipService

from .models import CommitteeConfig, Seat
from .services import CAP_FIELDS, CommitteeCommands

from django.utils.dateparse import parse_date


def seat_view(seat: Seat) -> dict:
    user = seat.user
    return {
        "id": seat.id, "position": seat.position,
        "user": {"id": user.id, "account_no": user.account_no, "nickname": user.nickname,
                 "phone": mask_phone(user.phone) if user.phone else None},
        "term_start": seat.term_start, "term_end": seat.term_end, "status": seat.status,
    }


class SeatSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [seat_view(r) for r in rows]


class AdminSeatListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Seat.objects.select_related("user").order_by("-id")
        position = request.query_params.get("position")
        status_param = request.query_params.get("status")
        if position:
            qs = qs.filter(position=position)
        if status_param:
            qs = qs.filter(status=status_param)
        return page_response(qs, request, SeatSerializer)

    def post(self, request):
        data = request.data or {}
        position = data.get("position")
        if position not in {"CHAIR", "VICE_CHAIR", "MEMBER", "REPRESENTATIVE"}:
            raise ApiError("INVALID_VALUE", "position 不合法")
        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "user_id 不合法") from exc
        from apps.accounts.models import User

        if not User.objects.filter(id=user_id).exists():
            raise ApiError("NOT_FOUND", "用户不存在", 404)
        if not MembershipService.is_owner_of_any(user_id):
            raise ApiError("NOT_AN_OWNER", "目标须是有效产权业主", 422)
        term_start = parse_date(str(data.get("term_start"))) if data.get("term_start") else timezone.localdate()
        if term_start is None:
            raise ApiError("INVALID_VALUE", "term_start 格式不正确")
        if term_start < timezone.localdate():
            raise ApiError("INVALID_VALUE", "任期开始日不得早于今天")
        seat = CommitteeCommands.grant(user_id=user_id, position=position, term_start=term_start,
                                       admin_id=request.user.id)
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
    return result


_ = NotFound
