"""MOD-183：审批步骤、步骤审批人、实例步骤状态与动作归属。"""
from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    ApprovalFlow = apps.get_model("approval", "ApprovalFlow")
    FlowApprover = apps.get_model("approval", "FlowApprover")
    ApprovalStep = apps.get_model("approval", "ApprovalStep")
    StepApprover = apps.get_model("approval", "StepApprover")
    ApprovalInstance = apps.get_model("approval", "ApprovalInstance")
    ApprovalStepState = apps.get_model("approval", "ApprovalStepState")
    ApprovalAction = apps.get_model("approval", "ApprovalAction")

    # 1) 既有 DESIGNATED 流程折算为 1 步（REQ-FUNC-327）
    for flow in ApprovalFlow.objects.filter(mode="DESIGNATED"):
        step, _ = ApprovalStep.objects.get_or_create(
            flow_id=flow.id, order=1, defaults={"name": flow.name, "strategy": "ANY"})
        ids = list(FlowApprover.objects.filter(flow_id=flow.id).values_list("user_id", flat=True))
        for user_id in ids:
            StepApprover.objects.get_or_create(step_id=step.id, user_id=user_id)

    # 2) 在办实例生成步骤状态快照
    for instance in ApprovalInstance.objects.filter(status="PENDING"):
        snapshot = instance.flow_snapshot or {}
        steps = snapshot.get("steps") or []
        if not steps:
            flow = ApprovalFlow.objects.filter(id=instance.flow_id).first()
            ids = snapshot.get("approver_ids") or []
            if not ids and flow is not None:
                ids = list(FlowApprover.objects.filter(flow_id=flow.id).values_list("user_id", flat=True))
            steps = [{"order": 1, "name": snapshot.get("name") or (flow.name if flow else instance.subject_type),
                      "strategy": "ANY", "approver_ids": list(ids)}]
        if snapshot.get("mode") == "HALF_MAJORITY":
            continue
        first = None
        for index, item in enumerate(steps):
            order = item.get("order") or index + 1
            state = ApprovalStepState.objects.create(
                instance_id=instance.id, step_order=order, name=item.get("name") or f"第{order}步",
                strategy=item.get("strategy") or "ANY", approver_ids=list(item.get("approver_ids") or []),
                status="ACTIVE" if index == 0 else "PENDING",
                reached_at=instance.submitted_at if index == 0 else None,
            )
            if first is None:
                first = state
        if first is not None:
            instance.current_step_order = first.step_order
            instance.save(update_fields=["current_step_order"])
            ApprovalAction.objects.filter(instance_id=instance.id).update(
                step_order=first.step_order, step_state_id=first.id)


def backwards(apps, schema_editor):
    FlowApprover = apps.get_model("approval", "FlowApprover")
    ApprovalStep = apps.get_model("approval", "ApprovalStep")
    StepApprover = apps.get_model("approval", "StepApprover")
    ApprovalStepState = apps.get_model("approval", "ApprovalStepState")

    # 单步 ANY 流程可回填到 FlowApprover；多步流程回滚会丢失步骤数据（[MANUAL_ROLLBACK_REQUIRED]）
    for step in ApprovalStep.objects.filter(order=1, strategy="ANY"):
        if ApprovalStep.objects.filter(flow_id=step.flow_id).count() != 1:
            continue
        for row in StepApprover.objects.filter(step_id=step.id):
            FlowApprover.objects.get_or_create(flow_id=step.flow_id, user_id=row.user_id)
    ApprovalStepState.objects.all().delete()
    ApprovalStep.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("approval", "0002_clean_half_majority_approvers"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField()),
                ("name", models.CharField(max_length=60)),
                ("strategy", models.CharField(choices=[("ANY", "或签"), ("ALL", "会签")], default="ANY", max_length=4)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("flow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="steps", to="approval.approvalflow")),
            ],
            options={"ordering": ["order"]},
        ),
        migrations.AddConstraint(
            model_name="approvalstep",
            constraint=models.UniqueConstraint(fields=("flow", "order"), name="uniq_flow_step_order"),
        ),
        migrations.CreateModel(
            name="StepApprover",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="approvers", to="approval.approvalstep")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="approval_steps", to="accounts.user")),
            ],
        ),
        migrations.AddConstraint(
            model_name="stepapprover",
            constraint=models.UniqueConstraint(fields=("step", "user"), name="uniq_step_approver"),
        ),
        migrations.CreateModel(
            name="ApprovalStepState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step_order", models.PositiveSmallIntegerField()),
                ("name", models.CharField(max_length=60)),
                ("strategy", models.CharField(choices=[("ANY", "或签"), ("ALL", "会签")], default="ANY", max_length=4)),
                ("approver_ids", models.JSONField(default=list)),
                ("status", models.CharField(choices=[("PENDING", "未开始"), ("ACTIVE", "进行中"),
                                                     ("APPROVED", "已通过"), ("REJECTED", "已拒绝")],
                                            default="PENDING", max_length=10)),
                ("reached_at", models.DateTimeField(blank=True, null=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("instance", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="step_states", to="approval.approvalinstance")),
            ],
            options={"ordering": ["step_order"]},
        ),
        migrations.AddConstraint(
            model_name="approvalstepstate",
            constraint=models.UniqueConstraint(fields=("instance", "step_order"), name="uniq_instance_step"),
        ),
        migrations.AddField(
            model_name="approvalinstance",
            name="current_step_order",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="approvalaction",
            name="step_state",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="actions", to="approval.approvalstepstate"),
        ),
        migrations.AddField(
            model_name="approvalaction",
            name="step_order",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]
