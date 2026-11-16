<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T17:55:28+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽（INCREMENTAL）

> 编号接续全仓最大值（已 grep `project_workspace/*/architecture/`）：MOD-111~118、IFC-299~315（ADR-106~116 见 architecture_design.md）。
> 模块 = 本次新建/修改的代码单元，路径相对仓库根；后端前缀 `backend/apps/`。HTTP 路径省略前缀 `/api/v1`；错误体统一为 `{code, message, details?}`（`core/errors.py` 的 `ApiError`）。只写签名与契约，不写函数体。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-111 | 商铺归类规则与改库命令 | **新建** `registry/shops.py`、`registry/management/commands/relocate_shops.py`；**修改** `registry/underground.py`（`write_backup`/`_read_backup`/`verify_backup` 仅加带缺省值的关键字参数 `format_name`） | 识别商铺、预演冲突、备份、事务内更新与核对、还原；默认 dry-run | REQ-FUNC-186/188；REQ-NFUNC-036；US-195 | MOD-112（`SHOP_BUILDING`）、`registry.underground` 低层函数、`registry.models`、`core.audit` |
| MOD-112 | 楼栋排序与选项显示名 | **修改** `registry/ordering.py`（保留楼栋表与层级）、`registry/services.py`（`RegistryService.options` 加 `level_label`） | 第一级 编号楼栋 → 地下车位 → 商铺 → 其他文字；商铺第二级显示名 | REQ-FUNC-185/186/187；US-193/194 | 无（`ordering` 仅标准库） |
| MOD-113 | 导出命令加固 | **修改** `registry/exporting.py`（新增 `pending_shop_units`、`check_output_location`、`default_output_name`）、`registry/management/commands/export_registry_import_file.py` | 输出位置守卫、商铺未归类守卫、`--output-dir` 自动日期命名 | REQ-FUNC-189；REQ-NFUNC-036；US-196 | MOD-112（`SHOP_BUILDING`）、既有 `registry.exporting` |
| MOD-114 | 清册核对与追加 | **新建** `registry/ownership.py` | 姓名归一与"同一业主"比对；申诉通过后的追加规则（同名追加号码、同号拒绝） | REQ-FUNC-194/195/196/197/198；REQ-NFUNC-035/037；US-200~204 | `registry.models` |
| MOD-115 | 认证与申诉后端 | **修改** `residency/models.py`（`Appeal.owner_name`）、`residency/views.py`（`CertificationView`、`AppealListCreateView`、`AdminAppealListView`、`AppealAdminSerializer`、`AdminAppealDecisionView`）、`residency/apps.py`（`AppealAttachmentPolicy`）；**新建** `residency/migrations/0003_appeal_owner_name.py` | 姓名必填与统一失败响应；申诉产权人名字；后台列表字段；通过时追加清册并写审计；附件无权 403 | REQ-FUNC-190~198；REQ-NFUNC-034/035/037；US-197~204 | MOD-114、`core.attachments`、`core.audit`、`residency.services` |
| MOD-116 | 席位生效判定与授予校验 | **新建** `committee/effective.py`；**修改** `committee/services.py`、`committee/views.py`、`accounts/directory.py`、`accounts/views.py`（用户列表席位预取 :430-433） | "在任"统一加开始日条件；授予按结束日 > 今天；未生效席位占名额；`effective` 字段 | REQ-FUNC-199/200；US-205/206 | 无新依赖（`committee.effective` 仅 Django `Q`） |
| MOD-117 | Web 前端 | **新建** `frontend/src/admin/parts/ProofThumbs.vue`；**修改** `frontend/src/portal/Units.vue`、`frontend/src/portal/parts/UnitCascader.vue`、`frontend/src/admin/AdminAppeals.vue`、`frontend/src/admin/AdminSeats.vue`、`frontend/src/shared/api.js` | 姓名输入与转申诉、申诉多附件与产权人名字、后台申诉列表/缩略图/大图、席位"待生效"、第二级显示名 | REQ-FUNC-187/190~197/199/200；REQ-NFUNC-034；US-194/197~202、205/206 | IFC-300、IFC-306~310、IFC-312 |
| MOD-118 | 小程序 | **修改** `miniprogram/pages/units/index.vue`、`miniprogram/components/UnitPicker.vue`、`miniprogram/utils/api.js` | 姓名输入与转申诉、申诉多图与产权人名字、第二级显示名 | REQ-FUNC-187/192/193/195/196；US-194、199~202 | IFC-300、IFC-306、IFC-307 |

备注（不改动的单元，已核实）：
- `registry/importing.py`、`import_spec.py`、`import_template.py`：导出自检继续复用，不改。
- `residency/auto_bind.py`、`accounts/views.py:116`、`identity/views.py:47`：手机号注册/绑定自动绑定通路，**不改**（Q-OA-23=A、C-61）。
- `committee/services.py::expire_due`（:215-217）：只处理 `term_end < today`，不改。
- `registry/models.py`、`committee/models.py`：不改（唯一的模型改动是 `residency.Appeal` 一列）。
- 后台清册页（`AdminRegistry.vue`）与 `GET /admin/registry/units/filter-options`：不改；商铺改库后楼栋下拉自动含"商铺"（取值来自库内去重 + `sorted_values`）。

## 模块详情

### MOD-112 楼栋排序与选项显示名

**文件**：`backend/apps/registry/ordering.py`（修改）、`backend/apps/registry/services.py`（修改 `RegistryService.options`，现 :23-81）。测试：`backend/tests/unit/test_registry_ordering.py`（更新）、`backend/tests/integration/test_owner_auth_options.py`（新建）。

```python
# registry/ordering.py（新增/修改部分；其余 IFC-285~287 保持）
UNDERGROUND_BUILDING: str = "地下车位"                         # 既有（:6）
SHOP_BUILDING: str = "商铺"                                    # 新增：保留楼栋名唯一定义处
RESERVED_BUILDINGS: dict[str, int] = {UNDERGROUND_BUILDING: 1, SHOP_BUILDING: 2}   # 名称 -> 楼栋级层级号
# NaturalKey 形状不变：(层级, 数值, 文字段序列, 原始文本)
def natural_key(value: str | None, level: Level) -> NaturalKey: ...                # IFC-299（修改 IFC-285）
```

#### IFC-299 `natural_key`（修改 IFC-285，仅楼栋层级变化）
- `level == "building"`：层级 `-1` 空；`0` 整数（去"栋"后缀）；`1` 地下车位；`2` 商铺；`3` 其他文字（拆数字段/非数字段，规则同旧"层级 1"）。保留名判断为去首尾空白后**全等**。
- 其余三个层级（`unit_no`/`floor`/`room`）不变：`-1` 空、`0` 整数、`1` 其他文字；"商铺"二字出现在 `unit_no` 等层级时只是普通文字。
- 商铺第二级的值（`1栋`、`2栋`、`10栋`、`建设南路142号`）在 `unit_no` 层级均为"其他文字"，按数字段数值比较，得到 `1栋 < 2栋 < 10栋 < 建设南路…`（数字段键 `(0,n,"")` 小于非数字段键 `(1,0,s)`）；纯数字 `unit_no`（`"1"`）仍在其前（层级 0）。
- 输入校验：不抛异常；非 `str` 按空串处理（同旧）。

#### IFC-300 `GET /units/options`（修改 IFC-288/IFC-152，仅新增可选响应键）
- 鉴权：`IsMember`（`registry/views.py:61` 起 `UnitOptionsView`，不改）；输入校验与 `400 INVALID_QUERY`（`building/unit_no/floor` ≤32 字符、缺上级参数）**完全不变**。
- 响应：`{level, skipped, has_empty, options}`；新增**可选**键 `level_label: str`——仅当 `level == "unit_no"` 且请求的 `building == SHOP_BUILDING` 时返回 `"楼栋/门牌"`，其他情形不返回该键（不置 null，保持既有响应字典相等）。
- 第一级：`sorted_values(buildings, "building")`，顺序 编号楼栋 → 地下车位 → 商铺 → 其他文字（AC-193-01/04）；清册无商铺记录则不出现"商铺"（AC-193-05，由数据驱动，无特例）。
- 商铺路径：`building=商铺` → `level="unit_no"`（`has_empty=false`，商铺 `unit_no` 全非空）→ `floor`（空则 `skipped` 含 `"floor"`，自动跳过）→ `room`（既有机制，`options` 每项 `value, unit_id, unit_type, unit_type_label, area, label`）。选项总数等于该原楼栋下商铺记录数，无重复无遗漏（AC-194-03，因 `unit_id` 逐行输出）。

