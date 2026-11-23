"""台账视图（IFC-110~112）。"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.config import SystemConfig
from apps.core.errors import ApiError
from apps.core.money import money
from apps.core.permissions import IsCommitteeMember, IsIncomeMember, IsMember
from apps.core.serializers import page_response

from . import historical
from .models import HistoricalExpenseBatch, LedgerReport
from .services import LedgerService


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
        return page_response(qs, request, ReportSerializer)


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
    permission_classes = [IsMember]

    def get(self, request, report_id: int):
        report = LedgerReport.objects.filter(id=report_id).first()
        if report is None:
            raise ApiError("NOT_FOUND", "台账不存在", 404)
        return Response(report_detail(report))


class ReportSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [report_summary(r) for r in rows]


def _batch_view(batch: HistoricalExpenseBatch) -> dict:
    return {
        "id": batch.id, "file_name": batch.file_name,
        "imported_by": batch.imported_by_id,
        "imported_by_label": getattr(batch.imported_by, "nickname", "") or f"用户#{batch.imported_by_id}",
        "status": batch.status, "total_rows": batch.total_rows,
        "imported_rows": batch.imported_rows, "skipped_rows": batch.skipped_rows,
        "failed_rows": batch.failed_rows, "total_amount": money(batch.total_amount),
        "created_at": batch.created_at, "voided_at": batch.voided_at, "void_reason": batch.void_reason,
    }


def _row_view(row) -> dict:
    return {
        "line_no": row.line_no, "occurred_on": row.occurred_on, "amount": money(row.amount) if row.amount is not None else None,
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
        batch, errors, total_rows = historical.import_file(
            file_name=upload.name or "historical_expense", raw=upload.read(), user=request.user)
        payload = {"batch": _batch_view(batch) if batch else None, "errors": errors[:100],
                   "total_rows": total_rows}
        return Response(payload, status=status.HTTP_201_CREATED if batch else status.HTTP_200_OK)


class HistoricalExpenseBatchListView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request):
        qs = HistoricalExpenseBatch.objects.select_related("imported_by").order_by("-created_at", "-id")
        return page_response(qs, request, HistoricalExpenseBatchSerializer)


class HistoricalExpenseBatchDetailView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request, batch_id: int):
        batch = HistoricalExpenseBatch.objects.select_related("imported_by").filter(id=batch_id).first()
        if batch is None:
            raise ApiError("NOT_FOUND", "导入批次不存在", 404)
        return Response({**_batch_view(batch), "rows": [_row_view(row) for row in batch.rows.all()]})


class HistoricalExpenseBatchVoidView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, batch_id: int):
        batch = historical.void_batch(batch_id, user=request.user,
                                      reason=(request.data or {}).get("reason", ""))
        return Response({**_batch_view(batch), "rows": [_row_view(row) for row in batch.rows.all()]})


def report_summary(report: LedgerReport) -> dict:
    return {"id": report.id, "period_type": report.period_type, "year": report.year,
            "quarter": report.quarter, "total_income": money(report.total_income),
            "total_expense": money(report.total_expense), "balance": money(report.balance),
            "stale": report.stale, "generated_at": report.generated_at}


def report_detail(report: LedgerReport) -> dict:
    detail = report.detail
    # ADR-091 / ocap REQ-FUNC-050 OQ-08：报表明细默认不显示支出事由（不写回数据库）
    if not SystemConfig.get("report.show_expense_reason") and isinstance(detail, list):
        detail = [({**row, "summary": None} if isinstance(row, dict) and row.get("direction") == "EXPENSE"
                   else row) for row in detail]
    return {**report_summary(report), "detail": detail}
