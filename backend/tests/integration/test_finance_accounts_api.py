"""账户与报表链式口径集成测试（GROUP_D，PHASE_08）。

溯源：US-322/324/325/326/327/328/330 的 AC-401/403/404/405/406/407/409。
覆盖真实 DRF 认证、权限、ORM 与路由，不调用外部服务。
"""
from datetime import date
from decimal import Decimal

from apps.approval.models import ApprovalInstance
from apps.claims.models import Claim
from apps.core.models import AuditLog
from apps.ledger.models import LedgerAccount, LedgerEntry, LedgerReport
from apps.ledger.services import AccountService, LedgerService
from tests.support import ApiTestBase


def _post(direction, amount, occurred_on, source_id, account):
    return LedgerService.post(direction=direction, amount=Decimal(amount),
                              occurred_on=occurred_on, entry_type="TEST", summary="集成测试",
                              source_type="int_test", source_id=source_id, account=account)


class AccountApiTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.member, _, _ = self.make_owner()
        self.member_token = self.token_of(self.member)
        self.admin, self.admin_token = self.make_admin()
        self.account = AccountService.default_account()

    def test_summary_permissions_shape_and_totals(self):
        """TC-INT-1407 / AC-405-04、AC-409-01、AC-409-02：成员可看，游客/管理员被拒；合计与账户明细结构。"""
        _post("INCOME", "120.00", date(2025, 3, 1), 1, self.account)
        _post("EXPENSE", "20.00", date(2025, 3, 2), 2, self.account)
        resp = self.api("get", "/ledger/accounts/summary", token=self.member_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["total_balance"], "100.00")
        row = resp.data["accounts"][0]
        self.assertEqual(row["balance"], "100.00")
        self.assertEqual(row["account_no"], "")
        self.assertEqual(len(row["recent_entries"]), 2)
        self.assertEqual(row["recent_entries"][0]["amount"], "20.00")

        self.assert_error(self.api("get", "/ledger/accounts/summary"), 401)
        self.assert_error(self.api("get", "/ledger/accounts/summary", token=self.admin_token),
                          403, "FORBIDDEN")

    def test_summary_enabled_filter_and_recent_zero(self):
        """TC-INT-1408 / AC-405-04、AC-409-04：status=ENABLED 过滤停用账户；recent=0 不返回明细。"""
        disabled = LedgerAccount.objects.create(name="停用账户", status="DISABLED")
        resp = self.api("get", "/ledger/accounts/summary?status=ENABLED&recent=0",
                        token=self.member_token)
        self.assert_ok(resp)
        ids = [row["id"] for row in resp.data["accounts"]]
        self.assertNotIn(disabled.id, ids)
        self.assertEqual(resp.data["accounts"][0]["recent_entries"], [])

    def test_admin_account_crud_validation_and_audit(self):
        """TC-INT-1409 / AC-404-01、AC-404-02、AC-404-04、AC-404-05：创建、唯一校验、必填校验、管理员权限。"""
        resp = self.api("post", "/admin/ledger/accounts",
                        {"name": "专项维修资金", "account_no": "ZJ-001"}, token=self.admin_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["balance"], "0.00")
        self.assertEqual(resp.data["account_no"], "ZJ-001")
        self.assertTrue(AuditLog.objects.filter(action="ACCOUNT_CREATED").exists())

        dup = self.api("post", "/admin/ledger/accounts",
                       {"name": "重复", "account_no": "ZJ-001"}, token=self.admin_token)
        self.assert_error(dup, 409, "ACCOUNT_NO_EXISTS")
        self.assert_error(self.api("post", "/admin/ledger/accounts", {"name": "", "account_no": "X"},
                                   token=self.admin_token), 400, "INVALID_VALUE")
        self.assert_error(self.api("post", "/admin/ledger/accounts",
                                   {"name": "非管理员", "account_no": "N-1"}, token=self.member_token),
                          403, "FORBIDDEN")

        listed = self.api("get", "/admin/ledger/accounts", token=self.admin_token)
        self.assert_ok(listed)
        self.assertGreaterEqual(listed.data["count"], 2)

    def test_patch_name_account_no_status_and_default_transfer(self):
        """TC-INT-1410 / AC-404-02、AC-404-03、AC-405-01：改名不动流水，默认转移唯一，停用保留历史。"""
        other = LedgerAccount.objects.create(name="账户B", account_no="B-001")
        _post("INCOME", "50.00", date(2025, 4, 1), 11, self.account)
        before = AccountService.balance(self.account)

        resp = self.api("patch", f"/admin/ledger/accounts/{other.id}",
                        {"name": "账户B改名", "is_default": True}, token=self.admin_token)
        self.assert_ok(resp)
        other.refresh_from_db()
        self.account.refresh_from_db()
        self.assertTrue(other.is_default)
        self.assertFalse(self.account.is_default)
        self.assertEqual(AccountService.balance(self.account), before)

        resp = self.api("patch", f"/admin/ledger/accounts/{other.id}",
                        {"status": "DISABLED"}, token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "DISABLED")
        self.assertEqual(LedgerEntry.objects.filter(account=self.account).count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="ACCOUNT_UPDATED").exists())


class ReportChainApiTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.member, _, _ = self.make_owner()
        self.member_token = self.token_of(self.member)
        self.account = AccountService.default_account()

    def test_report_list_filters_and_chain_fields(self):
        """TC-INT-1411 / AC-401-01、AC-401-02、AC-403-01、AC-403-06：新报表含期初期末，可按年报/季报过滤。"""
        _post("INCOME", "300.00", date(2025, 2, 1), 21, self.account)
        LedgerService.generate(period_type="QUARTER", year=2025, quarter=1)
        LedgerService.generate(period_type="YEAR", year=2025)

        years = self.api("get", "/ledger/reports?period_type=YEAR", token=self.member_token)
        self.assert_ok(years)
        self.assertEqual(years.data["count"], 1)
        self.assertEqual(years.data["results"][0]["opening_balance"], "0.00")
        self.assertEqual(years.data["results"][0]["closing_balance"], "300.00")

        quarters = self.api("get", "/ledger/reports?period_type=QUARTER", token=self.member_token)
        self.assert_ok(quarters)
        self.assertEqual(quarters.data["results"][0]["quarter"], 1)

    def test_report_detail_account_perspective(self):
        """TC-INT-1412 / AC-402-05、AC-403-03：详情默认全组织口径，带 account_id 时按账户实时计算。"""
        other = LedgerAccount.objects.create(name="账户C", account_no="C-001")
        _post("INCOME", "200.00", date(2025, 6, 1), 31, self.account)
        _post("EXPENSE", "80.00", date(2025, 6, 2), 32, other)
        report = LedgerService.generate(period_type="QUARTER", year=2025, quarter=2)

        org = self.api("get", f"/ledger/reports/{report.id}", token=self.member_token)
        self.assert_ok(org)
        self.assertEqual(org.data["total_income"], "200.00")
        self.assertEqual(org.data["closing_balance"], "120.00")

        view = self.api("get", f"/ledger/reports/{report.id}?account_id={other.id}",
                        token=self.member_token)
        self.assert_ok(view)
        self.assertEqual(view.data["total_income"], "0.00")
        self.assertEqual(view.data["total_expense"], "80.00")
        self.assertEqual(view.data["closing_balance"], "-80.00")

        missing = self.api("get", f"/ledger/reports/{report.id}?account_id=999999",
                           token=self.member_token)
        self.assert_error(missing, 404, "NOT_FOUND")

    def test_legacy_report_detail_keeps_nulls(self):
        """TC-INT-1413 / AC-403-06：旧口径报表详情不再计算期初期末。"""
        report = LedgerReport.objects.create(period_type="YEAR", year=2024,
                                             total_income=Decimal("10.00"),
                                             total_expense=Decimal("5.00"),
                                             balance=Decimal("5.00"), legacy=True)
        resp = self.api("get", f"/ledger/reports/{report.id}", token=self.member_token)
        self.assert_ok(resp)
        self.assertTrue(resp.data["legacy"])
        self.assertIsNone(resp.data["opening_balance"])
        self.assertIsNone(resp.data["closing_balance"])


class PostingAccountApiTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.account = LedgerAccount.objects.create(name="收入专户", account_no="IN-001")

    def _approve(self, subject_type: str, subject_id: int):
        instance = ApprovalInstance.objects.get(subject_type=subject_type, subject_id=subject_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(resp)

    def test_income_sheet_uses_selected_account(self):
        """TC-INT-1414 / AC-407-01、AC-407-02：收入表提交时选定账户，审批生效后流水归属该账户。"""
        flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])
        resp = self.api("post", "/admin/income/sheets",
                        {"records": [{"日期": "2025-05-01", "金额": "66.00", "收入类别": "物业费",
                                     "来源说明": "停车费"}],
                         "account_id": self.account.id}, token=self.clerk_token)
        self.assert_ok(resp, 201)
        sheet_id = resp.data["id"]
        self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                 {"approval_flow_id": flow.id}, token=self.clerk_token)
        self._approve("income_sheet", sheet_id)
        entry = LedgerEntry.objects.get(source_type="income_record", source_id__isnull=False,
                                        amount=Decimal("66.00"))
        self.assertEqual(entry.account_id, self.account.id)

    def test_income_sheet_rejects_disabled_account(self):
        """TC-INT-1415 / AC-407-04：停用账户提交返回 ACCOUNT_UNAVAILABLE。"""
        self.account.status = "DISABLED"
        self.account.save(update_fields=["status"])
        resp = self.api("post", "/admin/income/sheets",
                        {"records": [{"日期": "2025-05-01", "金额": "1.00", "收入类别": "物业费"}],
                         "account_id": self.account.id}, token=self.clerk_token)
        self.assert_error(resp, 409, "ACCOUNT_UNAVAILABLE")
        self.assertFalse(LedgerEntry.objects.exists())

    def test_advance_uses_selected_account(self):
        """TC-INT-1416 / AC-407-03：备用金申请选定账户，审批通过后支出归属该账户。"""
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])
        resp = self.api("post", "/claims/advances",
                        {"amount": "50.00", "reason": "购买清洁用品", "expected_usage": "公共区域清洁",
                         "expected_settle_on": "2099-01-01", "approval_flow_id": flow.id,
                         "account_id": self.account.id}, token=self.clerk_token)
        self.assert_ok(resp, 201)
        claim_id = resp.data["id"]
        self._approve("claim", claim_id)
        entry = LedgerEntry.objects.get(source_type="claim", source_id=claim_id)
        self.assertEqual(entry.account_id, self.account.id)
        self.assertEqual(Claim.objects.get(id=claim_id).account_id, self.account.id)