**依赖**：无。

---

### MOD-111 商铺归类规则与改库命令

**文件**：`backend/apps/registry/shops.py`（新建）、`backend/apps/registry/management/commands/relocate_shops.py`（新建）、`backend/apps/registry/underground.py`（修改：三个函数增加可选参数）。测试：`backend/tests/unit/test_shop_relocation_rules.py`、`backend/tests/integration/test_shop_relocation_cmd.py`（SQLite 测试库 + `call_command`，不连接测试机，画像 P8）。

```python
# registry/underground.py（仅此三处签名增加缺省参数，其余不动；旧调用不变）
def write_backup(path: Path, plan: "RelocationPlan | ShopPlan", rows: list[UnitRow], counts: Counts,
                 *, format_name: str = BACKUP_FORMAT) -> BackupInfo: ...
def verify_backup(path: Path, *, format_name: str = BACKUP_FORMAT) -> BackupInfo: ...
def _read_backup(path: Path, *, format_name: str = BACKUP_FORMAT) -> tuple[BackupInfo, list[UnitRow]]: ...

# registry/shops.py
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal
from .ordering import SHOP_BUILDING
from .underground import ApplyResult, BackupInfo, Counts, RestoreResult, UnitRow

SHOP_TYPE: str = "SHOP"
SHOP_BACKUP_FORMAT: str = "ocap-shop-backup/1"

@dataclass(frozen=True)
class ShopMove:
    unit_id: int
    old_building: str
    old_unit_no: str                 # 必为空串，否则进入冲突
    old_specific_part: str
    new_unit_no: str                 # = shop_unit_no(old_building)
    new_specific_part: str           # = build_specific_part(SHOP_BUILDING, new_unit_no, floor, room)

@dataclass(frozen=True)
class ShopConflict:
    kind: Literal["specific_part", "tuple", "unit_no_occupied", "too_long", "empty_building"]
    key: str                         # 冲突的新标识 / 四元组文本 / 旧楼栋
    unit_ids: tuple[int, ...]

@dataclass(frozen=True)
class ShopPlan:
    total_units: int
    shop_units: int                  # 类型为商铺的记录数（含已在目标楼栋）
    already_target: int
    moves: tuple[ShopMove, ...]
    conflicts: tuple[ShopConflict, ...]
    old_building_counts: dict[str, int]        # 被改记录的旧楼栋写法分布
    second_level_values: int                    # 去重后的 new_unit_no 个数（预期约 33，Q-OA-26）
    floor_spellings: dict[str, int]             # 被改记录的楼层写法分布（Q-OA-29）
    foreign_in_target: int                      # 楼栋已是"商铺"但类型不是商铺的记录数（C-60，仅提示）

def shop_unit_no(old_building: str) -> str: ...                                   # IFC-301
def plan_shop_relocation(rows: Iterable[UnitRow]) -> ShopPlan: ...                 # IFC-301：纯函数
def apply_shop_relocation(plan: ShopPlan, backup: BackupInfo, expected_changes: int) -> ApplyResult: ...   # IFC-301
def restore_shop_backup(path: Path, apply: bool) -> RestoreResult: ...             # IFC-301
class ShopRelocationConflict(Exception): ...
class ShopRelocationAborted(Exception): ...
class ShopRelocationVerifyError(Exception): ...
```

#### IFC-301 规则与执行函数契约
- **`shop_unit_no(old_building)`**：`strip()`；全为 ASCII/全角数字 → 返回 `原值 + "栋"`；已以"栋"结尾或含其他文字 → 原值；空串 → 返回空串，调用方把旧楼栋为空的记录记为 `empty_building` 冲突。结果长度 > 32 → 调用方记 `too_long` 冲突。
- **识别**：`unit_type == SHOP_TYPE`；`building == SHOP_BUILDING` → `already_target`（不进 `moves`，幂等，AC-195-04）；其余进入 `moves`。类型为空/其他/非商铺的记录不受影响（C-60）。
- **冲突预演（最终状态）**：被改记录取新值、其余取旧值；检查 (a) `specific_part.casefold()` 重复、(b) 四元组重复、(c) `old_unit_no` 非空（`unit_no_occupied`）、(d) 新 `unit_no` 超 32 字（`too_long`）或旧楼栋为空（`empty_building`）。`conflicts` 非空时 `apply_shop_relocation` 直接抛 `ShopRelocationConflict`，不写任何数据（AC-195-03）。
- **`apply_shop_relocation`**：要求 `expected_changes == len(plan.moves)`；`transaction.atomic()` 内 `select_for_update` 锁定类型为商铺的记录并重算计划，数量或 id 集合与备份不一致抛 `ShopRelocationAborted`；逐行 `RegistryUnit.objects.filter(id=…, building=old_building, unit_no=old_unit_no).update(building=SHOP_BUILDING, unit_no=new_unit_no, specific_part=new_specific_part, updated_at=now)`，每条必须恰好影响 1 行；同事务写一条 `AuditService.record(actor=AuditActor("SYSTEM", None, "management_command"), action="REGISTRY_UNIT_CHANGED", object_type="registry", object_id="shop_relocation", result="SUCCESS", detail={"change": "shop_relocation", "moved": N})`；提交前核对 `Counts`（专有部分、业主、手机号、有效认证绑定）前后相等、被改记录 `building == SHOP_BUILDING` 且 `unit_no == shop_unit_no(备份中的旧楼栋)`（**原信息丢失数 = 0**）、`unaffected_fingerprint` 前后相等；任一不符抛 `ShopRelocationVerifyError`（整体回滚）。`IntegrityError` 转 `ShopRelocationAborted`。
- **`restore_shop_backup`**：先 `verify_backup(path, format_name=SHOP_BACKUP_FORMAT)`；对备份每条记录检查"当前存在且 `building == SHOP_BUILDING`"，否则列出并中止；`apply=True` 时事务内把备份全部列（含 `unit_no`、`updated_at`）原值写回，再核对 `Counts` 与备份头部一致、逐记录与备份差异为 0；`apply=False` 只报告。

#### IFC-302 命令 `python manage.py relocate_shops`（CLI）
```
relocate_shops                                              # dry-run（默认，只读）
relocate_shops --apply --backup PATH --expect-changes N
relocate_shops --restore PATH                               # 还原 dry-run（只读）
relocate_shops --restore PATH --apply                       # 实际还原
        [--list-limit N]                                    # 明细最多条数，1~100000，缺省 50
```
- **鉴权**：无 HTTP 鉴权；只能在目标机 shell 以部署用户执行；须用户当轮另行授权（C-57），子代理不得 ssh（画像 P9）；没有 `--apply` 一律只读，不创建文件。
- **输入校验与退出码**：同 `relocate_underground_parking`（IFC-295）：`--apply` 必须同时给 `--backup` 与 `--expect-changes`（非负整数）；`--backup` 路径已存在或父目录不存在 → 退出码 3 且不触库；`--restore` 不与 `--backup`/`--expect-changes` 同用；`--list-limit` 越界 → `CommandError`（1）；0 正常（含无需修改）；1 参数错误；2 冲突/数量不符/核对失败（已回滚）；3 备份或还原文件问题。
- **输出（stdout）**：`total_units`、`shop_units`、`already_target`、`would_change`、`conflicts`、`second_level_values`、`foreign_in_target`、`old_building|<值>|<数>`、`floor|<写法>|<数>`、`conflict|<kind>|<key>|<id,id…>`、`move|<id>|<旧标识>|<新标识>`（受 `--list-limit` 限）；apply/restore 额外输出 `before_*`/`after_*`（units、owners、phones、active_memberships）、`lost_origin=0`、`differences`。**不输出姓名、手机号**（C-59）。
- 备份文件：JSON Lines，`format = "ocap-shop-backup/1"`，字段同 `UnitRow`（含旧 `unit_no`、`updated_at`），0600、`O_EXCL`、`fsync`、回读校验后才触库，不含个人信息；建议路径 `/home/yangyang/ocap/snapshots/shops-<TS>.jsonl`。

