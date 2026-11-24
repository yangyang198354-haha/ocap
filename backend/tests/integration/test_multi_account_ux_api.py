"""PHASE_08 集成测试：多账户落账（收入导入/报销/历史支出）与报表按账户口径。

溯源：AC-411-02、AC-412-01、AC-413-02、AC-415-02、AC-416-01~04、AC-419-01、AC-420-02、AC-422-01/02。
"""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.models import Attachment
from apps.claims.models import Claim
from apps.income.models import IncomeSheet
from apps.ledger.models import HistoricalExpenseBatch, HistoricalExpenseRow, LedgerAccount, LedgerEntry
from apps.ledger.services import AccountService, LedgerService
from tests.support import ApiTestBase

HISTORY_HEADER = ["日期", "金额", "支出类别", "用途/事由", "备注"]
INCOME_HEADER = ["日期", "金额", "收入类别", "来源说明", "备注"]
HISTORY_BASE = "/admin/ledger/historical-expenses"


def income_csv(rows) -> SimpleUploadedFile:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(INCOME_HEADER)
    for row in rows:
        writer.writerow(row)
    return SimpleUploadedFile("income.csv", ("\ufeff" + buffer.getvalue()).encode("utf-8"),
                              content_type="text/csv")


def history_csv(rows) -> SimpleUploadedFile:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HISTORY_HEADER)
    for row in rows:
        writer.writerow(row)
    return SimpleUploadedFile("历史支出.csv", ("\ufeff" + buffer.getvalue()).encode("utf-8"),
                              content_type="text/csv")


def invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class MultiAccountBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, self.chair_token = self.make_user(nickname="主任")
        self.make_seat(self.chair, "CHAIR")
        self.approver, self.approver_token = self.make_user(nickname="财务委员")
        self.make_seat(self.approver, "MEMBER")
        self.income_flow = self.make_flow(scope="INCOME", approvers=[self.approver])
        self.expense_flow = self.make_flow(scope="EXPENSE", approvers=[self.approver])
        self.account_a = AccountService.default_account()
        self.account_b = LedgerAccount.objects.create(name="账户B")
        self.account_c = LedgerAccount.objects.create(name="账户C")

    def approve(self, instance_id, token=None):
        return self.assert_ok(self.api("post", f"/approval/instances/{instance_id}/decision",
                                       {"action": "APPROVE"}, token=token or self.approver_token))

    def reject(self, instance_id, comment="票据不合规"):
        return self.assert_ok(self.api("post", f"/approval/instances/{instance_id}/decision",
                                       {"action": "REJECT", "comment": comment},
                                       token=self.approver_token))


class IncomeImportAccountTests(MultiAccountBase):
    """TC-INT-2001：AC-411-02、AC-412-01。"""

    def test_import_assigns_account_and_dedupe_is_per_account(self):
        rows = [["2025-06-01", "88.00", "停车费", "临时停车", ""]]
        first = self.assert_ok(self.upload("/admin/income/sheets/import",
                                           {"file": income_csv(rows), "account_id": self.account_b.id},
                                           token=self.chair_token), 201).json()
        self.assertEqual(first["account_id"], self.account_b.id)
        self.assertEqual(first["account_name"], "账户B")
        sheet = IncomeSheet.objects.get(id=first["id"])
        self.assertEqual(sheet.account_id, self.account_b.id)

        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet.id}/submit",
                                {"approval_flow_id": self.income_flow.id}, token=self.chair_token))

        duplicate = self.assert_ok(self.upload("/admin/income/sheets/import",
                                               {"file": income_csv(rows),
                                                "account_id": self.account_b.id},
                                               token=self.chair_token)).json()
        self.assertIsNone(duplicate["sheet"], "同账户已审批中的同内容收入导入应全部跳过")
        self.assertEqual(duplicate["import_summary"]["imported"], 0)

        other = self.assert_ok(self.upload("/admin/income/sheets/import",
                                           {"file": income_csv(rows),
                                            "account_id": self.account_c.id},
                                           token=self.chair_token), 201).json()
        self.assertEqual(other["account_id"], self.account_c.id)
        self.assertEqual(other["import_summary"]["imported"], 1, "不同账户的同内容收入不应被判重")

    def test_import_rejects_disabled_or_unknown_account(self):
        disabled = LedgerAccount.objects.create(name="停用账户", status="DISABLED")
        body = self.assert_error(self.upload("/admin/income/sheets/import",
                                             {"file": income_csv(
                                                 [["2025-06-01", "8.00", "其他", "", ""]]),
                                              "account_id": disabled.id},
                                             token=self.chair_token), 409, "ACCOUNT_UNAVAILABLE")
        self.assertIn("账户", body["message"])
        self.assertEqual(IncomeSheet.objects.count(), 0)


