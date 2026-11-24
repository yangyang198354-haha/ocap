"""PHASE_07 单元测试：历史支出导入的纯函数规则（MOD-194）。
溯源：AC-333-01、AC-334-02、AC-334-03、AC-334-05。
"""
import io
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.ledger.historical import (
    MAX_FILE_BYTES, TEMPLATE_COLUMNS, ParsedRow, _parse_amount, _parse_date, _validate, build_template,
)


class HistoricalExpenseParseDateTests(SimpleTestCase):
    def test_accepts_iso_slash_date_and_date_object(self):
        self.assertEqual(_parse_date("2022-07-01"), date(2022, 7, 1))
        self.assertEqual(_parse_date("2022/07/01"), date(2022, 7, 1))
        self.assertEqual(_parse_date(date(2024, 3, 15)), date(2024, 3, 15))
        self.assertEqual(_parse_date(datetime(2026, 9, 30, 12, 0)), date(2026, 9, 30))

    def test_rejects_empty_and_invalid_and_nonexistent_dates(self):
        self.assertIsNone(_parse_date(""))
        self.assertIsNone(_parse_date(None))
        self.assertIsNone(_parse_date("2022-13-01"))
        self.assertIsNone(_parse_date("2022-02-30"))


class HistoricalExpenseParseAmountTests(SimpleTestCase):
    def setUp(self):
        patcher = patch("apps.ledger.historical.SystemConfig.amount_max",
                        return_value=Decimal("1000000"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_accepts_positive_up_to_two_decimals_and_commas(self):
        self.assertEqual(_parse_amount("1234.50"), Decimal("1234.50"))
        self.assertEqual(_parse_amount("1,234.50"), Decimal("1234.50"))

    def test_rejects_zero_negative_three_decimals_and_non_numeric(self):
        for raw in ("0", "-1", "1.234", "abc", "", None):
            self.assertIsNone(_parse_amount(raw), raw)


class HistoricalExpenseValidateTests(SimpleTestCase):
    def setUp(self):
        patcher = patch("apps.ledger.historical.SystemConfig.amount_max",
                        return_value=Decimal("1000000"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _values(self, **overrides):
        values = {"日期": "2022-07-01", "金额": "100.00", "支出类别": "维修",
                  "用途/事由": "更换电梯钢丝绳", "备注": ""}
        values.update(overrides)
        return values

    def test_valid_row_becomes_parsed_row(self):
        row = _validate(self._values(), 2)
        self.assertIsInstance(row, ParsedRow)
        self.assertEqual(row.occurred_on, date(2022, 7, 1))
        self.assertEqual(row.duplicate_key, (date(2022, 7, 1), 100, "维修", "更换电梯钢丝绳"))

    def test_future_date_is_error(self):
        result = _validate(self._values(日期="2999-01-01"), 2)
        self.assertIsInstance(result, str)
        self.assertIn("今天", result)

    def test_length_limits(self):
        self.assertIn("超长", _validate(self._values(支出类别="类" * 33), 2))
        self.assertIn("超长", _validate(self._values(**{"用途/事由": "用" * 201}), 2))
        self.assertIn("超长", _validate(self._values(备注="备" * 201), 2))

    def test_invalid_amount_and_date_return_reason(self):
        self.assertIsInstance(_validate(self._values(金额="0"), 2), str)
        self.assertIsInstance(_validate(self._values(日期=""), 2), str)


class HistoricalExpenseTemplateTests(SimpleTestCase):
    def test_xlsx_template_has_expected_columns_and_notes_sheet(self):
        from openpyxl import load_workbook

        content, content_type = build_template("xlsx")
        self.assertIn("spreadsheetml", content_type)
        wb = load_workbook(io.BytesIO(content))
        self.assertEqual(wb.sheetnames[0], "历史支出")
        self.assertEqual([c.value for c in wb["历史支出"][1]], list(TEMPLATE_COLUMNS))
        self.assertIn("填写说明", wb.sheetnames)

    def test_csv_template_header_is_bom_fixed_column_order(self):
        content, content_type = build_template("csv")
        self.assertTrue(content_type.startswith("text/csv"))
        text = content.decode("utf-8-sig")
        self.assertEqual(text.strip().split(","), list(TEMPLATE_COLUMNS))

    def test_unknown_file_type_rejected(self):
        from apps.core.errors import ApiError

        with self.assertRaises(ApiError):
            build_template("pdf")

    def test_size_limit_is_five_megabytes(self):
        self.assertEqual(MAX_FILE_BYTES, 5 * 1024 * 1024)
