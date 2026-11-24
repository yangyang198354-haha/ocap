"""PHASE_09 端到端旅程：多账户收入→报销→历史支出全链路与报表按账户口径。

溯源：US-341、US-342、US-344、US-348；AC-412-01、AC-413-02、AC-415-02、AC-416-02、AC-419-01、AC-420-02。
critical path 口径：替代（多步 API 旅程；本机无浏览器/真机 E2E 驱动）。
"""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.approval.models import ApprovalInstance
from apps.core.models import Attachment
from apps.ledger.services import AccountService, LedgerAccount, LedgerService
from tests.support import ApiTestBase


def csv_upload(name: str, header: list[str], rows: list[list]) -> SimpleUploadedFile:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return SimpleUploadedFile(name, ("\ufeff" + buffer.getvalue()).encode("utf-8"),
                              content_type="text/csv")


def invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class MultiAccountFinanceJourneyTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, self.chair_token = self.make_user(nickname="主任")
        self.make_seat(self.chair, "CHAIR")
        self.approver, self.approver_token = self.make_user(nickname="财务委员")
        self.make_seat(self.approver, "MEMBER")
        self.income_flow = self.make_flow(scope="INCOME", approvers=[self.approver])
        self.expense_flow = self.make_flow(scope="EXPENSE", approvers=[self.approver])
        self.account_a = AccountService.default_account()
        self.account_b = LedgerAccount.objects.create(name="公共收益账户")
        self.today = date.today()
        self.quarter = (self.today.month - 1) // 3 + 1

    def approve(self, instance_id):
        return self.assert_ok(self.api("post", f"/approval/instances/{instance_id}/decision",
                                       {"action": "APPROVE"}, token=self.approver_token))

    def test_income_reimbursement_and_historical_expense_all_land_in_selected_account(self):
        # 步骤 1：收入批量导入到账户 B，并提交审批
        income = self.assert_ok(self.upload(
            "/admin/income/sheets/import",
            {"file": csv_upload("income.csv", ["日期", "金额", "收入类别", "来源说明", "备注"],
                                [[str(self.today), "500.00", "停车费", "地面临时停车", ""]]),
             "account_id": self.account_b.id}, token=self.chair_token), 201).json()
        self.assertEqual(income["account_id"], self.account_b.id)
        self.assert_ok(self.api("post", f"/admin/income/sheets/{income['id']}/submit",
                                {"approval_flow_id": self.income_flow.id}, token=self.chair_token))
        income_instance = ApprovalInstance.objects.get(subject_type="income_sheet",
                                                       subject_id=income["id"])
        self.approve(income_instance.id)

        # 步骤 2：报销记到账户 B，审批通过后入账
        claim = self.assert_ok(self.api(
            "post", "/claims/reimbursements",
            {"amount": "300.50", "reason": "打印费",
             "occurred_on": str(self.today - timedelta(days=1)),
             "invoice_ids": [str(invoice(self.chair).id)],
             "approval_flow_id": self.expense_flow.id,
             "account_id": self.account_b.id}, token=self.chair_token), 201).json()
        self.assertEqual(claim["account_name"], "公共收益账户")
        claim_instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim["id"])
        self.approve(claim_instance.id)

        # 步骤 3：历史支出导入到账户 B，审批通过后才入账
        batch = self.assert_ok(self.upload(
            "/admin/ledger/historical-expenses/import",
            {"file": csv_upload("历史支出.csv", ["日期", "金额", "支出类别", "用途/事由", "备注"],
                                [[str(self.today - timedelta(days=2)), "100.00", "维修",
                                  "更换门禁", ""]]),
             "account_id": self.account_b.id,
             "approval_flow_id": self.income_flow.id}, token=self.chair_token), 201).json()["batch"]
        self.assertEqual(batch["status"], "PENDING")
        self.assertEqual(batch["posted_rows"], 0)
        self.assertEqual(AccountService.balance(self.account_b), Decimal("199.50"))
        self.approve(batch["approval_instance_id"])

        # 步骤 4：账户余额只反映账户 B，默认账户 A 不受影响
        self.assertEqual(AccountService.balance(self.account_b), Decimal("99.50"))
        self.assertEqual(AccountService.balance(self.account_a), Decimal("0.00"))

        # 步骤 5：生成当季报表，列表按 B 口径展示，与详情一致
        report = LedgerService.generate(period_type="QUARTER", year=self.today.year,
                                        quarter=self.quarter)
        listed = self.assert_ok(self.api(
            "get", f"/ledger/reports?period_type=QUARTER&year={self.today.year}"
                   f"&account_id={self.account_b.id}", token=self.chair_token)).json()
        row = next(item for item in listed["results"] if item["id"] == report.id)
        self.assertEqual(row["total_income"], "500.00")
        self.assertEqual(row["total_expense"], "400.50")
        self.assertEqual(row["balance"], "99.50")

        detail_b = self.assert_ok(self.api(
            "get", f"/ledger/reports/{report.id}?account_id={self.account_b.id}",
            token=self.chair_token)).json()
        self.assertEqual(detail_b["total_income"], row["total_income"])
        self.assertEqual(detail_b["total_expense"], row["total_expense"])
        self.assertEqual(detail_b["balance"], row["balance"])

        detail_a = self.assert_ok(self.api(
            "get", f"/ledger/reports/{report.id}?account_id={self.account_a.id}",
            token=self.chair_token)).json()
        self.assertEqual(detail_a["total_income"], "0.00")
        self.assertEqual(detail_a["total_expense"], "0.00")

        org = self.assert_ok(self.api("get", f"/ledger/reports/{report.id}",
                                      token=self.chair_token)).json()
        self.assertEqual(org["total_income"], "500.00")
        self.assertEqual(org["total_expense"], "400.50")
