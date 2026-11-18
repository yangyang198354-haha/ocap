"""清理"半数同意 + 指定审批人"的脏数据（修复问题二）。

历史上管理端允许把 HALF_MAJORITY（半数同意）流程同时配置审批人，这些审批人会被
写入 FlowApprover，并随决议提交进入 ApprovalInstance.flow_snapshot.approver_ids，
导致半数同意决议错误地出现在 /approval/tasks 审批待办里，审批人点"同意"时被
ApprovalEngine.decide() 以 USE_VOTE_ENDPOINT（"半数同意决议请使用投票接口"）拒绝。

半数同意决议应走投票接口判定，不应有审批人。此迁移：
1. 删除所有 HALF_MAJORITY 流程上的 FlowApprover；
2. 把所有 flow_snapshot.mode == HALF_MAJORITY 的实例快照里的 approver_ids 清空。
"""
from django.db import migrations


def clean_half_majority_approvers(apps, schema_editor):
    ApprovalFlow = apps.get_model("approval", "ApprovalFlow")
    FlowApprover = apps.get_model("approval", "FlowApprover")
    ApprovalInstance = apps.get_model("approval", "ApprovalInstance")

    half_flow_ids = list(
        ApprovalFlow.objects.filter(mode="HALF_MAJORITY").values_list("id", flat=True)
    )
    if half_flow_ids:
        FlowApprover.objects.filter(flow_id__in=half_flow_ids).delete()

    for instance in ApprovalInstance.objects.all():
        snapshot = instance.flow_snapshot or {}
        if snapshot.get("mode") == "HALF_MAJORITY" and snapshot.get("approver_ids"):
            snapshot["approver_ids"] = []
            instance.flow_snapshot = snapshot
            instance.save(update_fields=["flow_snapshot"])


def noop_reverse(apps, schema_editor):
    # 清理不可逆（也不应恢复脏数据）。
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("approval", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(clean_half_majority_approvers, noop_reverse),
    ]
