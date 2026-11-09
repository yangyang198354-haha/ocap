"""房屋关系视图（IFC-050~054）。"""
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.attachments import AttachmentService
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound, RateLimited
from apps.core.masking import mask_phone
from apps.core.models import Attachment
from apps.core.permissions import IsAdmin, IsMember
from apps.core.ratelimit import RateLimiter
from apps.core.serializers import page_response
from apps.registry.models import RegistryUnit
from apps.registry.services import RegistryService

from .models import Appeal, Membership, ResidentApplication
from .services import MembershipService


def _unit_view(unit: RegistryUnit) -> dict:
    return {"unit_id": unit.id, "specific_part": unit.specific_part}


class CertificationView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        decision = RateLimiter.hit(f"certify:{request.user.id}", limit=30, window_seconds=3600)
        if not decision.allowed:
            raise RateLimited(decision.retry_after)
        unit_id = (request.data or {}).get("unit_id")
        try:
            unit_id = int(unit_id)
        except (TypeError, ValueError) as exc:
            raise ApiError("INVALID_VALUE", "缺少专有部分") from exc
        unit = RegistryService.get_unit(unit_id)
        if unit is None:
            raise ApiError("NOT_FOUND", "专有部分不存在", 404)
        if not request.user.phone:
            raise ApiError("PHONE_REQUIRED", "请先绑定手机号", 409)
        if MembershipService.is_owner_of(request.user.id, unit_id):
            raise ApiError("ALREADY_CERTIFIED", "已是该专有部分产权业主", 409)
        if not RegistryService.phone_registered(unit_id, request.user.phone):
            detail = {"appeal_available": True}
            raise ApiError("PHONE_NOT_IN_REGISTRY", "手机号与清册不一致，可提交产权申诉", 422, detail)
        role = MembershipService.certify_owner(request.user.id, unit_id, "REGISTRY")
        return Response({**_unit_view(unit), "role": role}, status=status.HTTP_201_CREATED)


class AppealListCreateView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        rows = Appeal.objects.filter(user=request.user).select_related("unit").order_by("-submitted_at")
        return Response([appeal_view(a) for a in rows])

    def post(self, request):
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
            appeal = Appeal.objects.create(user=request.user, unit=unit)
            AttachmentService.link(parsed, linked_type="appeal", linked_id=str(appeal.id),
                                   purpose="APPEAL_PROOF", owner=request.user)
            AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                                action="APPEAL_SUBMITTED", object_type="appeal",
                                object_id=str(appeal.id), result="SUCCESS")
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
        rows = rows if many else [rows]
        self.data = [self._one(r) for r in rows]

    @staticmethod
    def _one(appeal: Appeal) -> dict:
        proofs = Attachment.objects.filter(linked_type="appeal", linked_id=str(appeal.id))
        return {
            "id": appeal.id, "unit": _unit_view(appeal.unit), "status": appeal.status,
            "submitted_at": appeal.submitted_at, "decided_at": appeal.decided_at,
            "reject_reason": appeal.reject_reason,
            "applicant": {"id": appeal.user_id, "account_no": appeal.user.account_no,
                          "phone": mask_phone(appeal.user.phone) if appeal.user.phone else None},
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
        if appeal.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该申诉已处理", 409)
        with transaction.atomic():
            if decision == "APPROVE":
                role = MembershipService.certify_owner(appeal.user_id, appeal.unit_id, "APPEAL")
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
        return Response(appeal_view(appeal))


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
                .select_related("unit").order_by("-created_at"))
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
