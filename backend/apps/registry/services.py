"""清册服务（MOD-033 / IFC-043、IFC-152、IFC-162）。"""
import re

from .models import RegistryPhone, RegistryUnit

_FLOOR_NUMBER_RE = re.compile(r"^(?P<sign>负|-)?(?P<number>\d+)$")


def _floor_sort_key(value: str) -> tuple:
    """楼层按数值升序（负层在前）；非纯数字楼层排在数字之后，按文本排序。"""
    text = (value or "").strip()
    match = _FLOOR_NUMBER_RE.match(text)
    if not match:
        return (1, 0, text)
    number = int(match.group("number"))
    if match.group("sign"):
        number = -number
    return (0, number, text)


class RegistryService:
    @staticmethod
    def phone_registered(unit_id: int, phone: str) -> bool:
        return RegistryPhone.objects.filter(unit_id=unit_id, phone=phone).exists()

    @staticmethod
    def get_unit(unit_id: int) -> RegistryUnit | None:
        return RegistryUnit.objects.filter(id=unit_id).first()

    @staticmethod
    def units_by_phone(phone: str) -> list[RegistryUnit]:
        """该手机号登记的全部专有部分（IFC-162，按 id 升序去重）。"""
        if not phone:
            return []
        return list(RegistryUnit.objects.filter(phones__phone=phone).distinct().order_by("id"))

    @staticmethod
    def options(*, building: str | None = None, unit_no: str | None = None,
                floor: str | None = None) -> dict:
        """逐级选项；参数为 None 表示"尚未选择"，空串表示"该层为空"（IFC-152）。"""
        qs = RegistryUnit.objects.all()
        if building is not None:
            qs = qs.filter(building=building)
        if unit_no is not None:
            qs = qs.filter(unit_no=unit_no)
        if floor is not None:
            qs = qs.filter(floor=floor)

        skipped: list[str] = []
        if building is None:
            values = sorted(set(qs.values_list("building", flat=True)))
            return {"level": "building", "skipped": skipped, "has_empty": False,
                    "options": [{"value": v} for v in values]}

        for level, column in (("unit_no", "unit_no"), ("floor", "floor")):
            if (unit_no if level == "unit_no" else floor) is not None:
                continue
            values = sorted(set(qs.values_list(column, flat=True)),
                            key=_floor_sort_key if level == "floor" else None)
            non_empty = [v for v in values if v]
            if not non_empty:
                skipped.append(level)
                continue
            return {"level": level, "skipped": skipped, "has_empty": "" in values,
                    "options": [{"value": v} for v in non_empty]}

        options = []
        for unit in qs.order_by("room"):
            parts = []
            type_label = unit.get_unit_type_display() if unit.unit_type else None
            if type_label:
                parts.append(type_label)
            if unit.area is not None:
                parts.append(f"{unit.area} ㎡")
            options.append({
                "value": unit.room,
                "unit_id": unit.id,
                "unit_type": unit.unit_type,
                "unit_type_label": type_label,
                "area": str(unit.area) if unit.area is not None else None,
                "label": f"{unit.room}（{' '.join(parts)}）" if parts else unit.room,
            })
        return {"level": "room", "skipped": skipped, "has_empty": False, "options": options}
