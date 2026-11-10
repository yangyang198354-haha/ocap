"""MOD-031：导入模板生成（IFC-158）。"""
import csv
import io

from .import_spec import IMPORT_COLUMNS, UNIT_TYPE_TEXT, column_specs

# 示例覆盖：同一专有部分 3 行（多位业主）、一位无手机号业主、一个车位（单元/楼层为空）
EXAMPLE_ROWS = [
    ["1栋", "1单元", "3", "301", "住宅", "89.50", "张三", "13800000001"],
    ["1栋", "1单元", "3", "301", "住宅", "89.50", "李四", "13800000002"],
    ["1栋", "1单元", "3", "301", "住宅", "89.50", "王芳", ""],
    ["车库", "", "", "A-088", "车位", "12.50", "赵云", ""],
]

_NOTES = [
    "同一专有部分有多位业主时，每位业主单独一行，并重复填写类型与面积。",
    "同一专有部分内姓名相同的行视为同一位业主，其手机号会合并。",
    "没有登记手机号的业主只能在导入后通过产权申诉认证。",
    f"专有部分类型取值：{UNIT_TYPE_TEXT}。",
]


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
