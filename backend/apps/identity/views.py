"""身份视图（IFC-030~034）。"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import AccountService
from apps.core.errors import ApiError
from apps.core.masking import PHONE_RE, mask_phone
from apps.core.permissions import IsAdmin, IsMember
from apps.core.serializers import page_response
from apps.residency.auto_bind import AutoBindService
from apps.residency.models import Membership

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


class PhoneBindView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        kind = AccountService.session_kind_of(request.auth)  # 合并后旧令牌会被删除，先取类型
        result = IdentityService.bind_phone(request.user, str(data.get("phone", "")),
                                            str(data.get("code", "")))
        response = _merge_response(kind, result)
        # 合并成功后旧会话失效、不再自动绑定（Q4=A）；首次绑定才触发（IFC-161）。
        response["auto_bound"] = (
            [] if response["merged"] else [item.as_dict() for item in AutoBindService.bind_by_phone(request.user)]
        )
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
        rows = rows if many else [rows]
        self.data = [{
            "id": m.id, "unit_id": m.unit_id, "specific_part": m.unit.specific_part,
            "role": m.role, "source": m.source, "certified_at": m.certified_at,
            "user": {"id": m.user_id, "account_no": m.user.account_no,
                     "nickname": m.user.nickname,
                     "phone": mask_phone(m.user.phone) if m.user.phone else None},
        } for m in rows]


class AdminMembershipListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = (Membership.objects.filter(ended_at__isnull=True)
              .select_related("unit", "user").order_by("-id"))
        role = request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        q = request.query_params.get("q", "")[:32]
        if q:
            from django.db.models import Q

            qs = qs.filter(Q(user__account_no__icontains=q) | Q(user__nickname__icontains=q)
                           | Q(unit__specific_part__icontains=q))
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
