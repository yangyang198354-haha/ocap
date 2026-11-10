"""PHASE_07 单元测试补充（缺陷回流 DEF-007~009，TC-UNIT-307 起）。

xlsx 工作簿在测试内用 openpyxl 构造，不入库二进制文件；依赖缺失时 skip 并写明原因。
"""
import io
from unittest import mock, skipUnless

from django.test import SimpleTestCase

from apps.core.errors import ApiError
from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.importing import Deadline, read_rows
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.auto_bind import AutoBindService
from apps.residency.models import Membership
from apps.residency.services import MembershipService
from tests.support import ApiTestBase

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:  # pragma: no cover
    HAS_OPENPYXL = False

NEED_OPENPYXL = skipUnless(HAS_OPENPYXL, "未安装 openpyxl（画像 P4：不自行安装）")


def workbook_bytes(build) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(IMPORT_COLUMNS)
    build(wb, ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@NEED_OPENPYXL
class XlsxUnitTests(SimpleTestCase):
    def test_tc_unit_307_template_text_columns(self):
        """TC-UNIT-307 / AC-093-04（DEF-007）：build_xlsx 的 A/B/C/D/H 列为文本格式，E/F/G 不是。"""
        from openpyxl import load_workbook

        from apps.registry.import_template import build_xlsx

        sheet = load_workbook(io.BytesIO(build_xlsx())).worksheets[0]
        for col in "ABCDH":
            self.assertEqual(sheet.column_dimensions[col].number_format, "@", col)
            for r in range(2, 6):
                self.assertEqual(sheet[f"{col}{r}"].number_format, "@", f"{col}{r}")
        for col in "EFG":
            self.assertEqual(sheet[f"{col}2"].number_format, "General", col)

    def test_tc_unit_309_read_rows_merged_cells_hidden_column_second_sheet(self):
        """TC-UNIT-309 / AC-093-03（DEF-008）：合并区域非首行取到左上角值；隐藏列、第二工作表不影响。"""
        def build(wb, ws):
            for i, name in enumerate(["张三", "李四", "王五"], start=2):
                ws.append([None, "1单元", "3", f"30{i}", "住宅", "89.50", name, ""])
            ws["A2"] = "1栋"
            ws.merge_cells("A2:A4")
            ws.column_dimensions["E"].hidden = True
            other = wb.create_sheet("填写说明")
            other.append(["楼栋", "垃圾"])

        rows = read_rows("x.xlsx", workbook_bytes(build), Deadline(60))
        self.assertEqual([r.cells["楼栋"] for r in rows], ["1栋", "1栋", "1栋"])
        self.assertEqual([r.cells["业主姓名"] for r in rows], ["张三", "李四", "王五"])
        self.assertEqual([r.row_no for r in rows], [2, 3, 4])
        self.assertEqual({r.cells["专有部分类型"] for r in rows}, {"住宅"})

    def test_tc_unit_310_read_rows_text_cells_kept(self):
        """TC-UNIT-310 / AC-093-04：文本 "0801"/"08"/"13800000000" 原样；数值整数不带 ".0"。"""
        def build(wb, ws):
            ws.append(["1栋", "08", "8", "0801", "住宅", 89.5, "张三", "13800000000"])
            ws["D2"].number_format = "@"
            ws.append(["1栋", "08", 3.0, 801, "住宅", 89.5, "李四", ""])

        rows = read_rows("x.xlsx", workbook_bytes(build), Deadline(60))
        self.assertEqual((rows[0].cells["单元"], rows[0].cells["户号"], rows[0].cells["手机号"]),
                         ("08", "0801", "13800000000"))
        self.assertEqual((rows[1].cells["楼层"], rows[1].cells["户号"]), ("3", "801"))


class AutoBindIsolationUnitTests(ApiTestBase):
    def _three_units(self, phone):
        units = []
        for room in ("101", "102", "103"):
            unit = RegistryUnit.objects.create(building="1", unit_no="1", floor="1", room=room)
            owner = RegistryOwner.objects.create(unit=unit, name=f"业主{room}")
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
            units.append(unit)
        return units

    def test_tc_unit_308_one_unit_failure_does_not_stop_others(self):
        """TC-UNIT-308 / AC-102-02（DEF-009）：3 个单元中 1 个抛异常（另试 ApiError），其余仍绑定且库状态正确。"""
        for failure in (RuntimeError("boom"), ApiError("SOME_ERROR", "拒绝")):
            with self.subTest(failure=type(failure).__name__):
                Membership.objects.all().delete()
                RegistryPhone.objects.all().delete()
                RegistryOwner.objects.all().delete()
                RegistryUnit.objects.all().delete()
                phone = "13800000099" if isinstance(failure, RuntimeError) else "13800000098"
                units = self._three_units(phone)
                user, _ = self.make_user(phone=phone)
                real = MembershipService.certify_owner
                bad_unit_id = units[0].id

                def patched(user_id, unit_id, source, origin=None):
                    if unit_id == bad_unit_id:
                        raise failure
                    return real(user_id, unit_id, source, origin=origin)

                with mock.patch.object(MembershipService, "certify_owner", side_effect=patched), \
                        self.assertLogs("apps.residency.auto_bind", level="WARNING"):
                    bound = AutoBindService.bind_by_phone(user)

                self.assertEqual({b.unit_id for b in bound}, {units[1].id, units[2].id})
                self.assertEqual(
                    set(Membership.objects.filter(user=user, ended_at__isnull=True).values_list("unit_id", flat=True)),
                    {units[1].id, units[2].id})
                self.assertFalse(Membership.objects.filter(user=user, unit=units[0]).exists())
                self.assertEqual(Membership.objects.filter(user=user, role="HEAD").count(), 2)
