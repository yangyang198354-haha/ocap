"""MOD-031：导入模板生成（IFC-158）。"""
import csv
import io

from .import_spec import EXAMPLE_ROWS, IMPORT_COLUMNS, SUFFIX_RULES, UNIT_TYPE_TEXT, column_specs

_NOTES = [
    "同一专有部分有多位业主时，每位业主单独一行，并重复填写类型与面积。",
    "同一专有部分内姓名相同的行视为同一位业主，其手机号会合并。",
    "没有登记手机号的业主只能在导入后通过产权申诉认证。",
    f"专有部分类型取值：{UNIT_TYPE_TEXT}。",
    "请勿用 Excel 直接另存 csv 改写编号（前导零会丢失），推荐使用 xlsx 模板；楼栋、单元、楼层、户号、手机号列为文本格式。",
    *SUFFIX_RULES,
]

# 数据表中需保持文本的列（A 楼栋、B 单元、C 楼层、D 户号、H 手机号）
_TEXT_COLUMNS = ["A", "B", "C", "D", "H"]


def _col_index(letter: str) -> int:
    return ord(letter) - ord("A") + 1


def build_csv() -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORT_COLUMNS)
    writer.writerows(EXAMPLE_ROWS)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def build_xlsx() -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "清册导入"
    sheet.append(IMPORT_COLUMNS)
    for row in EXAMPLE_ROWS:
        sheet.append(row)
    # DEF-007：楼栋/单元/楼层/户号/手机号整列设为文本，避免 Excel 把 0801 存成数字 801
    for column in _TEXT_COLUMNS:
        sheet.column_dimensions[column].number_format = "@"
        for row_cells in sheet.iter_rows(min_row=2, min_col=_col_index(column), max_col=_col_index(column)):
            for cell in row_cells:
                cell.number_format = "@"

    notes = workbook.create_sheet("填写说明")
    notes.append(["列名", "是否必填", "填写规则", "示例"])
    for spec in column_specs():
        notes.append([spec.name, spec.required, spec.allowed, spec.example])
    notes.append([])
    for note in _NOTES:
        notes.append([note])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
