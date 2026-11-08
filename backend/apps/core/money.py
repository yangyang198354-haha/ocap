"""金额序列化：统一两位小数（定点，避免浮点）。"""
from decimal import Decimal, ROUND_HALF_UP


def money(value) -> str:
    if value is None:
        return "0.00"
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"
