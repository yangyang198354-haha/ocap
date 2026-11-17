# MOD-134 / implements IFC-338 / depends 无（仅标准库）
"""专有部分类型与面积的展示口径（/me 与 /me/housing 共用，未登记显示"未登记"）。"""
from decimal import Decimal

UNREGISTERED = "未登记"


def unit_type_label(unit) -> str:
    return unit.get_unit_type_display() if unit.unit_type else UNREGISTERED


def area_text(unit) -> str | None:
    return str(unit.area.quantize(Decimal("0.01"))) if unit.area is not None else None


def area_display(unit) -> str:
    text = area_text(unit)
    return f"{text} ㎡" if text else UNREGISTERED