**依赖**：MOD-112（`SHOP_BUILDING`）、`registry.underground`（`UnitRow/Counts/BackupInfo/ApplyResult/RestoreResult`、`load_rows`、`read_counts`、`unaffected_fingerprint`、`write_backup`、`verify_backup`、`_read_backup`）、`registry.models`（`RegistryUnit`、`build_specific_part`）、`core.audit`。`read_counts` 内对 `residency.models.Membership` 是函数内延迟导入（既有，`underground.py:read_counts`），本模块不新增 `registry → residency` 模块级依赖。

---

### MOD-113 导出命令加固

**文件**：`backend/apps/registry/exporting.py`（修改，仅新增函数）、`backend/apps/registry/management/commands/export_registry_import_file.py`（修改）。测试：`backend/tests/unit/test_registry_export_location.py`、`backend/tests/integration/test_owner_auth_export_cmd.py`。

```python
# registry/exporting.py（新增）
class OutputLocationError(Exception): ...
def pending_shop_units() -> int: ...                       # 只读：类型为商铺且楼栋不是 SHOP_BUILDING 的记录数
def check_output_location(path: Path) -> None: ...         # IFC-303：违反抛 OutputLocationError
def default_output_name(now: datetime, suffix: str = ".xlsx") -> str: ...   # "registry_import_YYYYMMDD-HHMMSS" + suffix
```

#### IFC-303 命令 `export_registry_import_file`（修改 IFC-297）
```
export_registry_import_file (--output PATH | --output-dir DIR) [--overwrite] [--allow-gaps] [--allow-unrelocated]
```
- **鉴权**：同 IFC-297（目标机 shell、用户另行授权导出，C-57）；全程只读（不调用任何写 API、不写审计，沿用）。
- **输入校验**：`--output` 与 `--output-dir` 恰好给一个（否则 `CommandError`，退出码 1）；`--output` 扩展名须为 `.xlsx`/`.csv`；`--output-dir` 须为已存在目录，文件名取 `default_output_name(...)`（不覆盖已存在文件，冲突则退出码 3）。
- **位置守卫（`check_output_location`，对两种输出方式都执行，失败退出码 3、不触库）**：解析后的绝对路径不得位于 `settings.BASE_DIR.parent`（部署根）、`settings.MEDIA_ROOT`、`settings.STATIC_ROOT`（若已设置）之内；其父目录须属当前进程用户，且 `mode & 0o077 == 0`（即 700 或更严）。文件由既有 `write_export_file` 以 0600 创建。
- **商铺未归类守卫**：`pending_shop_units() > 0` 且无 `--allow-unrelocated` → 退出码 2，不生成文件，输出 `pending_shop_units=N`；带 `--allow-unrelocated` 时继续并输出 `structure=legacy`（交付说明须写明文件为旧结构）；`pending == 0` 时输出 `structure=shop_relocated`。
- 其余（只读快照、`read_rows`+`plan_import` 自检、`imported == relocated_units`、计数差为 0、gaps 处理、退出码 0/1/2/3）同 IFC-297；输出只含计数与专有部分 id，**不含姓名与手机号**（C-59）。商铺改库后 `relocated_units`（上批地下车位口径）应为 0，`precheck_would_create_*` 与 `precheck_would_update_units` 应为 0。
- 文件名约定：带日期时间、一次性快照，不自动覆盖、不随清册自动更新（Q-OA-06=A）。推荐输出目录 `/home/yangyang/ocap_exports/`（700，由主会话授权时创建）。

**依赖**：MOD-112（`SHOP_BUILDING`）、`registry.models.RegistryUnit`、既有 `registry.exporting`/`import_template`/`importing`；`django.conf.settings`。

---

### MOD-114 清册核对与追加

**文件**：`backend/apps/registry/ownership.py`（新建）。测试：`backend/tests/unit/test_owner_name_matching.py`、`backend/tests/integration/test_owner_append_rules.py`。

```python
# registry/ownership.py —— 依赖 registry.models 与标准库；不依赖 residency/core.audit
from dataclasses import dataclass
from typing import Literal

OWNER_NAME_MAX: int = 64

def normalize_owner_name(text: str | None) -> str: ...                                  # IFC-304
def owner_matches(unit_id: int, name: str, phone: str | None) -> bool: ...              # IFC-304

@dataclass(frozen=True)
class AppendResult:
    result: Literal["OWNER_ADDED", "PHONE_ADDED", "UNCHANGED"]
    owner_id: int
    owner_phone_written: bool          # 本次是否写入了号码
    names_before: tuple[str, ...]      # 该专有部分追加前的有名业主姓名
    names_after: tuple[str, ...]
    phone_masked: str | None           # 如 "138****0009"；无号码为 None

class PhoneOwnedByOtherOwner(Exception): ...                                             # 视图翻译为 409
def append_owner_from_appeal(unit_id: int, name: str, phone: str | None) -> AppendResult: ...   # IFC-305
```

#### IFC-304 姓名归一与同一业主比对
- `normalize_owner_name`：非 `str`/`None` → `""`；把全角空格 `U+3000` 替换为半角空格，再 `strip()`；**不**去中间空格、不做大小写/繁简/拼音/模糊处理。`"　张三 "→"张三"`，`"张 三"` 保持含中间空格（AC-200-05）。
- `owner_matches(unit_id, name, phone)`：`name` 归一后为空，或 `phone` 为空 → `False`；否则读取该专有部分中手机号等于 `phone` 的 `RegistryPhone`（同一专有部分内手机号唯一，至多 1 行）及其业主，业主 `name` 为 `None`/空 → `False`；否则当且仅当 `normalize_owner_name(owner.name) == normalize_owner_name(name)` 返回 `True`。比较在 Python 内进行（不依赖 MySQL 排序规则）。无副作用。
- 输入校验：长度上限由调用方（视图）在归一后检查（≤ `OWNER_NAME_MAX`）。

#### IFC-305 申诉通过追加清册
- **前置**：调用方已在 `transaction.atomic()` 内；函数内先 `RegistryUnit.objects.select_for_update().filter(id=unit_id)`。
- `name` 须非空（调用方对无产权人名字的历史申诉不调用）；`phone` 可为 `None`（账号无手机号）。
- 规则：在该专有部分已有业主中按 `normalize_owner_name` 找同名者 → 复用，否则新建 `RegistryOwner(unit, name=归一姓名)`；`phone` 为 `None` → 不写号码；`phone` 已属**另一位**业主（`RegistryPhone(unit, phone)` 存在且 `owner_id` 不同）→ 抛 `PhoneOwnedByOtherOwner`；已属同一业主 → `UNCHANGED`；否则 `RegistryPhone.objects.create(unit, owner, phone)`。原有业主、号码与已认证身份不动（C-58）。**不调用** `AutoBindService`、不触碰 `Membership`（C-61）。
- 返回 `AppendResult`；`IntegrityError`（并发唯一约束）由调用方事务回滚，调用方转 409。

**依赖**：`registry.models`（`RegistryOwner`、`RegistryPhone`、`RegistryUnit`）。

---

### MOD-115 认证与申诉后端

**文件**：`backend/apps/residency/models.py`、`backend/apps/residency/views.py`、`backend/apps/residency/apps.py`（修改）；`backend/apps/residency/migrations/0003_appeal_owner_name.py`（新建，手写）。测试：`backend/tests/integration/test_owner_auth_certification.py`、`test_owner_auth_appeals.py`、`backend/tests/e2e/test_owner_auth_v2_journeys.py`。

