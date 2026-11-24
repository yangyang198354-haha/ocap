"""PHASE_08 集成测试：历史支出批量导入 API（MOD-194/195/197，IFC-408~412）。
溯源：AC-333-01/02、AC-334-01~05、AC-335-01/02、AC-336-01/02、AC-337-01~03、AC-338-01。
"""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from apps.approval.models import ApprovalInstance
from apps.claims.models import Claim
from apps.core.audit import AuditLog
from apps.ledger.models import HistoricalExpenseBatch, HistoricalExpenseRow, LedgerEntry, LedgerReport
from tests.support import ApiTestBase

HEADER = ["日期", "金额", "支出类别", "用途/事由", "备注"]
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
BASE = "/admin/ledger/historical-expenses"


def xlsx_bytes(rows, first_title="历史支出", extra_sheets=None, header=HEADER) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = first_title
    ws.append(header)
    for row in rows:
        ws.append(row)
    for title, sheet_rows in (extra_sheets or {}).items():
        sheet = wb.create_sheet(title)
        for row in sheet_rows:
            sheet.append(row)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def csv_bytes(rows, header=HEADER) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def xlsx_upload(name="历史支出.xlsx", rows=(), **kwargs) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, xlsx_bytes(list(rows), **kwargs), content_type=XLSX_TYPE)


def csv_upload(name="历史支出.csv", rows=(), header=HEADER) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, csv_bytes(list(rows), header), content_type="text/csv")


class HistoryExpenseTestBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, self.ctoken = self.make_user(nickname="主任")
        self.make_seat(self.chair, "CHAIR")
        self.approver, self.approver_token = self.make_user(nickname="财务委员")
        self.make_seat(self.approver, "MEMBER")
        self.flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])
        self.owner, self.otoken, _ = self.make_owner()
        self.admin, self.atoken = self.make_admin()

    def import_file(self, upload, token=None):
        return self.upload(f"{BASE}/import",
                           {"file": upload, "approval_flow_id": self.flow.id},
                           token=token or self.ctoken)

    def approve(self, batch_id, token=None):
        batch = HistoricalExpenseBatch.objects.get(id=batch_id)
        self.assert_ok(self.api("post", f"/approval/instances/{batch.approval_instance_id}/decision",
                                {"action": "APPROVE"}, token=token or self.approver_token))

    def batches(self, token=None):
        return self.api("get", f"{BASE}/batches", token=token or self.ctoken)


class TemplateTests(HistoryExpenseTestBase):
    def test_ac_333_01_template_downloads_xlsx_and_csv_with_fixed_columns(self):
        resp = self.api("get", f"{BASE}/template", token=self.ctoken)
        self.assert_ok(resp)
        self.assertIn("spreadsheetml", resp["Content-Type"])
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(resp.content))
        self.assertEqual([c.value for c in wb[wb.sheetnames[0]][1]], HEADER)
        self.assertIn("填写说明", wb.sheetnames)

        csv_resp = self.api("get", f"{BASE}/template", {"file_type": "csv"}, token=self.ctoken)
        self.assert_ok(csv_resp)
        self.assertEqual(csv_resp.content.decode("utf-8-sig").strip().split(","), HEADER)

    def test_ac_333_02_template_permissions(self):
        self.assertEqual(self.api("get", f"{BASE}/template", token=self.otoken).status_code, 403)
        self.assertEqual(self.api("get", f"{BASE}/template").status_code, 401)
        self.assertEqual(self.api("get", f"{BASE}/template", token=self.atoken).status_code, 403)