class ClaimAccountTests(MultiAccountBase):
    """TC-INT-2002：AC-413-02。"""

    def test_reimbursement_uses_selected_account_after_approval(self):
        payload = {"amount": "300.50", "reason": "打印费",
                   "occurred_on": str(date.today() - timedelta(days=1)),
                   "invoice_ids": [str(invoice(self.chair).id)],
                   "approval_flow_id": self.expense_flow.id,
                   "account_id": self.account_b.id}
        created = self.assert_ok(self.api("post", "/claims/reimbursements", payload,
                                          token=self.chair_token), 201).json()
        self.assertEqual(created["account_id"], self.account_b.id)
        self.assertEqual(created["account_name"], "账户B")
        self.assertEqual(LedgerEntry.objects.count(), 0)

        from apps.approval.models import ApprovalInstance

        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=created["id"])
        self.approve(instance.id)

        claim = Claim.objects.get(id=created["id"])
        self.assertEqual(claim.status, "APPROVED")
        entries = LedgerEntry.objects.filter(source_type="claim", source_id=claim.id)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().account_id, self.account_b.id)
        self.assertEqual(entries.first().amount, Decimal("300.50"))
        self.assertEqual(AccountService.balance(self.account_b), Decimal("-300.50"))
        self.assertEqual(AccountService.balance(self.account_a), Decimal("0.00"))


class HistoricalAccountTests(MultiAccountBase):
    """TC-INT-2003 / 2004 / 2005：AC-415-02、AC-416-01~04、AC-422-01/02。"""

    def _import(self, rows, account=None):
        return self.upload(f"{HISTORY_BASE}/import",
                           {"file": history_csv(rows),
                            "approval_flow_id": self.income_flow.id,
                            "account_id": (account or self.account_b).id},
                           token=self.chair_token)

    def test_pending_then_approved_posts_to_selected_account_only(self):
        rows = [["2025-05-01", "100.00", "维修", "更换灯泡", ""],
                ["2025-05-02", "50.00", "保洁", "楼道清洁", ""],
                ["2025-05-01", "100.00", "维修", "更换灯泡", ""]]
        body = self.assert_ok(self._import(rows), 201).json()
        batch_id = body["batch"]["id"]
        self.assertEqual(body["batch"]["account_id"], self.account_b.id)
        self.assertEqual(body["batch"]["account_name"], "账户B")
        self.assertEqual(body["batch"]["status"], "PENDING")
        self.assertEqual(body["batch"]["posted_rows"], 0)
        self.assertEqual(HistoricalExpenseRow.objects.filter(batch_id=batch_id,
                                                             status="PENDING").count(), 2)
        self.assertEqual(LedgerEntry.objects.count(), 0, "审批通过前不得写入台账")

        self.approve(body["batch"]["approval_instance_id"])

        batch = HistoricalExpenseBatch.objects.get(id=batch_id)
        self.assertEqual(batch.status, "IMPORTED")
        self.assertIsNotNone(batch.decided_at)
        entries = LedgerEntry.objects.filter(source_type="historical_expense", source_id=batch_id)
        self.assertEqual(entries.count(), 2, "重复行不得入账")
        self.assertTrue(all(entry.account_id == self.account_b.id for entry in entries))
        self.assertEqual(AccountService.balance(self.account_b), Decimal("-150.00"))
        self.assertEqual(AccountService.balance(self.account_a), Decimal("0.00"))

        listed = self.assert_ok(self.api("get", f"{HISTORY_BASE}/batches",
                                         token=self.chair_token)).json()
        row = next(item for item in listed["results"] if item["id"] == batch_id)
        self.assertEqual(row["posted_rows"], 2)
        self.assertEqual(row["account_name"], "账户B")

    def test_reject_then_reimport_creates_new_batch_and_withdraw_blocks_ledger(self):
        rows = [["2025-07-01", "66.00", "维修", "门禁维修", ""]]
        first = self.assert_ok(self._import(rows), 201).json()["batch"]

        self.reject(first["approval_instance_id"])

        rejected = self.assert_ok(self.api("get", f"{HISTORY_BASE}/batches/{first['id']}",
                                           token=self.chair_token)).json()
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["posted_rows"], 0)
        self.assertEqual(LedgerEntry.objects.count(), 0)

        second = self.assert_ok(self._import(rows), 201).json()["batch"]
        self.assertNotEqual(second["id"], first["id"])
        self.assertEqual(second["status"], "PENDING")
        HistoricalExpenseBatch.objects.get(id=first["id"])
        self.assertEqual(HistoricalExpenseBatch.objects.get(id=first["id"]).status, "REJECTED")

        self.approve(second["approval_instance_id"])
        entries = LedgerEntry.objects.filter(source_type="historical_expense",
                                             source_id=second["id"])
        self.assertEqual(entries.count(), 1, "仅新批次入账")
        self.assertEqual(HistoricalExpenseRow.objects.filter(batch_id=first["id"],
                                                             status="IMPORTED").count(), 0)

        third_rows = [["2025-07-02", "77.00", "维修", "门锁更换", ""]]
        third = self.assert_ok(self._import(third_rows), 201).json()["batch"]
        withdrawn = self.assert_ok(self.api("post",
                                            f"{HISTORY_BASE}/batches/{third['id']}/withdraw",
                                            token=self.chair_token)).json()
        self.assertEqual(withdrawn["status"], "WITHDRAWN")
        self.assertEqual(withdrawn["posted_rows"], 0)
        self.assertEqual(LedgerEntry.objects.filter(source_type="historical_expense",
                                                    source_id=third["id"]).count(), 0)
        self.assert_error(self.api("post", f"{HISTORY_BASE}/batches/{third['id']}/withdraw",
                                   token=self.chair_token), 409, "INVALID_STATE")
        self.assert_error(self.api("post", f"{HISTORY_BASE}/batches/{third['id']}/void",
                                   {"reason": "误操作"}, token=self.chair_token),
                          409, "INVALID_STATE")


