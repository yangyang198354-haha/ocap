"""MOD-031：清册导入规格（单一来源）。

列定义、限制常量、字段校验与文案都从这里取，导入引擎、模板下载与格式说明接口共用。
"""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.conf import settings

from .models import UNIT_TYPE_CHOICES

MAX_FILE_BYTES: int = 5 * 1024 * 1024
MAX_DATA_ROWS: int = 20000
DEFAULT_TIME_BUDGET_SECONDS: int = 60
MAX_AREA: Decimal = Decimal("99999999.99")

COLUMN_BUILDING = "楼栋"
COLUMN_UNIT = "单元"
COLUMN_FLOOR = "楼层"
COLUMN_ROOM = "户号"
COLUMN_TYPE = "专有部分类型"
COLUMN_AREA = "专有部分面积（平方米）"
COLUMN_OWNER = "业主姓名"
COLUMN_PHONE = "手机号"

IMPORT_COLUMNS: list[str] = [
    COLUMN_BUILDING,
    COLUMN_UNIT,
    COLUMN_FLOOR,
    COLUMN_ROOM,
    COLUMN_TYPE,
    COLUMN_AREA,
    COLUMN_OWNER,
    COLUMN_PHONE,
]

UNIT_TYPE_LABELS: dict[str, str] = {label: code for code, label in UNIT_TYPE_CHOICES}
UNIT_TYPE_TEXT = "、".join(label for _, label in UNIT_TYPE_CHOICES)

_AREA_RE = re.compile(r"^\d+(\.\d+)?$")


def time_budget_seconds() -> int:
    try:
        return int(getattr(settings, "REGISTRY_IMPORT_TIME_BUDGET_SECONDS", DEFAULT_TIME_BUDGET_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_TIME_BUDGET_SECONDS


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    required: str
    allowed: str
    example: str


def column_specs() -> list[ColumnSpec]:
    return [
        ColumnSpec(COLUMN_BUILDING, "必填", "最多 32 字符，不含“-”", "1栋"),
        ColumnSpec(COLUMN_UNIT, "选填", "最多 32 字符，不含“-”；没有单元留空", "1单元"),
        ColumnSpec(COLUMN_FLOOR, "选填", "最多 32 字符，不含“-”；没有楼层留空", "3"),
        ColumnSpec(COLUMN_ROOM, "必填", "最多 32 字符，可含“-”", "301"),
        ColumnSpec(COLUMN_TYPE, "新专有部分必填", f"取值：{UNIT_TYPE_TEXT}", "住宅"),
        ColumnSpec(COLUMN_AREA, "仅车位必填", "大于 0，最多 2 位小数", "89.50"),
        ColumnSpec(COLUMN_OWNER, "必填", "1~64 字符；同一专有部分多位业主各占一行", "张三"),
        ColumnSpec(COLUMN_PHONE, "选填", "11 位手机号；多个用英文分号 ; 分隔", "13800000001"),
    ]


def spec_payload() -> dict:
    return {
        "file_types": [".csv", ".xlsx"],
        "max_file_mb": MAX_FILE_BYTES // (1024 * 1024),
        "max_rows": MAX_DATA_ROWS,
        "excel_sheet_note": "仅读取第一个工作表",
        "time_budget_seconds": time_budget_seconds(),
        "unit_types": [{"code": code, "label": label} for code, label in UNIT_TYPE_CHOICES],
        "columns": [
            {"name": s.name, "required": s.required, "allowed": s.allowed, "example": s.example}
            for s in column_specs()
        ],
        "notes": [
            "同一专有部分有多位业主时，每位业主单独一行，并重复填写类型与面积。",
            "同一专有部分内姓名相同的行视为同一位业主，其手机号会合并。",
            "多位业主共用同一手机号会导致该行导入失败。",
            "没有登记手机号的业主只能在导入后通过产权申诉认证。",
            "类型、面积与已有记录不一致时，该专有部分本次导入失败，不会部分覆盖。",
            "CSV 请使用 UTF-8 编码；Excel 请使用 .xlsx（仅读取第一个工作表）。",
            "请勿用 Excel 直接另存 csv 改写编号（前导零会丢失），推荐使用 xlsx 模板。",
            "单个文件不超过 5 MB、数据行不超过 20000 行。",
        ],
    }


def _check_level(name: str, value: str, *, allow_dash: bool) -> str | None:
    if len(value) > 32:
        return f"{name}过长（最多 32 字符）"
    if not allow_dash and "-" in value:
        return f"{name}不得含“-”"
    return None


def validate_unit_fields(*, building: str, unit_no: str, floor: str, room: str) -> str | None:
    """返回首个错误文案或 None；单条接口与导入共用（顺序：楼栋 → 户号 → 单元 → 楼层）。"""
    building = (building or "").strip()
    unit_no = (unit_no or "").strip()
    floor = (floor or "").strip()
    room = (room or "").strip()

    if not building:
        return "缺少楼栋"
    error = _check_level("楼栋", building, allow_dash=False)
    if error:
        return error
    if not room:
        return "缺少户号"
    error = _check_level("户号", room, allow_dash=True)
    if error:
        return error
    for label, value in (("单元", unit_no), ("楼层", floor)):
        error = _check_level(label, value, allow_dash=False)
        if error:
            return error
    return None


def parse_area(text: str) -> tuple[Decimal | None, str | None]:
    """空值返回 (None, None)；合法返回 (Decimal, None)；非法返回 (None, 文案)。"""
    value = (text or "").strip()
    if not value:
        return None, None
    if not _AREA_RE.match(value):
        return None, "专有部分面积须为大于 0 的数值"
    try:
        area = Decimal(value)
    except InvalidOperation:
        return None, "专有部分面积须为大于 0 的数值"
    if area <= 0:
        return None, "专有部分面积须为大于 0 的数值"
    if -area.as_tuple().exponent > 2:
        return None, "专有部分面积最多 2 位小数"
    if area > MAX_AREA:
        return None, "专有部分面积超出可登记范围"
    return area, None


def parse_unit_type(text: str) -> tuple[str | None, str | None]:
    """空值返回 (None, None)；中文标签返回 (代码, None)；非法返回 (None, 文案)。"""
    value = (text or "").strip()
    if not value:
        return None, None
    code = UNIT_TYPE_LABELS.get(value)
    if not code:
        return None, f"专有部分类型不在允许范围内（{UNIT_TYPE_TEXT}）"
    return code, None
