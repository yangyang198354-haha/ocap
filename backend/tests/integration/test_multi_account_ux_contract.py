"""PHASE_08 契约测试：多账户 UI 的 Web/小程序调用 → 后端路由与字段。

溯源：AC-410-01、AC-411-02、AC-412-01、AC-415-01~03、AC-416-04、AC-418-01~03、
AC-419-02、AC-420-01/02、AC-421-01~03、AC-423-01/02、AC-424-01/02。
"""
import csv
import io
from datetime import date, timedelta
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.models import Attachment
from apps.ledger.services import LedgerAccount
from tests.integration.test_frontend_contract import (MINI_API, REPO, WEB_API, extract_calls,
                                                      resolve_path)
from tests.support import ApiTestBase

NEW_WEB_CALLS = {
    ("member", "GET", "/ledger/accounts/summary"),
    ("member", "POST", "/admin/income/sheets/import"),
    ("member", "POST", "/admin/ledger/historical-expenses/import"),
    ("member", "POST", "/admin/ledger/historical-expenses/batches/${id}/withdraw"),
    ("member", "GET", "/ledger/reports"),
    ("member", "GET", "/ledger/reports/${id}"),
}
NEW_MINI_CALLS = {
    ("member", "GET", "/ledger/accounts/summary"),
    ("member", "POST", "/claims/reimbursements"),
    ("member", "POST", "/claims/advances"),
}


def test_source(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


class MultiAccountRouteContractTests(ApiTestBase):
    """TC-INT-2008：新增调用逐个可解析到后端路由，且视图支持对应方法。"""

    def test_new_client_calls_resolve_and_support_method(self):
        for source, required in ((WEB_API, NEW_WEB_CALLS), (MINI_API, NEW_MINI_CALLS)):
            calls = extract_calls(source)
            found = {c[:3] for c in calls}
            missing = required - found
            self.assertEqual(missing, set(), f"{source.name} 缺少新增调用：{missing}")
            problems = []
            for client, method, template, where in calls:
                if (client, method, template) not in required:
                    continue
                try:
                    match = resolve_path(template)
                except Exception as exc:  # Resolver404
                    problems.append(f"{where} {method} {template}: 无法解析（{exc}）")
                    continue
                view_cls = getattr(match.func, "cls", None)
                if view_cls is None or not hasattr(view_cls, method.lower()):
                    problems.append(f"{where} {method} {template}: 视图不支持该方法")
            self.assertEqual(problems, [], "\n" + "\n".join(problems))


class MultiAccountFieldContractTests(ApiTestBase):
    """TC-INT-2008：客户端提交字段与后端读取字段一致，响应字段可供页面渲染。"""

    def setUp(self):
        super().setUp()
        self.member, self.token = self.make_user()
        self.make_seat(self.member, "CHAIR")
        self.approver, self.approver_token = self.make_user()
        self.make_seat(self.approver, "MEMBER")
        self.flow = self.make_flow(scope="INCOME", approvers=[self.approver])
        self.expense_flow = self.make_flow(scope="EXPENSE", approvers=[self.approver])
        self.account = LedgerAccount.objects.create(name="契约账户")

    def test_web_client_appends_account_and_flow_fields(self):
        web = test_source("frontend/src/shared/api.js")
        self.assertIn("body.append('account_id', accountId)", web)
        self.assertEqual(web.count("body.append('account_id', accountId)"), 2,
                         "收入导入与历史支出导入都应提交 account_id")
        self.assertIn("body.append('approval_flow_id', flowId)", web)
        self.assertIn("withdrawBatch", web)

    def test_ui_sources_use_shared_account_select_and_account_scoped_report_detail(self):
        self.assertIn("AccountSelect", test_source("frontend/src/portal/Income.vue"))
        self.assertIn("AccountSelect", test_source("frontend/src/portal/Claims.vue"))
        historical = test_source("frontend/src/portal/HistoricalExpenses.vue")
        self.assertIn("AccountSelect", historical)
        self.assertIn("accountId: accountId.value, flowId: flowId.value", historical)

        reports = test_source("frontend/src/portal/Reports.vue")
        self.assertIn("reports-account-grid", reports)
        self.assertIn("selectedAccountId", reports)
        self.assertIn(':account-id="selectedAccountId"', reports)

        detail = test_source("frontend/src/portal/ReportDetailDialog.vue")
        self.assertNotIn("el-select", detail, "报表详情右上角不应再有账户下拉")
        self.assertNotIn("全部账户", detail)
        self.assertIn("is-income", detail)
        self.assertIn("is-expense", detail)

        admin_accounts = test_source("frontend/src/admin/AdminAccounts.vue")
        self.assertIn("account-actions", admin_accounts)
        self.assertIn('<el-button size="small" @click="openEdit(row)">编辑</el-button>', admin_accounts)
        self.assertNotIn("el-link", admin_accounts, "操作按钮不应使用与背景同色的链接样式")

    def test_miniprogram_claims_loads_enabled_accounts_and_posts_account_id(self):
        mini = test_source("miniprogram/utils/api.js")
        self.assertIn("/ledger/accounts/summary", mini)
        page = test_source("miniprogram/pages/claims/index.vue")
        self.assertIn("api.accounts({ status: 'ENABLED'", page)
        self.assertIn("account_id: accountId", page)
        self.assertIn("请选择入账账户", page)

    def test_backend_response_fields_match_client_expectations(self):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["日期", "金额", "收入类别", "来源说明", "备注"])
        writer.writerow(["2025-08-01", "12.00", "停车费", "临停", ""])
        upload = SimpleUploadedFile("income.csv", ("\ufeff" + buffer.getvalue()).encode("utf-8"),
                                    content_type="text/csv")
        sheet = self.assert_ok(self.upload("/admin/income/sheets/import",
                                           {"file": upload, "account_id": self.account.id},
                                           token=self.token), 201).json()
        for field in ("account_id", "account_name"):
            self.assertIn(field, sheet)
        self.assertEqual(sheet["account_name"], "契约账户")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["日期", "金额", "支出类别", "用途/事由", "备注"])
        writer.writerow(["2025-08-02", "9.00", "维修", "门把手", ""])
        upload = SimpleUploadedFile("历史支出.csv", ("\ufeff" + buffer.getvalue()).encode("utf-8"),
                                    content_type="text/csv")
        batch = self.assert_ok(self.upload("/admin/ledger/historical-expenses/import",
                                           {"file": upload, "account_id": self.account.id,
                                            "approval_flow_id": self.flow.id},
                                           token=self.token), 201).json()["batch"]
        for field in ("status", "posted_rows", "account_id", "account_name",
                      "approval_instance_id", "decided_at"):
            self.assertIn(field, batch)
        self.assertEqual(batch["posted_rows"], 0)
        self.assertIsNotNone(batch["approval_instance_id"])

        Attachment.objects.create(
            owner_type="MEMBER", owner_id=self.member.id, purpose="INVOICE",
            original_name="inv.pdf", content_type="application/pdf", size=1024,
            sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
        )
        invoice = Attachment.objects.filter(owner_id=self.member.id, purpose="INVOICE").first()
        claim = self.assert_ok(self.api(
            "post", "/claims/reimbursements",
            {"amount": "20.00", "reason": "契约", "occurred_on": str(date.today() - timedelta(days=1)),
             "invoice_ids": [str(invoice.id)], "approval_flow_id": self.expense_flow.id,
             "account_id": self.account.id}, token=self.token), 201).json()
        self.assertEqual(claim["account_id"], self.account.id)
        self.assertEqual(claim["account_name"], "契约账户")
