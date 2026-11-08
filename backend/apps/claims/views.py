"""报销视图（IFC-100~104）。"""
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approval.models import ApprovalFlow
from apps.approval.services import ApprovalEngine
from apps.committee.services import CommitteeQuery
from apps.core.attachments import AttachmentService, count_limit, linked_attachment_list
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.core.money import money
from apps.core.permissions import IsAdmin, IsIncomeMember, IsMember
from apps.core.serializers import page_response

from .models import Claim

MAX_AMOUNT = Decimal("1000000.00")


def claim_view(claim: Claim) -> dict:
    return {
        "id": claim.id, "type": claim.type, "amount": money(claim.amount), "reason": claim.reason,
        "occurred_on": claim.occurred_on, "expected_usage": claim.expected_usage,
        "expected_settle_on": claim.expected_settle_on, "advance_id": claim.advance_id,
        "settlement_id": claim.settlement_id, "status": claim.status, "revision": claim.revision,
        "ledger_posted": claim.ledger_posted, "created_at": claim.created_at,
        "decided_at": claim.decided_at, "submitter_id": claim.submitter_id,
        "attachments": linked_attachment_list("claim", claim.id),
    }


class ClaimSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [claim_view(r) for r in rows]


def _parse_amount(raw) -> Decimal:
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ApiError("INVALID_VALUE", "金额格式不正确") from exc
    if amount < Decimal("0.01") or amount > MAX_AMOUNT:
        raise ApiError("INVALID_VALUE", "金额须在 0.01~1000000 之间")
    if amount.as_tuple().exponent < -2:
        raise ApiError("INVALID_VALUE", "金额最多两位小数")
    return amount


def _parse_invoice_ids(values, *, required=False) -> list:
    if required and not values:
        raise ApiError("INVALID_VALUE", "报销须上传至少一张发票")
    if len(values) > int(count_limit("INVOICE")):
        raise ApiError("ATTACHMENT_LIMIT", "附件数量超过上限")
    parsed = []
    for raw in values:
        try:
            parsed.append(uuid.UUID(str(raw)))
        except ValueError as exc:
            raise ApiError("ATTACHMENT_LIMIT", "附件 id 不合法") from exc
    return parsed


def _flow(data: dict, scope: str) -> ApprovalFlow:
    try:
        return ApprovalFlow.objects.get(id=int(data.get("approval_flow_id")), scope=scope,
                                        is_active=True)
    except (TypeError, ValueError, ApprovalFlow.DoesNotExist) as exc:
        raise ApiError("INVALID_VALUE", "审批流程不可用") from exc


def _applicant_labels(user) -> str:
    return ",".join(CommitteeQuery.identity_labels(user.id))


class ReimbursementCreateView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        amount = _parse_amount(data.get("amount"))
        reason = str(data.get("reason", "")).strip()
        if not (1 <= len(reason) <= 500):
            raise ApiError("INVALID_VALUE", "事由须为 1~500 字符")
        occurred_on = parse_date(str(data.get("occurred_on", "")))
        if occurred_on is None:
            raise ApiError("INVALID_VALUE", "请填写费用发生日期")
        if occurred_on > date.today():
            raise ApiError("INVALID_VALUE", "发生日期不得晚于今日")
        invoice_ids = _parse_invoice_ids(data.get("invoice_ids") or [], required=True)
        flow = _flow(data, "EXPENSE")
        with transaction.atomic():
            claim = Claim.objects.create(type="REIMBURSEMENT", submitter=request.user,
                                         applicant_labels=_applicant_labels(request.user),
                                         amount=amount, reason=reason, occurred_on=occurred_on)
            AttachmentService.link(invoice_ids, linked_type="claim", linked_id=str(claim.id),
                                   purpose="INVOICE", owner=request.user)
            ApprovalEngine.submit(scope="EXPENSE", subject_type="claim", subject_id=claim.id,
                                  flow_id=flow.id, submitter=request.user)
        return Response(claim_view(claim), status=status.HTTP_201_CREATED)


class AdvanceCreateView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        amount = _parse_amount(data.get("amount"))
        reason = str(data.get("reason", "")).strip()
        if not (1 <= len(reason) <= 500):
            raise ApiError("INVALID_VALUE", "事由须为 1~500 字符")
        expected_usage = str(data.get("expected_usage", "")).strip()
        if not (1 <= len(expected_usage) <= 200):
            raise ApiError("INVALID_VALUE", "资金用途须为 1~200 字符")
        expected_settle_on = parse_date(str(data.get("expected_settle_on", "")))
        if expected_settle_on is None or expected_settle_on <= date.today():
            raise ApiError("INVALID_VALUE", "预计核销日期须晚于今日")
        flow = _flow(data, "EXPENSE")
        with transaction.atomic():
            claim = Claim.objects.create(type="ADVANCE", submitter=request.user,
                                         applicant_labels=_applicant_labels(request.user),
                                         amount=amount, reason=reason,
                                         expected_usage=expected_usage,
                                         expected_settle_on=expected_settle_on)
            ApprovalEngine.submit(scope="EXPENSE", subject_type="claim", subject_id=claim.id,
                                  flow_id=flow.id, submitter=request.user)
        return Response(claim_view(claim), status=status.HTTP_201_CREATED)