class ImportTests(HistoryExpenseTestBase):
    def test_ac_334_01_valid_rows_write_expense_ledger_only(self):
        rows = [["2022-07-01", "100.00", "维修", "更换电梯钢丝绳", ""],
                ["2024-03-15", "200.50", "保洁", "年度保洁费", "含税"],
                ["2026-09-30", "300.00", "绿化", "修剪树木", ""]]
        resp = self.import_file(xlsx_upload(rows=rows))
        body = self.assert_ok(resp, 201).json()
        self.assertEqual(body["batch"]["imported_rows"], 3)
        self.assertEqual(body["batch"]["total_rows"], 3)
        self.assertEqual(body["batch"]["total_amount"], "600.50")
        batch = HistoricalExpenseBatch.objects.get(id=body["batch"]["id"])
        # 导入后进入审批，通过前不写台账
        self.assertEqual(batch.status, "PENDING")
        self.assertEqual(LedgerEntry.objects.filter(source_type="historical_expense",
                                                    source_id=batch.id).count(), 0)
        self.assertEqual(ApprovalInstance.objects.filter(subject_type="historical_expense_batch",
                                                         subject_id=batch.id).count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="HISTORICAL_EXPENSE_SUBMITTED",
                                                 object_id=str(batch.id)).exists())
        self.approve(batch.id)
        entries = LedgerEntry.objects.filter(source_type="historical_expense", source_id=batch.id)
        self.assertEqual(entries.count(), 3)
        self.assertTrue(all(e.direction == "EXPENSE" and e.status == "ACTIVE" for e in entries))
        self.assertEqual(entries.get(seq=2).occurred_on, date(2022, 7, 1))
        # 历史导入不得污染申请链路
        self.assertEqual(Claim.objects.count(), 0)
        batch.refresh_from_db()
        self.assertEqual(batch.status, "IMPORTED")
        self.assertTrue(AuditLog.objects.filter(action="HISTORICAL_EXPENSE_IMPORTED",
                                                 object_id=str(batch.id)).exists())

    def test_ac_334_02_mixed_rows_import_valid_and_report_line_numbers(self):
        rows = [["2022-07-01", "100.00", "维修", "正常行", ""],
                ["", "50.00", "维修", "日期为空", ""],
                ["2022-02-30", "50.00", "维修", "日期不存在", ""],
                ["2022-07-02", "0", "维修", "金额为零", ""],
                ["2022-07-03", "-5", "维修", "金额为负", ""],
                ["2022-07-04", "1.234", "维修", "三位小数", ""],
                ["2022-07-05", "10", "类" * 33, "类别超长", ""]]
        body = self.assert_ok(self.import_file(csv_upload(rows=rows)), 201).json()
        self.assertEqual(body["batch"]["imported_rows"], 1)
        self.assertEqual(body["batch"]["failed_rows"], 6)
        self.assertEqual([e["row"] for e in body["errors"]], [3, 4, 5, 6, 7, 8])
        self.approve(body["batch"]["id"])
        self.assertEqual(LedgerEntry.objects.filter(source_type="historical_expense").count(), 1)

    def test_ac_334_02_all_invalid_creates_no_batch_or_ledger(self):
        rows = [["", "0", "维修", "坏行", ""], ["2999-01-01", "10", "维修", "未来", ""]]
        body = self.assert_ok(self.import_file(csv_upload(rows=rows)), 200).json()
        self.assertIsNone(body["batch"])
        self.assertEqual(len(body["errors"]), 2)
        self.assertEqual(HistoricalExpenseBatch.objects.count(), 0)
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_ac_334_03_duplicates_within_file_existing_and_remark_ignored(self):
        first = self.assert_ok(self.import_file(csv_upload(rows=[
            ["2022-07-01", "100.00", "维修", "更换钢丝绳", "第一次"],
        ])), 201).json()
        self.assertEqual(first["batch"]["imported_rows"], 1)

        dup = self.assert_ok(self.import_file(csv_upload(rows=[
            ["2022-07-01", "100.00", "维修", "更换钢丝绳", "备注不同也算重复"],
            ["2022-07-02", "100.00", "维修", "更换钢丝绳", "新日期"],
            ["2022-07-02", "100.00", "维修", "更换钢丝绳", "文件内重复"],
        ])), 201).json()
        self.assertEqual(dup["batch"]["imported_rows"], 1)
        self.assertEqual(dup["batch"]["skipped_rows"], 2)
        self.assertEqual([e["reason"] for e in dup["errors"]], ["DUPLICATE", "DUPLICATE"])
        self.assertEqual([e["row"] for e in dup["errors"]], [2, 4])

    def test_ac_334_04_size_row_limit_and_first_sheet_only(self):
        too_big = SimpleUploadedFile("big.xlsx", b"x" * (5 * 1024 * 1024 + 1), content_type=XLSX_TYPE)
        body = self.assert_error(self.import_file(too_big), 413, "FILE_TOO_LARGE")
        self.assertIn("message", body)

        rows = [[f"2022-07-{i % 28 + 1:02d}", "1.00", "维修", f"第{i}行", ""] for i in range(5001)]
        over = self.assert_error(self.import_file(csv_upload(rows=rows)), 400, "IMPORT_FILE_INVALID")
        self.assertIn("5000", over["message"])
        self.assertEqual(HistoricalExpenseBatch.objects.count(), 0)

        multi = xlsx_upload(rows=[["2022-07-01", "10.00", "维修", "首表", ""]],
                            extra_sheets={"第二表": [["bad"], ["rows"]]})
        ok = self.assert_ok(self.import_file(multi), 201).json()
        self.assertEqual(ok["batch"]["imported_rows"], 1)

        first_is_notes = xlsx_upload(rows=[], first_title="说明", header=["填写说明"],
                                     extra_sheets={"历史支出": [HEADER, ["2022-07-01", "10", "维修", "第二表", ""]]})
        body = self.assert_error(self.import_file(first_is_notes), 400, "IMPORT_COLUMNS_MISSING")
        self.assertEqual(sorted(body["details"]["columns"]), sorted(HEADER))

    def test_ac_334_05_missing_column_and_future_date(self):
        missing = csv_upload(rows=[["2022-07-01", "10.00", "维修", "缺备注列"]], header=HEADER[:4])
        body = self.assert_error(self.import_file(missing), 400, "IMPORT_COLUMNS_MISSING")
        self.assertEqual(body["details"]["columns"], ["备注"])

        future = (date.today() + timedelta(days=1)).isoformat()
        result = self.assert_ok(self.import_file(csv_upload(rows=[
            ["2022-07-01", "10.00", "维修", "合法", ""],
            [future, "10.00", "维修", "未来日期", ""],
        ])), 201).json()
        self.assertEqual(result["batch"]["imported_rows"], 1)
        self.assertEqual(result["errors"][0]["row"], 3)
        self.assertIn("今天", result["errors"][0]["detail"])


