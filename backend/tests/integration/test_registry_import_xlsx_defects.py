"""PHASE_08 集成测试补充（缺陷回流 DEF-007~011，TC-INT-304 起）。

xlsx 经真实 API 上传（openpyxl 在测试内构造工作簿，不入库二进制）；auto_bind 只对
MembershipService.certify_owner 按单元打补丁，AutoBindService 本身为被测对象。
"""
import io
from datetime import timedelta
from unittest import mock, skipUnless

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from apps.residency.services import MembershipService
from tests.integration.test_registry_import_enhancement import (
    IMPORT_URL, RegistryImportTestBase, csv_bytes, row)

try:
    from openpyxl import Workbook, load_workbook
    HAS_OPENPYXL = True
except ImportError:  # pragma: no cover
    HAS_OPENPYXL = False

NEED_OPENPYXL = skipUnless(HAS_OPENPYXL, "未安装 openpyxl（画像 P4：不自行安装）")
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def make_xlsx(rows, build=None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(IMPORT_COLUMNS)
    for r in rows:
        ws.append(r)
    if build:
        build(wb, ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class XlsxImportBase(RegistryImportTestBase):
    def import_xlsx(self, raw, dry_run=False, data=None):
        upload = SimpleUploadedFile("registry.xlsx", raw, content_type=XLSX_TYPE)
        payload = dict(data or {})
        if dry_run:
            payload["dry_run"] = "1"
        return self.upload(IMPORT_URL, {"file": upload}, data=payload or None, token=self.admin_token)


@NEED_OPENPYXL
class XlsxImportTests(XlsxImportBase):
    def test_tc_int_304_text_cells_preserved(self):
        """TC-INT-304 / AC-093-04：xlsx 文本单元格 "0801"/"08"/"13800000000" 导入后原样保存。"""
        def build(wb, ws):
            for ref in ("B2", "D2", "H2"):
                ws[ref].number_format = "@"

        resp = self.import_xlsx(make_xlsx([["1", "08", "8", "0801", "住宅", "89.50", "张三", "13800000000"]], build))
        self.assert_ok(resp)
        self.assertEqual((resp.data["imported"], resp.data["failed"]), (1, 0))
        unit = RegistryUnit.objects.get()
        self.assertEqual((unit.unit_no, unit.floor, unit.room), ("08", "8", "0801"))
        self.assertEqual(unit.specific_part, "1栋08单元8层0801号")
        self.assertEqual(RegistryPhone.objects.get().phone, "13800000000")

    def test_tc_int_305_merged_building_cells_span_owners(self):
        """TC-INT-305 / AC-093-03：楼栋列合并单元格跨多行业主，所有业主导入成功。"""
        def build(wb, ws):
            ws.merge_cells("A2:A4")

        rows = [["1栋", "1", "3", "301", "住宅", "89.50", "张三", "13800000011"],
                [None, "1", "3", "301", "住宅", "89.50", "李四", "13800000012"],
                [None, "1", "3", "301", "住宅", "89.50", "王五", ""]]
        resp = self.import_xlsx(make_xlsx(rows, build))
        self.assert_ok(resp)
        self.assertEqual((resp.data["rows_total"], resp.data["failed"], resp.data["owners_created"]), (3, 0, 3))
        unit = RegistryUnit.objects.get()
        self.assertEqual(unit.building, "1栋")
        self.assertEqual(sorted(o.name for o in RegistryOwner.objects.filter(unit=unit)), ["张三", "李四", "王五"])

    def test_tc_int_306_hidden_column_and_second_sheet_ignored(self):
        """TC-INT-306 / AC-093-03：隐藏列、第二工作表（含同表头的干扰数据）不影响导入，仅读首个工作表。"""
        def build(wb, ws):
            ws.column_dimensions["F"].hidden = True
            other = wb.create_sheet("干扰")
            other.append(IMPORT_COLUMNS)
            other.append(["9", "9", "9", "999", "住宅", "10.00", "不应导入", "13800009999"])

        resp = self.import_xlsx(make_xlsx([["1", "1", "3", "301", "住宅", "89.50", "张三", "13800000021"]], build))
        self.assert_ok(resp)
        self.assertEqual((resp.data["rows_total"], resp.data["imported"], resp.data["failed"]), (1, 1, 0))
        self.assertEqual(RegistryUnit.objects.count(), 1)
        self.assertEqual(str(RegistryUnit.objects.get().area), "89.50")
        self.assertFalse(RegistryOwner.objects.filter(name="不应导入").exists())

    def test_tc_int_307_downloaded_template_text_columns(self):
        """TC-INT-307 / AC-093-01、AC-093-04（DEF-007）：API 下载的 xlsx 模板 A/B/C/D/H 列为文本格式。"""
        resp = self.client_for(self.admin_token).get(
            "/api/v1/admin/registry/import/template", {"file_type": "xlsx"})
        self.assertEqual(resp.status_code, 200)
        wb = load_workbook(io.BytesIO(b"".join(resp.streaming_content) if resp.streaming else resp.content))
        sheet = wb.worksheets[0]
        self.assertEqual([c.value for c in sheet[1]], IMPORT_COLUMNS)
        for col in "ABCDH":
            self.assertEqual(sheet.column_dimensions[col].number_format, "@", col)
            self.assertEqual(sheet[f"{col}2"].number_format, "@", col)
        self.assertEqual(wb.worksheets[1].title, "填写说明")

    def test_tc_int_311_downloaded_template_imports_back(self):
        """TC-INT-311 / AC-093-01：下载的 xlsx 模板（含示例行）不改动直接上传，示例行全部成功。"""
        resp = self.client_for(self.admin_token).get(
            "/api/v1/admin/registry/import/template", {"file_type": "xlsx"})
        raw = b"".join(resp.streaming_content) if resp.streaming else resp.content
        result = self.import_xlsx(raw)
        self.assert_ok(result)
        self.assertEqual((result.data["rows_total"], result.data["failed"]), (6, 0))
        self.assertEqual(result.data["imported"], 4)


class AutoBindDefectTests(RegistryImportTestBase):
    def test_tc_int_308_one_unit_bind_failure_keeps_others(self):
        """TC-INT-308 / AC-102-02（DEF-009）：同号 3 个专有部分，1 个绑定抛异常，其余 2 个注册时仍绑定。"""
        phone = "13800000041"
        units = []
        for room in ("101", "102", "103"):
            unit = self.make_registry_unit(room=room)
            self.add_owner(unit, f"业主{room}", [phone])
            units.append(unit)
        bad = units[1].id
        real = MembershipService.certify_owner

        def flaky(user_id, unit_id, source, origin=None):
            if unit_id == bad:
                raise RuntimeError("模拟单元绑定失败")
            return real(user_id, unit_id, source, origin=origin)

        with mock.patch.object(MembershipService, "certify_owner", side_effect=flaky), \
                self.assertLogs("apps.residency.auto_bind", level="ERROR"):
            code = self.request_code(phone, "REGISTER")
            resp = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual({item["unit_id"] for item in resp.data["auto_bound"]}, {units[0].id, units[2].id})
        user = self.user_of(resp.data["token"])
        active = Membership.objects.filter(user=user, ended_at__isnull=True)
        self.assertEqual(set(active.values_list("unit_id", flat=True)), {units[0].id, units[2].id})
        self.assertEqual(active.filter(role="HEAD", source="REGISTRY").count(), 2)
        self.assertFalse(Membership.objects.filter(user=user, unit_id=bad).exists())


class DryRunFormAndNameFillTests(RegistryImportTestBase):
    ROWS = [row(room="101", name="张三", phone="13800000051")]

    def _post(self, value):
        upload = SimpleUploadedFile("r.csv", csv_bytes(self.ROWS), content_type="text/csv")
        resp = self.upload(IMPORT_URL, {"file": upload}, data={"dry_run": value}, token=self.admin_token)
        self.assert_ok(resp)
        return resp

    def test_tc_int_309_multipart_dry_run_values(self):
        """TC-INT-309 / AC-100-01（DEF-010）：表单 dry_run="false"/"0" 为正式导入，"true"/"1" 为预检。"""
        for value in ("false", "0"):
            RegistryUnit.objects.all().delete()
            resp = self._post(value)
            self.assertIs(resp.data["dry_run"], False, value)
            self.assertEqual(RegistryUnit.objects.count(), 1, value)
        for value in ("true", "1", "TRUE"):
            RegistryUnit.objects.all().delete()
            resp = self._post(value)
            self.assertIs(resp.data["dry_run"], True, value)
            self.assertEqual(RegistryUnit.objects.count(), 0, value)
            self.assertEqual(resp.data["imported"], 1, value)

    def test_tc_int_310_name_fill_updates_updated_at(self):
        """TC-INT-310 / AC-099-02（DEF-011）：同手机号补填姓名后 RegistryOwner.updated_at 更新。"""
        unit = self.make_registry_unit(room="101")
        legacy = RegistryOwner.objects.create(unit=unit, name=None)
        RegistryPhone.objects.create(unit=unit, owner=legacy, phone="13800000052")
        old = timezone.now() - timedelta(days=30)
        RegistryOwner.objects.filter(id=legacy.id).update(updated_at=old)

        resp = self.import_rows([row(room="101", name="张三", phone="13800000052")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["owners_named"], 1)
        legacy.refresh_from_db()
        self.assertEqual(legacy.name, "张三")
        self.assertGreater(legacy.updated_at, old + timedelta(days=29))
        self.assertEqual(RegistryOwner.objects.filter(unit=unit).count(), 1)
