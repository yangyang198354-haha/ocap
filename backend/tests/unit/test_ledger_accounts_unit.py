"""账户余额与报表链式口径单元测试（GROUP_D，PHASE_07）。

溯源：US-322/324/325/326/327/328、US-330 的 AC-401/403/404/405/406/407/409。
本层只测服务与模型，不经过 HTTP。
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.core.errors import ApiError
from apps.ledger.models import LedgerAccount, LedgerEntry, LedgerReport
from apps.ledger.services import AccountService, LedgerService


def _post(direction, amount, occurred_on, source_id, account=None, summary="测试"):
    return LedgerService.post(direction=direction, amount=Decimal(amount),
                              occurred_on=occurred_on, entry_type="TEST", summary=summary,
                              source_type="unit_test", source_id=source_id, account=account)


class AccountServiceTests(TestCase):
    def test_balance_only_counts_active_entries(self):
        """TC-UNIT-1401 / AC-405-01、AC-405-02：余额 = 有效收入 − 有效支出。"""
        account = AccountService.default_account()
        _post("INCOME", "100.00", date(2025, 1, 5), 1, account=account)
        _post("EXPENSE", "30.00", date(2025, 1, 6), 2, account=account)
        voided = _post("EXPENSE", "999.00", date(2025, 1, 7), 3, account=account)
        LedgerEntry.objects.filter(id=voided.id).update(status="VOIDED")
        self.assertEqual(AccountService.balance(account), Decimal("70.00"))

    def test_recent_entries_order_limit_and_status(self):
        """TC-UNIT-1402 / AC-409-03、AC-409-04、AC-409-05：仅 ACTIVE，日期倒序、同日 id 倒序，最多 10 条。"""
        account = AccountService.default_account()
        ids = []
        for i in range(12):
            entry = _post("INCOME", "1.00", date(2025, 2, 1), 100 + i, account=account)
            ids.append(entry.id)
        voided = _post("INCOME", "9.00", date(2025, 3, 1), 999, account=account)
        LedgerEntry.objects.filter(id=voided.id).update(status="VOIDED")
        rows = AccountService.recent_entries(account, 10)
        self.assertEqual(len(rows), 10)
        self.assertNotIn(voided.id, [r.id for r in rows])
        self.assertEqual([r.id for r in rows][0], ids[-1])
        self.assertEqual([r.id for r in rows][1], ids[-2])
        self.assertEqual(rows[0].occurred_on, date(2025, 2, 1))

    def test_default_account_and_implicit_assignment(self):
        """TC-UNIT-1403 / AC-406-01、AC-406-02、AC-407-01：默认账户存在，未指定账户的写入归入默认账户。"""
        default = AccountService.default_account()
        self.assertTrue(default.is_default)
        entry = LedgerEntry.objects.create(direction="INCOME", amount=Decimal("5.00"),
                                           occurred_on=date(2025, 4, 1), entry_type="TEST",
                                           source_type="unit_test", source_id=9001)
        self.assertEqual(entry.account_id, default.id)

    def test_resolve_account_rejects_disabled_or_missing(self):
        """TC-UNIT-1406 / AC-407-04：账户不存在或停用 → ACCOUNT_UNAVAILABLE。"""
        with self.assertRaises(ApiError) as missing:
            AccountService.resolve_account(10 ** 6)
        self.assertEqual(missing.exception.code, "ACCOUNT_UNAVAILABLE")
        account = LedgerAccount.objects.create(name="停用账户", status="DISABLED")
        with self.assertRaises(ApiError) as disabled:
            AccountService.resolve_account(account.id)
        self.assertEqual(disabled.exception.code, "ACCOUNT_UNAVAILABLE")


class ReportChainTests(TestCase):
    def setUp(self):
        self.account = AccountService.default_account()

    def test_quarter_and_year_chain(self):
        """TC-UNIT-1404 / AC-403-01、AC-403-02、AC-403-03、AC-403-06：期初=期间前累计，期末=期初+收支，年度对齐季度。"""
        _post("INCOME", "100.00", date(2025, 2, 1), 1, account=self.account)
        q1 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=1)
        q2 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)
        self.assertEqual(q1.opening_balance, Decimal("0.00"))
        self.assertEqual(q1.closing_balance, Decimal("100.00"))
        self.assertEqual(q2.opening_balance, q1.closing_balance)

        _post("EXPENSE", "20.00", date(2025, 5, 10), 2, account=self.account)
        q2 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)
        q3 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=3)
        q4 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=4)
        year = LedgerService.generate(period_type="YEAR", year=2025)
        self.assertEqual(q2.opening_balance, Decimal("100.00"))
        self.assertEqual(q2.closing_balance, Decimal("80.00"))
        self.assertEqual(q3.opening_balance, q2.closing_balance)
        self.assertEqual(q4.opening_balance, q3.closing_balance)
        self.assertEqual(year.opening_balance, q1.opening_balance)
        self.assertEqual(year.closing_balance, q4.closing_balance)
        self.assertEqual(year.closing_balance - year.opening_balance,
                         year.total_income - year.total_expense)

    def test_void_marks_later_periods_and_cascade(self):
        """TC-UNIT-1405 / AC-403-05：作废/补录波及覆盖期间及之后，重算目标期间后级联刷新后续期间。"""
        _post("INCOME", "100.00", date(2025, 2, 1), 1, account=self.account)
        LedgerService.generate(period_type="QUARTER", year=2025, quarter=1)
        LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)
        LedgerService.generate(period_type="QUARTER", year=2025, quarter=3)

        _post("EXPENSE", "20.00", date(2025, 4, 10), 2, account=self.account)
        stale = set(LedgerReport.objects.filter(stale=True).values_list("quarter", flat=True))
        self.assertEqual(stale, {2, 3})

        q2 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)
        q3 = LedgerReport.objects.get(period_type="QUARTER", year=2025, quarter=3)
        self.assertEqual(q2.closing_balance, Decimal("80.00"))
        self.assertEqual(q3.opening_balance, q2.closing_balance)
        self.assertEqual(q3.closing_balance, Decimal("80.00"))
        self.assertFalse(q3.stale)

    def test_legacy_report_has_null_open_close(self):
        """TC-UNIT-1407 / AC-403-06：旧口径报表不写期初期末。"""
        report = LedgerReport.objects.create(period_type="QUARTER", year=2024, quarter=1,
                                             total_income=Decimal("1.00"),
                                             total_expense=Decimal("0.00"),
                                             balance=Decimal("1.00"), legacy=True)
        self.assertIsNone(report.opening_balance)
        self.assertIsNone(report.closing_balance)
