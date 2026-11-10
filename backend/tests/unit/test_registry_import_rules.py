"""PHASE_07 单元测试：清册导入规则（MOD-031 纯函数）。

覆盖 US-092/093/096/098 中不依赖数据库的取值、拼接与模板契约。
"""
import csv
import io
from datetime import date, datetime
from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from apps.registry.import_spec import (
    COLUMN_AREA,
    COLUMN_BUILDING,
    COLUMN_OWNER,
    COLUMN_PHONE,
    IMPORT_COLUMNS,
    column_specs,
    parse_area,
    parse_unit_type,
    spec_payload,
    time_budget_seconds,
    validate_unit_fields,
)
from apps.registry.import_template import build_csv
from apps.registry.importing import cell_text
from apps.registry.models import build_specific_part


class ParseAreaTests(SimpleTestCase):
    def test_tc_unit_101_valid_areas(self):
        """TC-UNIT-101 / AC-096-01、AC-093-04：正整数与两位小数可解析，前导零不受影响。"""
        cases = {"89.50": Decimal("89.50"), "60": Decimal("60"), "0.01": Decimal("0.01"),
                 "12.5": Decimal("12.5")}
        for text, expected in cases.items():
            area, error = parse_area(text)
            self.assertEqual((area, error), (expected, None), text)

    def test_tc_unit_102_invalid_and_empty_areas(self):
        """TC-UNIT-102 / AC-096-04：abc/-5/0/12.345 各有明确文案；空值为未填而非错误。"""
        self.assertEqual(parse_area(""), (None, None))
        self.assertEqual(parse_area("  "), (None, None))
        for text in ("abc", "-5", "0", "0.00", "1e3"):
            area, error = parse_area(text)
            self.assertIsNone(area, text)
            self.assertEqual(error, "专有部分面积须为大于 0 的数值", text)
        area, error = parse_area("12.345")
        self.assertIsNone(area)
        self.assertEqual(error, "专有部分面积最多 2 位小数")

    def test_tc_unit_103_unit_type_labels(self):
        """TC-UNIT-103 / AC-096-03：中文标签映射为代码；集合外取值给出允许范围文案。"""
        mapping = {"住宅": "RESIDENCE", "公寓": "APARTMENT", "商铺": "SHOP",
                   "车位": "PARKING", "其他": "OTHER"}
        for label, code in mapping.items():
            self.assertEqual(parse_unit_type(label), (code, None))
        self.assertEqual(parse_unit_type(""), (None, None))
        code, error = parse_unit_type("别墅")
        self.assertIsNone(code)
        self.assertEqual(error, "专有部分类型不在允许范围内（住宅、公寓、商铺、车位、其他）")


class UnitFieldRuleTests(SimpleTestCase):
    def test_tc_unit_104_required_fields_and_order(self):
        """TC-UNIT-104 / AC-098-04：楼栋、户号必填；单元与楼层可空。"""
        base = dict(building="1", unit_no="", floor="", room="301")
        self.assertIsNone(validate_unit_fields(**base))
        self.assertEqual(validate_unit_fields(building="", unit_no="", floor="", room="301"), "缺少楼栋")
        self.assertEqual(validate_unit_fields(building="1", unit_no="", floor="", room=""), "缺少户号")
        self.assertEqual(validate_unit_fields(building="1", unit_no="u" * 33, floor="", room="301"),
                         "单元过长（最多 32 字符）")
        self.assertEqual(validate_unit_fields(building="1", unit_no="-", floor="", room="301"),
                         "单元不得含“-”")
        self.assertEqual(validate_unit_fields(building="1", unit_no="", floor="f" * 33, room="301"),
                         "楼层过长（最多 32 字符）")
        self.assertIsNone(validate_unit_fields(building="1", unit_no="", floor="", room="A-088"))

    def test_tc_unit_105_cell_text_normalization(self):
        """TC-UNIT-105 / AC-093-04：数字单元格不出现 .0，布尔与日期稳定输出。"""
        self.assertEqual(cell_text(None), "")
        self.assertEqual(cell_text("  0801 "), "0801")
        self.assertEqual(cell_text(True), "TRUE")
        self.assertEqual(cell_text(42), "42")
        self.assertEqual(cell_text(3.0), "3")
        self.assertEqual(cell_text(3.5), "3.5")
        self.assertEqual(cell_text(Decimal("89.50")), "89.5")
        self.assertEqual(cell_text(Decimal("140.00")), "140")
        self.assertEqual(cell_text(date(2026, 11, 10)), "2026-11-10")
        self.assertEqual(cell_text(datetime(2026, 11, 10, 8, 30)), "2026-11-10T08:30:00")

    def test_tc_unit_106_specific_part_skips_empty_levels(self):
        """TC-UNIT-106 / AC-098-01、AC-098-05：空层级不产生多余分隔符，四级齐全时与旧规则相同。"""
        self.assertEqual(build_specific_part("1", "2", "3", "301"), "1-2-3-301")
        self.assertEqual(build_specific_part("车库", "", "", "A-088"), "车库-A-088")
        self.assertEqual(build_specific_part("1", "", "3", "301"), "1-3-301")


