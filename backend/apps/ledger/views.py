"""台账视图（IFC-110~112、IFC-409~414）。"""
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.errors import ApiError
from apps.core.money import money
from apps.core.permissions import IsAdmin, IsCommitteeMember, IsIncomeMember, IsMember
from apps.core.serializers import page_response

from . import historical
from .models import HistoricalExpenseBatch, LedgerAccount, LedgerReport
from .services import (AccountService, LedgerService, _aggregate, _opening_balance, _period_range,
                       _totals_by_period)


def _recent_entry_view(entry, *, show_expense_reason: bool) -> dict:
    return {"id": entry.id, "occurred_on": str(entry.occurred_on), "direction": entry.direction,
            "amount": money(entry.amount), "entry_type": entry.entry_type,
            "summary": entry.summary if entry.direction != "EXPENSE" or show_expense_reason else None}


def account_view(account: LedgerAccount) -> dict:
    return {"id": account.id, "name": account.name, "account_no": account.account_no or "",
            "status": account.status, "is_default": account.is_default,
            "balance": money(AccountService.balance(account))}


class AccountSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [account_view(row) for row in rows]


class AccountSummaryView(APIView):
    """IFC-409：全部/启用账户余额与最近流水（登录用户可查看）。"""

    permission_classes = [IsMember]

    def get(self, request):
        status = request.query_params.get("status")
        if status not in ("ENABLED", "ALL"):
            status = "ALL"
        try:
            recent = int(request.query_params.get("recent", 10))
        except (TypeError, ValueError):
            recent = 10
        recent = min(max(recent, 0), 20)
        summary = AccountService.summary(status=status, recent=recent)
        show_expense_reason = recent > 0 and bool(SystemConfig.get("report.show_expense_reason"))
        accounts = [{"id": row["id"], "name": row["name"], "account_no": row["account_no"],
                     "status": row["status"], "is_default": row["is_default"],
                     "balance": money(row["balance"]),
                     "recent_entries": [_recent_entry_view(e, show_expense_reason=show_expense_reason)
                                        for e in row["recent_entries"]]}
                    for row in summary["accounts"]]
        return Response({"total_balance": money(summary["total_balance"]), "accounts": accounts})


def _parse_name(raw) -> str:
    name = str(raw if raw is not None else "").strip()
    if not (1 <= len(name) <= 64):
        raise ApiError("INVALID_VALUE", "名称须为 1~64 字符")
    return name


def _parse_account_no(raw) -> str | None:
    value = str(raw if raw is not None else "").strip()
    if len(value) > 32:
        raise ApiError("INVALID_VALUE", "账户号最多 32 字符")
    return value or None


def _ensure_account_no_free(account_no: str | None, *, exclude_id: int | None = None) -> None:
    if account_no is None:
        return
    qs = LedgerAccount.objects.filter(account_no=account_no)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        raise ApiError("ACCOUNT_NO_EXISTS", "账户号已存在", 409)


class AdminAccountListView(APIView):
    """IFC-410/411：管理端账户列表与创建（仅管理员）。"""

    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LedgerAccount.objects.all()
        status = request.query_params.get("status")
        if status in ("ENABLED", "DISABLED"):
            qs = qs.filter(status=status)
        return page_response(qs, request, AccountSerializer)

    def post(self, request):
        data = request.data or {}
        name = _parse_name(data.get("name"))
        account_no = _parse_account_no(data.get("account_no"))
        _ensure_account_no_free(account_no)
        with transaction.atomic():
            account = LedgerAccount.objects.create(
                name=name, account_no=account_no,
                is_default=not LedgerAccount.objects.exists(),
                created_by_admin_id=request.user.id)
            AuditService.record(actor=_admin_actor(request), action="ACCOUNT_CREATED",
                                object_type="ledger_account", object_id=str(account.id),
                                result="SUCCESS",
                                detail={"after": _account_snapshot(account)})
        return Response(account_view(account), status=201)


class AdminAccountDetailView(APIView):
    """IFC-412：管理端编辑账户（名称/账户号/状态/默认），仅管理员。"""

    permission_classes = [IsAdmin]

    def patch(self, request, account_id: int):
        account = LedgerAccount.objects.filter(id=account_id).first()
        if account is None:
            raise ApiError("NOT_FOUND", "账户不存在", 404)
        data = request.data or {}
        before = _account_snapshot(account)
        updates = {}
        if "name" in data:
            updates["name"] = _parse_name(data.get("name"))
        if "account_no" in data:
            account_no = _parse_account_no(data.get("account_no"))
            _ensure_account_no_free(account_no, exclude_id=account.id)
            updates["account_no"] = account_no
        if "status" in data:
            status = str(data.get("status") or "")
            if status not in ("ENABLED", "DISABLED"):
                raise ApiError("INVALID_VALUE", "status 不合法")
            updates["status"] = status
        make_default = data.get("is_default")
        with transaction.atomic():
            if make_default is True:
                LedgerAccount.objects.exclude(id=account.id).filter(is_default=True).update(is_default=False)
                updates["is_default"] = True
            elif make_default is False:
                updates["is_default"] = False
            if updates:
                for field, value in updates.items():
                    setattr(account, field, value)
                account.save(update_fields=[*updates, "updated_at"])
            AuditService.record(actor=_admin_actor(request), action="ACCOUNT_UPDATED",
                                object_type="ledger_account", object_id=str(account.id),
                                result="SUCCESS",
                                detail={"before": before, "after": _account_snapshot(account)})
        return Response(account_view(account))