```python
# residency/models.py：Appeal 增加一列（ADR-111）
owner_name = models.CharField(max_length=64, blank=True, default="")
```

#### IFC-306 `POST /certifications`（修改 IFC-050 一族，`residency/views.py:46-69`）
- 鉴权：`IsMember`（不变）；限频 `certify:{user.id}` 30 次/3600 秒（不变，REQ-NFUNC-037），限频先于任何校验。
- 请求：`{ "unit_id": int, "name": str }`。
- 输入校验与错误：

| 条件 | 状态码 / code / message |
|---|---|
| `unit_id` 缺失或非整数 | 400 `INVALID_VALUE` "缺少专有部分"（不变） |
| `name` 缺失 / 非字符串 / `normalize_owner_name` 后为空 | 400 `NAME_REQUIRED` "请输入姓名"（不发起比对、不认证） |
| `name` 归一后 > 64 字 | 400 `INVALID_VALUE` "姓名过长（最多 64 字）" |
| 专有部分不存在 | 404 `NOT_FOUND`（不变） |
| 已是该专有部分产权业主 | 409 `ALREADY_CERTIFIED`（不变） |
| `owner_matches(unit_id, name, user.phone)` 为假（姓名错 / 手机号错 / 该专有部分无此业主 / 清册姓名为空 / 账号无手机号，**同一出口**） | 422 `OWNER_NOT_MATCHED`，message 固定为"姓名与手机号未能通过清册核对，可上传产权证明提交申诉"，`details={"appeal_available": true}` |
| 成功 | 201 `{unit_id: int, specific_part: str, role: "HEAD"\|"OWNER"}`（不变） |

- 删除：`PHONE_REQUIRED`（409）与 `PHONE_NOT_IN_REGISTRY`（422）在本接口不再返回（accounts 的 `PHONE_REQUIRED` 是另一接口，`accounts/views.py:89`，不动）。
- 成功后沿用 `MembershipService.certify_owner(user.id, unit_id, "REGISTRY")`（首位认证者为户主，不变）；第二套房与首次认证同路径，**认证过程不写清册**（REQ-FUNC-198）。响应与日志不含清册姓名/手机号。

#### IFC-307 `POST /appeals`（修改，`residency/views.py:80-119`）
- 鉴权：`IsMember`（不变）。请求：`{ "unit_id": int, "owner_name": str, "proof_ids": list[str(uuid)] }`。
- 新增校验：`owner_name` 缺失 / 非字符串 / 归一后为空 → 400 `NAME_REQUIRED` "请输入产权人名字"；归一后 > 64 字 → 400 `INVALID_VALUE` "产权人名字过长（最多 64 字）"；校验在 `unit` 存在与 `ALREADY_CERTIFIED` 判断之后、附件校验之前，失败不产生申诉。
- 其余不变：`proof_ids` 为空 → 400 `PROOF_REQUIRED`；> 5 → 400 `ATTACHMENT_LIMIT`；同一用户同一专有部分已有待审 → 409 `APPEAL_PENDING`；附件格式与大小由上传接口按 `APPEAL_PROOF` 规格（jpg/jpeg/png/pdf、≤10MB、≤5 个，`core/attachments.py:19-20`）。无手机号用户同样至少 1 个资料（AC-202-02）。
- 存储：`Appeal.owner_name = normalize_owner_name(owner_name)`。
- 响应：201，`appeal_view(appeal)`（字段集合不变：`id, unit, status, submitted_at, decided_at, reject_reason`；**不加 `owner_name`**，契约测试 `test_frontend_contract.py:619` 锁定成员侧字段集）。

#### IFC-308 `GET /admin/appeals`（修改 IFC-053 一族，`residency/views.py:122-149`）
- 鉴权：`IsAdmin`（未登录 401、非管理员 403，不变）。查询参数 `status`（不变）、`page`、`page_size`（上限 100，`core/serializers.py`）。
- 响应：`{count, page, page_size, results: list[AdminAppealItem]}`：

```python
class AdminAppealItem(TypedDict):
    id: int                                   # 申诉编码，前端显示 "#{id}"（Q-OA-08=A，不新增存储）
    unit: dict                                # {"unit_id": int, "specific_part": str}
    status: str                               # PENDING|APPROVED|REJECTED|CLOSED
    submitted_at: str                         # ISO8601；申诉时间
    decided_at: str | None
    reject_reason: str | None
    owner_name: str | None                    # 申诉提交的产权人名字；历史申诉为 None（前端显示"未提供"）
    applicant: dict                           # {"id": int, "account_no": str, "nickname": str | None,
                                              #  "phone": str | None（脱敏，如 138****0009）, "has_phone": bool}
    proof: list[dict]                         # [{"id": str(uuid), "name": str, "size": int, "content_type": str}]，缩略图数量 = len(proof)
```
- 性能：附件按"当前页全部申诉 id"一次 `Attachment.objects.filter(linked_type="appeal", linked_id__in=[...])` 查询并分组，`select_related("user", "unit")` 保持，页内查询数不随行数增长（M-SA-010）。
- 不返回完整手机号（C-63）。

#### IFC-309 `POST /admin/appeals/{appeal_id}/decision`（修改 IFC-054 一族，`residency/views.py:152-186`）
- 鉴权：`IsAdmin`。请求 `{decision: "APPROVE"|"REJECT", reject_reason?: str(≤500)}`（不变）。
- `APPROVE` 在**同一 `transaction.atomic()`** 内顺序执行：`certify_owner(appeal.user_id, appeal.unit_id, "APPEAL")` → 若 `appeal.owner_name` 非空：`append_owner_from_appeal(unit_id, appeal.owner_name, appeal.user.phone or None)` → 写审计 `APPEAL_DECIDED`（不变）→ 写审计 `REGISTRY_UNIT_CHANGED`（`detail={"change":"appeal_append_owner","appeal_id","unit_id","result","names_before","names_after","phone_masked"}`，REQ-NFUNC-035；`owner_name` 为空时 `detail={"change":"appeal_append_owner","appeal_id","unit_id","result":"SKIPPED_NO_OWNER_NAME","note":"无产权人名字，未更新清册"}`）→ 保存申诉状态。
- 响应：200，`appeal_view(appeal)` 加 `registry_update`：`{"result": "OWNER_ADDED"|"PHONE_ADDED"|"UNCHANGED"|"SKIPPED_NO_OWNER_NAME", "owner_phone_written": bool, "notice": str | None}`；账号无手机号时 `notice = "该产权人无联系电话"`。`REJECT` 响应不含 `registry_update`，清册不变（AC-203-09）。
- 新增错误：409 `PHONE_OWNED_BY_OTHER`（`PhoneOwnedByOtherOwner`；整笔回滚：申诉仍 PENDING、认证关系未建立、清册无变化，AC-203-04）；追加过程任何未预期异常（含 `IntegrityError`）→ 事务回滚，409 `REGISTRY_UPDATE_FAILED` "清册更新失败，申诉保持待审"（AC-203-05）。既有 `ALREADY_CLOSED`、`ALREADY_DECIDED`、`NOT_FOUND`、`INVALID_VALUE` 不变。

#### IFC-310 `GET /attachments/{attachment_id}/download`（修改策略，`residency/apps.py:23-33`）
- 鉴权：`IsMemberOrAdmin`（不变，未登录 401）。`AppealAttachmentPolicy.can_open(linked_id, principal)`：申诉不存在或 `principal is None` → `False`（404）；管理员 → `True`；申诉人本人 → `True`；**其他已登录用户 → 抛 `ApiError("FORBIDDEN", "无权查看该资料", 403)`**（响应体仅 JSON 错误，无资料字节，AC-198-04）。
- 其余（`Content-Disposition`、`X-Content-Type-Options: nosniff`）不变。缩略图与大图都经此接口取回，不新增公开地址（REQ-NFUNC-034）。

#### 迁移 `0003_appeal_owner_name.py`
- `dependencies = [("residency", "0002_closed_status")]`；`operations = [migrations.AddField(model_name="appeal", name="owner_name", field=models.CharField(blank=True, default="", max_length=64))]`；手写、单 app，文件头不含 "Generated by Django"（画像 P6）。可逆（默认 `RemoveField`）。

