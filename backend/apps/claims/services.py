"""报销服务（IFC-103/104）：审批回调中入账/作废台账。"""
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.ledger.services import LedgerService

from .models import Claim


def on_approved(subject_id: int) -> None:
    claim = Claim.objects.filter(id=subject_id, status="PENDING").first()
    if claim is None:
        return
    claim.status = "APPROVED"
    claim.decided_at = timezone.now()
    if claim.type == "SETTLEMENT":
        _approve_settlement(claim)
    elif not claim.ledger_posted:
        occurred_on = claim.occurred_on or claim.decided_at.date()
        LedgerService.post(direction="EXPENSE", amount=claim.amount, occurred_on=occurred_on,
                           entry_type=claim.type, summary=claim.reason, source_type="claim",
                           source_id=claim.id, seq=0)
        claim.ledger_posted = True
    claim.save(update_fields=["status", "decided_at", "ledger_posted", "updated_at"])
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="CLAIM_DECIDED",
                        object_type="claim", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": "APPROVED"})


def _approve_settlement(claim: Claim) -> None:
    """核销通过（REQ-FUNC-041/058，CR-017）：关联报销单不再单独计入支出（作废其台账），
    支出只按差额（实际花费合计 − 预借额）调整，差额为负即"多退"。"""
    for reimbursement in Claim.objects.filter(settlement_id=claim.id, type="REIMBURSEMENT"):
        if reimbursement.ledger_posted:
            LedgerService.void_by_source(source_type="claim", source_id=reimbursement.id)
            reimbursement.ledger_posted = False
            reimbursement.save(update_fields=["ledger_posted", "updated_at"])
    if claim.amount != 0 and not claim.ledger_posted:
        LedgerService.post(direction="EXPENSE", amount=claim.amount,
                           occurred_on=claim.decided_at.date(), entry_type=claim.type,
                           summary=claim.reason, source_type="claim", source_id=claim.id,
                           seq=0, allow_negative=True)
        claim.ledger_posted = True


def on_rejected(subject_id: int) -> None:
    _close(subject_id, "REJECTED")


def on_withdrawn(subject_id: int) -> None:
    _close(subject_id, "WITHDRAWN")


def _close(subject_id: int, status: str) -> None:
    claim = Claim.objects.filter(id=subject_id, status="PENDING").first()
    if claim is None:
        return
    if claim.ledger_posted:
        LedgerService.void_by_source(source_type="claim", source_id=claim.id)
        claim.ledger_posted = False
    claim.status = status
    claim.decided_at = timezone.now()
    claim.save(update_fields=["status", "decided_at", "ledger_posted", "updated_at"])
    if claim.type == "SETTLEMENT":
        # 核销未完成：释放借款与关联报销单，允许重新核销
        Claim.objects.filter(settlement_id=claim.id).update(settlement_id=None)
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="CLAIM_DECIDED",
                        object_type="claim", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": status})


class ClaimAttachmentPolicy:
    def can_open(self, linked_id: str, principal) -> bool:
        claim = Claim.objects.filter(id=linked_id).first()
        if claim is None or principal is None:
            return False
        if getattr(principal, "is_admin_principal", False):
            return True
        from apps.approval.services import ApprovalEngine

        user_id = getattr(principal, "id", None)
        if claim.submitter_id == user_id:
            return True
        instance = ApprovalEngine.pending_instance("claim", claim.id)
        if instance is not None and user_id in (instance.flow_snapshot.get("approver_ids") or []):
            return True
        return False
