"""审批引擎（IFC-082/083）。"""
from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError

from .models import ApprovalAction, ApprovalFlow, ApprovalInstance, FlowApprover

_CALLBACKS: dict[str, dict] = {}


def register_callbacks(subject_type: str, *, on_approved=None, on_rejected=None, on_withdrawn=None) -> None:
    _CALLBACKS[subject_type] = {
        "approved": on_approved, "rejected": on_rejected, "withdrawn": on_withdrawn,
    }


def _run(subject_type: str, kind: str, subject_id: int) -> None:
    handler = (_CALLBACKS.get(subject_type) or {}).get(kind)
    if handler is not None:
        handler(subject_id)


class ApprovalEngine:
    @staticmethod
    def submit(*, scope: str, subject_type: str, subject_id: int, flow_id: int, submitter,
               revision: int = 1) -> ApprovalInstance:
        flow = ApprovalFlow.objects.filter(id=flow_id).first()
        if flow is None:
            raise ApiError("NOT_FOUND", "审批流程不存在", 404)
        if not flow.is_active:
            raise ApiError("FLOW_INACTIVE", "审批流程已停用", 409)
        if flow.scope != scope:
            raise ApiError("INVALID_VALUE", "审批流程适用范围不匹配")
        approver_ids = list(FlowApprover.objects.filter(flow=flow).values_list("user_id", flat=True))
        if scope in {"EXPENSE", "INCOME"}:
            from apps.committee.services import CommitteeQuery

            eligible = [uid for uid in approver_ids if uid != submitter.id and CommitteeQuery.is_member(uid)]
            if not eligible:
                raise ApiError("NO_ELIGIBLE_APPROVER", "审批流程中没有其他可审批的人", 422)
        elif flow.mode == "DESIGNATED" and not approver_ids:
            raise ApiError("INVALID_VALUE", "审批流程没有审批人")
        with transaction.atomic():
            ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id,
                                            status="PENDING").update(
                status="WITHDRAWN", pending_slot=None, decided_at=timezone.now())
            instance = ApprovalInstance.objects.create(
                scope=scope, subject_type=subject_type, subject_id=subject_id, flow=flow,
                flow_snapshot={"name": flow.name, "mode": flow.mode, "approver_ids": approver_ids},
                submitter=submitter, revision=revision, pending_slot=1,
            )
            ApprovalAction.objects.create(instance=instance, actor=submitter, action="SUBMIT")
        return instance

    @staticmethod
    def withdraw(instance_id: int, actor) -> ApprovalInstance:
        with transaction.atomic():
            instance = ApprovalInstance.objects.select_for_update().filter(id=instance_id).first()
            if instance is None:
                raise ApiError("NOT_FOUND", "审批实例不存在", 404)
            if instance.submitter_id != actor.id:
                raise ApiError("FORBIDDEN", "仅发起人可撤回", 403)
            updated = ApprovalInstance.objects.filter(id=instance_id, status="PENDING").update(
                status="WITHDRAWN", pending_slot=None, decided_at=timezone.now(),
            )
            if not updated:
                raise ApiError("ALREADY_DECIDED", "该申请已处理", 409)
            ApprovalAction.objects.create(instance=instance, actor=actor, action="WITHDRAW")
        _run(instance.subject_type, "withdrawn", instance.subject_id)
        instance.refresh_from_db()
        return instance

    @staticmethod
    def resubmit(*, scope: str, subject_type: str, subject_id: int, flow_id: int, submitter,
                 revision: int) -> ApprovalInstance:
        latest = (ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id)
                  .order_by("-revision").first())
        if latest is not None and latest.status not in {"REJECTED", "WITHDRAWN"}:
            raise ApiError("NOT_RESUBMITTABLE", "当前状态不可重新提交", 409)
        return ApprovalEngine.submit(scope=scope, subject_type=subject_type, subject_id=subject_id,
                                     flow_id=flow_id, submitter=submitter, revision=revision + 1)

    @staticmethod
    def decide(instance_id: int, actor, action: str, comment: str = "") -> ApprovalInstance:
        if action not in {"APPROVE", "REJECT"}:
            raise ApiError("INVALID_VALUE", "action 不合法")
        instance = ApprovalInstance.objects.select_related("submitter").filter(id=instance_id).first()
        if instance is None:
            raise ApiError("NOT_FOUND", "审批实例不存在", 404)
        if instance.flow_snapshot.get("mode") == "HALF_MAJORITY":
            raise ApiError("USE_VOTE_ENDPOINT", "半数同意决议请使用投票接口", 409)
        approver_ids = instance.flow_snapshot.get("approver_ids") or []
        if actor.id not in approver_ids:
            raise ApiError("FORBIDDEN", "不在该实例审批人名单内", 403)
        from apps.committee.services import CommitteeQuery

        if not CommitteeQuery.is_member(actor.id):
            raise ApiError("APPROVER_NO_LONGER_ELIGIBLE", "审批人当前已不是业委会成员", 403)
        if instance.scope in {"EXPENSE", "INCOME"} and actor.id == instance.submitter_id:
            raise ApiError("SELF_APPROVAL_FORBIDDEN", "不得审批自己的申请", 403)
        new_status = "APPROVED" if action == "APPROVE" else "REJECTED"
        updated = ApprovalInstance.objects.filter(id=instance_id, status="PENDING").update(
            status=new_status, decided_at=timezone.now(), decided_by=actor, pending_slot=None,
        )
        if not updated:
            raise ApiError("ALREADY_DECIDED", "该审批已处理", 409)
        ApprovalAction.objects.create(instance=instance, actor=actor, action=action, comment=comment[:500])
        AuditService.record(actor=AuditActor("MEMBER", actor.id, actor.identity_label),
                            action="RESOLUTION_DECIDED" if instance.scope == "RESOLUTION"
                            else ("CLAIM_DECIDED" if instance.scope == "EXPENSE" else "INCOME_DECIDED"),
                            object_type=instance.subject_type, object_id=str(instance.subject_id),
                            result="SUCCESS", detail={"decision": new_status})
        _run(instance.subject_type, "approved" if action == "APPROVE" else "rejected", instance.subject_id)
        instance.refresh_from_db()
        return instance

    @staticmethod
    def is_original_approver(instance_id: int, user_id: int) -> bool:
        instance = ApprovalInstance.objects.filter(id=instance_id).first()
        return instance is not None and user_id in (instance.flow_snapshot.get("approver_ids") or [])

    @staticmethod
    def pending_instance(subject_type: str, subject_id: int) -> ApprovalInstance | None:
        return ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id,
                                               status="PENDING").first()

    @staticmethod
    def pending_subject_ids(subject_type: str, user_id: int) -> list[int]:
        instances = ApprovalInstance.objects.filter(subject_type=subject_type, status="PENDING")
        return [i.subject_id for i in instances
                if user_id in (i.flow_snapshot.get("approver_ids") or [])]


def subject_title(subject_type: str, subject_id: int) -> str:
    if subject_type == "resolution":
        from apps.resolutions.models import Resolution

        row = Resolution.objects.filter(id=subject_id).first()
        return row.title if row else f"决议#{subject_id}"
    if subject_type == "claim":
        from apps.claims.models import Claim

        row = Claim.objects.filter(id=subject_id).first()
        return row.reason[:60] if row else f"申请#{subject_id}"
    if subject_type == "income_sheet":
        from apps.income.models import IncomeSheet

        row = IncomeSheet.objects.filter(id=subject_id).first()
        return (row.title or f"收入表#{subject_id}") if row else f"收入表#{subject_id}"
    return f"{subject_type}#{subject_id}"