class SettlementCreateView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request):
        data = request.data or {}
        reason = str(data.get("reason", "")).strip()
        flow = _flow(data, "EXPENSE")
        try:
            advance_id = int(data["advance_id"])
        except (KeyError, TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "缺少 advance_id") from None
        reimbursement_ids = data.get("reimbursement_ids") or []
        if not isinstance(reimbursement_ids, list) or not (1 <= len(reimbursement_ids) <= 50):
            raise ApiError("INVALID_VALUE", "reimbursement_ids 须为 1~50 个")
        with transaction.atomic():
            advance = Claim.objects.filter(id=advance_id, type="ADVANCE",
                                           status="APPROVED").first()
            if advance is None:
                raise ApiError("INVALID_VALUE", "借款不存在或未通过审批")
            if advance.settlement_id is not None:
                raise ApiError("SETTLED", "该借款已结算", 409)
            reimbursements = list(Claim.objects.filter(id__in=reimbursement_ids,
                                                       type="REIMBURSEMENT",
                                                       status="APPROVED"))
            if len(reimbursements) != len(set(reimbursement_ids)):
                raise ApiError("INVALID_VALUE", "存在无效或重复的报销单")
            if any(r.settlement_id is not None for r in reimbursements):
                raise ApiError("SETTLED", "部分报销单已结算", 409)
            total_reimburse = sum((r.amount for r in reimbursements), Decimal("0.00"))
            amount = total_reimburse - advance.amount
            if amount < 0:
                raise ApiError("INVALID_VALUE", "报销总额不得低于借款金额")
            settlement = Claim.objects.create(type="SETTLEMENT", submitter=request.user,
                                              applicant_labels=_applicant_labels(request.user),
                                              amount=amount, reason=reason,
                                              advance_id=advance_id)
            advance.settlement_id = settlement.id
            advance.save(update_fields=["settlement_id", "updated_at"])
            Claim.objects.filter(id__in=[r.id for r in reimbursements]).update(
                settlement_id=settlement.id)
            ApprovalEngine.submit(scope="EXPENSE", subject_type="claim", subject_id=settlement.id,
                                  flow_id=flow.id, submitter=request.user)
        return Response(claim_view(settlement), status=status.HTTP_201_CREATED)


class ClaimListView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        qs = Claim.objects.select_related("submitter").order_by("-created_at")
        scope = request.query_params.get("scope", "mine")
        if scope == "mine":
            qs = qs.filter(submitter=request.user)
        elif scope == "todo":
            qs = _todo_qs(request.user)
        else:
            raise ApiError("INVALID_VALUE", "scope 不合法")
        for param in ("type", "status"):
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{param: value})
        return page_response(qs, request, ClaimSerializer)


def _todo_qs(user):
    from apps.approval.services import ApprovalEngine

    ids = ApprovalEngine.pending_subject_ids("claim", user.id)
    return Claim.objects.filter(id__in=ids)


class ClaimDetailView(APIView):
    permission_classes = [IsMember]

    def get(self, request, claim_id: int):
        claim = Claim.objects.filter(id=claim_id).first()
        if claim is None:
            raise ApiError("NOT_FOUND", "申请不存在", 404)
        if claim.submitter_id == request.user.id:
            return Response(claim_view(claim))
        from apps.approval.services import ApprovalEngine

        instance = ApprovalEngine.pending_instance("claim", claim.id)
        approver_ids = (instance.flow_snapshot.get("approver_ids") or []) if instance else []
        if request.user.id in approver_ids:
            return Response(claim_view(claim))
        if CommitteeQuery.is_member(request.user.id):
            return Response(claim_view(claim))
        raise ApiError("FORBIDDEN", "无权查看", 403)


class ClaimWithdrawView(APIView):
    permission_classes = [IsMember]

    def post(self, request, claim_id: int):
        claim = Claim.objects.filter(id=claim_id, submitter=request.user).first()
        if claim is None:
            raise ApiError("NOT_FOUND", "申请不存在或非本人提交", 404)
        if claim.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该申请已处理", 409)
        instance = ApprovalEngine.pending_instance("claim", claim.id)
        if instance is None:
            raise ApiError("NOT_FOUND", "审批实例不存在", 404)
        ApprovalEngine.withdraw(instance.id, request.user)
        claim.refresh_from_db()
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="CLAIM_WITHDRAWN", object_type="claim",
                            object_id=str(claim.id), result="SUCCESS")
        return Response(claim_view(claim))


class ClaimResubmitView(APIView):
    permission_classes = [IsMember]

    def post(self, request, claim_id: int):
        claim = Claim.objects.filter(id=claim_id, submitter=request.user).first()
        if claim is None:
            raise ApiError("NOT_FOUND", "申请不存在或非本人提交", 404)
        if claim.status not in {"REJECTED", "WITHDRAWN"}:
            raise ApiError("NOT_RESUBMITTABLE", "当前状态不可重新提交", 409)
        data = request.data or {}
        amount = _parse_amount(data.get("amount", claim.amount))
        reason = str(data.get("reason", claim.reason)).strip()
        if not (1 <= len(reason) <= 500):
            raise ApiError("INVALID_VALUE", "事由须为 1~500 字符")
        invoice_ids = _parse_invoice_ids(data.get("invoice_ids") or [])
        flow = _flow(data, "EXPENSE")
        with transaction.atomic():
            claim.amount = amount
            claim.reason = reason
            claim.status = "PENDING"
            claim.decided_at = None
            claim.revision += 1
            claim.save()
            if invoice_ids:
                AttachmentService.link(invoice_ids, linked_type="claim", linked_id=str(claim.id),
                                       purpose="INVOICE", owner=request.user)
            ApprovalEngine.resubmit(scope="EXPENSE", subject_type="claim", subject_id=claim.id,
                                    flow_id=flow.id, submitter=request.user, revision=claim.revision)
        return Response(claim_view(claim))


class AdminClaimListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Claim.objects.select_related("submitter").order_by("-created_at")
        for param in ("type", "status"):
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{param: value})
        return page_response(qs, request, ClaimSerializer)
