"""身份视图（IFC-030~034）。"""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import AccountService
from apps.core.errors import ApiError
from apps.core.masking import PHONE_RE, mask_phone
from apps.core.permissions import IsAdmin, IsMember
from apps.core.serializers import page_response
from apps.residency.models import Membership
from apps.residency.phone_match import PhoneMatchService

from .services import IdentityService


def _merge_response(kind: str, result: dict) -> dict:
    """合并成功后旧会话已失效：为主账号签发同类型的新令牌（IFC-071/072，AC-012-01）。"""
    primary = result.pop("primary")
    result.pop("report", None)
    if result["merged"]:
        result["token"] = AccountService.issue_token(primary, session_kind=kind)
        result["user"] = {"id": primary.id, "account_no": primary.account_no,
                          "nickname": primary.nickname, "avatar_url": primary.avatar_url,
                          "status": primary.status}
    return result


class MeView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        return Response(IdentityService.me(request.user))


class UserProfileView(APIView):
    """MOD-154 / IFC-370：登录用户查看他人 profile（字段白名单，ADR-147）。"""

    permission_classes = [IsMember]

    def get(self, request, user_id: int):
        return Response(IdentityService.public_profile(user_id, viewer=request.user))


class PhoneBindView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        kind = AccountService.session_kind_of(request.auth)  # 合并后旧令牌会被删除，先取类型
        result = IdentityService.bind_phone(request.user, str(data.get("phone", "")),
                                            str(data.get("code", "")))
        response = _merge_response(kind, result)
        # ADR-130：auto_bound 已弃用、恒为空（保留仅为兼容）；首次绑定（非合并）开启待确认状态，合并则不触发并使其失效
        response["auto_bound"] = []
        if response["merged"]:
            PhoneMatchService.expire(request.user)
            response["registry_match"] = {"pending": False, "count": 0}
        else:
            count = PhoneMatchService.open_prompt(request.user)
            response["registry_match"] = {"pending": count > 0, "count": count}
        return Response(response)


class PhoneChangeView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        kind = AccountService.session_kind_of(request.auth)
        result = IdentityService.change_phone(
            request.user, str(data.get("old_phone", "")), str(data.get("new_phone", "")),
            str(data.get("old_code", "")), str(data.get("new_code", "")),
        )
        PhoneMatchService.expire(request.user)  # 更换手机号不触发匹配，原待确认状态失效（AC-239-05）
        return Response(_merge_response(kind, result))


class CancelAccountView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        phone = str(data.get("phone", ""))
        if not PHONE_RE.match(phone):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        IdentityService.cancel(request.user, phone, str(data.get("code", "")))
        return Response(status=status.HTTP_204_NO_CONTENT)


class MembershipSerializer:
    def __init__(self, rows, many=False, context=None):
        from apps.registry import display as registry_display

        rows = rows if many else [rows]
        self.data = [{
            "id": m.id, "unit_id": m.unit_id, "specific_part": m.unit.specific_part,
            # REQ-FUNC-284：房屋关系表拆列展示楼栋/单元/楼层/房号/类型/面积
            "building": m.unit.building, "unit_no": m.unit.unit_no or None,
            "floor": m.unit.floor or None, "room": m.unit.room,
            "unit_type": registry_display.unit_type_label(m.unit),
            "area": registry_display.area_text(m.unit),
            "role": m.role, "source": m.source, "certified_at": m.certified_at,
            "user": {"id": m.user_id, "account_no": m.user.account_no,
                     "nickname": m.user.nickname,
                     "phone": mask_phone(m.user.phone) if m.user.phone else None},
        } for m in rows]


def _owner_unit_ids(term: str):
    """AC-269-01：按清册业主姓名反查专有部分，使该业主名下的同住人也进入结果。"""
    return Membership.objects.filter(
        ended_at__isnull=True, role__in=("HEAD", "OWNER"),
        registry_owner__name__icontains=term,
    ).values("unit_id")


class AdminMembershipListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = (Membership.objects.filter(ended_at__isnull=True)
              .select_related("unit", "user", "registry_owner").order_by("-id"))
        role = request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        # MOD-159 / IFC-374：楼栋/单元/楼层过滤与姓名/电话搜索（ADR-153）
        building = request.query_params.get("building")
        unit_no = request.query_params.get("unit_no")
        floor = request.query_params.get("floor")
        if building:
            qs = qs.filter(unit__building=building)
        if unit_no:
            qs = qs.filter(unit__unit_no=unit_no)
        if floor:
            qs = qs.filter(unit__floor=floor)
        # REQ-FUNC-284：独立的"专有部分标识 / 户号"过滤，同时包含匹配两者（D-04）
        unit_keyword = request.query_params.get("unit_keyword", "")[:64]
        if unit_keyword:
            qs = qs.filter(Q(unit__specific_part__icontains=unit_keyword)
                           | Q(unit__room__icontains=unit_keyword))
        name = request.query_params.get("name", "")[:32]
        if name:
            qs = qs.filter(Q(registry_owner__name__icontains=name)
                           | Q(unit_id__in=_owner_unit_ids(name)))
        phone = request.query_params.get("phone", "").strip()
        if phone:
            if not phone.isdigit() or not 4 <= len(phone) <= 11:
                raise ApiError("INVALID_QUERY", "phone 须为 4~11 位数字")
            if len(phone) == 4:
                qs = qs.filter(user__phone__endswith=phone)
            else:
                qs = qs.filter(user__phone__icontains=phone)
        q = request.query_params.get("q", "")[:32]
        if q:
            # D-07：关键词框只匹配姓名/账号/昵称；专有部分与户号由 unit_keyword 命中
            qs = qs.filter(Q(user__account_no__icontains=q) | Q(user__nickname__icontains=q)
                           | Q(registry_owner__name__icontains=q)
                           | Q(unit_id__in=_owner_unit_ids(q)))
        return page_response(qs, request, MembershipSerializer)


class AdminMembershipRevokeView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        data = request.data or {}
        try:
            user_id = int(data.get("user_id"))
            unit_id = int(data.get("unit_id"))
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "user_id 与 unit_id 必填") from exc
        return Response(IdentityService.revoke_membership(user_id, unit_id, request.user.id))
