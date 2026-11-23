"""审批引擎（IFC-082/083、IFC-408）。"""
from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError

from .models import (ApprovalAction, ApprovalFlow, ApprovalInstance, ApprovalStep, ApprovalStepState,
                     FlowApprover)

_CALLBACKS: dict[str, dict] = {}


def register_callbacks(subject_type: str, *, on_approved=None, on_rejected=None, on_withdrawn=None) -> None:
    _CALLBACKS[subject_type] = {
        "approved": on_approved, "rejected": on_rejected, "withdrawn": on_withdrawn,
    }


def _run(subject_type: str, kind: str, subject_id: int) -> None:
    handler = (_CALLBACKS.get(subject_type) or {}).get(kind)
    if handler is not None:
        handler(subject_id)


def _flow_steps(flow: ApprovalFlow) -> list[dict]:
    steps = list(ApprovalStep.objects.filter(flow=flow).order_by("order").prefetch_related("approvers"))
    if steps:
        return [{"order": s.order, "name": s.name, "strategy": s.strategy,
                 "approver_ids": [a.user_id for a in s.approvers.all()]} for s in steps]
    # 兼容：升级前创建的流程只有 FlowApprover，折算为 1 步（REQ-FUNC-327）
    ids = list(FlowApprover.objects.filter(flow=flow).values_list("user_id", flat=True))
    return [{"order": 1, "name": flow.name, "strategy": "ANY", "approver_ids": ids}]


def _snapshot_steps(instance: ApprovalInstance) -> list[dict]:
    states = list(instance.step_states.order_by("step_order"))
    if states:
        return [{"order": s.step_order, "name": s.name, "strategy": s.strategy,
                 "approver_ids": list(s.approver_ids or []), "status": s.status,
                 "reached_at": s.reached_at, "decided_at": s.decided_at} for s in states]
    snapshot = instance.flow_snapshot or {}
    steps = snapshot.get("steps") or []
    if steps:
        return [{**item, "status": "PENDING", "reached_at": None, "decided_at": None} for item in steps]
    ids = snapshot.get("approver_ids") or []
    return [{"order": 1, "name": snapshot.get("name") or "", "strategy": "ANY",
             "approver_ids": list(ids), "status": "PENDING", "reached_at": None, "decided_at": None}]


def _ensure_states(instance: ApprovalInstance) -> None:
    """为缺少步骤状态的旧在办实例补建快照状态。"""
    if instance.step_states.exists():
        return
    if (instance.flow_snapshot or {}).get("mode") == "HALF_MAJORITY":
        return
    for index, item in enumerate(_snapshot_steps(instance)):
        ApprovalStepState.objects.create(
            instance=instance, step_order=item["order"], name=item["name"] or f"第{item['order']}步",
            strategy=item.get("strategy") or "ANY", approver_ids=list(item.get("approver_ids") or []),
            status="ACTIVE" if index == 0 else "PENDING",
            reached_at=instance.submitted_at if index == 0 else None,
        )
    first = instance.step_states.order_by("step_order").first()
    if first is not None:
        instance.current_step_order = first.step_order
        instance.save(update_fields=["current_step_order"])


