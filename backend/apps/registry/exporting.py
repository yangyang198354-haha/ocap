# MOD-110 / implements IFC-296 / depends MOD-109（plan_relocation、load_rows）、registry.importing、import_spec、import_template
"""清册导出文件生成（AUTH-01）：全程只读；自检后原子落盘；不输出姓名、手机号（C-55、C-56）。"""
import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .import_spec import (
    COLUMN_BUILDING, COLUMN_FLOOR, COLUMN_OWNER, COLUMN_PHONE, COLUMN_ROOM,
    COLUMN_UNIT, IMPORT_COLUMNS, MAX_DATA_ROWS, MAX_FILE_BYTES,
)
from .import_template import build_data_csv, build_data_xlsx
from .importing import Deadline, plan_import, read_rows
from .models import UNIT_TYPE_CHOICES, RegistryOwner, RegistryPhone, RegistryUnit, build_specific_part
from .ordering import SHOP_BUILDING
from .underground import TARGET_BUILDING, Conflict, load_rows, plan_relocation

VERIFY_BUDGET_SECONDS = 600
_TYPE_LABELS = dict(UNIT_TYPE_CHOICES)


@dataclass(frozen=True)
class ExportCounts:
    units: int
    owners_named: int
    phones_distinct: int


@dataclass(frozen=True)
class ExportGaps:
    units_without_named_owner: tuple[int, ...]
    unnamed_owners: int


@dataclass(frozen=True)
class ExportBundle:
    rows: list[list[str]]
    db_counts: ExportCounts
    gaps: ExportGaps
    relocated_units: int
    relocated_owners: int
    relocated_phones: int
    conflicts: tuple[Conflict, ...]


@dataclass(frozen=True)
class VerifyReport:
    file_counts: ExportCounts
    diff: dict[str, int]
    rows_failed: int
    imported: int
    updated: int
    owners_created: int
    phones_created: int
    expected_imported: int
    roundtrip_mismatches: int
    ok: bool


def build_export_bundle() -> ExportBundle:
    """IFC-296：在一个事务快照内只读取清册，生成导入模板行。"""
    with transaction.atomic():
        unit_rows = load_rows()
        plan = plan_relocation(unit_rows)
        moved = {m.unit_id for m in plan.moves}
        owners_by_unit: dict[int, list[tuple[int, str | None]]] = {}
        for owner_id, unit_id, name in RegistryOwner.objects.order_by("id").values_list("id", "unit_id", "name"):
            owners_by_unit.setdefault(unit_id, []).append((owner_id, name))
        phones_by_owner: dict[int, list[str]] = {}
        all_phones: set[str] = set()
        for owner_id, phone in RegistryPhone.objects.order_by("id").values_list("owner_id", "phone"):
            phones_by_owner.setdefault(owner_id, []).append(phone)
            all_phones.add(phone)

    rows: list[list[str]] = []
    without_owner: list[int] = []
    unnamed = 0
    relocated_owners = 0
    relocated_phones = 0
    for unit in unit_rows:
        building = TARGET_BUILDING if unit.id in moved else unit.building
        named = 0
        for owner_id, name in owners_by_unit.get(unit.id, []):
            if name is None or not name.strip():
                unnamed += 1
                continue
            named += 1
            phones = phones_by_owner.get(owner_id, [])
            if unit.id in moved:
                relocated_owners += 1
                relocated_phones += len(phones)
            rows.append([
                building, unit.unit_no, unit.floor, unit.room,
                _TYPE_LABELS.get(unit.unit_type, "") if unit.unit_type else "",
                unit.area if unit.area is not None else "",
                name, ";".join(phones),
            ])
        if named == 0:
            without_owner.append(unit.id)

    return ExportBundle(
        rows=rows,
        db_counts=ExportCounts(units=len(unit_rows), owners_named=len(rows), phones_distinct=len(all_phones)),
        gaps=ExportGaps(tuple(without_owner), unnamed),
        relocated_units=len(moved),
        relocated_owners=relocated_owners,
        relocated_phones=relocated_phones,
        conflicts=plan.conflicts,
    )


def render_file(bundle: ExportBundle, file_name: str) -> bytes:
    lowered = file_name.lower()
    if lowered.endswith(".xlsx"):
        return build_data_xlsx(bundle.rows)
    if lowered.endswith(".csv"):
        return build_data_csv(bundle.rows)
    raise ValueError("仅支持 .xlsx 或 .csv")


