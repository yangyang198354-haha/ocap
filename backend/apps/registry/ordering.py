# MOD-104 / implements IFC-285, IFC-286, IFC-287 / depends 无（仅标准库）
"""数字自然顺序排序规则（ADR-097、ADR-098）：楼栋、单元、楼层、户号及已认证房屋共用。"""
import re
from typing import Iterable, Literal

UNDERGROUND_BUILDING: str = "地下车位"  # 跨模块字面量的唯一定义处（ADR-099）
LEVEL_SUFFIXES: dict[str, str] = {"building": "栋", "unit_no": "单元", "floor": "层", "room": "号"}
Level = Literal["building", "unit_no", "floor", "room"]
# (层级, 数值, 文字段序列, 原始文本)；层级：-1 空；0 整数；1 其他文字；2 保留名
NaturalKey = tuple[int, int, tuple[tuple[int, int, str], ...], str]

_ARABIC_RE = re.compile(r"[0-9０-９]+")
_SEGMENT_RE = re.compile(r"(\d+|\D+)")
_CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_ZERO = ("零", "〇")


def _parse_cn_number(text: str) -> int | None:
    """中文数字 0~99（零〇一二两三四五六七八九十）；其余返回 None。"""
    if not text:
        return None
    if "十" in text:
        head, _, tail = text.partition("十")
        if "十" in tail:
            return None
        if head == "":
            tens = 1
        elif len(head) == 1 and head in _CN_DIGITS and head not in _CN_ZERO:
            tens = _CN_DIGITS[head]
        else:
            return None
        if tail == "":
            ones = 0
        elif len(tail) == 1 and tail in _CN_DIGITS and tail not in _CN_ZERO:
            ones = _CN_DIGITS[tail]
        else:
            return None
        return tens * 10 + ones
    if len(text) == 1 and text in _CN_DIGITS:
        return _CN_DIGITS[text]
    return None


def parse_integer_text(text: str | None, suffix: str = "") -> int | None:
    """解析带符号整数；去首尾空白与一次可选后缀；不匹配返回 None（IFC-287）。"""
    value = text.strip() if isinstance(text, str) else ""
    if suffix and value.endswith(suffix) and len(value) > len(suffix):
        value = value[: -len(suffix)].strip()
    if not value:
        return None
    negative = False
    if value[0] in ("负", "-"):
        negative = True
        value = value[1:]
    if not value:
        return None
    if _ARABIC_RE.fullmatch(value):
        number = int(value)
    else:
        parsed = _parse_cn_number(value)
        if parsed is None:
            return None
        number = parsed
    return -number if negative else number


def natural_key(value: str | None, level: Level) -> NaturalKey:
    """比较键（IFC-285）：空 < 整数（按数值）< 其他文字 < 保留名（仅楼栋"地下车位"）。"""
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        return (-1, 0, (), "")
    number = parse_integer_text(text, LEVEL_SUFFIXES[level])
    if number is not None:
        return (0, number, (), text)
    if level == "building" and text == UNDERGROUND_BUILDING:
        return (2, 0, (), text)
    segments = tuple(
        (0, int(part), "") if part[0].isdecimal() else (1, 0, part)
        for part in _SEGMENT_RE.findall(text)
    )
    return (1, 0, segments, text)


def unit_sort_key(building: str, unit_no: str, floor: str, room: str,
                  unit_id: int = 0) -> tuple[NaturalKey, NaturalKey, NaturalKey, NaturalKey, int]:
    """专有部分四级排序键，unit_id 为最终并列规则（IFC-286）。"""
    return (natural_key(building, "building"), natural_key(unit_no, "unit_no"),
            natural_key(floor, "floor"), natural_key(room, "room"), unit_id)


def sorted_values(values: Iterable[str], level: Level) -> list[str]:
    """去重后按自然顺序升序，不改写、不丢弃任何值。"""
    return sorted(set(values), key=lambda v: natural_key(v, level))