class BatchAndVoidTests(HistoryExpenseTestBase):
    def _import_three(self):
        body = self.assert_ok(self.import_file(xlsx_upload(rows=[
            ["2022-07-01", "100.00", "维修", "更换钢丝绳", ""],
            ["2022-08-01", "200.00", "保洁", "月度保洁", ""],
            ["2026-09-30", "300.00", "绿化", "修剪树木", ""],
        ])), 201).json()
        self.approve(body["batch"]["id"])
        return body

    def test_ac_335_01_and_02_batch_list_and_detail(self):
        imported = self._import_three()
        batch_id = imported["batch"]["id"]
        listing = self.assert_ok(self.batches()).json()
        self.assertEqual(listing["count"], 1)
        item = listing["results"][0]
        self.assertTrue({"created_at", "imported_by_label", "file_name", "total_rows", "imported_rows",
                         "skipped_rows", "failed_rows", "total_amount", "status"} <= set(item))
        self.assertEqual(item["total_amount"], "600.00")

        detail = self.assert_ok(self.api("get", f"{BASE}/batches/{batch_id}", token=self.ctoken)).json()
        self.assertEqual(len(detail["rows"]), 3)
        self.assertTrue({"line_no", "occurred_on", "amount", "category", "purpose", "remark",
                         "status", "error_message"} <= set(detail["rows"][0]))
        self.assertEqual(self.api("get", f"{BASE}/batches/{batch_id}", token=self.otoken).status_code, 403)

    def test_ac_336_01_void_batch_ledger_reports_and_audit(self):
        imported = self._import_three()
        batch_id = imported["batch"]["id"]
        report = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                         {"period_type": "QUARTER", "year": 2022, "quarter": 3},
                                         token=self.ctoken), 201).json()
        self.assertEqual(report["total_expense"], "300.00")

        voided = self.assert_ok(self.api("post", f"{BASE}/batches/{batch_id}/void",
                                         {"reason": "导入科目有误"}, token=self.ctoken)).json()
        self.assertEqual(voided["status"], "VOIDED")
        self.assertEqual(voided["void_reason"], "导入科目有误")
        self.assertFalse(LedgerEntry.objects.filter(source_type="historical_expense",
                                                    source_id=batch_id, status="ACTIVE").exists())
        self.assertTrue(LedgerReport.objects.get(id=report["id"]).stale)

        audit = AuditLog.objects.get(action="HISTORICAL_EXPENSE_VOIDED", object_id=str(batch_id))
        self.assertEqual(audit.actor_id, self.chair.id)
        self.assertEqual(audit.detail["reason"], "导入科目有误")
        self.assertEqual(audit.detail["imported_rows"], 3)
        self.assertEqual(audit.detail["total_amount"], "600.00")

    def test_ac_336_02_revoid_conflict_reimport_allowed_and_permissions(self):
        batch_id = self._import_three()["batch"]["id"]
        self.assert_ok(self.api("post", f"{BASE}/batches/{batch_id}/void", {"reason": "作废"}, token=self.ctoken))
        again = self.assert_error(self.api("post", f"{BASE}/batches/{batch_id}/void",
                                           {"reason": "重复作废"}, token=self.ctoken), 409, "ALREADY_VOIDED")
        self.assertIn("message", again)
        self.assertEqual(AuditLog.objects.filter(action="HISTORICAL_EXPENSE_VOIDED").count(), 1)
        self.assertEqual(self.api("post", f"{BASE}/batches/{batch_id}/void", {"reason": "x"},
                                  token=self.otoken).status_code, 403)

        again_import = self.assert_ok(self.import_file(xlsx_upload(rows=[
            ["2022-07-01", "100.00", "维修", "更换钢丝绳", ""],
            ["2022-08-01", "200.00", "保洁", "月度保洁", ""],
            ["2026-09-30", "300.00", "绿化", "修剪树木", ""],
        ])), 201).json()
        self.assertEqual(again_import["batch"]["imported_rows"], 3)


