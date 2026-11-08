"""台账视图（IFC-110~112）。"""
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.errors import ApiError
from apps.core.money import money
from apps.core.permissions import IsCommitteeMember, IsMember
from apps.core.serializers import page_response

from .models import LedgerReport
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


def report_summary(report: LedgerReport) -> dict:
    return {"id": report.id, "period_type": report.period_type, "year": report.year,
            "quarter": report.quarter, "total_income": money(report.total_income),
            "total_expense": money(report.total_expense), "balance": money(report.balance),
            "stale": report.stale, "generated_at": report.generated_at}


def report_detail(report: LedgerReport) -> dict:
    return {**report_summary(report), "detail": report.detail}