**依赖**：MOD-114（`ownership`）、`registry.services.RegistryService.get_unit`、`core.attachments`、`core.audit`、`core.masking.mask_phone`、`residency.services.MembershipService`。

---

### MOD-116 席位生效判定与授予校验

**文件**：`backend/apps/committee/effective.py`（新建）；`committee/services.py`、`committee/views.py`、`accounts/directory.py`、`accounts/views.py`（修改）。测试：`backend/tests/unit/test_seat_effective.py`、`backend/tests/integration/test_seat_grant_backfill.py`、`backend/tests/integration/test_seat_effective_callsites.py`。

```python
# committee/effective.py —— 仅依赖 django.db.models.Q 与 datetime
from datetime import date
from django.db.models import Q

def effective_q(today: date) -> Q: ...                  # IFC-311：Q(status="ACTIVE", term_start__lte=today, term_end__gte=today)
def is_effective(seat, today: date) -> bool: ...        # IFC-311：seat.status == "ACTIVE" and seat.term_start <= today <= seat.term_end
```

#### IFC-311 谓词与调用点
改用谓词的"在任"判断（`git grep -n "term_end__gte\|term_end >=" -- backend/apps` 已穷举）：

| 位置 | 现状 | 改为 |
|---|---|---|
| `committee/services.py:31-34` `CommitteeQuery.active_seat` | `status=ACTIVE, term_end>=今天` | `.filter(effective_q(today))` |
| `committee/services.py:52-57` `active_member_ids` | 同上 | 同上 |
| `committee/services.py:59-63` `active_representative_ids` | 同上 | 同上 |
| `committee/services.py:80-90` `denominator_for_half_majority`（非 CONFIGURED_CAP 分支） | 同上 | 同上（分母只数已生效的在任者） |
| `accounts/directory.py:23` `identity_view` | `s.status == "ACTIVE" and s.term_end >= today` | `is_effective(s, today)` |
| `accounts/views.py:430-433` 用户列表席位预取 | `status=ACTIVE, term_end__gte=今天` | `Seat.objects.filter(effective_q(today))` |

`CommitteeQuery.is_member/is_chair_or_vice/is_representative/identity_labels` 与 `core/permissions.py:50-101`、审批/报销/收入的 `CommitteeQuery.is_member` 调用均经 `active_seat`，自动生效，**不改**。`identity/services.py:61` 把 `status="ACTIVE"` 的席位交给 `identity_view`（由它过滤），`:62` 用 `active_seat`，均不改。**有意保持不变**的"含未生效席位"口径：`CommitteeCommands.grant` 的 `ALREADY_SEATED`（:107）与 `CAP_REACHED`（:111-113）计数（Q-OA-28=A）、`sync_after_ownership_change`、账号注销/合并时的席位处理、`config_view` 的超额计算。

#### IFC-312 席位授予与列表（修改 IFC-060/061 一族）
- `POST /admin/committee/seats`（`committee/views.py:48-72`）：鉴权 `IsAdmin`（不变）。请求 `{user_id: int, position: "CHAIR"|"VICE_CHAIR"|"MEMBER"|"REPRESENTATIVE", term_start?: "YYYY-MM-DD"}`；缺省 `term_start` = 今天。
  - 输入校验：`term_start` 格式非法 → 400 `INVALID_VALUE` "term_start 格式不正确"（不变）；**删除**"开始日 < 今天"分支；`term_start > 今天 + 5 年` → 400 `INVALID_VALUE` "任期开始日过远"（`[ASSUMPTION]` OQ-04）。其余 `INVALID_VALUE`/`NOT_FOUND`/`NOT_AN_OWNER` 不变。
  - `CommitteeCommands.grant(*, user_id, position, term_start, admin_id) -> Seat`：校验顺序 `TERM_NOT_CONFIGURED`（409）→ `CAP_NOT_CONFIGURED`（409）→ 计算 `term_end = add_months(term_start, 月数)`；`term_end <= 今天` → 400 `INVALID_VALUE`，message `按配置任期，该席位已于 {term_end:%Y-%m-%d} 结束，不能授予`（AC-205-02/03）→ `ALREADY_SEATED`（409，含未生效席位）→ `CAP_REACHED`（409，含未生效席位）。成功 201，行为与既有一致。
  - `CommitteeCommands.change(seat, *, position, admin_id)`：旧席位若**已生效**，新席位 `term_start=今天`（不变）；旧席位**未生效**（`term_start > 今天`），新席位沿用旧 `term_start`。
- `GET /admin/committee/seats` 与 `seat_view`：`{id, position, user, term_start, term_end, status, effective: bool}`，`effective = is_effective(seat, 今天)`；`status` 取值与既有一致（未生效的仍是 `ACTIVE`）。
- 权限与行为：未登录 401、非管理员 403（不变，AC-205-06）；到期任务 `expire_due`（`committee/services.py:215-217`）不改，只处理 `term_end < today`（AC-206-02）。

**依赖**：无项目内新依赖；`accounts.directory → committee.effective`（`accounts/directory.py:7` 已依赖 `committee.models`，方向不变）。

---

### MOD-117 Web 前端

**文件**：见总览。测试：`frontend/tests/owner_auth_v2.spec.js`（vitest，画像 P3）。

#### IFC-313 `frontend/src/shared/api.js` 契约
```js
// unitApi（既有 :44-47 附近）
certify: (unitId, name) => post('/certifications', { unit_id: unitId, name }),     // 修改：新增 name
createAppeal: (data) => post('/appeals', data),   // data: { unit_id: number, owner_name: string, proof_ids: string[1..5] }
// admin：无新增路径；缩略图/大图沿用既有
downloadAttachment: (id) => adminHttp.get(`/attachments/${id}/download`, { responseType: 'blob' }),   // :179，不改
```
- 路径均为字符串字面量、不带 `?`；管理端只调 `IsAdmin` 接口；用户端只调 `IsMember` 接口，满足 `test_frontend_contract.py:30-97`。

#### 页面行为
- **`portal/Units.vue`**：选房卡片增加 `el-input`（`maxlength=64`，`placeholder="请输入姓名"`，必填）；"认证产权"前端先校验非空（空 → 提示"请输入姓名"，不发请求）。认证失败 `e.code === 'OWNER_NOT_MATCHED'`：保留 `pickedUnitId` 与姓名，把姓名写入 `appeal.ownerName`，提示"姓名与手机号未能通过核对，请上传产权证明提交申诉"（**不显示任何清册信息**）并滚动到申诉卡片。申诉卡片：`产权人名字`输入（默认带入、可改、必填、≤64）、`el-upload`（`multiple`、`:limit="5"`、`accept=".jpg,.jpeg,.png,.pdf"`），已上传 id 列表，提交 `createAppeal({unit_id, owner_name, proof_ids})`。删除"先绑定手机号"类提示，改为"无手机号也可输入姓名并上传产权证明申诉"。
- **`portal/parts/UnitCascader.vue`**：单元级 `el-select` 的 `placeholder` 取 `levelLabel`（`ref('单元')`，由选项响应 `data.level_label || '单元'` 更新，选楼栋变更时复位）。
- **`admin/AdminAppeals.vue`**：每条申诉显示 `申诉编码 #{id}`、账号、`昵称`（无昵称显示"未设置"）、`产权人名字`（`owner_name ?? '未提供'`）、申诉时间（`submitted_at`）、专有部分坐落；`applicant.has_phone === false` 且待审时显示提示"申诉人无手机号：通过后清册只写姓名、不写联系电话"；`<ProofThumbs :proofs="item.proof" />`；通过后若 `registry_update.notice` 非空，`ElMessage.warning(notice)`；`PHONE_OWNED_BY_OTHER`/`REGISTRY_UPDATE_FAILED` 以 `errorText(e)` 展示并保持列表原位（不刷新页码与状态筛选）。手机号列表仍为脱敏（`applicant.phone`）。
- **`admin/parts/ProofThumbs.vue`（新建，IFC-315）**：

