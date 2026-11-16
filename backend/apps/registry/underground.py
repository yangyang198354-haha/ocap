# MOD-109 / implements IFC-294 / depends MOD-104（registry.ordering）、registry.models、core.audit
"""地下车位归属规则与修正（AUTH-02）：识别、冲突预演、备份、事务内更新与核对、还原。

只改 RegistryUnit.building / specific_part / updated_at；不触碰业主、手机号与认证绑定（C-52）。
备份与日志不含姓名、手机号（C-55）。
"""
import hashlib
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Literal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService

from .models import RegistryOwner, RegistryPhone, RegistryUnit, build_specific_part
from .ordering import UNDERGROUND_BUILDING, parse_integer_text

TARGET_BUILDING: str = UNDERGROUND_BUILDING
BACKUP_FORMAT: str = "ocap-underground-backup/1"
_CHUNK = 500
_ASSUMED_MAIN_BUILDINGS = ("1", "1栋")  # Q-SF-02b-3：预期的"负层车位所在楼栋"写法


class RelocationConflict(Exception):
    """改后专有部分标识或四元组与既有记录冲突。"""


class RelocationAborted(Exception):
    """计划与备份/期望数量不一致、更新行数异常或并发冲突。"""


class RelocationVerifyError(Exception):
    """事务内核对失败（调用方已回滚）。"""


class BackupError(Exception):
    """备份/还原文件问题。"""


@dataclass(frozen=True)
class UnitRow:
    id: int
    building: str
    unit_no: str
    floor: str
    room: str
    specific_part: str
    unit_type: str | None
    area: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Move:
    unit_id: int
    old_building: str
    old_specific_part: str
    new_specific_part: str


@dataclass(frozen=True)
class Conflict:
    kind: Literal["specific_part", "tuple"]
    key: str
    unit_ids: tuple[int, ...]


@dataclass(frozen=True)
class RelocationPlan:
    total_units: int
    candidates: int
    already_target: int
    moves: tuple[Move, ...]
    conflicts: tuple[Conflict, ...]
    old_building_counts: dict[str, int]
    parking_floor_spellings: dict[str, tuple[int, bool]]
    negative_floor_non_parking: int
    other_building_negative_parking: int


@dataclass(frozen=True)
class Counts:
    units: int
    owners: int
    phones: int
    active_memberships: int


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    records: int
    counts: Counts
    sha256: str


@dataclass(frozen=True)
class ApplyResult:
    moved: int
    before: Counts
    after: Counts


@dataclass(frozen=True)
class RestoreResult:
    restored: int
    differences: int
    before: Counts
    after: Counts


def is_negative_floor(floor: str | None) -> bool:
    """楼层为负层（"-1"、"负1"、"负一"、"负一层"…）；与排序同口径（IFC-287）。"""
    number = parse_integer_text(floor, "层")
    return number is not None and number < 0


def _chunks(values: list, size: int = _CHUNK):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def plan_relocation(rows: Iterable[UnitRow]) -> RelocationPlan:
    """纯函数：识别（类型为车位且楼层为负层）→ 最终状态冲突预演（IFC-294）。"""
    rows = list(rows)
    candidates = 0
    already_target = 0
    moves: list[Move] = []
    floor_counter: Counter = Counter()
    floor_recognized: dict[str, bool] = {}
    negative_non_parking = 0
    final_building: dict[int, str] = {}
    final_sp: dict[int, str] = {}

    for row in rows:
        negative = is_negative_floor(row.floor)
        if row.unit_type == "PARKING":
            floor_counter[row.floor] += 1
            floor_recognized[row.floor] = negative
        elif negative:
            negative_non_parking += 1
        final_building[row.id] = row.building
        final_sp[row.id] = row.specific_part
        if row.unit_type == "PARKING" and negative:
            candidates += 1
            if row.building == TARGET_BUILDING:
                already_target += 1
                continue
            new_sp = build_specific_part(TARGET_BUILDING, row.unit_no, row.floor, row.room)
            moves.append(Move(row.id, row.building, row.specific_part, new_sp))
            final_building[row.id] = TARGET_BUILDING
            final_sp[row.id] = new_sp

    moved_ids = {m.unit_id for m in moves}
    conflicts: list[Conflict] = []
    by_sp: dict[str, list[int]] = {}
    by_tuple: dict[tuple[str, str, str, str], list[int]] = {}
    for row in rows:
        by_sp.setdefault(final_sp[row.id].casefold(), []).append(row.id)
        key = (final_building[row.id], row.unit_no, row.floor, row.room)
        by_tuple.setdefault(key, []).append(row.id)
    for key, ids in by_sp.items():
        if len(ids) > 1 and moved_ids.intersection(ids):
            conflicts.append(Conflict("specific_part", final_sp[ids[0]], tuple(ids)))
    for key, ids in by_tuple.items():
        if len(ids) > 1 and moved_ids.intersection(ids):
            conflicts.append(Conflict("tuple", "|".join(key), tuple(ids)))

    old_counts = Counter(m.old_building for m in moves)
    return RelocationPlan(
        total_units=len(rows),
        candidates=candidates,
        already_target=already_target,
        moves=tuple(moves),
        conflicts=tuple(conflicts),
        old_building_counts=dict(old_counts),
        parking_floor_spellings={f: (n, floor_recognized[f]) for f, n in floor_counter.items()},
        negative_floor_non_parking=negative_non_parking,
        other_building_negative_parking=sum(
            1 for m in moves if m.old_building.strip() not in _ASSUMED_MAIN_BUILDINGS),
    )


