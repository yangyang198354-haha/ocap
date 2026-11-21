"""房屋关系视图（IFC-050~054）。"""
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.attachments import AttachmentService, StoredFile, count_limit
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound, RateLimited
from apps.core.masking import mask_phone
from apps.core.models import Attachment
from apps.core.permissions import IsAdmin, IsMember
from apps.core.ratelimit import RateLimiter
from apps.core.serializers import page_response
from apps.registry.models import RegistryUnit
from apps.registry.ownership import (
    OWNER_NAME_MAX, PhoneOwnedByOtherOwner, append_owner_from_appeal, matched_owner, normalize_owner_name,
    owner_matches,  # noqa: F401 - 既有测试以 apps.residency.views.owner_matches 为补丁目标，保留导出
)
from apps.registry.services import RegistryService

from .housing import housing_view
from .models import Appeal, Membership, ResidentApplication
from .phone_match import PhoneMatchService
from .services import MembershipService

MINE_LIMIT = 100  # IFC-263：我的申请/申诉只返回最近 100 条


def _unit_view(unit: RegistryUnit) -> dict:
    return {"unit_id": unit.id, "specific_part": unit.specific_part}


class MyHousingView(APIView):
    """GET /me/housing（IFC-261）：汇总身份、各房屋身份、同住人名单与待审数量。"""
    permission_classes = [IsMember]

    def get(self, request):
        payload = housing_view(request.user)
        summary = payload["summary"]
        return Response({
            "summary": {"code": summary["identity_code"], "label": summary["identity_label"]},
            "units": payload["units"],
            "pending_review_count": payload["pending_review_count"],
            "real_names": payload["real_names"],
        })


REGISTRY_CONFIRM_MAX = 500  # IFC-333：确认请求 unit_ids 上限（防滥用，非界面上限）


class RegistryMatchesView(APIView):
    """GET /me/registry-matches（IFC-332）：只作用于当前账号已验证手机号，无入参；不含清册姓名、手机号。"""
    permission_classes = [IsMember]

    def get(self, request):
        units = PhoneMatchService.pending_matches(request.user)
        return Response({"pending": bool(units), "total": len(units),
                         "units": [u.as_dict() for u in units]})


class RegistryMatchesConfirmView(APIView):
    """POST /me/registry-matches/confirm（IFC-333）：服务端以 units_by_phone(user.phone) 重算并做子集校验。"""
    permission_classes = [IsMember]

    def post(self, request):
        decision = RateLimiter.hit(f"certify:{request.user.id}", limit=30, window_seconds=3600)
        if not decision.allowed:
            raise RateLimited(decision.retry_after)
        raw = (request.data or {}).get("unit_ids")
        if (not isinstance(raw, list) or not raw
                or any(isinstance(v, bool) or not isinstance(v, int) for v in raw)):
            raise ApiError("INVALID_VALUE", "缺少专有部分")
        unit_ids = list(dict.fromkeys(raw))
        if len(unit_ids) > REGISTRY_CONFIRM_MAX:
            raise ApiError("INVALID_VALUE", "缺少专有部分")
        items = PhoneMatchService.confirm(request.user, unit_ids)
        succeeded = sum(1 for i in items if i.ok)
        return Response({"succeeded": succeeded, "failed": len(items) - succeeded,
                         "results": [i.as_dict() for i in items]})


