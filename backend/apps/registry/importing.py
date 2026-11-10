"""MOD-031：清册导入引擎（解析 → 计划 → 应用）。

预检（dry_run）与正式导入共用 plan_import：前者不调用 apply_plan，因此两者数字一致。
"""
import csv
import io
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.errors import ApiError
from apps.core.masking import PHONE_RE

from .import_spec import (
    COLUMN_AREA,
    COLUMN_BUILDING,
    COLUMN_FLOOR,
    COLUMN_OWNER,
    COLUMN_PHONE,
    COLUMN_ROOM,
    COLUMN_TYPE,
    COLUMN_UNIT,
    IMPORT_COLUMNS,
    MAX_DATA_ROWS,
    parse_area,
    parse_unit_type,
    validate_unit_fields,
)
from .models import RegistryOwner, RegistryPhone, RegistryUnit, build_specific_part

CHANGES_LIMIT = 1000


class ImportFileError(ApiError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("IMPORT_FILE_INVALID", message, 400, details)


class ImportColumnsMissing(ApiError):
    def __init__(self, columns: list[str]):
        message = f"缺少列：{'、'.join(columns)}，请使用新模板"
        super().__init__("IMPORT_COLUMNS_MISSING", message, 400, {"columns": columns})


class ImportTimeout(ApiError):
    def __init__(self, limit_seconds: int, stage: str):
        super().__init__(
            "IMPORT_TIMEOUT",
            "导入处理超过时间上限，已放弃本次导入",
            504,
            {"limit_seconds": limit_seconds, "stage": stage},
        )


class ImportConflict(ApiError):
    def __init__(self):
        super().__init__("IMPORT_CONFLICT", "有其他导入正在进行，请稍后重试", 409)


class Deadline:
    def __init__(self, seconds: float, started: float | None = None) -> None:
        self.seconds = float(seconds)
        self.started = time.monotonic() if started is None else started

    def check(self, stage: str) -> None:
        if time.monotonic() - self.started > self.seconds:
            raise ImportTimeout(int(self.seconds), stage)


@dataclass(frozen=True)
class RawRow:
    row_no: int
    cells: dict[str, str]


@dataclass
class RowError:
    row: int
    field: str | None
    reason: str


@dataclass
class PlannedUnit:
    key: str
    building: str
    unit_no: str
    floor: str
    room: str
    specific_part: str
    unit_type: str
    area: Decimal | None


@dataclass
class PlannedUnitUpdate:
    unit: RegistryUnit
    unit_type: str
    area: Decimal | None
    changed_fields: list[str]


@dataclass
class PlannedOwner:
    unit_key: str
    name: str
    unit_id: int | None = None
    phones: list[str] = field(default_factory=list)


@dataclass
class PlannedPhone:
    owner_ref: tuple
    phone: str


@dataclass
class PlannedNameFill:
    owner_id: int
    name: str


@dataclass
class PlannedPhoneMove:
    phone_id: int
    to_owner_ref: tuple


@dataclass
class UnitChange:
    specific_part: str
    fields: list[str]


@dataclass
class ImportPlan:
    rows_total: int = 0
    errors: list[RowError] = field(default_factory=list)
    units_to_create: list[PlannedUnit] = field(default_factory=list)
    units_to_update: list[PlannedUnitUpdate] = field(default_factory=list)
    owners_to_create: list[PlannedOwner] = field(default_factory=list)
    phones_to_create: list[PlannedPhone] = field(default_factory=list)
    owner_names_to_fill: list[PlannedNameFill] = field(default_factory=list)
    phone_moves: list[PlannedPhoneMove] = field(default_factory=list)
    owners_to_delete: list[int] = field(default_factory=list)
    changes: list[UnitChange] = field(default_factory=list)
    changes_truncated: bool = False
    owners_named: int = 0
    # 本次导入会改动（含业主/手机号变化）的既有专有部分键；用于 updated 计数（AC-099-01）
    touched: set = field(default_factory=set)

    @property
    def rows_failed(self) -> int:
        return len(self.errors)

    @property
    def rows_ok(self) -> int:
        return max(self.rows_total - self.rows_failed, 0)

    def summary(self) -> dict:
        truncated = self.changes_truncated or len(self.changes) > CHANGES_LIMIT
        return {
            "rows_total": self.rows_total,
            "rows_ok": self.rows_ok,
            "rows_failed": self.rows_failed,
            "imported": len(self.units_to_create),
            "updated": len(self.touched),
            "owners_created": len(self.owners_to_create),
            "phones_created": len(self.phones_to_create) + sum(len(o.phones) for o in self.owners_to_create),
            "failed": self.rows_failed,
            "errors": [{"row": e.row, "field": e.field, "reason": e.reason} for e in self.errors],
            "changes": [
                {"specific_part": c.specific_part, "fields": list(c.fields)}
                for c in self.changes[:CHANGES_LIMIT]
            ],
            "changes_truncated": truncated,
            "owners_named": self.owners_named,
        }


def cell_text(value: object) -> str:
    """把 xlsx/csv 单元格统一成去首尾空格的字符串（ADR-039 第 2 点）。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:g}"
    if isinstance(value, Decimal):
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value).strip()


def _normalize_header(values: list) -> tuple[dict[str, int], list[str]]:
    header = [cell_text(v) for v in values]
    index: dict[str, int] = {}
    for position, name in enumerate(header):
        if name and name not in index:
            index[name] = position
    missing = [column for column in IMPORT_COLUMNS if column not in index]
    return index, missing


def read_rows(name: str, raw: bytes, deadline: Deadline) -> list[RawRow]:
    """按扩展名解析 xlsx/csv，返回非空数据行（row_no 为文件物理行号，表头=1）。"""
    lowered = (name or "").lower()
    if lowered.endswith(".xlsx"):
        try:
            from openpyxl import load_workbook
        except ImportError as exc:  # pragma: no cover - 依赖缺失属部署问题
            raise ApiError("IMPORT_UNAVAILABLE", "服务器缺少表格解析组件", 503) from exc
        try:
            workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            sheet = workbook.worksheets[0]
            raw_rows = [[cell_text(c) for c in row] for row in sheet.iter_rows(values_only=True)]
            workbook.close()
        except Exception as exc:  # noqa: BLE001 - 任何解析异常都归一为文件无法解析
            raise ImportFileError("文件无法解析") from exc
    elif lowered.endswith(".csv"):
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ImportFileError("文件无法解析") from exc
        try:
            raw_rows = [[cell_text(c) for c in row] for row in csv.reader(io.StringIO(text))]
        except csv.Error as exc:
            raise ImportFileError("文件无法解析") from exc
    else:
        raise ImportFileError("仅支持 xlsx 或 csv")

    deadline.check("parse")
    if not raw_rows:
        raise ImportColumnsMissing(list(IMPORT_COLUMNS))

    index, missing = _normalize_header(raw_rows[0])
    if missing:
        raise ImportColumnsMissing(missing)

    rows: list[RawRow] = []
    for offset, values in enumerate(raw_rows[1:], start=2):
        cells = {column: (values[pos] if pos < len(values) else "") for column, pos in index.items()}
        if not any(v.strip() for v in cells.values()):
            continue
        rows.append(RawRow(row_no=offset, cells=cells))
        if len(rows) > MAX_DATA_ROWS:
            raise ImportFileError(f"文件行数超过 {MAX_DATA_ROWS}")
        if len(rows) % 500 == 0:
            deadline.check("parse")
    return rows


@dataclass
class _Owner:
    id: int | None
    name: str | None
    phones: set = field(default_factory=set)


class _UnitState:
    def __init__(self, unit: RegistryUnit | None):
        self.unit = unit
        self.owners: list[_Owner] = []
        self.name_index: dict[str, int] = {}
        self.phone_index: dict[str, int] = {}
        self.phone_ids: dict[str, int] = {}
        self.new_planned: dict[int, PlannedOwner] = {}

    def add_owner(self, owner: _Owner) -> int:
        self.owners.append(owner)
        idx = len(self.owners) - 1
        if owner.name:
            self.name_index.setdefault(owner.name.casefold(), idx)
        for phone in owner.phones:
            self.phone_index.setdefault(phone, idx)
        return idx


def _load_states(keys: dict[str, str], deadline: Deadline) -> dict[str, _UnitState]:
    states: dict[str, _UnitState] = {key: _UnitState(None) for key in keys}
    specific_parts = list(keys.values())
    if not specific_parts:
        return states

    units = (
        RegistryUnit.objects.filter(specific_part__in=specific_parts)
        .prefetch_related("owners__phones")
        .order_by("id")
    )
    for unit in units:
        key = unit.specific_part.casefold()
        state = states.get(key)
        if state is None:
            continue
        state.unit = unit
        for owner in unit.owners.all():
            phones = {p.phone for p in owner.phones.all()}
            state.add_owner(_Owner(id=owner.id, name=owner.name, phones=phones))
            for phone in owner.phones.all():
                state.phone_ids[phone.phone] = phone.id
    deadline.check("plan")
    return states


def _parse_row(cells: dict[str, str]) -> tuple[dict | None, RowError | None]:
    building = (cells.get(COLUMN_BUILDING) or "").strip()
    unit_no = (cells.get(COLUMN_UNIT) or "").strip()
    floor = (cells.get(COLUMN_FLOOR) or "").strip()
    room = (cells.get(COLUMN_ROOM) or "").strip()
    type_text = (cells.get(COLUMN_TYPE) or "").strip()
    area_text = (cells.get(COLUMN_AREA) or "").strip()
    name = (cells.get(COLUMN_OWNER) or "").strip()
    phone_text = (cells.get(COLUMN_PHONE) or "").strip()

    error = validate_unit_fields(building=building, unit_no=unit_no, floor=floor, room=room)
    if error:
        if "楼栋" in error:
            return None, RowError(0, COLUMN_BUILDING, error)
        if "户号" in error:
            return None, RowError(0, COLUMN_ROOM, error)
        return None, RowError(0, None, error)

    unit_type, type_error = parse_unit_type(type_text)
    if type_error:
        return None, RowError(0, COLUMN_TYPE, type_error)

    area, area_error = parse_area(area_text)
    if area_error:
        return None, RowError(0, COLUMN_AREA, area_error)

    if not name:
        return None, RowError(0, COLUMN_OWNER, "业主姓名不能为空")
    if len(name) > 64:
        return None, RowError(0, COLUMN_OWNER, "业主姓名过长（最多 64 字符）")

    phones: list[str] = []
    for candidate in phone_text.replace("\n", ";").replace("，", ";").split(";"):
        phone = candidate.strip()
        if not phone or phone in phones:
            continue
        if not PHONE_RE.match(phone):
            return None, RowError(0, COLUMN_PHONE, "手机号格式不正确")
        phones.append(phone)

    return {
        "building": building,
        "unit_no": unit_no,
        "floor": floor,
        "room": room,
        "unit_type": unit_type,
        "area": area,
        "name": name,
        "phones": phones,
        "specific_part": build_specific_part(building, unit_no, floor, room),
    }, None


def plan_import(rows: list[RawRow], deadline: Deadline) -> ImportPlan:
    plan = ImportPlan(rows_total=len(rows))

    parsed: list[tuple[RawRow, dict]] = []
    for row in rows:
        data, error = _parse_row(row.cells)
        if error:
            error.row = row.row_no
            plan.errors.append(error)
        else:
            parsed.append((row, data))

    groups: dict[str, list[tuple[RawRow, dict]]] = {}
    keys: dict[str, str] = {}
    for row, data in parsed:
        key = data["specific_part"].casefold()
        groups.setdefault(key, []).append((row, data))
        keys.setdefault(key, data["specific_part"])

    deadline.check("plan")
    states = _load_states(keys, deadline)

    for key, entries in groups.items():
        deadline.check("plan")
        state = states[key]
        existing = state.unit

        types = {data["unit_type"] for _, data in entries if data["unit_type"]}
        if len(types) > 1:
            for row, _ in entries:
                plan.errors.append(RowError(row.row_no, COLUMN_TYPE, "同一专有部分的类型不一致"))
            continue

        file_type = next(iter(types)) if types else None
        final_type = file_type or (existing.unit_type if existing else None)

        areas = {data["area"] for _, data in entries if data["area"] is not None}
        if len(areas) > 1:
            for row, _ in entries:
                plan.errors.append(RowError(row.row_no, COLUMN_AREA, "同一专有部分的面积不一致"))
            continue

        file_area = next(iter(areas)) if areas else None
        final_area = file_area if file_area is not None else (existing.area if existing else None)

        if final_type is None and existing is None:
            for row, _ in entries:
                plan.errors.append(RowError(row.row_no, COLUMN_TYPE, "专有部分类型为空"))
            continue
        if final_type == "PARKING" and final_area is None:
            for row, _ in entries:
                plan.errors.append(RowError(row.row_no, COLUMN_AREA, "车位的专有部分面积不能为空"))
            continue

        planned_unit: PlannedUnit | None = None
        if existing is None:
            first = entries[0][1]
            planned_unit = PlannedUnit(
                key=key,
                building=first["building"],
                unit_no=first["unit_no"],
                floor=first["floor"],
                room=first["room"],
                specific_part=first["specific_part"],
                unit_type=final_type,
                area=final_area,
            )
            plan.units_to_create.append(planned_unit)
        else:
            changed: list[str] = []
            if file_type and file_type != existing.unit_type:
                changed.append("unit_type")
            if file_area is not None and file_area != existing.area:
                changed.append("area")
            if changed:
                plan.units_to_update.append(
                    PlannedUnitUpdate(
                        unit=existing,
                        unit_type=file_type or existing.unit_type,
                        area=file_area if file_area is not None else existing.area,
                        changed_fields=changed,
                    )
                )
                plan.changes.append(UnitChange(existing.specific_part, changed))
                plan.touched.add(key)
                if len(plan.changes) > CHANGES_LIMIT:
                    plan.changes_truncated = True

        for row, data in entries:
            deadline.check("plan")
            error = _plan_row(plan, state, key, data)
            if error:
                error.row = row.row_no
                plan.errors.append(error)

    plan.errors.sort(key=lambda e: e.row)
    return plan


def _plan_row(plan: ImportPlan, state: _UnitState, unit_key: str, data: dict) -> RowError | None:
    """对单行做业主/手机号计划；任一步失败则整行不落计划（行级原子）。"""
    name: str = data["name"]
    name_key = name.casefold()
    phones: list[str] = data["phones"]

    target = state.name_index.get(name_key)
    name_fill_owner_id: int | None = None
    if target is None:
        for phone in phones:
            idx = state.phone_index.get(phone)
            if idx is not None and state.owners[idx].name is None and state.owners[idx].id is not None:
                target = idx
                name_fill_owner_id = state.owners[idx].id
                break

    new_owner = target is None
    row_phones: list[str] = []
    moves: list[tuple[int, str, int]] = []

    for phone in phones:
        holder = state.phone_index.get(phone)
        if holder is not None and holder != target:
            holder_owner = state.owners[holder]
            if holder_owner.name is not None or holder_owner.id is None:
                return RowError(0, COLUMN_PHONE, "手机号已登记给同一专有部分的另一位业主")
            phone_id = state.phone_ids.get(phone)
            if phone_id is not None:
                moves.append((holder, phone, phone_id))
            continue
        if holder is None:
            row_phones.append(phone)

    if not new_owner:
        owner = state.owners[target]
        for phone in row_phones:
            owner.phones.add(phone)
            state.phone_index[phone] = target
            if owner.id is not None:
                plan.phones_to_create.append(PlannedPhone(owner_ref=("existing", owner.id), phone=phone))
            else:
                state.new_planned[target].phones.append(phone)
        if name_fill_owner_id is not None:
            owner.name = name
            state.name_index[name_key] = target
            plan.owner_names_to_fill.append(PlannedNameFill(owner_id=name_fill_owner_id, name=name))
            plan.owners_named += 1
        owner_ref = ("existing", owner.id) if owner.id is not None else ("new", unit_key, owner.name)
    else:
        planned = PlannedOwner(
            unit_key=unit_key,
            name=name,
            unit_id=state.unit.id if state.unit else None,
            phones=list(row_phones),
        )
        plan.owners_to_create.append(planned)
        target = len(state.owners)
        state.owners.append(_Owner(id=None, name=name, phones=set(row_phones)))
        state.new_planned[target] = planned
        state.name_index[name_key] = target
        for phone in row_phones:
            state.phone_index[phone] = target
        owner_ref = ("new", unit_key, name)

    for holder_idx, phone, phone_id in moves:
        holder = state.owners[holder_idx]
        holder.phones.discard(phone)
        state.phone_index[phone] = target
        state.owners[target].phones.add(phone)
        if state.owners[target].id is None:
            state.new_planned[target].phones.append(phone)
        plan.phone_moves.append(PlannedPhoneMove(phone_id=phone_id, to_owner_ref=owner_ref))
        if not holder.phones and holder.id is not None and holder.id not in plan.owners_to_delete:
            plan.owners_to_delete.append(holder.id)

    if state.unit is not None and (new_owner or row_phones or moves or name_fill_owner_id is not None):
        plan.touched.add(unit_key)

    return None


def apply_plan(plan: ImportPlan, deadline: Deadline) -> None:
    try:
        with transaction.atomic():
            new_unit_ids = _create_units(plan, deadline)
            _update_units(plan, deadline)
            _fill_names(plan, deadline)
            owner_ids = _create_owners(plan, new_unit_ids, deadline)
            _create_phones(plan, owner_ids, deadline)
            _move_phones(plan, owner_ids, deadline)
            _delete_owners(plan, deadline)
    except IntegrityError as exc:
        raise ImportConflict() from exc


def _create_units(plan: ImportPlan, deadline: Deadline) -> dict[str, int]:
    if not plan.units_to_create:
        return {}
    RegistryUnit.objects.bulk_create(
        [
            RegistryUnit(
                building=u.building,
                unit_no=u.unit_no,
                floor=u.floor,
                room=u.room,
                specific_part=u.specific_part,
                unit_type=u.unit_type,
                area=u.area,
            )
            for u in plan.units_to_create
        ],
        batch_size=500,
    )
    deadline.check("apply")
    rows = RegistryUnit.objects.filter(
        specific_part__in=[u.specific_part for u in plan.units_to_create]
    ).values("id", "specific_part")
    return {row["specific_part"].casefold(): row["id"] for row in rows}


def _update_units(plan: ImportPlan, deadline: Deadline) -> None:
    if not plan.units_to_update:
        return
    now = timezone.now()
    units = []
    for update in plan.units_to_update:
        update.unit.unit_type = update.unit_type
        update.unit.area = update.area
        update.unit.updated_at = now
        units.append(update.unit)
    RegistryUnit.objects.bulk_update(units, ["unit_type", "area", "updated_at"], batch_size=500)
    deadline.check("apply")


def _fill_names(plan: ImportPlan, deadline: Deadline) -> None:
    if not plan.owner_names_to_fill:
        return
    owners = {
        owner.id: owner
        for owner in RegistryOwner.objects.filter(id__in=[f.owner_id for f in plan.owner_names_to_fill])
    }
    for fill in plan.owner_names_to_fill:
        owner = owners.get(fill.owner_id)
        if owner is not None:
            owner.name = fill.name
    if owners:
        RegistryOwner.objects.bulk_update(list(owners.values()), ["name", "updated_at"], batch_size=500)
    deadline.check("apply")


def _move_phones(plan: ImportPlan, owner_ids: dict[tuple[str, str], int], deadline: Deadline) -> None:
    if not plan.phone_moves:
        return
    by_owner: dict[int, list[int]] = {}
    for move in plan.phone_moves:
        ref = move.to_owner_ref
        owner_id = ref[1] if ref[0] == "existing" else owner_ids.get((ref[1], ref[2]))
        if owner_id is None:
            continue
        by_owner.setdefault(owner_id, []).append(move.phone_id)
    for owner_id, phone_ids in by_owner.items():
        RegistryPhone.objects.filter(id__in=phone_ids).update(owner_id=owner_id)
        deadline.check("apply")


def _delete_owners(plan: ImportPlan, deadline: Deadline) -> None:
    if not plan.owners_to_delete:
        return
    RegistryOwner.objects.filter(id__in=plan.owners_to_delete).delete()
    deadline.check("apply")


def _create_owners(plan: ImportPlan, new_unit_ids: dict[str, int], deadline: Deadline) -> dict[tuple[str, str], int]:
    if not plan.owners_to_create:
        return {}
    unit_key_by_id: dict[int, str] = {
        planned.unit_id: planned.unit_key for planned in plan.owners_to_create if planned.unit_id
    }
    unit_key_by_id.update({unit_id: key for key, unit_id in new_unit_ids.items()})

    owners: list[RegistryOwner] = []
    for planned in plan.owners_to_create:
        unit_id = planned.unit_id or new_unit_ids.get(planned.unit_key)
        if unit_id is None:
            continue
        owners.append(RegistryOwner(unit_id=unit_id, name=planned.name))
    if owners:
        RegistryOwner.objects.bulk_create(owners, batch_size=500)
    deadline.check("apply")

    result: dict[tuple[str, str], int] = {}
    if not owners:
        return result
    for row in RegistryOwner.objects.filter(
        unit_id__in=[o.unit_id for o in owners], name__in=sorted({o.name for o in owners})
    ).values("id", "unit_id", "name"):
        key = unit_key_by_id.get(row["unit_id"])
        if key is not None:
            result[(key, row["name"])] = row["id"]
    return result


def _create_phones(plan: ImportPlan, owner_ids: dict[tuple[str, str], int], deadline: Deadline) -> None:
    entries: list[tuple[int, str]] = []
    for planned in plan.phones_to_create:
        ref = planned.owner_ref
        owner_id = ref[1] if ref[0] == "existing" else owner_ids.get((ref[1], ref[2]))
        if owner_id is not None:
            entries.append((owner_id, planned.phone))
    for planned in plan.owners_to_create:
        owner_id = owner_ids.get((planned.unit_key, planned.name))
        if owner_id is None:
            continue
        for phone in planned.phones:
            entries.append((owner_id, phone))
    if not entries:
        return

    unit_by_owner = {
        row["id"]: row["unit_id"]
        for row in RegistryOwner.objects.filter(id__in={owner_id for owner_id, _ in entries}).values("id", "unit_id")
    }
    phones: list[RegistryPhone] = []
    seen: set[tuple[int, str]] = set()
    for owner_id, phone in entries:
        key = (owner_id, phone)
        if key in seen or owner_id not in unit_by_owner:
            continue
        seen.add(key)
        phones.append(RegistryPhone(owner_id=owner_id, unit_id=unit_by_owner[owner_id], phone=phone))
    if phones:
        RegistryPhone.objects.bulk_create(phones, batch_size=500)
    deadline.check("apply")
