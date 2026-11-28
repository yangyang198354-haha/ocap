"""台账服务（IFC-111~114、IFC-409/413/417）：追加式入账、作废留痕、账户余额、链式报表生成。"""
from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError

from .models import LedgerAccount, LedgerEntry, LedgerReport

DEFAULT_ACCOUNT_NAME = "第四届业主委员会基本账户"


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


def _aggregate(start: date, end: date, account: LedgerAccount | None = None) -> tuple[Decimal, Decimal, list]:
    """期间内有效流水合计与明细（ADR-180：账户筛选时附加 account 条件）。"""
    entries = LedgerEntry.objects.filter(status="ACTIVE", occurred_on__gte=start,
                                         occurred_on__lte=end)
    if account is not None:
        entries = entries.filter(account=account)
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")
    detail = []
    for entry in entries.order_by("occurred_on", "id"):
        detail.append({"direction": entry.direction, "occurred_on": str(entry.occurred_on),
                       "entry_type": entry.entry_type, "summary": entry.summary,
                       "amount": str(entry.amount), "source_type": entry.source_type,
                       "source_id": entry.source_id, "seq": entry.seq})
        if entry.direction == "INCOME":
            total_income += entry.amount
        else:
            total_expense += entry.amount
    return total_income, total_expense, detail


def _opening_balance(start: date, account: LedgerAccount | None = None) -> Decimal:
    """期初 = 期间开始日之前的有效流水累计（Q-FA-02：无初始结存，最早期间为 0）。"""
    entries = LedgerEntry.objects.filter(status="ACTIVE", occurred_on__lt=start)
    if account is not None:
        entries = entries.filter(account=account)
    agg = entries.aggregate(income=Sum("amount", filter=Q(direction="INCOME")),
                            expense=Sum("amount", filter=Q(direction="EXPENSE")))
    return (agg["income"] or Decimal("0.00")) - (agg["expense"] or Decimal("0.00"))


def _totals_by_period(reports, account: LedgerAccount) -> dict[int, tuple[Decimal, Decimal, Decimal, Decimal]]:
    """IFC-418：一次台账扫描按报表周期分桶，返回 {report.id: (收入, 支出, 期初结余, 期末结余)}（ADR-187）。

    期初/期末按账户累计口径计算，供报表列表展示“结余=期末余额”。
    """
    reports = list(reports)
    if not reports:
        return {}
    ranges = {report.id: _period_range(report.period_type, report.year, report.quarter)
              for report in reports}
    start = min(item[0] for item in ranges.values())
    end = max(item[1] for item in ranges.values())
    base = _opening_balance(start, account)
    dates = []
    income_prefix = [Decimal("0.00")]
    expense_prefix = [Decimal("0.00")]
    entries = (LedgerEntry.objects.filter(status="ACTIVE", account=account, occurred_on__gte=start,
                                          occurred_on__lte=end)
               .order_by("occurred_on", "id")
               .values_list("occurred_on", "direction", "amount"))
    for occurred_on, direction, amount in entries.iterator():
        dates.append(occurred_on)
        income_prefix.append(income_prefix[-1] + (amount if direction == "INCOME" else Decimal("0.00")))
        expense_prefix.append(expense_prefix[-1] + (amount if direction == "EXPENSE" else Decimal("0.00")))
    totals = {}
    for report_id, (period_start, period_end) in ranges.items():
        lo = bisect_left(dates, period_start)
        hi = bisect_right(dates, period_end)
        income = income_prefix[hi] - income_prefix[lo]
        expense = expense_prefix[hi] - expense_prefix[lo]
        opening = base + (income_prefix[lo] - income_prefix[0]) - (expense_prefix[lo] - expense_prefix[0])
        totals[report_id] = (income, expense, opening, opening + income - expense)
    return totals


class AccountService:
    """账户解析、余额与最近流水（MOD-192 / REQ-FUNC-336/337/341）。"""

    @staticmethod
    def default_account() -> LedgerAccount:
        account = LedgerAccount.objects.filter(is_default=True).order_by("id").first()
        if account is not None:
            return account
        account = LedgerAccount.objects.filter(name=DEFAULT_ACCOUNT_NAME).order_by("id").first()
        if account is not None:
            return account
        account = LedgerAccount.objects.create(name=DEFAULT_ACCOUNT_NAME, is_default=True)
        return account

    @staticmethod
    def resolve_account(account_id) -> LedgerAccount:
        """单据指定的账户；不存在或停用 → ACCOUNT_UNAVAILABLE（AC-328-04）。"""
        if account_id in (None, ""):
            return AccountService.default_account()
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "account_id 不合法") from None
        account = LedgerAccount.objects.filter(id=account_id).first()
        if account is None or account.status != "ENABLED":
            raise ApiError("ACCOUNT_UNAVAILABLE", "账户不可用", 409)
        return account

    @staticmethod
    def balance(account: LedgerAccount) -> Decimal:
        agg = LedgerEntry.objects.filter(account=account, status="ACTIVE").aggregate(
            income=Sum("amount", filter=Q(direction="INCOME")),
            expense=Sum("amount", filter=Q(direction="EXPENSE")))
        return (agg["income"] or Decimal("0.00")) - (agg["expense"] or Decimal("0.00"))

    @staticmethod
    def recent_entries(account: LedgerAccount, limit: int = 10) -> list[LedgerEntry]:
        if limit <= 0:
            return []
        return list(LedgerEntry.objects.filter(account=account, status="ACTIVE")
                    .order_by("-occurred_on", "-id")[:limit])

    @staticmethod
    def summary(*, status: str | None = None, recent: int = 10) -> dict:
        qs = LedgerAccount.objects.all()
        if status == "ENABLED":
            qs = qs.filter(status="ENABLED")
        accounts = []
        for account in qs:
            accounts.append({
                "id": account.id, "name": account.name,
                "account_no": account.account_no or "",
                "status": account.status, "is_default": account.is_default,
                "balance": AccountService.balance(account),
                "recent_entries": AccountService.recent_entries(account, recent),
            })
        total = sum((row["balance"] for row in accounts), Decimal("0.00"))
        return {"total_balance": total, "accounts": accounts}