def _admin_actor(request) -> AuditActor:
    return AuditActor("ADMIN", request.user.id, getattr(request.user, "username", "") or "管理员")


def _account_snapshot(account: LedgerAccount) -> dict:
    return {"name": account.name, "account_no": account.account_no or "",
            "status": account.status, "is_default": account.is_default}


class LedgerReportListView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        qs = LedgerReport.objects.all()
        period_type = request.query_params.get("period_type")
        if period_type:
            qs = qs.filter(period_type=period_type)
        year = request.query_params.get("year")
        if year:
            qs = qs.filter(year=int(year))
        account_id = request.query_params.get("account_id")
        if account_id in (None, ""):
            return page_response(qs, request, ReportSerializer)
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "account_id 不合法") from None
        account = LedgerAccount.objects.filter(id=account_id).first()
        if account is None:
            raise ApiError("NOT_FOUND", "账户不存在", 404)
        return page_response(qs, request, ReportSerializer, account=account)


class LedgerReportGenerateView(APIView):
    # 设计要求生成限业委会成员，管理员不可（IsCommitteeMember 对管理员返回 401）。
    permission_classes = [IsCommitteeMember]

    def post(self, request):
        data = request.data or {}
        period_type = str(data.get("period_type", "")).upper()
        if period_type not in {"QUARTER", "YEAR"}:
            raise ApiError("INVALID_VALUE", "period_type 不合法")
        try:
            year = int(data["year"])
        except (KeyError, TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "year 不合法") from None
        quarter = data.get("quarter")
        if period_type == "QUARTER":
            try:
                quarter = int(quarter)
            except (TypeError, ValueError):
                raise ApiError("INVALID_VALUE", "quarter 须为 1~4") from None
        else:
            quarter = None
        report = LedgerService.generate(period_type=period_type, year=year, quarter=quarter,
                                        generated_by_type="MEMBER", generated_by_id=request.user.id)
        return Response(report_detail(report), status=201)


class LedgerReportDetailView(APIView):
    """IFC-413：报表详情；可选 account_id 查看指定账户视角（ADR-179）。"""

    permission_classes = [IsMember]

    def get(self, request, report_id: int):
        report = LedgerReport.objects.filter(id=report_id).first()
        if report is None:
            raise ApiError("NOT_FOUND", "台账不存在", 404)
        account_id = request.query_params.get("account_id")
        if account_id in (None, ""):
            return Response(report_detail(report))
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "account_id 不合法") from None
        account = LedgerAccount.objects.filter(id=account_id).first()
        if account is None:
            raise ApiError("NOT_FOUND", "账户不存在", 404)
        start, end = _period_range(report.period_type, report.year, report.quarter)
        total_income, total_expense, detail = _aggregate(start, end, account)
        opening = _opening_balance(start, account)
        return Response({**report_summary(report), "legacy": False, "account_id": account.id,
                         "total_income": money(total_income),
                         "total_expense": money(total_expense),
                         "balance": money(total_income - total_expense),
                         "opening_balance": money(opening),
                         "closing_balance": money(opening + total_income - total_expense),
                         "detail": _mask_expense_reason(detail)})


class ReportSerializer:
    """IFC-418：传入 account 时按账户实时聚合覆盖金额（ADR-187）。"""

    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        account = (context or {}).get("account")
        totals = _totals_by_period(rows, account) if account is not None else None
        if totals is None:
            self.data = [report_summary(r) for r in rows]
        else:
            self.data = [report_summary(r, total_income=totals[r.id][0],
                                        total_expense=totals[r.id][1],
                                        opening_balance=totals[r.id][2],
                                        closing_balance=totals[r.id][3], legacy=False)
                         for r in rows]


def _batch_view(batch: HistoricalExpenseBatch) -> dict:
    return {
        "id": batch.id, "file_name": batch.file_name,
        "imported_by": batch.imported_by_id,
        "imported_by_label": getattr(batch.imported_by, "nickname", "") or f"用户#{batch.imported_by_id}",
        "status": batch.status, "total_rows": batch.total_rows,
        "imported_rows": batch.imported_rows, "skipped_rows": batch.skipped_rows,
        "failed_rows": batch.failed_rows, "total_amount": money(batch.total_amount),
        "posted_rows": _posted_rows(batch),
        "account_id": batch.account_id,
        "account_name": batch.account.name if batch.account_id else None,
        "approval_instance_id": batch.approval_instance_id, "decided_at": batch.decided_at,
        "created_at": batch.created_at, "voided_at": batch.voided_at, "void_reason": batch.void_reason,
    }