class RegistryMatchesDismissView(APIView):
    """POST /me/registry-matches/dismiss（IFC-334）：幂等。"""
    permission_classes = [IsMember]

    def post(self, request):
        PhoneMatchService.dismiss(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CertificationView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        decision = RateLimiter.hit(f"certify:{request.user.id}", limit=30, window_seconds=3600)
        if not decision.allowed:
            raise RateLimited(decision.retry_after)
        data = request.data or {}
        unit_id = data.get("unit_id")
        try:
            unit_id = int(unit_id)
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "缺少专有部分") from exc
        name = normalize_owner_name(data.get("name"))  # IFC-306：缺失/非字符串/空白一律视为空
        if not name:
            raise ApiError("NAME_REQUIRED", "请输入姓名")
        if len(name) > OWNER_NAME_MAX:
            raise ApiError("INVALID_VALUE", f"姓名过长（最多 {OWNER_NAME_MAX} 字）")
        unit = RegistryService.get_unit(unit_id)
        if unit is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        if MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
        # 姓名错 / 手机号错 / 无此业主 / 清册姓名为空 / 账号无手机号：同一出口（REQ-NFUNC-037）
        matched = matched_owner(unit_id, name, request.user.phone)
        if matched is None:
            raise ApiError("OWNER_NOT_MATCHED", "姓名与手机号未能通过清册核对，可上传产权证明提交申诉",
                           422, {"appeal_available": True})
        role = MembershipService.certify_owner(request.user.id, unit_id, "REGISTRY",
                                               verified_owner_id=matched.id, via="MANUAL")
        return Response({**_unit_view(unit), "role": role}, status=status.HTTP_201_CREATED)


class AppealListCreateView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        rows = (Appeal.objects.filter(user=request.user).select_related("unit")
                .order_by("-submitted_at")[:MINE_LIMIT])
        return Response([appeal_view(a) for a in rows])

    def post(self, request):
        if (request.content_type or "").startswith("multipart/form-data"):
            return self._post_multipart(request)  # IFC-345：一次提交分支（ADR-136）
        data = request.data or {}
        try:
            unit_id = int(data.get("unit_id"))
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "缺少专有部分") from exc
        unit = RegistryService.get_unit(unit_id)
        if unit is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        if MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
        owner_name = normalize_owner_name(data.get("owner_name"))  # IFC-307：必填，≤64 字
        if not owner_name:
            raise ApiError("NAME_REQUIRED", "请输入产权人名字")
        if len(owner_name) > OWNER_NAME_MAX:
            raise ApiError("INVALID_VALUE", f"产权人名字过长（最多 {OWNER_NAME_MAX} 字）")
        proof_ids = data.get("proof_ids") or []
        if not proof_ids:
            raise ApiError("PROOF_REQUIRED", "请上传产权证明", 400)
        if len(proof_ids) > 5:
            raise ApiError("ATTACHMENT_LIMIT", "附件数量超过上限", 400)
        if Appeal.objects.filter(user=request.user, unit=unit, status="PENDING").exists():
            raise ApiError("APPEAL_PENDING", "该专有部分已有待审申诉", 409)
        parsed = []
        for raw in proof_ids:
            try:
                parsed.append(uuid.UUID(str(raw)))
            except ValueError as exc:
                raise ApiError("ATTACHMENT_LIMIT", "附件 id 不合法") from exc
        with transaction.atomic():
            appeal = Appeal.objects.create(user=request.user, unit=unit, owner_name=owner_name)
            AttachmentService.link(parsed, linked_type="appeal", linked_id=str(appeal.id),
                                   purpose="APPEAL_PROOF", owner=request.user)
            AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                                action="APPEAL_SUBMITTED", object_type="appeal",
                                object_id=str(appeal.id), result="SUCCESS")
        return Response(appeal_view(appeal), status=status.HTTP_201_CREATED)

    @staticmethod
    def _post_multipart(request):
        """MOD-139 / IFC-345：校验顺序固定，任何一步失败均不落盘、不建记录；成功则事务内建申诉并落盘关联，
        事务失败时清理已落盘文件。"""
        data = request.data
        raw_unit = data.get("unit_id")
        try:
            unit_id = int(raw_unit)
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "缺少专有部分") from exc
        unit = RegistryService.get_unit(unit_id)
        if unit is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        if MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
        owner_name = normalize_owner_name(data.get("owner_name"))
        if not owner_name:
            raise ApiError("NAME_REQUIRED", "请输入产权人名字")
        if len(owner_name) > OWNER_NAME_MAX:
            raise ApiError("INVALID_VALUE", f"产权人名字过长（最多 {OWNER_NAME_MAX} 字）")
        files = request.FILES.getlist("files")
        if not files:
            raise ApiError("PROOF_REQUIRED", "请上传产权证明", 400)
        if len(files) > int(count_limit("APPEAL_PROOF")):
            raise ApiError("ATTACHMENT_LIMIT", "附件数量超过上限", 400)
        if Appeal.objects.filter(user=request.user, unit=unit, status="PENDING").exists():
            raise ApiError("APPEAL_PENDING", "该专有部分已有待审申诉", 409)
        decision = RateLimiter.hit(f"appeal_submit:{request.user.id}", limit=60, window_seconds=3600)
        if not decision.allowed:
            raise RateLimited(decision.retry_after)
        validated = [AttachmentService.validate_upload(f, "APPEAL_PROOF") for f in files]
        stored: list[StoredFile] = []
        try:
            with transaction.atomic():
                appeal = Appeal.objects.create(user=request.user, unit=unit, owner_name=owner_name)
                for item in validated:
                    _ref, saved = AttachmentService.store_validated(
                        item, purpose="APPEAL_PROOF", owner=request.user,
                        linked_type="appeal", linked_id=str(appeal.id))
                    stored.append(saved)
                AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                                    action="APPEAL_SUBMITTED", object_type="appeal",
                                    object_id=str(appeal.id), result="SUCCESS")
        except Exception:
            AttachmentService.discard(stored)
            raise
        return Response(appeal_view(appeal), status=status.HTTP_201_CREATED)


