"""审批壳（MOD-008）。"""
from django.db import models


class ApprovalFlow(models.Model):
    SCOPES = [("RESOLUTION", "决议"), ("EXPENSE", "支出"), ("INCOME", "收入")]
    MODES = [("DESIGNATED", "指定负责人"), ("HALF_MAJORITY", "半数同意")]

    scope = models.CharField(max_length=12, choices=SCOPES)
    name = models.CharField(max_length=60)
    mode = models.CharField(max_length=16, choices=MODES, default="DESIGNATED")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FlowApprover(models.Model):
    """审批人（deprecated，由 StepApprover 取代；保留用于回滚兜底，新代码不再写入）。"""
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, related_name="approvers")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="approval_flows")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["flow", "user"], name="uniq_flow_approver")]


class ApprovalStep(models.Model):
    """审批步骤（MOD-183）：有序、有名称、每步独立的或签/会签策略。"""
    STRATEGIES = [("ANY", "或签"), ("ALL", "会签")]

    flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=60)
    strategy = models.CharField(max_length=4, choices=STRATEGIES, default="ANY")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["flow", "order"], name="uniq_flow_step_order")]


class StepApprover(models.Model):
    step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE, related_name="approvers")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="approval_steps")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["step", "user"], name="uniq_step_approver")]


class ApprovalStepState(models.Model):
    """实例侧步骤快照状态（MOD-183）：到达时间、判定结果与审批人快照。"""
    STATUSES = [("PENDING", "未开始"), ("ACTIVE", "进行中"), ("APPROVED", "已通过"), ("REJECTED", "已拒绝")]

    instance = models.ForeignKey("ApprovalInstance", on_delete=models.CASCADE, related_name="step_states")
    step_order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=60)
    strategy = models.CharField(max_length=4, choices=ApprovalStep.STRATEGIES, default="ANY")
    approver_ids = models.JSONField(default=list)
    status = models.CharField(max_length=10, choices=STATUSES, default="PENDING")
    reached_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["step_order"]
        constraints = [models.UniqueConstraint(fields=["instance", "step_order"], name="uniq_instance_step")]


class ApprovalInstance(models.Model):
    STATUSES = [("PENDING", "待审批"), ("APPROVED", "通过"), ("REJECTED", "拒绝"), ("WITHDRAWN", "撤回")]

    scope = models.CharField(max_length=12, choices=ApprovalFlow.SCOPES)
    subject_type = models.CharField(max_length=32)
    subject_id = models.BigIntegerField()
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.PROTECT, related_name="instances")
    flow_snapshot = models.JSONField(default=dict)
    submitter = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="approval_submissions")
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    revision = models.IntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="approval_decisions")
    pending_slot = models.SmallIntegerField(null=True, blank=True, default=1)
    current_step_order = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subject_type", "subject_id", "pending_slot"],
                                    name="uniq_approval_pending")
        ]


class ApprovalAction(models.Model):
    ACTIONS = [("SUBMIT", "提交"), ("APPROVE", "通过"), ("REJECT", "拒绝"), ("WITHDRAW", "撤回")]

    instance = models.ForeignKey(ApprovalInstance, on_delete=models.CASCADE, related_name="actions")
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="approval_actions")
    action = models.CharField(max_length=8, choices=ACTIONS)
    comment = models.CharField(max_length=500, blank=True, default="")
    acted_at = models.DateTimeField(auto_now_add=True)
    step_state = models.ForeignKey(ApprovalStepState, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="actions")
    step_order = models.PositiveSmallIntegerField(null=True, blank=True)
