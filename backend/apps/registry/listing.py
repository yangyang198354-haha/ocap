# MOD-145 / implements IFC-362 / depends registry.ordering、registry.models
"""清册列表的服务端自然顺序排序与分页包装（ADR-142）：规则唯一来源是 ordering.py。"""
from .models import RegistryUnit
from .ordering import Level, natural_key, unit_sort_key

SORT_FIELDS: tuple[str, ...] = ("building", "unit_no", "floor", "room")
_INDEX = {"building": 1, "unit_no": 2, "floor": 3, "room": 4}  # 在 (id, building, unit_no, floor, room) 中的位置


def ordered_unit_ids(qs, sort: str | None, order: str) -> list[int]:
    """qs 为已过滤的 RegistryUnit 查询集（不含 prefetch）。默认键为 unit_sort_key；指定 sort 时在默认序之上
    对该列的单段自然键做稳定排序（desc 用 reverse=True，等值项保持原次序），id 为终极并列键。"""
    rows = list(qs.order_by().values_list("id", "building", "unit_no", "floor", "room"))
    rows.sort(key=lambda r: unit_sort_key(r[1], r[2], r[3], r[4], r[0]))
    if sort is not None:
        index = _INDEX[sort]
        level: Level = sort  # type: ignore[assignment]
        rows.sort(key=lambda r: natural_key(r[index], level), reverse=(order == "desc"))
    return [r[0] for r in rows]


class OrderedUnitPage:
    """供 core.serializers.page_response 使用的鸭子类型包装：count() 与 __getitem__(slice)。"""

    def __init__(self, ids: list[int]) -> None:
        self._ids = ids

    def count(self) -> int:
        return len(self._ids)

    def __getitem__(self, key: slice) -> list[RegistryUnit]:
        page_ids = self._ids[key]
        by_id = {u.id: u for u in RegistryUnit.objects.filter(id__in=page_ids).prefetch_related("owners__phones")}
        return [by_id[i] for i in page_ids if i in by_id]