class ReportAccountScopeTests(MultiAccountBase):
    """TC-INT-2006：AC-419-01、AC-420-02。"""

    def setUp(self):
        super().setUp()
        LedgerService.post(direction="INCOME", amount=Decimal("100.00"),
                           occurred_on=date(2025, 2, 10), entry_type="停车费",
                           source_type="test", source_id=1, account=self.account_a)
        LedgerService.post(direction="EXPENSE", amount=Decimal("20.00"),
                           occurred_on=date(2025, 3, 10), entry_type="维修",
                           source_type="test", source_id=2, account=self.account_a)
        LedgerService.post(direction="INCOME", amount=Decimal("200.00"),
                           occurred_on=date(2025, 2, 20), entry_type="场地费",
                           source_type="test", source_id=3, account=self.account_b)
        self.report = LedgerService.generate(period_type="QUARTER", year=2025, quarter=1)

    def test_report_list_and_detail_use_account_scope(self):
        scoped = self.assert_ok(self.api(
            "get", f"/ledger/reports?period_type=QUARTER&year=2025"
                   f"&account_id={self.account_a.id}", token=self.chair_token)).json()
        row = next(item for item in scoped["results"] if item["id"] == self.report.id)
        self.assertEqual(row["total_income"], "100.00")
        self.assertEqual(row["total_expense"], "20.00")
        self.assertEqual(row["balance"], "80.00")
        self.assertFalse(row["legacy"])

        org = self.assert_ok(self.api("get", "/ledger/reports?period_type=QUARTER&year=2025",
                                      token=self.chair_token)).json()
        org_row = next(item for item in org["results"] if item["id"] == self.report.id)
        self.assertEqual(org_row["total_income"], "300.00")
        self.assertEqual(org_row["total_expense"], "20.00")

        detail = self.assert_ok(self.api(
            "get", f"/ledger/reports/{self.report.id}?account_id={self.account_b.id}",
            token=self.chair_token)).json()
        self.assertEqual(detail["account_id"], self.account_b.id)
        self.assertEqual(detail["total_income"], "200.00")
        self.assertEqual(detail["total_expense"], "0.00")
        self.assertEqual(detail["balance"], "200.00")

    def test_report_account_param_validation(self):
        self.assert_error(self.api("get", "/ledger/reports?account_id=abc",
                                   token=self.chair_token), 400, "INVALID_VALUE")
        self.assert_error(self.api("get", "/ledger/reports?account_id=999999",
                                   token=self.chair_token), 404, "NOT_FOUND")
        self.assert_error(self.api("get", f"/ledger/reports/{self.report.id}?account_id=abc",
                                   token=self.chair_token), 400, "INVALID_VALUE")