def _step_actions(step_state: ApprovalStepState) -> tuple[set[int], set[int]]:
    rows = ApprovalAction.objects.filter(step_state=step_state, action__in=["APPROVE", "REJECT"])
    approvals = {row.actor_id for row in rows if row.action == "APPROVE"}
    rejects = {row.actor_id for row in rows if row.action == "REJECT"}
    return approvals, rejects


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
        steps = [] if flow.mode == "HALF_MAJORITY" else _flow_steps(flow)
        if flow.mode != "HALF_MAJORITY":
            if not steps or any(not step["approver_ids"] for step in steps):
                raise ApiError("INVALID_VALUE", "审批流程没有审批人")
            if scope in {"EXPENSE", "INCOME"}:
                from apps.committee.services import CommitteeQuery

                for step in steps:
                    eligible = [uid for uid in step["approver_ids"]
                                if uid != submitter.id and CommitteeQuery.is_member(uid)]
                    if not eligible:
                        raise ApiError("NO_ELIGIBLE_APPROVER", "审批流程中没有其他可审批的人", 422)
        with transaction.atomic():
            ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id,
                                            status="PENDING").update(
                status="WITHDRAWN", pending_slot=None, decided_at=timezone.now())
            all_ids = sorted({uid for step in steps for uid in step["approver_ids"]})
            instance = ApprovalInstance.objects.create(
                scope=scope, subject_type=subject_type, subject_id=subject_id, flow=flow,
                flow_snapshot={"schema_version": 2, "name": flow.name, "mode": flow.mode,
                               "approver_ids": all_ids, "steps": steps},
                submitter=submitter, revision=revision, pending_slot=1,
                current_step_order=steps[0]["order"] if steps else None,
            )
            for index, step in enumerate(steps):
                ApprovalStepState.objects.create(
                    instance=instance, step_order=step["order"], name=step["name"],
                    strategy=step["strategy"], approver_ids=list(step["approver_ids"]),
                    status="ACTIVE" if index == 0 else "PENDING",
                    reached_at=timezone.now() if index == 0 else None,
                )
            ApprovalAction.objects.create(instance=instance, actor=submitter, action="SUBMIT",
                                          step_order=steps[0]["order"] if steps else None)
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
                current_step_order=None,
            )
            if not updated:
                raise ApiError("ALREADY_DECIDED", "该申请已处理", 409)
            ApprovalAction.objects.create(instance=instance, actor=actor, action="WITHDRAW",
                                          step_order=instance.current_step_order)
        _run(instance.subject_type, "withdrawn", instance.subject_id)
        instance.refresh_from_db()
        return instance

    @staticmethod
    def resubmit(*, scope: str, subject_type: str, subject_id: int, flow_id: int, submitter,
                 revision: int) -> ApprovalInstance:
        latest = (ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id)
                  .order_by("-revision").first())
        # REQ-FUNC-269/270：审批失败即终局，原单只能撤回后重提，失败后须新建单据
        if latest is not None and latest.status != "WITHDRAWN":
            raise ApiError("NOT_RESUBMITTABLE", "该单据已结束，如需再次办理请新建", 409)
        return ApprovalEngine.submit(scope=scope, subject_type=subject_type, subject_id=subject_id,
                                     flow_id=flow_id, submitter=submitter, revision=revision + 1)

    @staticmethod
    def decide(instance_id: int, actor, action: str, comment: str = "") -> ApprovalInstance:
        if action not in {"APPROVE", "REJECT"}:
            raise ApiError("INVALID_VALUE", "action 不合法")
        comment = str(comment or "")
        if len(comment) > 500:
            raise ApiError("INVALID_VALUE", "审批意见最多 500 字")
        from apps.committee.services import CommitteeQuery

        with transaction.atomic():
            instance = (ApprovalInstance.objects.select_for_update()
                        .select_related("submitter").filter(id=instance_id).first())
            if instance is None:
                raise ApiError("NOT_FOUND", "审批实例不存在", 404)
            if instance.flow_snapshot.get("mode") == "HALF_MAJORITY":
                raise ApiError("USE_VOTE_ENDPOINT", "半数以上参与者同意的决议请使用投票接口", 409)
            if instance.status != "PENDING":
                raise ApiError("ALREADY_DECIDED", "该审批已处理", 409)
            _ensure_states(instance)
            step = (ApprovalStepState.objects.select_for_update()
                    .filter(instance=instance, step_order=instance.current_step_order).first())
            if step is None:
                raise ApiError("ALREADY_DECIDED", "该审批已处理", 409)
            if actor.id not in (step.approver_ids or []):
                raise ApiError("FORBIDDEN", "不在该步骤审批人名单内", 403)
            if not CommitteeQuery.is_member(actor.id):
                raise ApiError("APPROVER_NO_LONGER_ELIGIBLE", "审批人当前已不是业委会成员", 403)
            if instance.scope in {"EXPENSE", "INCOME"} and actor.id == instance.submitter_id:
                raise ApiError("SELF_APPROVAL_FORBIDDEN", "不得审批自己的申请", 403)
            if ApprovalAction.objects.filter(instance=instance, actor=actor, step_state=step,
                                             action__in=["APPROVE", "REJECT"]).exists():
                raise ApiError("ALREADY_DECIDED", "你已处理过该步骤", 409)

            ApprovalAction.objects.create(instance=instance, actor=actor, action=action,
                                          comment=comment, step_state=step, step_order=step.step_order)
            approvals, rejects = _step_actions(step)
            approver_ids = set(step.approver_ids or [])
            step_passed = False
            step_failed = False
            if step.strategy == "ALL":
                step_failed = bool(rejects)
                step_passed = not step_failed and approvals >= approver_ids
            else:
                step_passed = bool(approvals)
                step_failed = not step_passed and approver_ids and rejects >= approver_ids

            now = timezone.now()
            if step_failed:
                step.status = "REJECTED"
                step.decided_at = now
                step.save(update_fields=["status", "decided_at"])
                instance.status = "REJECTED"
                instance.decided_at = now
                instance.decided_by = actor
                instance.pending_slot = None
                instance.current_step_order = None
                instance.save(update_fields=["status", "decided_at", "decided_by", "pending_slot",
                                             "current_step_order"])
            elif step_passed:
                step.status = "APPROVED"
                step.decided_at = now
                step.save(update_fields=["status", "decided_at"])
                next_step = (ApprovalStepState.objects.filter(instance=instance,
                                                              step_order__gt=step.step_order)
                             .order_by("step_order").first())
                if next_step is None:
                    instance.status = "APPROVED"
                    instance.decided_at = now
                    instance.decided_by = actor
                    instance.pending_slot = None
                    instance.current_step_order = None
                    instance.save(update_fields=["status", "decided_at", "decided_by", "pending_slot",
                                                 "current_step_order"])
                else:
                    next_step.status = "ACTIVE"
                    next_step.reached_at = now
                    next_step.save(update_fields=["status", "reached_at"])
                    instance.current_step_order = next_step.step_order
                    instance.save(update_fields=["current_step_order"])
            else:
                instance.save(update_fields=[])

        if instance.status in {"APPROVED", "REJECTED"}:
            AuditService.record(actor=AuditActor("MEMBER", actor.id, actor.identity_label),
                                action="RESOLUTION_DECIDED" if instance.scope == "RESOLUTION"
                                else ("CLAIM_DECIDED" if instance.scope == "EXPENSE" else "INCOME_DECIDED"),
                                object_type=instance.subject_type, object_id=str(instance.subject_id),
                                result="SUCCESS", detail={"decision": instance.status})
            _run(instance.subject_type, "approved" if instance.status == "APPROVED" else "rejected",
                 instance.subject_id)
        instance.refresh_from_db()
        return instance

    @staticmethod
    def is_original_approver(instance_id: int, user_id: int) -> bool:
        instance = ApprovalInstance.objects.filter(id=instance_id).first()
        if instance is None:
            return False
        if user_id in (instance.flow_snapshot.get("approver_ids") or []):
            return True
        return any(user_id in (s.approver_ids or []) for s in instance.step_states.all())

    @staticmethod
    def pending_instance(subject_type: str, subject_id: int) -> ApprovalInstance | None:
        return ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id,
                                               status="PENDING").first()

    @staticmethod
    def pending_subject_ids(subject_type: str, user_id: int) -> list[int]:
        instances = ApprovalInstance.objects.filter(subject_type=subject_type, status="PENDING")
        result = []
        for instance in instances:
            if instance.flow_snapshot.get("mode") == "HALF_MAJORITY":
                continue
            step = (ApprovalStepState.objects.filter(instance=instance,
                                                     step_order=instance.current_step_order).first())
            if step is not None and user_id in (step.approver_ids or []):
                result.append(instance.subject_id)
        return result

    @staticmethod
    def current_step(instance: ApprovalInstance) -> ApprovalStepState | None:
        return (ApprovalStepState.objects.filter(instance=instance,
                                                 step_order=instance.current_step_order).first())

    @staticmethod
    def can_view(instance: ApprovalInstance, viewer) -> bool:
        from apps.accounts.models import AdminAccount

        if isinstance(viewer, AdminAccount) and viewer.is_active:
            return True
        if viewer.id == instance.submitter_id:
            return True
        if viewer.id in (instance.flow_snapshot.get("approver_ids") or []):
            return True
        return any(viewer.id in (s.approver_ids or []) for s in instance.step_states.all())

    @staticmethod
    def instance_id_of(subject_type: str, subject_id: int) -> int | None:
        return (ApprovalInstance.objects.filter(subject_type=subject_type, subject_id=subject_id)
                .order_by("-revision", "-id").values_list("id", flat=True).first())

    @staticmethod
    def timeline(instance_id: int, viewer) -> dict:
        from apps.accounts.directory import person_refs

        instance = (ApprovalInstance.objects.select_related("submitter")
                    .filter(id=instance_id).first())
        if instance is None:
            raise ApiError("NOT_FOUND", "审批实例不存在", 404)
        if not ApprovalEngine.can_view(instance, viewer):
            raise ApiError("FORBIDDEN", "无权查看该审批过程", 403)
        states = list(instance.step_states.order_by("step_order"))
        if not states:
            steps = _snapshot_steps(instance)
        else:
            steps = [{"order": s.step_order, "name": s.name, "strategy": s.strategy,
                      "approver_ids": list(s.approver_ids or []), "status": s.status,
                      "reached_at": s.reached_at, "decided_at": s.decided_at} for s in states]
        actions = list(ApprovalAction.objects.filter(instance=instance).order_by("acted_at", "id"))
        actor_ids = {row.actor_id for row in actions}
        approver_ids = {uid for step in steps for uid in (step.get("approver_ids") or [])}
        refs = person_refs({instance.submitter_id} | actor_ids | approver_ids)
        grouped: dict[int, list] = {}
        for row in actions:
            order = row.step_order or (steps[0]["order"] if steps else 1)
            actor = refs.get(row.actor_id) or {
                "id": row.actor_id, "display_name": f"用户#{row.actor_id}",
                "real_name": "", "avatar_url": None, "account_no": "",
            }
            grouped.setdefault(order, []).append({
                "actor_id": row.actor_id,
                "actor_label": actor["display_name"],
                "actor_avatar_url": actor["avatar_url"],
                "actor_account_no": actor["account_no"],
                "action": row.action,
                "comment": row.comment,
                "acted_at": row.acted_at,
                "legacy": row.step_state_id is None,
            })
        for step in steps:
            step["approvers"] = [refs.get(uid) or {
                "id": uid, "display_name": f"用户#{uid}", "real_name": "",
                "avatar_url": None, "account_no": "",
            } for uid in (step.get("approver_ids") or [])]
            step["actions"] = grouped.get(step["order"], [])
        submitter = refs.get(instance.submitter_id) or {
            "id": instance.submitter_id, "display_name": f"用户#{instance.submitter_id}",
            "real_name": "", "avatar_url": None, "account_no": "",
        }
        return {
            "id": instance.id, "scope": instance.scope, "subject_type": instance.subject_type,
            "subject_id": instance.subject_id, "subject_title": subject_title(instance.subject_type,
                                                                              instance.subject_id),
            "submitter": submitter, "submitter_label": submitter["display_name"],
            "status": instance.status, "current_step_order": instance.current_step_order,
            "submitted_at": instance.submitted_at, "decided_at": instance.decided_at,
            "steps": steps,
        }


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
