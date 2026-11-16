# MOD-111 / implements IFC-301 / depends MOD-112（SHOP_BUILDING）、registry.underground、registry.models、core.audit
"""商铺归类规则与改库（AUTH-03）：识别、冲突预演、备份、事务内更新与核对、还原。

只改 RegistryUnit.building / unit_no / specific_part / updated_at，且仅限类型为商铺的记录；
不触碰业主、手机号与认证绑定（C-58）。备份与日志不含姓名、手机号（C-59）。
"""
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Literal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService

from .models import RegistryUnit, build_specific_part
from .ordering import SHOP_BUILDING
from .underground import (
    ApplyResult, BackupInfo, RestoreResult, UnitRow, _chunks, _differences,
    _read_backup, load_rows, read_counts, unaffected_fingerprint, verify_backup,
)

SHOP_TYPE: str = "SHOP"
SHOP_BACKUP_FORMAT: str = "ocap-shop-backup/1"
UNIT_NO_MAX: int = 32  # RegistryUnit.unit_no 的 max_length（registry/models.py）
_DIGITS_RE = re.compile(r"[0-9０-９]+")


class ShopRelocationConflict(Exception):
    """改后专有部分标识或四元组与既有记录冲突，或存在无法归类的记录。"""


class ShopRelocationAborted(Exception):
    """计划与备份/期望数量不一致、更新行数异常或并发冲突。"""


class ShopRelocationVerifyError(Exception):
    """事务内核对失败（调用方已回滚）。"""


@dataclass(frozen=True)
class ShopMove:
    unit_id: int
    old_building: str
    old_unit_no: str
    old_specific_part: str
    new_unit_no: str
    new_specific_part: str


@dataclass(frozen=True)
class ShopConflict:
    kind: Literal["specific_part", "tuple", "unit_no_occupied", "too_long", "empty_building"]
    key: str
    unit_ids: tuple[int, ...]


@dataclass(frozen=True)
class ShopPlan:
    total_units: int
    shop_units: int
    already_target: int
    moves: tuple[ShopMove, ...]
    conflicts: tuple[ShopConflict, ...]
    old_building_counts: dict[str, int]
    second_level_values: int
    floor_spellings: dict[str, int]
    foreign_in_target: int


def shop_unit_no(old_building: str) -> str:
    """原楼栋/门牌 → 第二级取值：纯数字补"栋"，其余原样（去首尾空白）；空串返回空串（IFC-301）。"""
    text = old_building.strip() if isinstance(old_building, str) else ""
    if text and _DIGITS_RE.fullmatch(text):
        return text + "栋"
    return text


def plan_shop_relocation(rows: Iterable[UnitRow]) -> ShopPlan:
    """纯函数：识别（类型为商铺且楼栋非"商铺"）→ 最终状态冲突预演（IFC-301）。"""
    rows = list(rows)
    shop_units = 0
    already_target = 0
    foreign_in_target = 0
    moves: list[ShopMove] = []
    conflicts: list[ShopConflict] = []
    final_building: dict[int, str] = {}
    final_unit_no: dict[int, str] = {}
    final_sp: dict[int, str] = {}

    for row in rows:
        final_building[row.id] = row.building
        final_unit_no[row.id] = row.unit_no
        final_sp[row.id] = row.specific_part
        if row.unit_type != SHOP_TYPE:
            if row.building == SHOP_BUILDING:
                foreign_in_target += 1
            continue
        shop_units += 1
        if row.building == SHOP_BUILDING:
            already_target += 1
            continue
        new_unit_no = shop_unit_no(row.building)
        if not new_unit_no:
            conflicts.append(ShopConflict("empty_building", row.building, (row.id,)))
            continue
        if row.unit_no.strip():
            conflicts.append(ShopConflict("unit_no_occupied", f"{row.building}|{row.unit_no}", (row.id,)))
            continue
        if len(new_unit_no) > UNIT_NO_MAX:
            conflicts.append(ShopConflict("too_long", row.building, (row.id,)))
            continue
        new_sp = build_specific_part(SHOP_BUILDING, new_unit_no, row.floor, row.room)
        moves.append(ShopMove(row.id, row.building, row.unit_no, row.specific_part, new_unit_no, new_sp))
        final_building[row.id] = SHOP_BUILDING
        final_unit_no[row.id] = new_unit_no
        final_sp[row.id] = new_sp

    moved_ids = {m.unit_id for m in moves}
    by_sp: dict[str, list[int]] = {}
    by_tuple: dict[tuple[str, str, str, str], list[int]] = {}
    for row in rows:
        by_sp.setdefault(final_sp[row.id].casefold(), []).append(row.id)
        key = (final_building[row.id], final_unit_no[row.id], row.floor, row.room)
        by_tuple.setdefault(key, []).append(row.id)
    for ids in by_sp.values():
        if len(ids) > 1 and moved_ids.intersection(ids):
            conflicts.append(ShopConflict("specific_part", final_sp[ids[0]], tuple(ids)))
    for key, ids in by_tuple.items():
        if len(ids) > 1 and moved_ids.intersection(ids):
            conflicts.append(ShopConflict("tuple", "|".join(key), tuple(ids)))

    floors = Counter(row.floor for row in rows if row.id in moved_ids)
    return ShopPlan(
        total_units=len(rows), shop_units=shop_units, already_target=already_target,
        moves=tuple(moves), conflicts=tuple(conflicts),
        old_building_counts=dict(Counter(m.old_building for m in moves)),
        second_level_values=len({m.new_unit_no for m in moves}),
        floor_spellings=dict(floors), foreign_in_target=foreign_in_target)


