from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    name = "apps.approval"
    verbose_name = "审批引擎"

    def ready(self) -> None:
        from apps.core.user_refs import register_user_reference

        from .models import ApprovalAction, ApprovalInstance, FlowApprover, StepApprover

        register_user_reference(FlowApprover, "user", on_conflict="custom", handler=_merge_flow_approvers)
        register_user_reference(StepApprover, "user", on_conflict="custom", handler=_merge_step_approvers)
        for field in ("submitter", "decided_by"):
            register_user_reference(ApprovalInstance, field, on_conflict="move_all")
        register_user_reference(ApprovalAction, "actor", on_conflict="move_all")


def _merge_step_approvers(primary_id: int, secondary_id: int) -> list[str]:
    from .models import StepApprover

    moved = []
    for row in StepApprover.objects.filter(user_id=secondary_id):
        if StepApprover.objects.filter(step_id=row.step_id, user_id=primary_id).exists():
            row.delete()
            moved.append(f"drop:{row.step_id}")
        else:
            row.user_id = primary_id
            row.save(update_fields=["user"])
            moved.append(f"move:{row.step_id}")
    return moved


def _merge_flow_approvers(primary_id: int, secondary_id: int) -> list[str]:
    from .models import FlowApprover

    moved = []
    for row in FlowApprover.objects.filter(user_id=secondary_id):
        if FlowApprover.objects.filter(flow_id=row.flow_id, user_id=primary_id).exists():
            row.delete()
            moved.append(f"drop:{row.flow_id}")
        else:
            row.user_id = primary_id
            row.save(update_fields=["user"])
            moved.append(f"move:{row.flow_id}")
    return moved