class LedgerService:
    @staticmethod
    @transaction.atomic
    def post(*, direction, amount, occurred_on, entry_type, summary=None,
             source_type, source_id, seq=0, allow_negative=False,
             account: LedgerAccount | None = None) -> LedgerEntry:
        """写入或覆盖一条台账明细（同一 source 多次 post 会覆盖，不作废旧明细）。
        allow_negative 仅供备用金核销差额使用（多退为负，REQ-FUNC-058）。
        account 为空时归入默认账户；指定账户须存在且启用（IFC-417）。"""
        if direction not in {"INCOME", "EXPENSE"}:
            raise ApiError("INVALID_VALUE", "direction 不合法")
        if amount is None or amount == 0 or (amount < 0 and not allow_negative):
            raise ApiError("INVALID_VALUE", "金额须为正数")
        if account is None or account.status != "ENABLED":
            account = AccountService.resolve_account(getattr(account, "id", None))
        entry, _ = LedgerEntry.objects.update_or_create(
            source_type=source_type, source_id=source_id, seq=seq,
            defaults={"account": account, "direction": direction, "amount": amount,
                      "occurred_on": occurred_on, "entry_type": entry_type,
                      "summary": summary, "status": "ACTIVE"},
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
        """把覆盖期间及之后的已生成报表标记为过期（ADR-180：后续期间期初需重算）。"""
        for report in LedgerReport.objects.all().only("period_type", "year", "quarter", "stale"):
            _, end = _period_range(report.period_type, report.year, report.quarter)
            if end >= occurred_on and not report.stale:
                LedgerReport.objects.filter(id=report.id).update(stale=True)

    @staticmethod
    def _regenerate_after(report: LedgerReport) -> list[LedgerReport]:
        """重算受影响的既有报表（legacy=False），按期间起点升序，保证链式期初/期末一致。"""
        start, _ = _period_range(report.period_type, report.year, report.quarter)
        targets = []
        for row in LedgerReport.objects.filter(legacy=False).exclude(id=report.id):
            row_start, row_end = _period_range(row.period_type, row.year, row.quarter)
            if row_end >= start:
                targets.append((row_start, row_end, row))
        targets.sort(key=lambda item: (item[0], item[1]))
        regenerated = []
        for row_start, row_end, row in targets:
            total_income, total_expense, detail = _aggregate(row_start, row_end)
            opening = _opening_balance(row_start)
            LedgerReport.objects.filter(id=row.id).update(
                total_income=total_income, total_expense=total_expense,
                balance=total_income - total_expense, detail=detail,
                opening_balance=opening, closing_balance=opening + total_income - total_expense,
                stale=False, generated_at=timezone.now())
            row.refresh_from_db()
            regenerated.append(row)
        return regenerated

    @staticmethod
    def generate(*, period_type, year, quarter=None,
                 generated_by_type="MEMBER", generated_by_id=None) -> LedgerReport:
        """按 period_type/year/quarter 生成或覆盖全组织口径报表；历史由审计与原 LedgerEntry 留痕。
        期初=期间前累计、期末=期初+收入−支出；生成后级联重算受影响的后续报表（ADR-180）。"""
        start, end = _period_range(period_type, year, quarter)
        if start > date.today():
            raise ApiError("PERIOD_NOT_STARTED", "该周期尚未开始", 409)
        total_income, total_expense, detail = _aggregate(start, end)
        opening = _opening_balance(start)
        with transaction.atomic():
            report, created = LedgerReport.objects.update_or_create(
                period_type=period_type, year=year, quarter=quarter,
                defaults={"total_income": total_income, "total_expense": total_expense,
                          "balance": total_income - total_expense,
                          "opening_balance": opening,
                          "closing_balance": opening + total_income - total_expense,
                          "legacy": False, "detail": detail,
                          "stale": False, "generated_by_type": generated_by_type,
                          "generated_by_id": generated_by_id},
            )
            LedgerReport.objects.filter(id=report.id).update(generated_at=timezone.now())
            report.refresh_from_db()
            LedgerService._regenerate_after(report)
        AuditService.record(actor=AuditActor(generated_by_type, generated_by_id or 0,
                                             f"{generated_by_type}:{generated_by_id}"),
                            action="REPORT_GENERATED", object_type="ledger_report",
                            object_id=str(report.id), result="SUCCESS",
                            detail={"period_type": period_type, "year": year,
                                    "quarter": quarter, "created": created})
        return report

    @staticmethod
    def generate_due(today: date | None = None) -> list[LedgerReport]:
        """自动生成已结束周期的报表（REQ-FUNC-050，幂等）：
        上一个已结束的季度、上一个已结束的年度；尚无报表或报表已过期（stale）才重算。"""
        today = today or date.today()
        prev_year = today.year - 1
        if today.month <= 3:
            quarter_year, quarter = prev_year, 4
        else:
            quarter_year, quarter = today.year, (today.month - 1) // 3
        targets = [("QUARTER", quarter_year, quarter), ("YEAR", prev_year, None)]
        reports = []
        for period_type, year, q in targets:
            existing = LedgerReport.objects.filter(period_type=period_type, year=year,
                                                   quarter=q).first()
            if existing is not None and not existing.stale:
                continue
            reports.append(LedgerService.generate(period_type=period_type, year=year, quarter=q,
                                                  generated_by_type="SYSTEM"))
        return reports
