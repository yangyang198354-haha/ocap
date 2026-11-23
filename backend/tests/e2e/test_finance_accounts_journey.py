"""账户 + 链式报表端到端旅程（GROUP_D，PHASE_09，critical path 替代口径：多步 API 旅程）。

溯源：US-322/323/324/325/326/328/329/330。
US-327（存量流水迁入默认账户）依赖真实迁移；测试设置以模型直建表、不执行迁移，
故标 NOT_TESTABLE，列入人工验证清单。
"""
from datetime import date
from decimal import Decimal

from apps.approval.models import ApprovalInstance
from apps.ledger.models import LedgerAccount, LedgerEntry, LedgerReport
from apps.ledger.services import AccountService
from tests.support import ApiTestBase


class FinanceAccountJourneyTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.admin, self.admin_token = self.make_admin()
        self.flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])

    def test_account_report_journey(self):
        """TC-E2E-1401：建账户 → 录入并生效 → 余额/最近流水 → 生成链式报表 → 作废 → 级联重算 → 停用。"""
        # 1. 管理员创建账户（US-325 / AC-404-01）
        created = self.api("post", "/admin/ledger/accounts",
                           {"name": "停车费专户", "account_no": "PARK-001"}, token=self.admin_token)
        self.assert_ok(created, 201)
        account_id = created.data["id"]
        self.assertEqual(created.data["balance"], "0.00")

        # 2. 录入收入表并按所选账户生效（US-328 / AC-407-01、02）
        sheet = self.api("post", "/admin/income/sheets",
                         {"records": [{"日期": "2025-02-01", "金额": "100.00",
                                      "收入类别": "停车费", "来源说明": "2 月停车费"}],
                          "account_id": account_id}, token=self.clerk_token)
        self.assert_ok(sheet, 201)
        sheet_id = sheet.data["id"]
        self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                 {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        instance = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet_id)
        self.api("post", f"/approval/instances/{instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        entry = LedgerEntry.objects.get(source_type="income_record", amount=Decimal("100.00"))
        self.assertEqual(entry.account_id, account_id)

        # 3. 账户汇总：余额、最近流水、合计（US-326/329/330）
        summary = self.api("get", "/ledger/accounts/summary", token=self.clerk_token)
        self.assert_ok(summary)
        row = [r for r in summary.data["accounts"] if r["id"] == account_id][0]
        self.assertEqual(row["balance"], "100.00")
        self.assertEqual(len(row["recent_entries"]), 1)
        self.assertEqual(row["recent_entries"][0]["occurred_on"], "2025-02-01")

        # 4. 生成 Q1/Q2/年度报表，验证链式期初期末（US-324 / AC-403-01~03）
        for quarter in (1, 2):
            resp = self.api("post", "/ledger/reports/generate",
                            {"period_type": "QUARTER", "year": 2025, "quarter": quarter},
                            token=self.clerk_token)
            self.assert_ok(resp, 201)
        year = self.api("post", "/ledger/reports/generate",
                        {"period_type": "YEAR", "year": 2025}, token=self.clerk_token)
        self.assert_ok(year, 201)
        q1 = LedgerReport.objects.get(period_type="QUARTER", year=2025, quarter=1)
        q2 = LedgerReport.objects.get(period_type="QUARTER", year=2025, quarter=2)
        self.assertEqual(q1.opening_balance, Decimal("0.00"))
        self.assertEqual(q1.closing_balance, Decimal("100.00"))
        self.assertEqual(q2.opening_balance, q1.closing_balance)
        self.assertEqual(year.data["closing_balance"], str(q2.closing_balance))

        # 5. 过滤与详情（US-322 / AC-401-01、US-323 / AC-402-05）
        yearly = self.api("get", "/ledger/reports?period_type=YEAR", token=self.clerk_token)
        self.assert_ok(yearly)
        self.assertEqual(yearly.data["count"], 1)
        report_id = q2.id
        view = self.api("get", f"/ledger/reports/{report_id}?account_id={account_id}",
                        token=self.clerk_token)
        self.assert_ok(view)
        self.assertEqual(view.data["closing_balance"], "100.00")

        # 6. 作废收入表 → 报表过期 → 重新生成 → 级联后续期间（US-324 / AC-403-05）
        voided = self.api("post", f"/admin/income/sheets/{sheet_id}/void", token=self.approver_token)
        self.assert_ok(voided)
        self.assertTrue(LedgerReport.objects.filter(stale=True).count() >= 1)
        regen = self.api("post", "/ledger/reports/generate",
                         {"period_type": "QUARTER", "year": 2025, "quarter": 1},
                         token=self.clerk_token)
        self.assert_ok(regen, 201)
        q1.refresh_from_db()
        q2.refresh_from_db()
        self.assertEqual(q1.closing_balance, Decimal("0.00"))
        self.assertEqual(q2.opening_balance, Decimal("0.00"))
        self.assertEqual(q2.closing_balance, Decimal("0.00"))
        self.assertFalse(q2.stale)

        # 7. 停用账户：启用账户汇总不再包含，历史余额仍可查（AC-405-01、Q-FA-04）
        disabled = self.api("patch", f"/admin/ledger/accounts/{account_id}",
                            {"status": "DISABLED"}, token=self.admin_token)
        self.assert_ok(disabled)
        enabled = self.api("get", "/ledger/accounts/summary?status=ENABLED", token=self.clerk_token)
        self.assert_ok(enabled)
        self.assertNotIn(account_id, [r["id"] for r in enabled.data["accounts"]])
        self.assertEqual(AccountService.balance(LedgerAccount.objects.get(id=account_id)),
                         Decimal("0.00"))
