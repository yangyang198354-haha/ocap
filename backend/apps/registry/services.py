"""清册服务（IFC-043）。"""
from .models import RegistryPhone, RegistryUnit


class RegistryService:
    @staticmethod
    def phone_registered(unit_id: int, phone: str) -> bool:
        return RegistryPhone.objects.filter(unit_id=unit_id, phone=phone).exists()

    @staticmethod
    def get_unit(unit_id: int) -> RegistryUnit | None:
        return RegistryUnit.objects.filter(id=unit_id).first()

    @staticmethod
    def options(*, building: str | None = None, unit_no: str | None = None,
                floor: str | None = None) -> dict:
        qs = RegistryUnit.objects.all()
        if building:
            qs = qs.filter(building=building)
        if unit_no:
            qs = qs.filter(unit_no=unit_no)
        if floor:
            qs = qs.filter(floor=floor)
        if not building:
            values = sorted({u for u in qs.values_list("building", flat=True)})
            return {"level": "building", "options": [{"value": v} for v in values]}
        if not unit_no:
            values = sorted({u for u in qs.values_list("unit_no", flat=True)})
            return {"level": "unit_no", "options": [{"value": v} for v in values]}
        if not floor:
            values = sorted({u for u in qs.values_list("floor", flat=True)})
            return {"level": "floor", "options": [{"value": v} for v in values]}
        rows = qs.order_by("room")
        return {"level": "room",
                "options": [{"value": r.room, "unit_id": r.id} for r in rows]}
