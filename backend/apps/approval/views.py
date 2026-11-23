"""审批视图（IFC-080~082、IFC-402~407）。"""
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.core.permissions import IsAdmin, IsCommitteeMember, IsMemberOrAdmin
from apps.core.serializers import page_response

from .models import ApprovalFlow, ApprovalInstance, ApprovalStep, StepApprover
from .services import ApprovalEngine, subject_title

MAX_STEPS = 50
STRATEGIES = {"ANY", "ALL"}


def _approver_label(user_id: int) -> dict:
    from apps.accounts.models import User
    from apps.committee.services import CommitteeQuery

    user = User.objects.filter(id=user_id).first()
    labels = CommitteeQuery.identity_labels(user_id)
    return {"id": user_id, "nickname": getattr(user, "nickname", "") or f"用户#{user_id}",
            "identity_label": labels[0] if labels else "业委会成员"}


def _step_view(step: ApprovalStep) -> dict:
    return {"order": step.order, "name": step.name, "strategy": step.strategy,
            "approver_count": step.approvers.count(),
            "approvers": [_approver_label(row.user_id) for row in step.approvers.all()]}


def flow_view(flow: ApprovalFlow) -> dict:
    steps = [_step_view(step) for step in flow.steps.prefetch_related("approvers").order_by("order")]
    if steps:
        flat_ids = sorted({a["id"] for step in steps for a in step["approvers"]})
    else:
        flat_ids = list(flow.approvers.values_list("user_id", flat=True))
    return {
        "id": flow.id, "scope": flow.scope, "name": flow.name, "mode": flow.mode,
        "is_active": flow.is_active, "step_count": len(steps), "steps": steps,
        "approvers": [_approver_label(uid) for uid in flat_ids],
    }


class FlowSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [flow_view(r) for r in rows]


def _validate_flow_payload(data: dict, scope: str, mode: str, flow: ApprovalFlow | None = None):
    """校验并返回步骤列表；返回 None 表示本次不修改步骤。"""
    raw_steps = data.get("steps")
    approver_ids = data.get("approver_ids")
    if mode == "HALF_MAJORITY":
        if scope != "RESOLUTION":
            raise ApiError("INVALID_VALUE", "仅决议可使用半数以上参与者同意方式")
        # 半数同意由全体业委会成员投票判定，不设审批人；允许审批人会让决议错误地
        # 落入 /approval/tasks 待办，审批人点"同意"时又被 decide() 以 USE_VOTE_ENDPOINT 拒绝。
        if raw_steps or approver_ids:
            raise ApiError("INVALID_VALUE", "半数以上参与者同意的决议由全体业委会成员投票，不得设置审批人")
        return []

    if raw_steps is None:
        if approver_ids is None and flow is not None:
            return None
        ids = [int(uid) for uid in (approver_ids or [])]
        if not ids:
            raise ApiError("INVALID_VALUE", "指定负责人流程须至少一名审批人")
        raw_steps = [{"name": str(data.get("name") or (flow.name if flow else "") or "审批"),
                      "strategy": "ANY", "approver_ids": ids}]

    if not isinstance(raw_steps, list) or not (1 <= len(raw_steps) <= MAX_STEPS):
        raise ApiError("INVALID_STEPS", f"步骤须为 1~{MAX_STEPS} 个", 422)
    from apps.committee.services import CommitteeQuery

    steps = []
    for index, item in enumerate(raw_steps):
        if not isinstance(item, dict):
            raise ApiError("INVALID_STEPS", "步骤格式不合法", 422)
        name = str(item.get("name") or "")
        if not (1 <= len(name) <= 60):
            raise ApiError("INVALID_STEPS", "步骤名称须为 1~60 字符", 422)
        strategy = item.get("strategy") or "ANY"
        if strategy not in STRATEGIES:
            raise ApiError("INVALID_STEPS", "步骤策略须为 ANY 或 ALL", 422)
        ids = []
        for uid in item.get("approver_ids") or []:
            uid = int(uid)
            if uid not in ids:
                ids.append(uid)
        if not ids:
            raise ApiError("INVALID_STEPS", "每个步骤至少选择一名审批人", 422)
        for user_id in ids:
            if not CommitteeQuery.is_member(user_id):
                raise ApiError("APPROVER_NOT_COMMITTEE_MEMBER", "审批人须为现任业委会成员", 422)
        steps.append({"order": index + 1, "name": name, "strategy": strategy, "approver_ids": ids})
    return steps