class ReportIntegrationTests(HistoryExpenseTestBase):
    def _import_year(self):
        body = self.assert_ok(self.import_file(csv_upload(rows=[
            ["2022-07-01", "100.00", "维修", "更换钢丝绳", ""],
            ["2022-08-01", "200.00", "保洁", "月度保洁", ""],
            ["2026-09-30", "300.00", "绿化", "修剪树木", ""],
        ])), 201).json()
        self.approve(body["batch"]["id"])
        return body

    def test_ac_337_01_03_report_includes_history_then_excludes_after_void(self):
        imported = self._import_year()
        report = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                         {"period_type": "QUARTER", "year": 2022, "quarter": 3},
                                         token=self.ctoken), 201).json()
        self.assertEqual(report["total_expense"], "300.00")
        history_rows = [row for row in report["detail"] if row["source_type"] == "historical_expense"]
        self.assertEqual(len(history_rows), 2)
        self.assertEqual(history_rows[0]["source_id"], imported["batch"]["id"])

        self.assert_ok(self.api("post", f"{BASE}/batches/{imported['batch']['id']}/void",
                                {"reason": "重导"}, token=self.ctoken))
        self.assertTrue(self.assert_ok(self.api("get", f"/ledger/reports/{report['id']}",
                                                token=self.ctoken)).json()["stale"])
        regenerated = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                              {"period_type": "QUARTER", "year": 2022, "quarter": 3},
                                              token=self.ctoken), 201).json()
        self.assertEqual(regenerated["total_expense"], "0.00")

    def test_ac_337_02_report_visible_to_owner_and_anonymous_401(self):
        self._import_year()
        self.api("post", "/ledger/reports/generate",
                 {"period_type": "QUARTER", "year": 2022, "quarter": 3}, token=self.ctoken)
        listing = self.assert_ok(self.api("get", "/ledger/reports", token=self.otoken)).json()
        self.assertGreaterEqual(listing["count"], 1)
        self.assertEqual(self.api("get", "/ledger/reports").status_code, 401)


class PermissionMatrixTests(HistoryExpenseTestBase):
    def test_ac_338_01_all_endpoints_require_current_committee_member(self):
        imported = self.assert_ok(self.import_file(xlsx_upload(rows=[
            ["2022-07-01", "10.00", "维修", "权限矩阵", ""],
        ])), 201).json()
        batch_id = imported["batch"]["id"]
        calls = [
            ("get", f"{BASE}/template", None),
            ("get", f"{BASE}/batches", None),
            ("get", f"{BASE}/batches/{batch_id}", None),
        ]
        for method, path, data in calls:
            self.assertIn(getattr(self.api(method, path, data, token=self.ctoken), "status_code"), (200, 201))
            self.assertEqual(self.api(method, path, data, token=self.otoken).status_code, 403)
            self.assertEqual(self.api(method, path, data, token=self.atoken).status_code, 403)
            self.assertEqual(self.api(method, path, data).status_code, 401)
        for token, expected in ((self.otoken, 403), (self.atoken, 403)):
            resp = self.import_file(csv_upload(rows=[["2022-07-02", "1.00", "维修", "x", ""]]), token=token)
            self.assertEqual(resp.status_code, expected)
        anonymous = self.upload(f"{BASE}/import",
                                {"file": csv_upload(rows=[["2022-07-02", "1.00", "维修", "x", ""]])})
        self.assertEqual(anonymous.status_code, 401)