def appeal_view(appeal: Appeal) -> dict:
    return {
        "id": appeal.id, "unit": _unit_view(appeal.unit), "status": appeal.status,
        "submitted_at": appeal.submitted_at, "decided_at": appeal.decided_at,
        "reject_reason": appeal.reject_reason,
    }


class AdminAppealListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Appeal.objects.select_related("user", "unit").order_by("-submitted_at")
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return page_response(qs, request, AppealAdminSerializer)


class AppealAdminSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = list(rows) if many else [rows]
        # IFC-308：当前页全部申诉的附件一次查询并分组，页内查询数不随行数增长
        grouped: dict[str, list] = {}
        for proof in Attachment.objects.filter(
                linked_type="appeal", linked_id__in=[str(r.id) for r in rows]).order_by("created_at", "id"):
            grouped.setdefault(proof.linked_id, []).append(proof)
        self.data = [self._one(r, grouped.get(str(r.id), ())) for r in rows]

    @staticmethod
    def _one(appeal: Appeal, proofs=()) -> dict:
        user = appeal.user
        return {
            "id": appeal.id, "unit": _unit_view(appeal.unit), "status": appeal.status,
            "submitted_at": appeal.submitted_at, "decided_at": appeal.decided_at,
            "reject_reason": appeal.reject_reason,
            "owner_name": appeal.owner_name or None,  # 历史申诉为 None（前端显示"未提供"）
            "applicant": {"id": appeal.user_id, "account_no": user.account_no, "nickname": user.nickname,
                          "avatar_url": user.avatar_url,
                          "phone": user.phone or None,
                          "has_phone": bool(user.phone)},
            "proof": [{"id": str(p.id), "name": p.original_name, "size": p.size,
                       "content_type": p.content_type} for p in proofs],
        }


class AdminAppealDecisionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, appeal_id: int):
        data = request.data or {}
        decision = data.get("decision")
        if decision not in {"APPROVE", "REJECT"}:
            raise ApiError("INVALID_VALUE", "decision 不合法")
        appeal = Appeal.objects.select_related("unit", "user").filter(id=appeal_id).first()
        if appeal is None:
            raise ApiError("NOT_FOUND", "申诉不存在", 404)
        if appeal.status == "CLOSED":
            raise ApiError("ALREADY_CLOSED", "该申诉已关闭", 409)
        if appeal.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该申诉已处理", 409)
        registry_update = None
        with transaction.atomic():
            if decision == "APPROVE":
                role = MembershipService.certify_owner(appeal.user_id, appeal.unit_id, "APPEAL")
                registry_update, owner_id = self._append_registry(request, appeal)
                if owner_id is not None:  # IFC-354：申诉通过后记录核对的清册业主并尝试绑定席位
                    MembershipService.record_verified_owner(appeal.user_id, appeal.unit_id, owner_id, via="APPEAL")
                appeal.status = "APPROVED"
                detail = {"role": role}
            else:
                reason = str(data.get("reject_reason", ""))
                if not reason or len(reason) > 500:
                    raise ApiError("INVALID_VALUE", "拒绝须填写原因（≤500 字）")
                appeal.status = "REJECTED"
                appeal.reject_reason = reason
                detail = {"reason": reason}
            appeal.decided_at = timezone.now()
            appeal.decided_by_admin_id = request.user.id
            appeal.pending_slot = None
            appeal.save()
            AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                                action="APPEAL_DECIDED", object_type="appeal",
                                object_id=str(appeal.id), result="SUCCESS", detail=detail)
        payload = appeal_view(appeal)
        if registry_update is not None:
            payload["registry_update"] = registry_update
        return Response(payload)

    @staticmethod
    def _append_registry(request, appeal: Appeal) -> tuple[dict, int | None]:
        """IFC-309：同一事务内追加产权人与号码并写审计；任何失败抛 ApiError 使整笔回滚（ADR-114）。
        返回 (registry_update, 清册业主 id)；无产权人名字（历史申诉）时业主 id 为 None。"""
        actor = AuditActor("ADMIN", request.user.id, request.user.username)
        base = {"change": "appeal_append_owner", "appeal_id": appeal.id, "unit_id": appeal.unit_id}
        if not appeal.owner_name:
            AuditService.record(actor=actor, action="REGISTRY_UNIT_CHANGED", object_type="registry",
                                object_id=str(appeal.unit_id), result="SUCCESS",
                                detail={**base, "result": "SKIPPED_NO_OWNER_NAME",
                                        "note": "无产权人名字，未更新清册"})
            return {"result": "SKIPPED_NO_OWNER_NAME", "owner_phone_written": False, "notice": None}, None
        try:
            appended = append_owner_from_appeal(appeal.unit_id, appeal.owner_name, appeal.user.phone or None)
        except PhoneOwnedByOtherOwner as exc:
            raise ApiError("PHONE_OWNED_BY_OTHER", "该手机号已登记在本专有部分的另一位业主名下，无法更新清册",
                           409) from exc
        except ApiError:
            raise
        except Exception as exc:  # 含 IntegrityError：整笔回滚，申诉保持待审
            raise ApiError("REGISTRY_UPDATE_FAILED", "清册更新失败，申诉保持待审", 409) from exc
        AuditService.record(actor=actor, action="REGISTRY_UNIT_CHANGED", object_type="registry",
                            object_id=str(appeal.unit_id), result="SUCCESS",
                            detail={**base, "result": appended.result,
                                    "names_before": list(appended.names_before),
                                    "names_after": list(appended.names_after),
                                    "phone_masked": appended.phone_masked})
        return ({"result": appended.result, "owner_phone_written": appended.owner_phone_written,
                 "notice": None if appeal.user.phone else "该产权人无联系电话"}, appended.owner_id)


class ResidentApplicationCreateView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        try:
            unit_id = int((request.data or {}).get("unit_id"))
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "缺少专有部分") from exc
        if RegistryService.get_unit(unit_id) is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        if not Membership.objects.filter(unit_id=unit_id, ended_at__isnull=True,
                                         role__in=["HEAD", "OWNER"]).exists():
            raise ApiError("UNIT_HAS_NO_OWNER", "该专有部分暂无有效产权业主", 409)
        if MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
        if ResidentApplication.objects.filter(applicant=request.user, unit_id=unit_id,
                                              status="PENDING").exists():
            raise ApiError("APPLICATION_PENDING", "已有待审申请", 409)
        application = ResidentApplication.objects.create(applicant=request.user, unit_id=unit_id)
        return Response(application_view(application), status=status.HTTP_201_CREATED)


def application_view(application: ResidentApplication) -> dict:
    return {"id": application.id, "unit": _unit_view(application.unit), "status": application.status,
            "created_at": application.created_at, "decided_at": application.decided_at}


