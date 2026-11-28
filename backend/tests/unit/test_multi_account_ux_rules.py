"""GROUP_D 单元测试：多账户报表按账户分桶、历史支出审批中批次状态机与账户隔离去重。"""
from datetime import date
from decimal import Decimal

from apps.core.errors import ApiError
from apps.ledger import historical
from apps.ledger.models import HistoricalExpenseRow, LedgerAccount, LedgerEntry
from apps.ledger.services import AccountService, LedgerService, _totals_by_period
from tests.support import ApiTestBase

HEADER = "日期,金额,支出类别,用途/事由,备注\n"


def csv_bytes(*rows: str) -> bytes:
    return ("\ufeff" + HEADER + "".join(row + "\n" for row in rows)).encode("utf-8")


class TotalsByPeriodUnitTests(ApiTestBase):
    """TC-UNIT-2001：AC-419-01。"""

    def setUp(self):
        super().setUp()
        self.account_a = AccountService.default_account()
        self.account_b = LedgerAccount.objects.create(name="账户B")

    def _post(self, account, direction, amount, occurred_on, source_id):
        return LedgerService.post(direction=direction, amount=Decimal(amount), occurred_on=occurred_on,
                                  entry_type="测试", source_type="unit", source_id=source_id,
                                  account=account)

    def test_totals_bucketed_per_account_and_period(self):
        self._post(self.account_a, "INCOME", "100.00", date(2025, 2, 1), 1)
        self._post(self.account_a, "EXPENSE", "30.00", date(2025, 3, 1), 2)
        self._post(self.account_b, "INCOME", "200.00", date(2025, 2, 2), 3)
        self._post(self.account_b, "EXPENSE", "50.00", date(2025, 3, 2), 4)
        self._post(self.account_a, "INCOME", "10.00", date(2025, 5, 1), 5)
        voided = self._post(self.account_a, "EXPENSE", "999.00", date(2025, 2, 3), 6)
        voided.status = "VOIDED"
        voided.save(update_fields=["status"])

        q1 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=1)
        q2 = LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)

        a_totals = _totals_by_period([q1, q2], self.account_a)
        b_totals = _totals_by_period([q1, q2], self.account_b)

        self.assertEqual(a_totals[q1.id], (Decimal("100.00"), Decimal("30.00"),
                                           Decimal("0.00"), Decimal("70.00")))
        self.assertEqual(a_totals[q2.id], (Decimal("10.00"), Decimal("0.00"),
                                           Decimal("70.00"), Decimal("80.00")))
        self.assertEqual(b_totals[q1.id], (Decimal("200.00"), Decimal("50.00"),
                                           Decimal("0.00"), Decimal("150.00")))
        self.assertEqual(b_totals[q2.id], (Decimal("0.00"), Decimal("0.00"),
                                           Decimal("150.00"), Decimal("150.00")))
        self.assertEqual(_totals_by_period([], self.account_a), {})


class HistoricalBatchUnitTests(ApiTestBase):
    """TC-UNIT-2002 / 2003 / 2004：AC-416-01/03，AC-422-02。"""

    def setUp(self):
        super().setUp()
        self.account_a = AccountService.default_account()
        self.account_b = LedgerAccount.objects.create(name="账户B")
        self.submitter, _ = self.make_user()
        self.approver, _ = self.make_user()
        self.make_seat(self.approver)
        self.flow = self.make_flow(scope="INCOME", approvers=[self.approver])

    def _create(self, account, rows):
        return historical.create_pending_batch(
            file_name="历史支出.csv", raw=csv_bytes(*rows), user=self.submitter,
            account=account, flow_id=self.flow.id)

    def test_pending_batch_and_rows_without_ledger_and_account_isolated_dedupe(self):
        rows = ("2025-01-05,100.00,维修,更换灯泡,",
                "2025-01-06,200.00,保洁,楼道清洁,",
                "2025-01-05,100.00,维修,更换灯泡,")
        batch_a, errors_a, total = self._create(self.account_a, rows)

        self.assertEqual(total, 3)
        self.assertIsNotNone(batch_a)
        self.assertEqual(batch_a.status, "PENDING")
        self.assertEqual(batch_a.account_id, self.account_a.id)
        self.assertEqual(batch_a.imported_rows, 2)
        self.assertEqual(batch_a.skipped_rows, 1)
        self.assertIsNotNone(batch_a.approval_instance_id)
        self.assertEqual(HistoricalExpenseRow.objects.filter(batch=batch_a, status="PENDING").count(), 2)
        self.assertEqual(LedgerEntry.objects.filter(source_type=historical.SOURCE_TYPE,
                                                    source_id=batch_a.id).count(), 0)
        self.assertTrue(any(item["reason"] == "DUPLICATE" for item in errors_a))

        batch_b, _, _ = self._create(self.account_b, rows)
        self.assertEqual(batch_b.imported_rows, 2, "不同账户的同额同日同类同用途记录不应被判重")

    def test_approve_posts_entries_to_batch_account(self):
        batch, _, _ = self._create(self.account_a, ("2025-01-05,120.00,维修,更换灯泡,",))

        historical.on_approved(batch.id)

        batch.refresh_from_db()
        self.assertEqual(batch.status, "IMPORTED")
        self.assertIsNotNone(batch.decided_at)
        entries = LedgerEntry.objects.filter(source_type=historical.SOURCE_TYPE, source_id=batch.id)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().account_id, self.account_a.id)
        self.assertEqual(entries.first().direction, "EXPENSE")
        self.assertEqual(HistoricalExpenseRow.objects.get(batch=batch).status, "IMPORTED")
        self.assertEqual(AccountService.balance(self.account_a), Decimal("-120.00"))

    def test_reject_and_withdraw_keep_ledger_empty(self):
        rejected, _, _ = self._create(self.account_a, ("2025-01-05,10.00,维修,甲,",))
        withdrawn, _, _ = self._create(self.account_a, ("2025-01-06,20.00,维修,乙,",))

        historical.on_rejected(rejected.id)
        historical.on_withdrawn(withdrawn.id)

        rejected.refresh_from_db()
        withdrawn.refresh_from_db()
        self.assertEqual(rejected.status, "REJECTED")
        self.assertEqual(withdrawn.status, "WITHDRAWN")
        self.assertIsNotNone(rejected.decided_at)
        self.assertEqual(LedgerEntry.objects.count(), 0)
        self.assertEqual(AccountService.balance(self.account_a), Decimal("0.00"))

    def test_withdraw_batch_via_engine_and_void_guard(self):
        batch, _, _ = self._create(self.account_a, ("2025-01-05,30.00,维修,丙,",))

        with self.assertRaises(ApiError) as ctx:
            historical.void_batch(batch.id, user=self.submitter, reason="误操作")
        self.assertEqual(ctx.exception.code, "INVALID_STATE")
        self.assertEqual(ctx.exception.status_code, 409)

        result = historical.withdraw_batch(batch.id, user=self.submitter)
        self.assertEqual(result.status, "WITHDRAWN")
        self.assertEqual(LedgerEntry.objects.count(), 0)

        with self.assertRaises(ApiError) as again:
            historical.withdraw_batch(batch.id, user=self.submitter)
        self.assertEqual(again.exception.code, "INVALID_STATE")
