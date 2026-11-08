"""审批视图（IFC-080~082）。"""
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.core.permissions import IsAdmin, IsCommitteeMember
from apps.core.serializers import page_response

from .models import ApprovalFlow, ApprovalInstance, ApprovalAction, FlowApprover
from .services import ApprovalEngine, subject_title


def flow_view(flow: ApprovalFlow) -> dict:
    return {
        "id": flow.id, "scope": flow.scope, "name": flow.name, "mode": flow.mode,
        "is_active": flow.is_active,
        "approvers": [{"id": a.user_id, "nickname": a.user.nickname}
                      for a in flow.approvers.select_related("user")],
    }


class FlowSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [flow_view(r) for r in rows]


def _validate_flow_payload(data: dict, scope: str, mode: str) -> list[int]:
    if mode == "HALF_MAJORITY" and scope != "RESOLUTION":
        raise ApiError("INVALID_VALUE", "仅决议可使用半数同意方式")
    approver_ids = data.get("approver_ids") or []
    if mode == "DESIGNATED" and not approver_ids:
        raise ApiError("INVALID_VALUE", "指定负责人流程须至少一名审批人")
    from apps.committee.services import CommitteeQuery

    for user_id in approver_ids:
        if not CommitteeQuery.is_member(int(user_id)):
            raise ApiError("APPROVER_NOT_COMMITTEE_MEMBER", "审批人须为现任业委会成员", 422)
    return [int(uid) for uid in approver_ids]


class AdminFlowListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = ApprovalFlow.objects.order_by("id")
        scope = request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)
        return page_response(qs, request, FlowSerializer)

    def post(self, request):
        data = request.data or {}
        scope = data.get("scope")
        mode = data.get("mode", "DESIGNATED")
        if scope not in {"RESOLUTION", "EXPENSE", "INCOME"}:
            raise ApiError("INVALID_VALUE", "scope 不合法")
        name = str(data.get("name", ""))
        if not (1 <= len(name) <= 60):
            raise ApiError("INVALID_VALUE", "名称须为 1~60 字符")
        approver_ids = _validate_flow_payload(data, scope, mode)
        flow = ApprovalFlow.objects.create(scope=scope, name=name, mode=mode)
        FlowApprover.objects.bulk_create([FlowApprover(flow=flow, user_id=uid) for uid in approver_ids])
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow.id), result="SUCCESS", detail={"op": "create"})
        return Response(flow_view(flow), status=status.HTTP_201_CREATED)


class AdminFlowDetailView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, flow_id: int):
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "流程不存在", 404)
        data = request.data or {}
        scope = data.get("scope", flow.scope)
        mode = data.get("mode", flow.mode)
        approver_ids = _validate_flow_payload(
            {"approver_ids": data.get("approver_ids", list(flow.approvers.values_list("user_id", flat=True)))},
            scope, mode,
        )
        flow.scope = scope
        flow.mode = mode
        flow.name = str(data.get("name", flow.name))[:60]
        flow.save()
        flow.approvers.all().delete()
        FlowApprover.objects.bulk_create([FlowApprover(flow=flow, user_id=uid) for uid in approver_ids])
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow.id), result="SUCCESS", detail={"op": "update"})
        return Response(flow_view(flow))

    def delete(self, request, flow_id: int):
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "流程不存在", 404)
        if ApprovalInstance.objects.filter(flow=flow, status="PENDING").exists():
            flow.is_active = False
            flow.save(update_fields=["is_active"])
        else:
            flow.is_active = False
            flow.save(update_fields=["is_active"])
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow.id), result="SUCCESS", detail={"op": "deactivate"})
        return Response(status=status.HTTP_204_NO_CONTENT)


class FlowOptionListView(APIView):
    permission_classes = [IsCommitteeMember]

    def get(self, request):
        scope = request.query_params.get("scope")
        if scope not in {"RESOLUTION", "EXPENSE", "INCOME"}:
            raise ApiError("INVALID_QUERY", "scope 必填")
        rows = ApprovalFlow.objects.filter(scope=scope, is_active=True).order_by("id")
        return Response([{
            "id": f.id, "name": f.name, "mode": f.mode,
            "approvers": [{"id": a.user_id, "nickname": a.user.nickname}
                          for a in f.approvers.select_related("user")],
        } for f in rows])


class TaskListView(APIView):
    permission_classes = [IsCommitteeMember]

    def get(self, request):
        qs = ApprovalInstance.objects.filter(status="PENDING").select_related("submitter").order_by("submitted_at")
        scope = request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)
        rows = [i for i in qs if request.user.id in (i.flow_snapshot.get("approver_ids") or [])]
        data = [{
            "instance_id": i.id, "scope": i.scope, "subject_type": i.subject_type,
            "subject_id": i.subject_id, "subject_title": subject_title(i.subject_type, i.subject_id),
            "submitter_label": i.submitter.identity_label, "submitted_at": i.submitted_at,
        } for i in rows]
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        return Response({"count": len(data), "page": page, "page_size": page_size,
                         "results": data[(page - 1) * page_size: page * page_size]})


class InstanceDecisionView(APIView):
    permission_classes = [IsCommitteeMember]

    def post(self, request, instance_id: int):
        data = request.data or {}
        instance = ApprovalEngine.decide(instance_id, request.user, data.get("action"),
                                         str(data.get("comment", "")))
        return Response(instance_view(instance))


def instance_view(instance: ApprovalInstance) -> dict:
    return {
        "id": instance.id, "scope": instance.scope, "subject_type": instance.subject_type,
        "subject_id": instance.subject_id, "status": instance.status,
        "decided_at": instance.decided_at,
        "actions": [{"actor_id": a.actor_id, "action": a.action, "comment": a.comment,
                     "acted_at": a.acted_at} for a in instance.actions.all()],
    }


_ = (timezone, ApprovalAction)
