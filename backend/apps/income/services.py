"""收入服务（IFC-102/104）：审批回调入账、作废留痕、金额重算。"""
from decimal import Decimal

from django.db.models import Max, Min, Sum
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.ledger.services import LedgerService

from .models import IncomeSheet


def on_approved(subject_id: int) -> None:
    sheet = IncomeSheet.objects.filter(id=subject_id, status="PENDING").first()
    if sheet is None:
        return
    sheet.status = "EFFECTIVE"
    sheet.decided_at = timezone.now()
    sheet.effective_at = timezone.now()
    sheet.save(update_fields=["status", "decided_at", "effective_at", "updated_at"])
    for record in sheet.records.all():
        LedgerService.post(direction="INCOME", amount=record.amount,
                           occurred_on=record.occurred_on, entry_type=record.category or "INCOME",
                           summary=record.source_note, source_type="income_record",
                           source_id=record.id, seq=0)
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="INCOME_DECIDED",
                        object_type="income_sheet", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": "EFFECTIVE"})


def on_rejected(subject_id: int) -> None:
    IncomeSheet.objects.filter(id=subject_id, status="PENDING").update(
        status="REJECTED", decided_at=timezone.now())
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="INCOME_DECIDED",
                        object_type="income_sheet", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": "REJECTED"})


def on_withdrawn(subject_id: int) -> None:
    IncomeSheet.objects.filter(id=subject_id, status="PENDING").update(
        status="WITHDRAWN", decided_at=timezone.now())
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="INCOME_DECIDED",
                        object_type="income_sheet", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": "WITHDRAWN"})


def is_original_approver_of(sheet: IncomeSheet, user_id: int | None) -> bool:
    """AC-060-04/10（Q109=B）：作废权限只属于该收入表原审批流程指定的审批人。"""
    from apps.approval.models import ApprovalInstance
    from apps.approval.services import ApprovalEngine

    if user_id is None:
        return False
    instance = ApprovalInstance.objects.filter(
        subject_type="income_sheet", subject_id=sheet.id, status="APPROVED").order_by("-id").first()
    return instance is not None and ApprovalEngine.is_original_approver(instance.id, user_id)


def void_sheet(sheet_id: int, by_user) -> IncomeSheet:
    sheet = IncomeSheet.objects.filter(id=sheet_id).first()
    if sheet is None:
        from apps.core.errors import ApiError
        raise ApiError("NOT_FOUND", "收入表不存在", 404)
    if sheet.status != "EFFECTIVE":
        from apps.core.errors import ApiError
        raise ApiError("IMMUTABLE", "仅已生效收入表可作废", 409)
    if not is_original_approver_of(sheet, by_user.id):
        from apps.core.errors import ApiError
        AuditService.record(actor=AuditActor("MEMBER", by_user.id, by_user.identity_label),
                            action="INCOME_VOIDED", object_type="income_sheet",
                            object_id=str(sheet.id), result="DENIED")
        raise ApiError("FORBIDDEN", "仅原审批流程指定的审批人可作废", 403)
    for record in sheet.records.all():
        LedgerService.void_by_source(source_type="income_record", source_id=record.id)
    sheet.status = "VOID"
    sheet.void_reason = ""
    sheet.voided_by_id = by_user.id
    sheet.voided_at = timezone.now()
    sheet.save(update_fields=["status", "void_reason", "voided_by_id", "voided_at", "updated_at"])
    AuditService.record(actor=AuditActor("MEMBER", by_user.id, by_user.identity_label),
                        action="INCOME_VOIDED", object_type="income_sheet",
                        object_id=str(sheet.id), result="SUCCESS")
    return sheet


def recalculate(sheet: IncomeSheet) -> Decimal:
    total = sheet.records.aggregate(total=Sum("amount"))["total"]
    sheet.total_amount = total or Decimal("0.00")
    bounds = sheet.records.aggregate(first=Min("occurred_on"), last=Max("occurred_on"))
    sheet.period_start = bounds["first"]
    sheet.period_end = bounds["last"]
    sheet.save(update_fields=["total_amount", "period_start", "period_end", "updated_at"])
    return sheet.total_amount


class IncomeAttachmentPolicy:
    def can_open(self, linked_id: str, principal) -> bool:
        sheet = IncomeSheet.objects.filter(id=linked_id).first()
        if sheet is None or principal is None:
            return False
        if getattr(principal, "is_admin_principal", False):
            return True
        user_id = getattr(principal, "id", None)
        if sheet.submitted_by_id == user_id or sheet.status == "EFFECTIVE":
            return True
        from apps.approval.services import ApprovalEngine
        from apps.committee.services import CommitteeQuery

        instance = ApprovalEngine.pending_instance("income_sheet", sheet.id)
        if instance is not None and user_id in (instance.flow_snapshot.get("approver_ids") or []):
            return True
        return CommitteeQuery.is_member(user_id)
