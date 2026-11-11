# 手写迁移（画像 P6）：按 MOD-065 / IFC-244 重新生成专有部分标识。
# 规则为本次变更时刻的冻结副本，禁止随运行时 build_specific_part 修改（ADR-066）。
import re
import sys
from dataclasses import dataclass
from typing import Callable, Iterable

from django.db import migrations, transaction

PLACEHOLDER_PREFIX = "~regen~"
BATCH_SIZE = 200

_SUFFIXES = ("栋", "单元", "层", "号")
_PURE_NUMBER = re.compile(r"(?:负)?[0-9]+")


def _frozen_segment(value: str, suffix: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if text.endswith(suffix):
        return text
    if _PURE_NUMBER.fullmatch(text):
        return text + suffix
    return text


def _frozen_floor_is_implied_by_room(floor: str, room: str) -> bool:
    floor_text = (floor or "").strip()
    room_text = (room or "").strip()
    if not floor_text or not room_text:
        return False
    stem = floor_text[:-1] if floor_text.endswith("层") else floor_text
    if not stem:
        return False
    return room_text.startswith(stem + "层")


def _frozen_rule_v1(building: str, unit_no: str, floor: str, room: str) -> str:
    floor_text = (floor or "").strip()
    room_text = (room or "").strip()
    parts = [
        _frozen_segment(building, _SUFFIXES[0]),
        _frozen_segment(unit_no, _SUFFIXES[1]),
        "" if _frozen_floor_is_implied_by_room(floor_text, room_text) else _frozen_segment(floor_text, _SUFFIXES[2]),
        _frozen_segment(room_text, _SUFFIXES[3]),
    ]
    return "".join(part for part in parts if part)


def _frozen_legacy_rule(building: str, unit_no: str, floor: str, room: str) -> str:
    return "-".join(part for part in (building, unit_no, floor, room) if part)


@dataclass(frozen=True)
class UnitRow:
    id: int
    building: str
    unit_no: str
    floor: str
    room: str
    specific_part: str


@dataclass(frozen=True)
class RegenPlan:
    changes: list[tuple[int, str, str]]
    conflicts: list[tuple[list[int], str]]
    review: list[tuple[UnitRow, str]]


def _is_review_room(room: str) -> bool:
    text = (room or "").strip()
    return bool(text) and not _PURE_NUMBER.fullmatch(text)


def plan_regeneration(rows: Iterable[UnitRow],
                      rule: Callable[[str, str, str, str], str]) -> RegenPlan:
    changes: list[tuple[int, str, str]] = []
    finals: dict[int, str] = {}
    by_id: dict[int, UnitRow] = {}
    review: list[tuple[UnitRow, str]] = []
    for row in rows:
        by_id[row.id] = row
        new_value = rule(row.building, row.unit_no, row.floor, row.room)
        finals[row.id] = new_value
        if new_value != row.specific_part:
            changes.append((row.id, row.specific_part, new_value))
        if _is_review_room(row.room):
            review.append((row, new_value))

    groups: dict[str, list[int]] = {}
    for row_id, value in finals.items():
        groups.setdefault(value.casefold(), []).append(row_id)
    conflicts = [(ids, key) for key, ids in groups.items() if len(ids) > 1]
    return RegenPlan(changes=changes, conflicts=conflicts, review=review)


def _ordered_conflict_ids(plan: RegenPlan) -> list[int]:
    ids: list[int] = []
    for group_ids, _ in plan.conflicts:
        ids.extend(group_ids)
    return sorted(ids)


def _write_lines(stream, rows: Iterable[UnitRow], values: dict[int, str]) -> None:
    for row in rows:
        stream.write(f"{row.id}|{row.specific_part}|{values.get(row.id, '')}|"
                     f"{row.building}|{row.unit_no}|{row.floor}|{row.room}\n")


def _apply_plan(RegistryUnit, plan: RegenPlan, alias: str) -> None:
    if not plan.changes:
        return
    with transaction.atomic(using=alias):
        placeholders = [RegistryUnit(id=row_id, specific_part=f"{PLACEHOLDER_PREFIX}{row_id}")
                        for row_id, _, _ in plan.changes]
        RegistryUnit.objects.using(alias).bulk_update(placeholders, ["specific_part"], batch_size=BATCH_SIZE)
        final_rows = [RegistryUnit(id=row_id, specific_part=new_value)
                      for row_id, _, new_value in plan.changes]
        RegistryUnit.objects.using(alias).bulk_update(final_rows, ["specific_part"], batch_size=BATCH_SIZE)


def _regenerate(apps, schema_editor, rule: Callable[[str, str, str, str], str]) -> None:
    RegistryUnit = apps.get_model("registry", "RegistryUnit")
    alias = schema_editor.connection.alias
    rows = [
        UnitRow(id=item["id"], building=item["building"], unit_no=item["unit_no"],
                floor=item["floor"], room=item["room"], specific_part=item["specific_part"])
        for item in RegistryUnit.objects.using(alias).values(
            "id", "building", "unit_no", "floor", "room", "specific_part"
        ).iterator(chunk_size=1000)
    ]
    plan = plan_regeneration(rows, rule)
    if plan.conflicts:
        by_id = {row.id: row for row in rows}
        values = {row.id: rule(row.building, row.unit_no, row.floor, row.room) for row in rows}
        for group_ids, _ in plan.conflicts:
            _write_lines(sys.stderr, (by_id[group_id] for group_id in group_ids), values)
        raise RuntimeError(f"专有部分标识重新生成存在 {len(_ordered_conflict_ids(plan))} 条冲突记录，整批未生效")
    if RegistryUnit.objects.using(alias).filter(specific_part__startswith=PLACEHOLDER_PREFIX).exists():
        raise RuntimeError("专有部分标识中存在占位前缀 ~regen~，整批未生效")

    _apply_plan(RegistryUnit, plan, alias)

    sys.stdout.write(f"total={len(rows)} would_change={len(plan.changes)} review={len(plan.review)}\n")
    values = {row_id: value for row_id, _, value in plan.changes}
    _write_lines(sys.stdout, (row for row, _ in plan.review), values)


def regenerate_specific_parts(apps, schema_editor):
    _regenerate(apps, schema_editor, _frozen_rule_v1)


def restore_legacy_specific_parts(apps, schema_editor):
    _regenerate(apps, schema_editor, _frozen_legacy_rule)


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0004_phone_owner_required"),
    ]

    operations = [
        migrations.RunPython(regenerate_specific_parts, restore_legacy_specific_parts),
    ]
