"""PHASE_07 单元测试：导入文件生成函数（MOD-110，IFC-298）与前导零保真。

关联 US-187（AC-187-01、AC-187-04）。只用合成数据（C-55）。
"""
import io

from django.test import SimpleTestCase
from openpyxl import load_workbook

from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.import_template import build_data_csv, build_data_xlsx
from apps.registry.importing import Deadline, read_rows

ROWS = [
    ["地下车位", "", "负一", "0801", "车位", "12.50", "测试甲", "13800000000;13800000001"],
    ["1", "2", "9", "902", "住宅", "89.50", "测试乙", ""],
]


class DataFileBuilderTests(SimpleTestCase):
    def _cells(self, name, content):
        return [[raw.cells[column] for column in IMPORT_COLUMNS]
                for raw in read_rows(name, content, Deadline(60))]

    def test_tc_unit_631_xlsx_header_and_leading_zero_roundtrip(self):
        """AC-187-01/04：xlsx 表头=导入模板 8 列；'0801'、手机号保持文本，read_rows 回读逐格相等。"""
        content = build_data_xlsx(ROWS)
        sheet = load_workbook(io.BytesIO(content)).active
        self.assertEqual([c.value for c in sheet[1]], list(IMPORT_COLUMNS))
        self.assertEqual(len(IMPORT_COLUMNS), 8)
        self.assertEqual(self._cells("x.xlsx", content), ROWS)
        self.assertEqual(sheet.cell(row=2, column=4).value, "0801")
        self.assertEqual(sheet.cell(row=2, column=4).data_type, "s")

    def test_tc_unit_632_csv_header_bom_and_leading_zero_roundtrip(self):
        """AC-187-01/04：csv UTF-8 带 BOM，表头一致，前导零与长数字原样。"""
        content = build_data_csv(ROWS)
        self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(content.decode("utf-8-sig").splitlines()[0], ",".join(IMPORT_COLUMNS))
        cells = self._cells("x.csv", content)
        self.assertEqual(cells, ROWS)
        self.assertEqual(cells[0][3], "0801")
        self.assertEqual(cells[0][7], "13800000000;13800000001")