def _posted_rows(batch) -> int:
    annotated = getattr(batch, "posted_rows", None)
    if annotated is not None:
        return annotated
    return batch.rows.filter(status="IMPORTED").count()


def _row_view(row) -> dict:
    return {
        "line_no": row.line_no, "occurred_on": row.occurred_on,
        "amount": money(row.amount) if row.amount is not None else None,
        "category": row.category, "purpose": row.purpose, "remark": row.remark,
        "status": row.status, "error_message": row.error_message,
    }


class HistoricalExpenseBatchSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [_batch_view(row) for row in rows]


class HistoricalExpenseTemplateView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request):
        file_type = str(request.query_params.get("file_type") or "xlsx").lower()
        content, content_type = historical.build_template(file_type)
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="historical_expense_template.{file_type}"'
        return response


class HistoricalExpenseImportView(APIView):
    permission_classes = [IsIncomeMember]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        data = request.data or {}
        account = AccountService.resolve_account(data.get("account_id"))
        flow_id = data.get("approval_flow_id")
        if flow_id in (None, ""):
            raise ApiError("INVALID_VALUE", "请选择审批流程")
        try:
            flow_id = int(flow_id)
        except (TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "审批流程不合法") from None
        batch, errors, total_rows = historical.create_pending_batch(
            file_name=upload.name or "historical_expense", raw=upload.read(), user=request.user,
            account=account, flow_id=flow_id)
        payload = {"batch": _batch_view(batch) if batch else None, "errors": errors[:100],
                   "total_rows": total_rows}
        return Response(payload, status=status.HTTP_201_CREATED if batch else status.HTTP_200_OK)


class HistoricalExpenseBatchListView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request):
        qs = (HistoricalExpenseBatch.objects.select_related("imported_by", "account")
              .annotate(posted_rows=Count("rows", filter=Q(rows__status="IMPORTED")))
              .order_by("-created_at", "-id"))
        return page_response(qs, request, HistoricalExpenseBatchSerializer)


class HistoricalExpenseBatchDetailView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request, batch_id: int):
        batch = (HistoricalExpenseBatch.objects.select_related("imported_by", "account")
                 .annotate(posted_rows=Count("rows", filter=Q(rows__status="IMPORTED")))
                 .filter(id=batch_id).first())
        if batch is None:
            raise ApiError("NOT_FOUND", "导入批次不存在", 404)
        return Response({**_batch_view(batch), "rows": [_row_view(row) for row in batch.rows.all()]})


class HistoricalExpenseBatchVoidView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, batch_id: int):
        batch = historical.void_batch(batch_id, user=request.user,
                                      reason=(request.data or {}).get("reason", ""))
        return Response({**_batch_view(batch), "rows": [_row_view(row) for row in batch.rows.all()]})


class HistoricalExpenseBatchWithdrawView(APIView):
    """IFC-428：提交人撤回审批中的历史支出导入批次。"""

    permission_classes = [IsIncomeMember]

    def post(self, request, batch_id: int):
        batch = historical.withdraw_batch(batch_id, user=request.user)
        return Response({**_batch_view(batch), "rows": [_row_view(row) for row in batch.rows.all()]})


def _nullable_money(value):
    return None if value is None else money(value)


def report_summary(report: LedgerReport, *, total_income=None, total_expense=None,
                   opening_balance=None, closing_balance=None, legacy=None) -> dict:
    income = report.total_income if total_income is None else total_income
    expense = report.total_expense if total_expense is None else total_expense
    opening = report.opening_balance if opening_balance is None else opening_balance
    closing = report.closing_balance if closing_balance is None else closing_balance
    return {"id": report.id, "period_type": report.period_type, "year": report.year,
            "quarter": report.quarter, "total_income": money(income),
            "total_expense": money(expense), "balance": money(income - expense),
            "opening_balance": _nullable_money(opening),
            "closing_balance": _nullable_money(closing),
            "legacy": report.legacy if legacy is None else legacy,
            "stale": report.stale, "generated_at": report.generated_at}


def _mask_expense_reason(detail):
    # 默认显示事由，保留显式关闭时的隐藏行为，不改写报表快照。
    if SystemConfig.get("report.show_expense_reason") or not isinstance(detail, list):
        return detail
    return [({**row, "summary": None} if isinstance(row, dict) and row.get("direction") == "EXPENSE"
             else row) for row in detail]


def report_detail(report: LedgerReport) -> dict:
    return {**report_summary(report), "detail": _mask_expense_reason(report.detail)}