```js
// props
{ proofs: Array<{ id: string, name: string, size: number, content_type: string }> }
```
  图片项：进入可视区后（`IntersectionObserver`）经 `admin.downloadAttachment(id)` 取 Blob，`createImageBitmap(blob, { resizeWidth: 160 })` 降采样为缩略图后丢弃原 Blob，并发 ≤3，已取结果按 `id` 缓存；pdf 项：显示文件图标 + 文件名。点击任一项打开 `el-dialog`：图片显示大图（再取原图 Blob，`URL.createObjectURL`，关闭/切换/卸载时 `revokeObjectURL`），上一份/下一份逐个查看；pdf 用 `<iframe :src="blobUrl">` 预览，加载失败显示"预览失败"与下载入口（`<a :href="blobUrl" :download="name">`）。关闭弹出层不触发列表重载，页码与状态筛选保持（AC-198-01）。取 Blob 失败（含 401/403）显示占位与 `errorText`，不显示任何图片内容。
- **`admin/AdminSeats.vue`**：状态列对 `row.status === 'ACTIVE' && row.effective === false` 显示"待生效"标签；创建对话框日期选择器不再限制过去日期，提示"任期结束日按配置月数推算，须晚于今天"；服务端 400 message 直接展示。

---

### MOD-118 小程序

**文件**：`miniprogram/pages/units/index.vue`、`miniprogram/components/UnitPicker.vue`、`miniprogram/utils/api.js`（修改）。测试：`miniprogram/tests/owner_auth_v2.spec.js`（vitest）。

#### IFC-314 `miniprogram/utils/api.js` 契约
```js
certify: (unitId, name) => http.post('/certifications', { unit_id: unitId, name }),     // 修改：新增 name
createAppeal: (data) => http.post('/appeals', data),   // data: { unit_id: number, owner_name: string, proof_ids: string[1..5] }
```
- 无管理端调用，不改。路径字面量、不带 `?`。

#### 页面行为
- **`pages/units/index.vue`**：选房卡片增加姓名输入（`input`，`maxlength=64`，必填）；`certify()` 无姓名时 `toast('请输入姓名')` 不发请求；`e.code === 'OWNER_NOT_MATCHED'` 时保留已选房号与姓名、姓名带入申诉的"产权人名字"、提示"姓名与手机号未能通过核对，请上传产权证明提交申诉"（不含清册信息）。申诉卡片：`产权人名字`输入、`uni.chooseImage({ count: 5 - 已选数 })` 多选上传（保留已上传 id 列表，最多 5 个），提交 `createAppeal({unit_id, owner_name, proof_ids})`；删除"请先绑定手机号"提示。
- **`components/UnitPicker.vue`**：单元级文案由 `levelLabel`（`data.level_label || '单元'`）决定，选楼栋变更时复位；其余逻辑（`apply`/跳级）不变。小程序申诉资料仅图片（OQ-06）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-185 | US-193 | MOD-112（排序）、MOD-111（数据归类） |
| REQ-FUNC-186 | US-193、US-195 | MOD-111、MOD-112 |
| REQ-FUNC-187 | US-194 | MOD-112（选项与 `level_label`）、MOD-111（`unit_no` 承载）、MOD-117（UnitCascader）、MOD-118（UnitPicker） |
| REQ-FUNC-188 | US-195 | MOD-111 |
| REQ-FUNC-189 | US-196 | MOD-113 |
| REQ-FUNC-190 | US-197 | MOD-115（IFC-308）、MOD-117（AdminAppeals、ProofThumbs） |
| REQ-FUNC-191 | US-198 | MOD-115（IFC-310 策略）、MOD-117（ProofThumbs） |
| REQ-FUNC-192 | US-199 | MOD-115（IFC-307、迁移）、MOD-117、MOD-118 |
| REQ-FUNC-193 | US-200 | MOD-115（IFC-306）、MOD-114、MOD-117、MOD-118 |
| REQ-FUNC-194 | US-200 | MOD-114（IFC-304）、MOD-115（IFC-306；`auto_bind.py` 不改） |
| REQ-FUNC-195 | US-201、US-202 | MOD-115（IFC-306 统一 422）、MOD-117、MOD-118 |
| REQ-FUNC-196 | US-202 | MOD-115（IFC-306 去掉 `PHONE_REQUIRED`、IFC-307）、MOD-117、MOD-118 |
| REQ-FUNC-197 | US-203 | MOD-114（IFC-305）、MOD-115（IFC-309）、MOD-117（通知/错误展示） |
| REQ-FUNC-198 | US-204 | MOD-115（IFC-306 同路径；认证不写清册）、MOD-114 |
| REQ-FUNC-199 | US-205 | MOD-116（IFC-312） |
| REQ-FUNC-200 | US-206 | MOD-116（IFC-311）、MOD-117（AdminSeats） |
| REQ-NFUNC-034 | US-198 | MOD-115（IFC-310）、MOD-117 |
| REQ-NFUNC-035 | US-203 | MOD-115（IFC-309 审计）、MOD-114（`AppendResult`） |
| REQ-NFUNC-036 | US-195、US-196 | MOD-111（核对、备份、还原）、MOD-113（计数一致） |
| REQ-NFUNC-037 | US-200 | MOD-115（IFC-306 单一错误出口、限频沿用） |
| C-57 | US-195、US-196 | MOD-111、MOD-113（独立命令、须授权、不进部署流程） |
| C-58 / C-61 | US-203、US-204 | MOD-114（追加不触 `Membership`/不调 `AutoBindService`）、MOD-115 |
| C-59 | US-196 | MOD-113（位置守卫、输出只含计数） |
| C-60 | US-193、US-195 | MOD-111（仅 `unit_type == SHOP`）、MOD-112 |
| C-62 / C-63 | US-199、US-197 | MOD-115（附件规格沿用、列表手机号脱敏） |

REQ-FUNC-185~200 共 16 条均被覆盖，无空行。

## 依赖关系

```
MOD-111 → MOD-112（SHOP_BUILDING，常量）；→ registry.underground（低层函数，IFC-294 一族）；→ registry.models；→ core.audit
MOD-113 → MOD-112（SHOP_BUILDING）；→ 既有 registry.exporting / import_template / importing
MOD-115 → MOD-114（IFC-304、IFC-305）；→ core.attachments / core.audit / core.masking；→ residency.services
MOD-116 内部：committee.services / committee.views / accounts.directory / accounts.views → committee.effective
MOD-117 → IFC-300（HTTP，经 MOD-112）、IFC-306~310（HTTP，经 MOD-115）、IFC-312（HTTP，经 MOD-116）
MOD-118 → IFC-300、IFC-306、IFC-307（HTTP）
```

跨 app 导入方向：`residency.views → registry.ownership`（新增，同方向先例 `residency/views.py:19-20`）；`registry.shops → registry.underground → residency.models`（仅 `read_counts` 内函数内延迟导入，既有）；`accounts.directory → committee.effective`（`committee.effective` 无项目内导入）。`registry.ordering`、`registry.ownership`、`committee.effective` 不导入 `residency`/`accounts`。**已检查：无循环依赖**。

## 数据迁移

**有 1 项结构迁移 + 1 项需另行授权的数据修正（不通过迁移）。**

| 项 | 内容 |
|---|---|
| 新字段 | `residency.Appeal.owner_name`：`CharField(max_length=64, blank=True, default="")`；无新表、无新索引、不改既有唯一约束 |
| 迁移方式 | 手写 `backend/apps/residency/migrations/0003_appeal_owner_name.py`（`AddField`），依赖 `0002_closed_status`；单 app（画像 P6）；不得提交 `makemigrations` 产物（P8）；开发者需用 Django 5.2.x 对照核对（画像 P4，不得用 6.x）；`makemigrations --check --dry-run` 须无漂移 |
| 可逆性 | 可逆（`RemoveField`）。回滚后列内数据丢弃；已通过的申诉已追加的清册数据不随列回退（属业务数据，不可自动回退，`[MANUAL_ROLLBACK_REQUIRED]` 仅在需要撤销已追加的产权人时由管理员在清册页手工处理） |
| 数据风险 | 加列带缺省值，千行级表上锁表时间可忽略 `[ESTIMATE]`；历史申诉 `owner_name=""` 表示"未提供"，无需回填；随部署的 `migrate --noinput` 自动执行（`SKILL.md:149`），无需单独授权 |