def verify_export(content: bytes, file_name: str, bundle: ExportBundle) -> VerifyReport:
    """read_rows + plan_import（只读）+ 计数与逐格回读比对（AC-187-03/04、REQ-NFUNC-032）。"""
    deadline = Deadline(VERIFY_BUDGET_SECONDS)
    raw_rows = read_rows(file_name, content, deadline)
    plan = plan_import(raw_rows, deadline)
    summary = plan.summary()

    units: set[str] = set()
    owners: set[tuple[str, str]] = set()
    phones: set[str] = set()
    for raw in raw_rows:
        cells = raw.cells
        key = build_specific_part(cells[COLUMN_BUILDING], cells[COLUMN_UNIT], cells[COLUMN_FLOOR],
                                  cells[COLUMN_ROOM]).casefold()
        units.add(key)
        owners.add((key, cells[COLUMN_OWNER]))
        for part in cells[COLUMN_PHONE].split(";"):
            if part.strip():
                phones.add(part.strip())
    file_counts = ExportCounts(units=len(units), owners_named=len(owners), phones_distinct=len(phones))
    db = bundle.db_counts
    diff = {"units": file_counts.units - db.units,
            "owners_named": file_counts.owners_named - db.owners_named,
            "phones_distinct": file_counts.phones_distinct - db.phones_distinct}

    mismatches = abs(len(raw_rows) - len(bundle.rows))
    for raw, expected in zip(raw_rows, bundle.rows):
        actual = [raw.cells[column] for column in IMPORT_COLUMNS]
        if actual != [str(v).strip() for v in expected]:
            mismatches += 1

    has_gaps = bool(bundle.gaps.units_without_named_owner or bundle.gaps.unnamed_owners)
    ok = (
        summary["rows_failed"] == 0
        and summary["imported"] == bundle.relocated_units
        and summary["updated"] == 0
        and summary["owners_created"] == bundle.relocated_owners
        and summary["phones_created"] == bundle.relocated_phones
        and mismatches == 0
        and (has_gaps or not any(diff.values()))  # 有无法表达的记录时（--allow-gaps）差异另行报告
        and len(content) <= MAX_FILE_BYTES
        and len(bundle.rows) <= MAX_DATA_ROWS
    )
    return VerifyReport(
        file_counts=file_counts, diff=diff, rows_failed=summary["rows_failed"],
        imported=summary["imported"], updated=summary["updated"],
        owners_created=summary["owners_created"], phones_created=summary["phones_created"],
        expected_imported=bundle.relocated_units, roundtrip_mismatches=mismatches, ok=ok)


class OutputLocationError(Exception):
    """输出位置不满足守卫要求（IFC-303，MOD-113）。"""


def pending_shop_units() -> int:
    """只读：类型为商铺但楼栋不是"商铺"的记录数（尚未归类）。"""
    return RegistryUnit.objects.filter(unit_type="SHOP").exclude(building=SHOP_BUILDING).count()


def default_output_name(now: datetime, suffix: str = ".xlsx") -> str:
    return f"registry_import_{now:%Y%m%d-%H%M%S}{suffix}"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def check_output_location(path: Path) -> None:
    """IFC-303：不得位于部署根、MEDIA_ROOT、STATIC_ROOT 内；父目录须属当前用户且权限为 700 或更严（C-59）。"""
    target = Path(os.path.realpath(str(path)))
    forbidden = [Path(os.path.realpath(str(settings.BASE_DIR.parent))),
                 Path(os.path.realpath(str(settings.MEDIA_ROOT)))]
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        forbidden.append(Path(os.path.realpath(str(static_root))))
    for root in forbidden:
        if _inside(target, root):
            raise OutputLocationError(f"输出位置不得位于部署目录或站点目录内：{root}")
    parent = target.parent
    try:
        info = os.stat(str(parent))
    except OSError as exc:
        raise OutputLocationError(f"无法检查输出目录：{exc.strerror}") from exc
    if not hasattr(os, "getuid"):  # 非 POSIX 开发机无法表达 700，仅目标机（Linux）强制
        return
    if info.st_uid != os.getuid():
        raise OutputLocationError("输出目录须属于当前运行用户")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise OutputLocationError("输出目录权限过宽，须为 700 或更严")


def write_export_file(path: Path, content: bytes, overwrite: bool = False) -> None:
    """原子写：同目录 .part（O_EXCL、0600）→ fsync → os.replace；失败清除 .part。"""
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在：{path}")
    part = Path(str(path) + ".part")
    fd = os.open(str(part), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(part), str(path))
    except BaseException:
        try:
            os.unlink(str(part))
        except OSError:
            pass
        raise