def apply_shop_relocation(plan: ShopPlan, backup: BackupInfo, expected_changes: int) -> ApplyResult:
    """事务内锁定商铺记录、重算计划、逐行带旧值更新并核对；任何不符抛错并回滚。"""
    if plan.conflicts:
        raise ShopRelocationConflict(f"存在 {len(plan.conflicts)} 处冲突，整批停止")
    if expected_changes != len(plan.moves):
        raise ShopRelocationAborted(f"--expect-changes={expected_changes} 与计划 {len(plan.moves)} 不符")
    info, backup_rows = _read_backup(backup.path, format_name=SHOP_BACKUP_FORMAT)
    backup_ids = {r.id for r in backup_rows}
    if info.sha256 != backup.sha256 or backup_ids != {m.unit_id for m in plan.moves}:
        raise ShopRelocationAborted("备份内容与计划不一致")
    old_building_by_id = {r.id: r.building for r in backup_rows}

    try:
        with transaction.atomic():
            before = read_counts()
            list(RegistryUnit.objects.select_for_update().filter(unit_type=SHOP_TYPE)
                 .values_list("id", flat=True))
            fresh = plan_shop_relocation(load_rows())
            if fresh.conflicts:
                raise ShopRelocationConflict(f"存在 {len(fresh.conflicts)} 处冲突，整批停止")
            if len(fresh.moves) != expected_changes or {m.unit_id for m in fresh.moves} != backup_ids:
                raise ShopRelocationAborted("事务内重算的计划与备份不一致")
            fingerprint_before = unaffected_fingerprint(backup_ids)
            now = timezone.now()
            for move in fresh.moves:
                updated = RegistryUnit.objects.filter(
                    id=move.unit_id, building=move.old_building, unit_no=move.old_unit_no).update(
                    building=SHOP_BUILDING, unit_no=move.new_unit_no,
                    specific_part=move.new_specific_part, updated_at=now)
                if updated != 1:
                    raise ShopRelocationAborted(f"记录 {move.unit_id} 更新行数异常（{updated}）")
            AuditService.record(
                actor=AuditActor("SYSTEM", None, "management_command"), action="REGISTRY_UNIT_CHANGED",
                object_type="registry", object_id="shop_relocation", result="SUCCESS",
                detail={"change": "shop_relocation", "moved": len(fresh.moves)})
            after = read_counts()
            if after != before:
                raise ShopRelocationVerifyError("计数核对失败：专有部分/业主/手机号/有效认证绑定数发生变化")
            lost = 0
            for part in _chunks(sorted(backup_ids)):
                for unit_id, building, unit_no in RegistryUnit.objects.filter(id__in=part).values_list(
                        "id", "building", "unit_no"):
                    if building != SHOP_BUILDING or unit_no != shop_unit_no(old_building_by_id[unit_id]):
                        lost += 1
            if lost:
                raise ShopRelocationVerifyError(f"核对失败：{lost} 条被改记录的楼栋或原楼栋/门牌信息不符")
            if unaffected_fingerprint(backup_ids) != fingerprint_before:
                raise ShopRelocationVerifyError("核对失败：未受影响记录发生变化")
    except IntegrityError as exc:
        raise ShopRelocationAborted("写入触发唯一约束，事务已回滚") from exc
    return ApplyResult(moved=len(fresh.moves), before=before, after=after)


def restore_shop_backup(path: Path, apply: bool) -> RestoreResult:
    """按备份把全部列原值写回；apply=False 只报告。还原前要求这些记录当前仍是改后状态。"""
    verify_backup(path, format_name=SHOP_BACKUP_FORMAT)
    info, rows = _read_backup(path, format_name=SHOP_BACKUP_FORMAT)
    before = read_counts()
    missing: list[int] = []
    for part in _chunks([r.id for r in rows]):
        found = dict(RegistryUnit.objects.filter(id__in=part).values_list("id", "building"))
        missing.extend(i for i in part if found.get(i) != SHOP_BUILDING)
    if missing:
        raise ShopRelocationAborted(f"{len(missing)} 条记录当前不是修正后的状态，已中止：{missing[:20]}")
    if not apply:
        return RestoreResult(restored=0, differences=_differences(rows), before=before, after=before)
    try:
        with transaction.atomic():
            for r in rows:
                RegistryUnit.objects.filter(id=r.id).update(
                    building=r.building, unit_no=r.unit_no, floor=r.floor, room=r.room,
                    specific_part=r.specific_part, unit_type=r.unit_type,
                    area=Decimal(r.area) if r.area is not None else None,
                    created_at=datetime.fromisoformat(r.created_at),
                    updated_at=datetime.fromisoformat(r.updated_at))
            after = read_counts()
            if after != info.counts:
                raise ShopRelocationVerifyError("还原后计数与备份头部不一致")
            diff = _differences(rows)
            if diff:
                raise ShopRelocationVerifyError(f"还原后仍有 {diff} 条记录与备份不一致")
    except IntegrityError as exc:
        raise ShopRelocationAborted("还原触发唯一约束，事务已回滚") from exc
    return RestoreResult(restored=len(rows), differences=0, before=before, after=after)