**测试环境数据变更不通过迁移**：商铺归类（107 条）由 `relocate_shops`（MOD-111）执行，原因见 ADR-107（迁移会在每次部署的 `migrate --noinput` 自动执行，违反"另行授权"；测试环境 `MIGRATION_MODULES` 置空，迁移不被测试跑到）。

| 项 | 内容 |
|---|---|
| 变更内容 | 仅 `RegistryUnit.building`（改为"商铺"）、`unit_no`（写入原楼栋/门牌）、`specific_part`、`updated_at`，且仅限 `unit_type == SHOP` 且楼栋非"商铺"的记录；不改业主、手机号、认证绑定 |
| 可逆性 | 可逆：`--restore PATH [--apply]` 把备份中全部列原值写回，差异 0；备份 apply 前强制生成并回读校验 |
| 数据风险 | (1) 改后标识/四元组冲突 → 写入前预演，冲突整批停止，库不变；(2) 原 `unit_no` 非空会被覆盖 → 作为 `unit_no_occupied` 冲突，整批停止；(3) 纯数字楼栋补"栋"后 `1` 与 `1栋` 同值 → 二者同层同户号本就生成相同标识而无法共存，备份保留逐记录原值（ADR-106）；(4) 执行期并发导入 → 唯一约束报错使事务回滚；(5) 备份不含个人信息，仍 0600 存放于目标机 |
| 执行前提 | 用户当轮另行明确授权（C-57）；apply 须 `--backup` 与 `--expect-changes`；授权前对任何环境数据写入数为 0 |

## 受影响的运行单元 / 构建

| 运行单元（画像 P7） | 动作 |
|---|---|
| `ocap-backend`（gunicorn 127.0.0.1:9000，systemd） | 部署新代码；`migrate --noinput` 执行 residency 0003；重启 |
| Web 前端（`npm run build -- --base=/ocap/`） | 重新构建并替换 `/home/yangyang/ocap/web/ocap`（`Units.vue`、`UnitCascader.vue`、`AdminAppeals.vue`、`ProofThumbs.vue`、`AdminSeats.vue`、`api.js` 变化） |
| 小程序（uni-app） | **须重新构建并发布**（认证接口强制要求姓名；`units/index.vue`、`UnitPicker.vue`、`api.js` 变化）；发布属画像之外的人工步骤（部署手册 RU-4），E1 须在计划中注明 |
| nginx `ocap` 站点（8090） | 不变 |
| `ocap-run-due-jobs` timer | 不变（`expire_due` 代码语义不变） |
| 一次性操作（非常驻） | 商铺改库：目标机 `backend/` 下 `venv/bin/python manage.py relocate_shops …`；导出：同目录 `export_registry_import_file --output-dir /home/yangyang/ocap_exports …`；各自须用户当轮单独授权，均不属于部署步骤；导出目录由主会话授权时创建（700） |
| Freeark 服务、端口、目录、库 | 不触碰（画像 P7/P8） |
| 需要重新烧录的固件 / FPGA | 不适用 |

### 既有测试影响（GROUP_C 须同步更新，保持零新增失败）

| 测试 | 影响 |
|---|---|
| `backend/tests/unit/test_registry_ordering.py:68-73,83-91` | 楼栋级"地下车位"层级由 2 变 1；文字楼栋（如"A区"）现排在"地下车位""商铺"之后；断言与混合排序期望须按 ADR-108 更新；新增商铺用例 |
| `backend/tests/integration/test_registry_sort_options.py`、`test_unit_sort_filters_me.py`、`tests/e2e/test_unit_sort_filters_journeys.py` | 凡涉及文字楼栋与地下车位相对次序、以及 `/certifications` 调用的用例，按新次序与新入参更新 |
| 断言 `PHONE_NOT_IN_REGISTRY` 的约 15 处：`tests/e2e/test_gap_journeys.py:66`、`test_journeys.py:78`、`test_registry_import_journeys.py:149`、`test_unit_sort_filters_journeys.py:125-134`；`tests/integration/test_gap_must_have.py:435`、`test_product_review_gap_stories.py:87,103`、`test_registry_import_enhancement.py:837,856`、`test_registry_sort_options.py:124-136`、`test_residency_api.py:54`；`tests/smoke/test_flows_smoke.py:92` | 改为带 `name` 的请求并断言 422 `OWNER_NOT_MATCHED` |
| 断言 `PHONE_REQUIRED`（认证路径）：`tests/integration/test_gap_must_have.py:888-893`（AC-002-04）、`test_registry_import_enhancement.py:847` | 无手机号用户现得 422 `OWNER_NOT_MATCHED` 并可走申诉；`/me` 等其他功能不受限的断言保留 |
| 所有 `POST /certifications` 成功路径（凡 `git grep -ln "/certifications" -- backend/tests` 列出的 12 个文件）与 `backend/tests/remote/remote_cases.py`、`remote_client.py` | 请求补 `name`（取清册业主的合成姓名）；远程用例只用 `e2e_` 账号与合成数据（画像 P4-1） |
| 所有 `POST /appeals` 调用（`tests/e2e/test_journeys.py`、`test_product_review_journeys.py`；`tests/integration/test_product_review_ac.py`、`test_product_review_gap_stories.py`、`test_residency_api.py`、`test_rework_cr011_024.py`；`tests/remote/remote_cases.py`、`remote_client.py`） | 请求补 `owner_name`；通过申诉的断言须考虑清册追加副作用 |
| `backend/tests/integration/test_rework_cr011_024.py:376` | "无关普通用户不可见（404）"改为 403（ADR-112）；未登录 401 不变 |
| `backend/tests/integration/test_frontend_contract.py:619` | 成员侧 `/appeals/mine` 字段集不变，无需改；新增调用自动被路径/方法/权限解析覆盖 |
| `backend/tests/integration/test_product_review_ac.py:830-836`（TC-INT-472） | 断言"开始日早于今天 → 400 任期开始日不得早于今天"改写为 AC-205-01~03 的新口径 |
| 席位夹具（`tests/support.py:149`、`tests/smoke/test_flows_smoke.py:98-135`、`tests/unit/test_domain_rules.py:143,185-187`、`tests/integration/test_admin_user_directory.py:54`、`tests/e2e/test_admin_user_directory_journey.py:31` 等 `Seat.objects.create(term_start=…)`） | 这些夹具开始日均为今天或更早，仍视为生效；无需改动，但须在全量跑中确认 |
| `frontend/tests/*.spec.js`、`miniprogram/tests/api.spec.js:90`（`api.certify(9)`） | 小程序 `certify` 签名增加 `name`，该用例须改为带姓名并断言请求体 |
| 上批命令测试 `tests/unit/test_underground_rules.py`、`tests/integration/test_underground_relocation_cmd.py`、`test_registry_export_cmd.py` | 不应变化；用于证明 MOD-111/113 对 `underground.py`/`exporting.py` 的改动向后兼容（含导出命令新增的位置守卫：临时目录须 `0700`，`tempfile.mkdtemp` 默认满足） |

### 测试规划（路径遵守画像 P3；全部用 SQLite 测试库与合成数据，不连接测试机数据库，不使用真实姓名与手机号，C-59）

