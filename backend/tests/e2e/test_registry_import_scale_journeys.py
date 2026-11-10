"""PHASE_09 E2E 补充（缺陷回流）：20000 行规模旅程与 xlsx 模板旅程（TC-E2E-302 起）。

口径说明：耗时在测试环境（SQLite 内存库、单进程、开发机）计时，不是目标机（树莓派 + MySQL）口径；
目标机性能由人工验证清单 M-04~M-06 复核。
"""
import io
import time
from unittest import skipUnless

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.integration.test_registry_import_enhancement import csv_bytes, row
from tests.support import ApiTestBase

try:
    from openpyxl import load_workbook
    HAS_OPENPYXL = True
except ImportError:  # pragma: no cover
    HAS_OPENPYXL = False

IMPORT_URL = "/admin/registry/import"
TOTAL = 20000
BUDGET_SECONDS = 60


def scale_rows(total=TOTAL, invalid_every=0):
    rows = []
    for i in range(total):
        phone = f"137{i:08d}"
        if invalid_every and i % invalid_every == 0:
            phone = "12345"
        rows.append(row(building=f"B{i // 1000}", unit="1", floor=str(i % 30 + 1), room=str(i),
                        name=f"业主{i}", phone=phone))
    return rows


class ScaleJourneyBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def post_import(self, rows, dry_run):
        raw = csv_bytes(rows)
        self.assertLess(len(raw), 5 * 1024 * 1024, "样本须在 5 MB 限制内")
        upload = SimpleUploadedFile("registry.csv", raw, content_type="text/csv")
        started = time.monotonic()
        resp = self.upload(IMPORT_URL, {"file": upload}, data={"dry_run": "1"} if dry_run else None,
                           token=self.admin_token)
        elapsed = time.monotonic() - started
        self.assertEqual(resp.status_code, 200, resp.content[:300])
        self.assertLess(elapsed, BUDGET_SECONDS, f"耗时 {elapsed:.1f}s 超出 {BUDGET_SECONDS}s")
        self.assertLess(resp.data["elapsed_ms"], BUDGET_SECONDS * 1000)
        return resp, elapsed


class ScaleJourneyTests(ScaleJourneyBase):
    def test_tc_e2e_302_twenty_thousand_valid_rows(self):
        """TC-E2E-302 / AC-094-07、AC-100-07：20000 行合法 csv 预检（不写库）再正式导入，合计 20000，60 s 内。"""
        rows = scale_rows()
        dry, dry_elapsed = self.post_import(rows, dry_run=True)
        self.assertEqual((dry.data["rows_total"], dry.data["rows_ok"], dry.data["failed"]), (TOTAL, TOTAL, 0))
        self.assertEqual(dry.data["imported"] + dry.data["updated"], TOTAL)
        self.assertTrue(dry.data["dry_run"])
        self.assertEqual(RegistryUnit.objects.count(), 0)

        real, real_elapsed = self.post_import(rows, dry_run=False)
        self.assertEqual((real.data["rows_total"], real.data["rows_ok"], real.data["failed"]), (TOTAL, TOTAL, 0))
        self.assertEqual((real.data["imported"], real.data["owners_created"], real.data["phones_created"]),
                         (TOTAL, TOTAL, TOTAL))
        self.assertEqual(RegistryUnit.objects.count(), TOTAL)
        self.assertEqual(RegistryOwner.objects.count(), TOTAL)
        self.assertEqual(RegistryPhone.objects.count(), TOTAL)
        print(f"[TC-E2E-302] 20000 行合法：预检 {dry_elapsed:.1f}s，正式 {real_elapsed:.1f}s（SQLite 内存库）")

    def test_tc_e2e_303_twenty_thousand_rows_ten_percent_invalid(self):
        """TC-E2E-303 / AC-100-08、AC-100-07：20000 行含 10% 非法手机号，预检与正式一致，失败 2000，可导出错误清单数据。"""
        rows = scale_rows(invalid_every=10)
        dry, dry_elapsed = self.post_import(rows, dry_run=True)
        real, real_elapsed = self.post_import(rows, dry_run=False)
        for resp in (dry, real):
            self.assertEqual(resp.data["rows_total"], TOTAL)
            self.assertEqual(resp.data["rows_ok"] + resp.data["failed"], TOTAL)
            self.assertEqual(resp.data["failed"], 2000)
            self.assertEqual(resp.data["rows_ok"], 18000)
            self.assertEqual(resp.data["imported"], 18000)
            self.assertTrue(resp.data["errors"])
            self.assertEqual(resp.data["errors"][0]["field"], "手机号")
        for key in ("rows_total", "rows_ok", "failed", "imported", "updated", "owners_created", "phones_created"):
            self.assertEqual(dry.data[key], real.data[key], key)
        self.assertEqual(RegistryUnit.objects.count(), 18000)
        self.assertFalse(RegistryUnit.objects.filter(room="0").exists())  # 第 0 行为非法行，不写入
        print(f"[TC-E2E-303] 20000 行含 2000 非法：预检 {dry_elapsed:.1f}s，正式 {real_elapsed:.1f}s（SQLite 内存库）")


@skipUnless(HAS_OPENPYXL, "未安装 openpyxl（画像 P4：不自行安装）")
class XlsxTemplateJourneyTests(ScaleJourneyBase):
    def test_tc_e2e_304_xlsx_template_fill_import_register_bind(self):
        """TC-E2E-304 / AC-093-01、AC-093-03、AC-093-04、AC-102-01：下载 xlsx 模板→填入含前导零的文本数据→预检→导入→业主注册自动绑定。"""
        resp = self.client_for(self.admin_token).get(
            "/api/v1/admin/registry/import/template", {"file_type": "xlsx"})
        self.assertEqual(resp.status_code, 200)
        wb = load_workbook(io.BytesIO(b"".join(resp.streaming_content) if resp.streaming else resp.content))
        ws = wb.worksheets[0]
        ws.delete_rows(2, ws.max_row)
        phone = "13700040001"
        ws.append(["1栋", "08", "8", "0801", "住宅", "89.50", "张三", phone])
        ws.append(["1栋", "08", "8", "0801", "住宅", "89.50", "李四", ""])
        ws.merge_cells("A2:A3")
        buf = io.BytesIO()
        wb.save(buf)

        def upload(dry):
            f = SimpleUploadedFile("registry.xlsx", buf.getvalue(), content_type="application/octet-stream")
            return self.upload(IMPORT_URL, {"file": f}, data={"dry_run": "1"} if dry else None,
                               token=self.admin_token)

        dry = upload(True)
        self.assertEqual(dry.status_code, 200, dry.content[:300])
        self.assertEqual((dry.data["failed"], dry.data["imported"]), (0, 1))
        self.assertEqual(RegistryUnit.objects.count(), 0)
        real = upload(False)
        self.assertEqual((real.status_code, real.data["failed"], real.data["owners_created"]), (200, 0, 2))
        unit = RegistryUnit.objects.get()
        self.assertEqual((unit.building, unit.unit_no, unit.room, unit.specific_part), ("1栋", "08", "0801", "1栋-08-8-0801"))

        _, token, _ = self.register(phone)
        member = Membership.objects.get(user=self.user_of(token), unit=unit)
        self.assertEqual((member.role, member.source), ("HEAD", "REGISTRY"))