class ResidentApplicationMineView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        rows = (ResidentApplication.objects.filter(applicant=request.user)
                .select_related("unit").order_by("-created_at")[:MINE_LIMIT])
        return Response([application_view(a) for a in rows])


class ResidentApplicationToReviewView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        unit_ids = Membership.objects.filter(user=request.user, ended_at__isnull=True,
                                             role__in=["HEAD", "OWNER"]).values_list("unit_id", flat=True)
        rows = (ResidentApplication.objects.filter(unit_id__in=list(unit_ids), status="PENDING")
                .select_related("unit", "applicant").order_by("created_at"))
        return Response([{
            **application_view(a),
            "applicant": {"id": a.applicant_id, "account_no": a.applicant.account_no,
                          "nickname": a.applicant.nickname,
                          "phone": mask_phone(a.applicant.phone) if a.applicant.phone else None},
        } for a in rows])


class ResidentApplicationDecisionView(APIView):
    permission_classes = [IsMember]

    def post(self, request, application_id: int):
        application = (ResidentApplication.objects.select_related("unit")
                       .filter(id=application_id).first())
        if application is None:
            raise ApiError("NOT_FOUND", "申请不存在", 404)
        if not MembershipService.is_owner_of(request.user.id, application.unit_id):
            raise ApiError("FORBIDDEN", "仅该专有部分产权业主可审批", 403)
        decision = (request.data or {}).get("decision")
        if decision not in {"APPROVE", "REJECT"}:
            raise ApiError("INVALID_VALUE", "decision 不合法")
        updated = (ResidentApplication.objects.filter(id=application_id, status="PENDING")
                   .update(status="APPROVED" if decision == "APPROVE" else "REJECTED",
                           decided_by=request.user, decided_at=timezone.now(), pending_slot=None))
        if not updated:
            current = ResidentApplication.objects.filter(id=application_id).values_list(
                "status", flat=True).first()
            if current == "CLOSED":
                raise ApiError("ALREADY_CLOSED", "该申请已关闭", 409)
            raise ApiError("ALREADY_DECIDED", "该申请已处理", 409)
        if decision == "APPROVE" and not Membership.objects.filter(
            user_id=application.applicant_id, unit_id=application.unit_id, ended_at__isnull=True
        ).exists():
            Membership.objects.create(user_id=application.applicant_id, unit_id=application.unit_id,
                                      role="RESIDENT", source="APPLICATION", active_slot=1)
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="RESIDENT_APPLICATION_DECIDED", object_type="resident_application",
                            object_id=str(application_id), result="SUCCESS", detail={"decision": decision})
        application.refresh_from_db()
        return Response(application_view(application))


class ResidentRemoveView(APIView):
    permission_classes = [IsMember]

    def delete(self, request, unit_id: int, user_id: int):
        if not MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("FORBIDDEN", "仅该专有部分产权业主可移除同住人", 403)
        membership = Membership.objects.filter(user_id=user_id, unit_id=unit_id,
                                               role="RESIDENT", ended_at__isnull=True).first()
        if membership is None:
            raise ApiError("NOT_FOUND", "目标不是该专有部分同住人", 404)
        MembershipService.end_membership(membership.id, "REMOVED")
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="RESIDENT_REMOVED", object_type="membership",
                            object_id=str(membership.id), result="SUCCESS",
                            detail={"unit_id": unit_id, "user_id": user_id})
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnitLeaveView(APIView):
    permission_classes = [IsMember]

    def post(self, request, unit_id: int):
        membership = Membership.objects.filter(user=request.user, unit_id=unit_id,
                                               role="RESIDENT", ended_at__isnull=True).first()
        if membership is None:
            raise ApiError("NOT_FOUND", "不是该专有部分同住人", 404)
        MembershipService.end_membership(membership.id, "LEFT")
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="RESIDENT_LEFT", object_type="membership",
                            object_id=str(membership.id), result="SUCCESS")
        return Response(status=status.HTTP_204_NO_CONTENT)