def _to_row(unit: RegistryUnit) -> UnitRow:
    return UnitRow(
        id=unit.id, building=unit.building, unit_no=unit.unit_no, floor=unit.floor, room=unit.room,
        specific_part=unit.specific_part, unit_type=unit.unit_type,
        area=str(unit.area) if unit.area is not None else None,
        created_at=unit.created_at.isoformat(), updated_at=unit.updated_at.isoformat())


def load_rows() -> list[UnitRow]:
    """只读：全部专有部分（不含业主与手机号）。"""
    return [_to_row(u) for u in RegistryUnit.objects.order_by("id").iterator(chunk_size=1000)]


def read_counts() -> Counts:
    from apps.residency.models import Membership  # 函数内延迟导入，避免 registry → residency 模块级依赖

    return Counts(
        units=RegistryUnit.objects.count(),
        owners=RegistryOwner.objects.count(),
        phones=RegistryPhone.objects.count(),
        active_memberships=Membership.objects.filter(ended_at__isnull=True).count(),
    )


def unaffected_fingerprint(exclude_ids: set[int]) -> str:
    """除被改记录外所有记录的内容指纹（id、四级取值、标识、类型、面积）。"""
    digest = hashlib.sha256()
    qs = RegistryUnit.objects.order_by("id").values_list(
        "id", "building", "unit_no", "floor", "room", "specific_part", "unit_type", "area")
    for item in qs.iterator(chunk_size=1000):
        if item[0] in exclude_ids:
            continue
        digest.update(json.dumps([str(v) if v is not None else None for v in item],
                                 ensure_ascii=False).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _counts_dict(counts: Counts) -> dict:
    return asdict(counts)


def write_backup(path: Path, plan, rows: list[UnitRow], counts: Counts,
                 *, format_name: str = BACKUP_FORMAT) -> BackupInfo:
    """JSON Lines 备份：头 + 被改记录 + 末行 sha256；0600、O_EXCL、fsync、回读校验后才返回。

    plan 为任何带 moves（元素含 unit_id）的计划（地下车位 RelocationPlan 或商铺 ShopPlan，IFC-301）。
    """
    moved_ids = {m.unit_id for m in plan.moves}
    records = [r for r in rows if r.id in moved_ids]
    lines = [json.dumps({"format": format_name, "created_at": timezone.now().isoformat(),
                         "records": len(records), "counts": _counts_dict(counts)}, ensure_ascii=False)]
    lines.extend(json.dumps(asdict(r), ensure_ascii=False) for r in records)
    body = ("\n".join(lines) + "\n").encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    payload = body + json.dumps({"sha256": digest}).encode("utf-8") + b"\n"
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise BackupError(f"无法创建备份文件：{exc.strerror}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        info = verify_backup(path, format_name=format_name)
    except Exception:
        try:
            os.unlink(str(path))
        except OSError:
            pass
        raise
    if info.records != len(records) or info.sha256 != digest:
        raise BackupError("备份回读校验不一致")
    return info


def _read_backup(path: Path, *, format_name: str = BACKUP_FORMAT) -> tuple[BackupInfo, list[UnitRow]]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise BackupError(f"无法读取备份文件：{exc.strerror}") from exc
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if len(lines) < 2:
        raise BackupError("备份文件格式不正确")
    try:
        tail = json.loads(lines[-1])
        header = json.loads(lines[0])
        body = b"\n".join(lines[:-1]) + b"\n"
        rows = [UnitRow(**json.loads(line)) for line in lines[1:-1]]
        counts = Counts(**header["counts"])
    except (ValueError, TypeError, KeyError) as exc:
        raise BackupError("备份文件格式不正确") from exc
    if header.get("format") != format_name:
        raise BackupError("备份文件格式版本不受支持")
    digest = hashlib.sha256(body).hexdigest()
    if tail.get("sha256") != digest:
        raise BackupError("备份文件摘要校验失败")
    if header.get("records") != len(rows):
        raise BackupError("备份文件记录数与头部不一致")
    return BackupInfo(Path(path), len(rows), counts, digest), rows


def verify_backup(path: Path, *, format_name: str = BACKUP_FORMAT) -> BackupInfo:
    """校验头部、行数与末行 sha256。"""
    return _read_backup(path, format_name=format_name)[0]


def apply_relocation(plan: RelocationPlan, backup: BackupInfo, expected_changes: int) -> ApplyResult:
    """事务内锁定候选行、重算计划、逐行带旧值更新并核对；任何不符抛错并回滚。"""
    if plan.conflicts:
        raise RelocationConflict(f"存在 {len(plan.conflicts)} 处标识冲突，整批停止")
    if expected_changes != len(plan.moves):
        raise RelocationAborted(f"--expect-changes={expected_changes} 与计划 {len(plan.moves)} 不符")
    info, backup_rows = _read_backup(backup.path)
    backup_ids = {r.id for r in backup_rows}
    if info.sha256 != backup.sha256 or backup_ids != {m.unit_id for m in plan.moves}:
        raise RelocationAborted("备份内容与计划不一致")

    try:
        with transaction.atomic():
            before = read_counts()
            list(RegistryUnit.objects.select_for_update().filter(unit_type="PARKING").values_list("id", flat=True))
            fresh = plan_relocation(load_rows())
            if fresh.conflicts:
                raise RelocationConflict(f"存在 {len(fresh.conflicts)} 处标识冲突，整批停止")
            if len(fresh.moves) != expected_changes or {m.unit_id for m in fresh.moves} != backup_ids:
                raise RelocationAborted("事务内重算的计划与备份不一致")
            fingerprint_before = unaffected_fingerprint(backup_ids)
            now = timezone.now()
            for move in fresh.moves:
                updated = RegistryUnit.objects.filter(id=move.unit_id, building=move.old_building).update(
                    building=TARGET_BUILDING, specific_part=move.new_specific_part, updated_at=now)
                if updated != 1:
                    raise RelocationAborted(f"记录 {move.unit_id} 更新行数异常（{updated}）")
            AuditService.record(
                actor=AuditActor("SYSTEM", None, "management_command"), action="REGISTRY_UNIT_CHANGED",
                object_type="registry", object_id="underground_relocation", result="SUCCESS",
                detail={"change": "underground_relocation", "moved": len(fresh.moves)})
            after = read_counts()
            if after != before:
                raise RelocationVerifyError("计数核对失败：专有部分/业主/手机号/有效认证绑定数发生变化")
            ids = sorted(backup_ids)
            in_target = sum(RegistryUnit.objects.filter(id__in=part, building=TARGET_BUILDING).count()
                            for part in _chunks(ids))
            if in_target != len(ids):
                raise RelocationVerifyError("核对失败：被改记录的楼栋未全部为目标值")
            if unaffected_fingerprint(backup_ids) != fingerprint_before:
                raise RelocationVerifyError("核对失败：未受影响记录发生变化")
    except IntegrityError as exc:
        raise RelocationAborted("写入触发唯一约束，事务已回滚") from exc
    return ApplyResult(moved=len(fresh.moves), before=before, after=after)


def _differences(rows: list[UnitRow]) -> int:
    """当前库中与备份记录不一致（含不存在）的条数。"""
    current: dict[int, UnitRow] = {}
    for part in _chunks([r.id for r in rows]):
        for unit in RegistryUnit.objects.filter(id__in=part):
            current[unit.id] = _to_row(unit)
    return sum(1 for r in rows if current.get(r.id) != r)


def restore_from_backup(path: Path, apply: bool) -> RestoreResult:
    """按备份把全部列原值写回；apply=False 只报告。还原前要求这些记录当前仍是修正后的状态。"""
    info, rows = _read_backup(path)
    before = read_counts()
    missing: list[int] = []
    for part in _chunks([r.id for r in rows]):
        found = dict(RegistryUnit.objects.filter(id__in=part).values_list("id", "building"))
        missing.extend(i for i in part if found.get(i) != TARGET_BUILDING)
    if missing:
        raise RelocationAborted(f"{len(missing)} 条记录当前不是修正后的状态，已中止：{missing[:20]}")
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
                raise RelocationVerifyError("还原后计数与备份头部不一致")
            diff = _differences(rows)
            if diff:
                raise RelocationVerifyError(f"还原后仍有 {diff} 条记录与备份不一致")
    except IntegrityError as exc:
        raise RelocationAborted("还原触发唯一约束，事务已回滚") from exc
    return RestoreResult(restored=len(rows), differences=0, before=before, after=after)
