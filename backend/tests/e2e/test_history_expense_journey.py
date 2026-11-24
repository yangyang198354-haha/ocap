"""PHASE_09 E2E：业委会成员历史支出补录 → 生成往年季度报表 → 作废 → 重导的完整旅程。
溯源：AC-334-01、AC-335-01、AC-336-01/02、AC-337-01/03、AC-338-01。
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from apps.ledger.models import HistoricalExpenseBatch, LedgerEntry
from tests.support import ApiTestBase
BASE = "/admin/ledger/historical-expenses"
HEADER = ["日期", "金额", "支出类别", "用途/事由", "备注"]


def expense_xlsx() -> SimpleUploadedFile:
    wb = Workbook()
    ws = wb.active
    ws.append(HEADER)
    for row in (["2022-07-01", "100.00", "维修", "更换电梯钢丝绳", ""],
                ["2022-08-15", "200.00", "保洁", "季度保洁", "含税"],
                ["2022-09-30", "50.50", "绿化", "修剪树木", ""]):
        ws.append(row)
    out = io.BytesIO()
    wb.save(out)
    return SimpleUploadedFile("历史支出.xlsx", out.getvalue(),
                              content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


class HistoryExpenseJourneyTests(ApiTestBase):
    def test_tc_e2e_history_expense_full_journey(self):
        chair, token = self.make_user(nickname="主任")
        self.make_seat(chair, "CHAIR")
        approver, approver_token = self.make_user(nickname="财务委员")
        self.make_seat(approver, "MEMBER")
        flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[approver])
        _, owner_token, _ = self.make_owner()

        def upload_import():
            return self.upload(f"{BASE}/import",
                               {"file": expense_xlsx(), "approval_flow_id": flow.id}, token=token)

        def approve(batch_id):
            self.assert_ok(self.api(
                "post", f"/approval/instances/{HistoricalExpenseBatch.objects.get(id=batch_id).approval_instance_id}/decision",
                {"action": "APPROVE"}, token=approver_token))

        # 1) 导入 2022Q3 三笔历史支出，提交审批后通过才入账
        imported = self.assert_ok(upload_import(), 201).json()
        batch_id = imported["batch"]["id"]
        self.assertEqual(imported["batch"]["imported_rows"], 3)
        self.assertEqual(imported["batch"]["status"], "PENDING")
        self.assertFalse(LedgerEntry.objects.filter(source_type="historical_expense",
                                                    source_id=batch_id).exists())
        approve(batch_id)
        self.assertEqual(LedgerEntry.objects.filter(source_type="historical_expense", source_id=batch_id).count(), 3)

        # 2) 批次列表可见
        listing = self.assert_ok(self.api("get", f"{BASE}/batches", token=token)).json()
        self.assertEqual(listing["results"][0]["total_amount"], "350.50")

        # 3) 生成 2022Q3 报表，包含三笔历史支出
        report = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                         {"period_type": "QUARTER", "year": 2022, "quarter": 3},
                                         token=token), 201).json()
        self.assertEqual(report["total_expense"], "350.50")
        self.assertEqual(len([r for r in report["detail"] if r["source_type"] == "historical_expense"]), 3)

        # 4) 业主可查看报表
        self.assert_ok(self.api("get", f"/ledger/reports/{report['id']}", token=owner_token))

        # 5) 整批作废 → 报表过期 → 重算为 0
        self.assert_ok(self.api("post", f"{BASE}/batches/{batch_id}/void", {"reason": "科目错误"}, token=token))
        self.assertTrue(self.assert_ok(self.api("get", f"/ledger/reports/{report['id']}", token=token)).json()["stale"])
        regenerated = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                              {"period_type": "QUARTER", "year": 2022, "quarter": 3},
                                              token=token), 201).json()
        self.assertEqual(regenerated["total_expense"], "0.00")

        # 6) 作废后可重新导入同一批数据（重新提交审批并再次入账）
        again = self.assert_ok(upload_import(), 201).json()
        self.assertEqual(again["batch"]["imported_rows"], 3)
        approve(again["batch"]["id"])
        self.assertEqual(HistoricalExpenseBatch.objects.filter(status="VOIDED").count(), 1)
        self.assertEqual(HistoricalExpenseBatch.objects.filter(status="IMPORTED").count(), 1)

        # 7) 非委员不能导入
        denied = self.upload(f"{BASE}/import",
                             {"file": expense_xlsx(), "approval_flow_id": flow.id}, token=owner_token)
        self.assertEqual(denied.status_code, 403)