def _save_steps(flow: ApprovalFlow, steps: list[dict]) -> None:
    flow.steps.all().delete()
    # FlowApprover 为 deprecated 旧结构：改配置时同步清空，避免两套审批人并存
    flow.approvers.all().delete()
    for item in steps:
        step = ApprovalStep.objects.create(flow=flow, order=item["order"], name=item["name"],
                                           strategy=item["strategy"])
        StepApprover.objects.bulk_create([StepApprover(step=step, user_id=uid)
                                          for uid in item["approver_ids"]])


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
        if mode not in {"DESIGNATED", "HALF_MAJORITY"}:
            raise ApiError("INVALID_VALUE", "mode 不合法")
        name = str(data.get("name", ""))
        if not (1 <= len(name) <= 60):
            raise ApiError("INVALID_VALUE", "名称须为 1~60 字符")
        steps = _validate_flow_payload(data, scope, mode)
        flow = ApprovalFlow.objects.create(scope=scope, name=name, mode=mode)
        _save_steps(flow, steps or [])
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow.id), result="SUCCESS",
                            detail={"op": "create", "steps_count": len(steps or [])})
        return Response(flow_view(flow), status=status.HTTP_201_CREATED)


class AdminFlowDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, flow_id: int):
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "流程不存在", 404)
        return Response(flow_view(flow))

    def put(self, request, flow_id: int):
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "流程不存在", 404)
        data = request.data or {}
        scope = data.get("scope", flow.scope)
        mode = data.get("mode", flow.mode)
        steps = _validate_flow_payload(data, scope, mode, flow)
        flow.scope = scope
        flow.mode = mode
        flow.name = str(data.get("name", flow.name))[:60]
        if "is_active" in data:
            flow.is_active = bool(data["is_active"])
        flow.save()
        if steps is not None:
            _save_steps(flow, steps)
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow.id), result="SUCCESS",
                            detail={"op": "update", "steps_count": flow.steps.count()})
        return Response(flow_view(flow))

    def delete(self, request, flow_id: int):
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "流程不存在", 404)
        # 物理删除；被审批记录引用时（ApprovalInstance.flow 为 PROTECT）只能停用，
        # 否则历史审批单会失去流程归属。
        used = ApprovalInstance.objects.filter(flow=flow).count()
        if used:
            raise ApiError("FLOW_IN_USE",
                           f"该流程已被 {used} 条审批记录使用，不能删除；如不再使用，请停用该流程",
                           409, {"count": used})
        name = flow.name
        try:
            flow.delete()
        except ProtectedError as exc:
            raise ApiError("FLOW_IN_USE", "该流程已被审批记录使用，不能删除；如不再使用，请停用该流程",
                           409) from exc
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="APPROVAL_FLOW_CHANGED", object_type="approval_flow",
                            object_id=str(flow_id), result="SUCCESS",
                            detail={"op": "delete", "name": name})
        return Response(status=status.HTTP_204_NO_CONTENT)


class FlowOptionListView(APIView):
    permission_classes = [IsCommitteeMember]

    def get(self, request):
        scope = request.query_params.get("scope")
        if scope not in {"RESOLUTION", "EXPENSE", "INCOME"}:
            raise ApiError("INVALID_QUERY", "scope 必填")
        rows = ApprovalFlow.objects.filter(scope=scope, is_active=True).order_by("id")
        return Response([{
            "id": f.id, "name": f.name, "mode": f.mode, "step_count": f.steps.count(),
            "steps": [{"order": s.order, "name": s.name, "strategy": s.strategy,
                       "approvers": [{"id": a.user_id, "nickname": a.user.nickname}
                                     for a in s.approvers.select_related("user")]}
                      for s in f.steps.order_by("order")],
            "approvers": [{"id": a.user_id, "nickname": a.user.nickname}
                          for a in f.approvers.select_related("user")],
        } for f in rows])


class TaskListView(APIView):
    permission_classes = [IsCommitteeMember]

    def get(self, request):
        from .models import ApprovalStepState

        qs = ApprovalInstance.objects.filter(status="PENDING").select_related("submitter").order_by("submitted_at")
        scope = request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)
        rows = []
        for instance in qs:
            step = (ApprovalStepState.objects.filter(instance=instance,
                                                     step_order=instance.current_step_order).first())
            if step is None or request.user.id not in (step.approver_ids or []):
                continue
            rows.append((instance, step))
        data = [{
            "instance_id": i.id, "scope": i.scope, "subject_type": i.subject_type,
            "subject_id": i.subject_id, "subject_title": subject_title(i.subject_type, i.subject_id),
            "submitter_label": i.submitter.identity_label, "submitted_at": i.submitted_at,
            "step_order": step.step_order, "step_name": step.name, "step_strategy": step.strategy,
            "step_reached_at": step.reached_at,
        } for i, step in rows]
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        return Response({"count": len(data), "page": page, "page_size": page_size,
                         "results": data[(page - 1) * page_size: page * page_size]})


class InstanceDecisionView(APIView):
    permission_classes = [IsCommitteeMember]

    def post(self, request, instance_id: int):
        data = request.data or {}
        ApprovalEngine.decide(instance_id, request.user, data.get("action"),
                              str(data.get("comment", "")))
        return Response(ApprovalEngine.timeline(instance_id, request.user))


class InstanceDetailView(APIView):
    permission_classes = [IsMemberOrAdmin]

    def get(self, request, instance_id: int):
        return Response(ApprovalEngine.timeline(instance_id, request.user))
