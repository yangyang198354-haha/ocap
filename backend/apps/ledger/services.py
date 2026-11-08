"""台账服务（IFC-111~114）：追加式入账、作废留痕、按周期生成报表、定时生成。"""
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError

from .models import LedgerEntry, LedgerReport


def _period_range(period_type: str, year: int, quarter: int | None = None) -> tuple[date, date]:
    if period_type == "QUARTER":
        if quarter is None or quarter not in (1, 2, 3, 4):
            raise ApiError("INVALID_VALUE", "季度须为 1~4")
        start = date(year, (quarter - 1) * 3 + 1, 1)
        end = (date(year, quarter * 3 + 1, 1) - timedelta(days=1)) if quarter < 4 \
            else date(year, 12, 31)
    elif period_type == "YEAR":
        start = date(year, 1, 1)
        end = date(year, 12, 31)
    else:
        raise ApiError("INVALID_VALUE", "period_type 不合法")
    return start, end


class LedgerService:
    @staticmethod
    @transaction.atomic
    def post(*, direction, amount, occurred_on, entry_type, summary=None,
             source_type, source_id, seq=0) -> LedgerEntry:
        """写入或覆盖一条台账明细（同一 source 多次 post 会覆盖，不作废旧明细）。"""
        if direction not in {"INCOME", "EXPENSE"}:
            raise ApiError("INVALID_VALUE", "direction 不合法")
        if amount is None or amount <= 0:
            raise ApiError("INVALID_VALUE", "金额须为正数")
        entry, _ = LedgerEntry.objects.update_or_create(
            source_type=source_type, source_id=source_id, seq=seq,
            defaults={"direction": direction, "amount": amount, "occurred_on": occurred_on,
                      "entry_type": entry_type, "summary": summary, "status": "ACTIVE"},
        )
        LedgerService._mark_reports_stale(occurred_on)
        return entry

    @staticmethod
    @transaction.atomic
    def void_by_source(source_type, source_id) -> int:
        """作废某来源下所有有效明细，留痕并标记受影响报表过期。"""
        entries = list(LedgerEntry.objects.filter(source_type=source_type, source_id=source_id,
                                                  status="ACTIVE"))
        count = LedgerEntry.objects.filter(id__in=[e.id for e in entries]).update(
            status="VOIDED", voided_at=timezone.now())
        for entry in entries:
            LedgerService._mark_reports_stale(entry.occurred_on)
        return count

    @staticmethod
    def _mark_reports_stale(occurred_on: date) -> None:
        """把覆盖 occurred_on 的已生成报表标记为过期。"""
        for report in LedgerReport.objects.all().only("period_type", "year", "quarter"):
            start, end = _period_range(report.period_type, report.year, report.quarter)
            if start <= occurred_on <= end and not report.stale:
                LedgerReport.objects.filter(id=report.id).update(stale=True)

    @staticmethod
    def generate(*, period_type, year, quarter=None,
                 generated_by_type="MEMBER", generated_by_id=None) -> LedgerReport:
        """按 period_type/year/quarter 生成或覆盖报表；历史由审计与原 LedgerEntry 留痕。"""
        start, end = _period_range(period_type, year, quarter)
        if start > date.today():
            raise ApiError("PERIOD_NOT_STARTED", "该周期尚未开始", 409)
        entries = (LedgerEntry.objects.filter(status="ACTIVE", occurred_on__gte=start,
                                              occurred_on__lte=end)
                   .order_by("occurred_on", "id"))
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        detail = []
        for entry in entries:
            detail.append({"direction": entry.direction, "occurred_on": str(entry.occurred_on),
                           "entry_type": entry.entry_type, "summary": entry.summary,
                           "amount": str(entry.amount), "source_type": entry.source_type,
                           "source_id": entry.source_id, "seq": entry.seq})
            if entry.direction == "INCOME":
                total_income += entry.amount
            else:
                total_expense += entry.amount
        with transaction.atomic():
            report, created = LedgerReport.objects.update_or_create(
                period_type=period_type, year=year, quarter=quarter,
                defaults={"total_income": total_income, "total_expense": total_expense,
                          "balance": total_income - total_expense, "detail": detail,
                          "stale": False, "generated_by_type": generated_by_type,
                          "generated_by_id": generated_by_id},
            )
            LedgerReport.objects.filter(id=report.id).update(generated_at=timezone.now())
            report.refresh_from_db()
        AuditService.record(actor=AuditActor(generated_by_type, generated_by_id or 0,
                                             f"{generated_by_type}:{generated_by_id}"),
                            action="REPORT_GENERATED", object_type="ledger_report",
                            object_id=str(report.id), result="SUCCESS",
                            detail={"period_type": period_type, "year": year,
                                    "quarter": quarter, "created": created})
        return report

    @staticmethod
    def generate_due(today: date | None = None) -> list[LedgerReport]:
        """季度末/年末自动生成报表；已生成则置 stale 后重算，标记其他覆盖周期 stale。"""
        today = today or date.today()
        reports = []
        year = today.year
        if today.month == 12 and today.day == 31:
            reports.append(LedgerService.generate(period_type="YEAR", year=year,
                                                  generated_by_type="SYSTEM"))
        if today.month in (3, 6, 9, 12) and today.day == 28:  # 用该月最后一天近似
            q = (today.month - 1) // 3 + 1
            reports.append(LedgerService.generate(period_type="QUARTER", year=year, quarter=q,
                                                  generated_by_type="SYSTEM"))
        return reports