class ImportSpecContractTests(SimpleTestCase):
    def test_tc_unit_107_spec_payload_matches_page_copy(self):
        """TC-UNIT-107 / AC-092-01：格式说明含文件类型、5MB、20000 行、首工作表与 8 列规则。"""
        payload = spec_payload()
        self.assertEqual(payload["file_types"], [".csv", ".xlsx"])
        self.assertEqual(payload["max_file_mb"], 5)
        self.assertEqual(payload["max_rows"], 20000)
        self.assertIn("第一个工作表", payload["excel_sheet_note"])
        self.assertEqual([c["name"] for c in payload["columns"]], IMPORT_COLUMNS)
        self.assertEqual(len(payload["columns"]), 8)
        required = {c["name"]: c["required"] for c in payload["columns"]}
        self.assertEqual(required[COLUMN_BUILDING], "必填")
        self.assertEqual(required[COLUMN_OWNER], "必填")
        self.assertEqual(required[COLUMN_PHONE], "选填")
        self.assertEqual(required[COLUMN_AREA], "仅车位必填")
        self.assertEqual(payload["time_budget_seconds"], 60)
        self.assertGreaterEqual(len(payload["notes"]), 5)
        text = "".join(payload["notes"])
        self.assertIn("单独一行", text)
        self.assertIn("姓名相同", text)

    def test_tc_unit_108_column_specs_cover_all_columns(self):
        """TC-UNIT-108 / AC-092-01：列规则表覆盖全部 8 列且每列有允许取值与示例。"""
        specs = column_specs()
        self.assertEqual([s.name for s in specs], IMPORT_COLUMNS)
        for spec in specs:
            self.assertTrue(spec.required and spec.allowed and spec.example, spec.name)

    @override_settings(REGISTRY_IMPORT_TIME_BUDGET_SECONDS="75")
    def test_tc_unit_109_time_budget_setting(self):
        """TC-UNIT-109 / AC-094-07：时间预算可由设置覆盖，非法值回落 60 秒。"""
        self.assertEqual(time_budget_seconds(), 75)
        with override_settings(REGISTRY_IMPORT_TIME_BUDGET_SECONDS="abc"):
            self.assertEqual(time_budget_seconds(), 60)


class CsvTemplateTests(SimpleTestCase):
    def test_tc_unit_110_csv_template_headers_examples_and_bom(self):
        """TC-UNIT-110 / AC-093-01、AC-093-02：UTF-8 BOM、8 列表头、4 个示例覆盖多业主/空手机号/车位。"""
        raw = build_csv()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(rows[0], IMPORT_COLUMNS)
        self.assertEqual(len(rows), 5)
        examples = rows[1:]
        same_unit = {}
        for row in examples:
            same_unit.setdefault(row[3], []).append(row)
        self.assertEqual(len(same_unit["301"]), 3)
        self.assertEqual(sum(1 for row in examples if not row[7]), 2)
        parking = next(row for row in examples if row[4] == "车位")
        self.assertEqual(parking[1:3], ["", ""])
        self.assertEqual(parking[5], "12.50")