| 文件 | 内容（关联 AC） |
|---|---|
| `backend/tests/unit/test_registry_ordering.py`（更新）、`backend/tests/integration/test_owner_auth_options.py`（新建） | 楼栋层级 1~10 → 地下车位 → 商铺 → "配套用房"（AC-193-01/04/05）；商铺第二级 `1栋<2栋<10栋<建设南路…`、`level_label` 仅商铺出现、空层级跳过、选项数 = 记录数（AC-194-01~04）；类型空/其他仍在原栋（AC-193-03） |
| `backend/tests/unit/test_shop_relocation_rules.py`、`backend/tests/integration/test_shop_relocation_cmd.py` | `shop_unit_no`（`1→1栋`、`1栋→1栋`、`建设南路142号` 原样、超长）；dry-run 零写（`CaptureQueriesContext`）；四类冲突整批停止；备份无姓名手机号；apply 前后计数/绑定/未受影响指纹相等；4347 同类记录（楼层"负1"）；已认证绑定与待审申诉不受影响（AC-195-06）；重复执行 0 改动；`--restore` 差异 0；缺参数/备份路径已存在的退出码；`lost_origin == 0`（AC-195-01~05、07） |
| `backend/tests/unit/test_registry_export_location.py`、`backend/tests/integration/test_owner_auth_export_cmd.py` | 位置守卫（部署根/MEDIA_ROOT 内拒绝、父目录 0755 拒绝、700 通过）；`--output-dir` 日期命名与不覆盖；`pending_shop_units>0` 退出码 2；改库后导出自检 `precheck_*` 为 0、楼栋列"商铺"、前导零与手机号文本原值；零写；失败无残留 `.part`（AC-196-01~07） |
| `backend/tests/unit/test_owner_name_matching.py`、`backend/tests/integration/test_owner_auth_certification.py` | 姓名归一与同一业主比对（AC-200-01/04/05/06）；缺姓名 400 且无比对（AC-200-02）；四种失败响应状态码与文案逐字相同（AC-200-07）；限频 31 次（AC-200-08）；注册/绑定手机号自动绑定不变（AC-200-09）；无手机号 422 且不得自动认证（AC-202-01/04）；第二套房不写清册（AC-204-01~03）；响应体不含清册姓名/手机号（AC-201-02） |
| `backend/tests/integration/test_owner_append_rules.py`、`test_owner_auth_appeals.py` | 追加/同名追加号码/同号拒绝/无手机号/历史申诉/回滚（认证、清册、状态均不变）/不触发他人认证/审计内容与手机号脱敏（AC-203-01~09）；申诉产权人名字必填与 64 字边界（AC-199-02/03）；管理端列表字段、"未设置""未提供"、手机号脱敏、状态筛选（AC-197-01~05）；附件 403/401/本人与管理员可读（AC-198-04/05）；页内查询数不随行数增长 |
| `backend/tests/unit/test_seat_effective.py`、`test_seat_grant_backfill.py`、`test_seat_effective_callsites.py` | 谓词边界（开始日=今天、结束日=今天）；授予 AC-205-01~05、`term_start` 上界；`change` 对未生效席位保持开始日；对**表中每个调用点**断言未来席位不生效（`/me` 身份与 `committee`、`IsCommitteeMember`、审批可选人、报销、收入、用户列表预取、半数分母）；到期任务不误处理未来席位（AC-206-02）；占名额与阻止重复授予（AC-206-04） |
| `backend/tests/e2e/test_owner_auth_v2_journeys.py` | 关键链路：选房第一级 → 商铺 → 姓名核对失败 → 转申诉 → 管理员通过 → 清册追加 → 同一用户再次认证成功；席位补录与未来席位（critical path，前后端契约由 `test_frontend_contract.py` 与前端测试守护，画像 P5） |
| `frontend/tests/owner_auth_v2.spec.js`、`miniprogram/tests/owner_auth_v2.spec.js` | 请求体含 `name`/`owner_name`；`OWNER_NOT_MATCHED` 转申诉并带入姓名；多附件 ≤5；`level_label` 占位；`ProofThumbs` 懒加载/弹窗/pdf 预览失败给下载；`AdminSeats` "待生效" |

## 领域与外部依赖出处

画像 P11 有条目，但本批**不新增、不改变对任何闭源 / 外部 API 的调用**（微信、阿里云短信、邮件均不涉及；小程序未新增 `wx.*` 接口）。下表登记接口契约引用的现有代码事实。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-299/300 | 现有楼栋层级（-1/0/1/2）、保留名"地下车位"、`options()` 响应结构与跳级逻辑 | [CODE: backend/apps/registry/ordering.py:6,68-80]、[CODE: backend/apps/registry/services.py:23-81] |
| IFC-301/302 | 低层备份/核对函数与命令流程（dry-run、`--apply/--backup/--expect-changes/--restore`、退出码 0/1/2/3） | [CODE: backend/apps/registry/underground.py（`write_backup`、`apply_relocation`、`restore_from_backup`）]、[CODE: backend/apps/registry/management/commands/relocate_underground_parking.py] |
| IFC-301 | `build_specific_part` 生成标识；`unit_no`/`floor` 长度 32 与四元组/标识唯一 | [CODE: backend/apps/registry/models.py:23-31,47-56,62-63,73] |
| IFC-303 | 导出命令只读、自检、`write_export_file`（`.part`→`os.replace`、0600）；部署根 = `settings.BASE_DIR.parent`；`MEDIA_ROOT = BASE_DIR/var/attachments` | [CODE: backend/apps/registry/exporting.py]、[CODE: backend/config/settings.py:5,87] |
| IFC-303 | 部署预检要求 `/home/yangyang/ocap` 仅 `backend/web/snapshots`；后端叠加解包、回滚 `rm -rf backend` | [CODE: .claude/skills/ocap-deploy/SKILL.md:93,132,280] |
| IFC-304/305 | 同专有部分内业主姓名唯一、手机号唯一；业主姓名可空（回填遗留）；`certify_owner` 对专有部分行加锁 | [CODE: backend/apps/registry/models.py:83-103]、[CODE: backend/apps/residency/services.py:49] |
| IFC-306 | 现认证流程：限频 30/3600、`PHONE_REQUIRED`/`PHONE_NOT_IN_REGISTRY`、`certify_owner(..., "REGISTRY")` | [CODE: backend/apps/residency/views.py:46-69] |
| IFC-306 | 手机号注册/绑定自动绑定通路（不改） | [CODE: backend/apps/residency/auto_bind.py:26-50]、[CODE: backend/apps/accounts/views.py:116]、[CODE: backend/apps/identity/views.py:47] |
| IFC-307/308/309 | 现申诉创建、后台列表、决定流程与审计动作；附件规格 jpg/jpeg/png/pdf、≤10MB、≤5 | [CODE: backend/apps/residency/views.py:80-186]、[CODE: backend/apps/core/attachments.py:19-20]、[CODE: backend/apps/core/audit.py:11-15] |
| IFC-310 | 附件下载鉴权与策略；无权时 404；`IsMemberOrAdmin` | [CODE: backend/apps/core/attachments.py:112-132]、[CODE: backend/apps/residency/apps.py:23-33]、[CODE: backend/apps/core/permissions.py:37] |
| IFC-311/312 | 席位"在任"现仅看 `term_end`；授予校验与任期计算；`ALREADY_SEATED`/`CAP_REACHED` 计数 | [CODE: backend/apps/committee/services.py:31-62,80-90,92-120,215-217]、[CODE: backend/apps/committee/views.py:48-72]、[CODE: backend/apps/accounts/directory.py:20-25]、[CODE: backend/apps/accounts/views.py:430-433] |
| IFC-313/314 | 现 `certify`/`createAppeal` 调用与契约守护测试解析规则 | [CODE: frontend/src/shared/api.js:44-47,179]、[CODE: miniprogram/utils/api.js:28-31]、[CODE: backend/tests/integration/test_frontend_contract.py:30-97,613-622] |
| IFC-315 | 管理端经 axios 取 Blob 再打开附件的现有做法 | [CODE: frontend/src/admin/AdminAppeals.vue（`openProof`）] |
| ADR-116 | `uni.chooseFile` 在小程序不受支持；`wx.chooseMessageFile` 仅 mp-weixin、参数见微信文档 | [WEB: https://uniapp.dcloud.net.cn/api/media/file.html，2026-11-16]（微信文档不在仓库，未采用，OQ-06） |
