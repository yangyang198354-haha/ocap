<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T11:49:53+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：逐级选房排序统一、地下车位归属修正与后台清册过滤器（INCREMENTAL）

> 编号接续全仓最大值（已 grep `project_workspace/*/architecture/`）：MOD-104~110、IFC-285~298（ADR-097~105 见 architecture_design.md）。
> 模块 = 本次新建/修改的代码单元，路径相对仓库根；后端前缀 `backend/apps/`。HTTP 路径省略前缀 `/api/v1`；错误体统一为 `{code, message, details?}`（`core/errors.py`，沿用 `ApiError`）。
> 只写签名与契约，不写函数体。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-104 | 自然顺序排序规则 | **新建** `registry/ordering.py` | 唯一定义"数字自然顺序"比较键与保留楼栋名常量；纯函数、无数据库访问 | REQ-FUNC-173/174/175/184；US-183、184、192 | 无（仅标准库） |
| MOD-105 | 逐级选项排序接入 | **修改** `registry/services.py`（删除 `_floor_sort_key` :9-19，改 `RegistryService.options` :38-83） | 楼栋/单元/楼层/户号四级用统一键排序；响应结构不变 | REQ-FUNC-173/174/175/176/177；US-183~186 | MOD-104 |
| MOD-106 | 已认证房屋排序统一 | **修改** `identity/services.py`（`IdentityService._units` :48）、`residency/housing.py`（`housing_view` :41-68） | `/me` 与 `/me/housing` 的房屋行共用同一排序键 | REQ-FUNC-184；US-192 | MOD-104 |
| MOD-107 | 后台清册过滤 API | **修改** `registry/views.py`（`AdminUnitListView.get` :74-90；新增 `AdminUnitFilterOptionsView`）、`registry/urls.py` | 增加楼栋/单元/户号/姓名/电话过滤并与现有 `q`、`unit_type` 同时生效；提供楼栋、单元下拉取值 | REQ-FUNC-180/181/182；REQ-NFUNC-033；US-189、190 | MOD-104 |
| MOD-108 | 后台清册页过滤器 | **修改** `frontend/src/admin/AdminRegistry.vue`、`frontend/src/shared/api.js`（:141 附近） | 六个过滤器 + 原标识搜索 + 重置；全部中文占位与空状态 | REQ-FUNC-180/181/183；US-189~191 | IFC-291、IFC-292 |
| MOD-109 | 地下车位归属规则与修正（AUTH-02） | **新建** `registry/underground.py`、`registry/management/commands/relocate_underground_parking.py` | 识别、冲突预演、备份、事务内更新与核对、还原；默认 dry-run | REQ-FUNC-179；REQ-NFUNC-032；US-188 | MOD-104、registry.models、core.audit |
| MOD-110 | 清册导出文件生成（AUTH-01） | **新建** `registry/exporting.py`、`registry/management/commands/export_registry_import_file.py`；**修改** `registry/import_template.py`（仅新增函数） | 只读导出、按导入模板生成文件、自检与一致性核对、原子落盘 | REQ-FUNC-178；REQ-NFUNC-032；US-187 | MOD-109（仅 `plan_relocation` 纯规则）、`registry/importing.py`、`registry/import_spec.py` |

备注（不改动的单元，已核实）：
- Web 用户端 `frontend/src/portal/parts/UnitCascader.vue`、`Home.vue:45`、`Me.vue:11`、`Units.vue:8`，小程序 `miniprogram/components/UnitPicker.vue`、`miniprogram/pages/index/index.vue:42`、`miniprogram/pages/me/index.vue:24`，以及 `miniprogram/utils/api.js`：只渲染服务端返回的顺序，无客户端排序（`grep "\.sort(\|sorted("` 在 `frontend/src/portal`、`miniprogram/pages|components|utils` 无结果），**不改文件**；它们由集成/前端契约测试守护（见测试规划）。
- 导入引擎 `registry/importing.py`、`registry/import_spec.py`：只被 MOD-110 调用，不改。
- 后端 `registry/models.py` 不改，故**无迁移**。

## 模块详情

### MOD-104 自然顺序排序规则

**文件**：`backend/apps/registry/ordering.py`（新建）。测试：`backend/tests/unit/test_registry_ordering.py`。

```python
# registry/ordering.py —— 仅依赖标准库（re、typing）
UNDERGROUND_BUILDING: str = "地下车位"                       # 跨模块字面量的唯一定义处（ADR-099）
LEVEL_SUFFIXES: dict[str, str] = {"building": "栋", "unit_no": "单元", "floor": "层", "room": "号"}
Level = Literal["building", "unit_no", "floor", "room"]
NaturalKey = tuple[int, int, tuple[tuple[int, int, str], ...], str]
    # (层级, 数值, 文字段序列, 原始文本)；层级：-1 空；0 整数；1 其他文字；2 保留名

def parse_integer_text(text: str | None, suffix: str = "") -> int | None: ...      # IFC-287
def natural_key(value: str | None, level: Level) -> NaturalKey: ...                # IFC-285
def unit_sort_key(building: str, unit_no: str, floor: str, room: str,
                  unit_id: int = 0) -> tuple[NaturalKey, NaturalKey, NaturalKey, NaturalKey, int]: ...   # IFC-286
def sorted_values(values: Iterable[str], level: Level) -> list[str]: ...           # 去重后按 natural_key 升序
```

#### IFC-287 `parse_integer_text`
- 输入：任意字符串或 None；`suffix` 为该层级的可选后缀（`LEVEL_SUFFIXES[level]`）。
- 处理：去首尾空白；若以 `suffix` 结尾且去掉后缀后非空则去掉一次；匹配 `^(负|-)?(数字|中文数字)$`；数字为 ASCII/全角阿拉伯数字，中文数字支持 零〇一二两三四五六七八九十 组成的 0~99（如 十、十一、二十、二十一）。
- 返回：带符号整数；不匹配返回 `None`（含空串、超过 99 的中文数字、`B1` 等）。
- 同时被 MOD-109 用于"楼层为负层"判断（`parse_integer_text(floor, "层") < 0`），保证排序与识别同口径。
- 校验：不抛异常；非 `str` 输入（`None`）按空串处理。

#### IFC-285 `natural_key`
- 返回比较键，规则见 ADR-098：层级 -1（空串/None）→ 0（`parse_integer_text` 成功，数值升序）→ 1（其他文字：拆为数字段 `(0, n, "")` 与非数字段 `(1, 0, s)` 的序列，非数字段按码位比较）→ 2（仅 `level == "building"` 且去空白后等于 `UNDERGROUND_BUILDING`）。末位元素为去空白后的原文，作确定性并列规则。
- 键之间可直接比较（元素类型逐位一致，不会出现 int 与 str 混比）。
- 不做任何输入改写：不修改、不丢弃、不合并值（"-1" 与 "负一" 并存时相邻、均保留）。

#### IFC-286 `unit_sort_key`
- 返回 `(natural_key(building,"building"), natural_key(unit_no,"unit_no"), natural_key(floor,"floor"), natural_key(room,"room"), unit_id)`；`unit_id` 为最终并列规则，使刷新顺序稳定（基线 AC-157-01）。

**依赖**：无。**外部依赖**：无。

---

### MOD-105 逐级选项排序接入

**文件**：`backend/apps/registry/services.py`（修改）。`UnitOptionsView`（`registry/views.py:57-71`）不改。测试：`backend/tests/integration/test_registry_sort_options.py`。

#### IFC-288 `GET /units/options`（修改 IFC-152，仅排序）
- 鉴权：`IsMember`（沿用 `registry/views.py` `UnitOptionsView.permission_classes`）；输入校验与错误（`building/unit_no/floor` ≤32 字符、缺上级参数 → `400 INVALID_QUERY`）**完全不变**。
- 响应结构不变：`{level, skipped, has_empty, options}`，`options` 为列表，`level="room"` 时每项含 `value, unit_id, unit_type, unit_type_label, area, label`。
- 排序（变更点）：
  - `level="building"`：`sorted_values(values, "building")`；"地下车位" 排在所有其他楼栋之后。
  - `level="unit_no"`、`"floor"`：`sorted_values(values_non_empty, level)`；`has_empty` 判定与"未划分"项位置逻辑不变（空值不进 `options`，客户端把它放最前）。
  - `level="room"`：对候选 `RegistryUnit` 按 `(natural_key(room,"room"), id)` 升序，**取代** `qs.order_by("room")`（`services.py:68`）。
- 地下车位：无任何特例代码。库里存在 `building="地下车位"` 的记录时它就是普通一项；选中后单元级全空 → `skipped=["unit_no"]`，楼层为负层（负二在前、负一其后）；没有此类记录则不出现（AC-185-03）。
- 兼容：旧楼层键 `_floor_sort_key` 的"负/-+阿拉伯数字"行为是新规则的子集（AC-183-03 不退化）；`git grep _floor_sort_key -- backend` 仅 `services.py` 内部引用，无测试导入，可直接删除。

**依赖**：MOD-104。

---

### MOD-106 已认证房屋排序统一

**文件**：`backend/apps/identity/services.py`（修改 `IdentityService._units`，原 :42-50）、`backend/apps/residency/housing.py`（修改 `housing_view`，原 :39-68）。测试：`backend/tests/integration/test_unit_sort_filters_me.py`。

#### IFC-289 `GET /me` 的 `identities.units` 顺序（修改）
- 鉴权、字段、状态码不变。顺序：先按专有部分去重取最高角色（既有规则，`identity/services.py:42-47`），再按 `unit_sort_key(unit.building, unit.unit_no, unit.floor, unit.room, unit.id)` 升序，**取代** `(unit.specific_part, unit_id)`（`:48`）。

#### IFC-290 `GET /me/housing` 的 `units` 顺序（修改）
- 鉴权、字段不变。顺序：`units` 在组装时对 `memberships` 按 `(unit_sort_key(...), membership.id)` 升序遍历；**传给 `identity_view` 的 `memberships`、`residents_by_unit` 的 `certified_at, id` 排序保持不变**（汇总身份与房屋行身份相互独立，AC-192-03）。数据库查询处 `order_by("certified_at", "id")`（`housing.py:41`）可保留，仅作为 `sorted` 前的稳定输入。
- 同一专有部分有两条有效记录（产权业主 + 同住人，`test_identity_display.py:118-123` 的场景）仍各出一行，二者按 `membership.id` 相邻；`/me` 对同一专有部分只出一行。因此两处"不同专有部分"的相对顺序逐项一致（AC-192-01/02）。
- 无有效记录（游客）：`units == []`，不报错（AC-192-04）。

**依赖**：MOD-104、既有 `apps.accounts.directory.identity_view`。依赖方向：`identity.services`/`residency.housing → registry.ordering`（`registry.ordering` 无任何项目内导入，不会形成环）。

---

### MOD-107 后台清册过滤 API

**文件**：`backend/apps/registry/views.py`（修改 `AdminUnitListView.get`，新增 `AdminUnitFilterOptionsView`）、`backend/apps/registry/urls.py`（修改）。测试：`backend/tests/integration/test_admin_registry_filters.py`。

```python
# registry/urls.py 追加（须置于 "admin/registry/units/<int:unit_id>" 之前或之后均可，int 转换器不会匹配该字面量）
path("admin/registry/units/filter-options", AdminUnitFilterOptionsView.as_view()),     # IFC-292
```

#### IFC-291 `GET /admin/registry/units`（修改 IFC-153，仅新增查询参数）
- 鉴权：`IsAdmin`（`core/permissions.py:19-24`；非管理员 403 `FORBIDDEN`，未登录 401 `UNAUTHORIZED`；被拒时不返回任何清册数据，REQ-NFUNC-033）。
- 查询参数（全部可选，缺省或空串表示不限制）：

| 参数 | 类型 / 校验 | 匹配 | 错误 |
|---|---|---|---|
| `q` | str ≤64（不变） | `specific_part` 包含（不变） | `400 INVALID_QUERY` "q 过长（最多 64 字符）"（不变，AC-190-03） |
| `unit_type` | 五个代码之一或 `UNSET`（不变） | 精确 / 未登记 | `400 INVALID_QUERY`（不变） |
| `building` | str ≤32 | 精确（`building=`） | `400 INVALID_QUERY` "building 过长（最多 32 字符）" |
| `unit_no` | str ≤32 | 精确 | 同上，参数名替换 |
| `room` | str ≤32 | 精确 | 同上 |
| `owner_name` | str ≤64 | 存在某位业主 `name` 包含（`Exists(RegistryOwner…, name__icontains=…)`） | `400 INVALID_QUERY` "owner_name 过长（最多 64 字符）" |
| `owner_phone` | 须匹配 `^\d{1,11}$` | 存在某条业主手机号 `phone` 包含（`Exists(RegistryPhone…, phone__contains=…)`） | `400 INVALID_QUERY` "owner_phone 须为 1~11 位数字" |
| `page`、`page_size` | 不变（`core/serializers.py:4-13`，页大小 1~100） | — | 非法值回落默认（既有行为） |

- 语义：所有给出的条件取交集；姓名条件与手机号条件各自独立（不要求同一位业主）；`Exists` 子查询，不 JOIN，列表不出现重复行，`count` 为过滤后总数（AC-189-01）。清空全部条件等于无过滤（AC-189-08）。过滤后无结果：`200` 且 `count=0, results=[]`（AC-189-06）。
- 响应：与 IFC-153 完全相同 `{count, page, page_size, results: [RegistryUnitAdminSerializer]}`；`owners` 含姓名与完整手机号（仅管理端，`registry/serializers.py`）。排序仍为 `id`。
- 审计：只读，不写审计。

#### IFC-292 `GET /admin/registry/units/filter-options`（新）
- 鉴权：`IsAdmin`；无参数；不接受请求体。
- 响应 200：

```python
class FilterOptions(TypedDict):
    buildings: list[str]     # 清册中全部非空楼栋的去重取值，按 sorted_values(…, "building")，"地下车位" 在最后
    unit_nos: list[str]      # 清册中全部非空单元的去重取值，按 sorted_values(…, "unit_no")
```
- 不含任何姓名、手机号；取值只来自 `RegistryUnit.building` / `unit_no`（`values_list` + `distinct`）。
- 错误：401/403 同 IFC-291。

**依赖**：MOD-104、`core.permissions.IsAdmin`、`core.errors.ApiError`、`core.serializers.page_response`、registry.models。

---

### MOD-108 后台清册页过滤器

**文件**：`frontend/src/admin/AdminRegistry.vue`（修改，原筛选区 :7-12 与脚本 `load()`）、`frontend/src/shared/api.js`（修改 `admin` 对象，原 :141）。测试：`frontend/tests/registry_filters.spec.js`（vitest，画像 P3）。

#### IFC-293 `frontend/src/shared/api.js` 契约
```js
registryUnits: (params) => adminHttp.get('/admin/registry/units', { params }),    // 既有；params 新增键：building, unit_no, room, owner_name, owner_phone（值为空串或 undefined 时不传）
registryFilterOptions: () => adminHttp.get('/admin/registry/units/filter-options'),   // 新增；返回 { buildings: string[], unit_nos: string[] }
```
- 路径写成字符串字面量、不带 `?`、管理端只调用 `IsAdmin` 接口，满足 `backend/tests/integration/test_frontend_contract.py:30-97` 的解析规则；小程序 `miniprogram/utils/api.js` **无管理端调用，不改**。

#### 页面行为（`AdminRegistry.vue`）
- 过滤区控件（顺序）：标识搜索（保留，`placeholder="专有部分标识搜索"`，行为不变）、楼栋（`el-select`，`filterable clearable placeholder="楼栋"`，选项来自 `registryFilterOptions().buildings`）、单元（同上，`placeholder="单元"`，`unit_nos`）、户号（`el-input clearable placeholder="户号" maxlength=32`）、类型（`el-select clearable placeholder="全部类型"`，选项沿用"全部类型 / 未登记类型 / 住宅 / 公寓 / 商铺 / 车位 / 其他"）、产权业主姓名（`el-input clearable placeholder="产权业主姓名" maxlength=64`）、产权业主电话（`el-input clearable placeholder="产权业主电话" maxlength=11`，仅数字），以及"重置"按钮。**不出现楼层过滤**（AC-189-09）。
- 任一条件变化或回车 → `page=1` 后调用 `load()`；`load()` 把非空条件映射为 IFC-291 的查询参数；"重置"清空全部条件并重新加载（AC-189-08）。
- 中文化（ADR-105）：每个 `el-select` 显式 `placeholder`；下拉 `no-data-text="暂无数据"`；表格 `empty-text="暂无数据"`（AC-191-01~03）。不引入全局 locale。
- 错误展示沿用 `errorText(e)`（400 `INVALID_QUERY` 的中文 `message` 直接显示）。
- 下拉取值在页面挂载时请求一次；失败时下拉为空但不阻塞列表（用 `ElMessage.error(errorText(e))` 提示）。

**依赖**：IFC-291、IFC-292。

---

### MOD-109 地下车位归属规则与修正（AUTH-02）

**文件**：`backend/apps/registry/underground.py`（新建，规则与执行函数）、`backend/apps/registry/management/commands/relocate_underground_parking.py`（新建，命令外壳）。测试：`backend/tests/unit/test_underground_rules.py`、`backend/tests/integration/test_underground_relocation_cmd.py`（SQLite 测试库 + `call_command`，不连接测试机，画像 P8）。

```python
# registry/underground.py
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

TARGET_BUILDING: str = UNDERGROUND_BUILDING          # 来自 registry.ordering
BACKUP_FORMAT: str = "ocap-underground-backup/1"

@dataclass(frozen=True)
class UnitRow:                      # 规则输入（不含任何个人信息）
    id: int; building: str; unit_no: str; floor: str; room: str
    specific_part: str; unit_type: str | None; area: str | None
    created_at: str; updated_at: str            # ISO8601 文本

@dataclass(frozen=True)
class Move:
    unit_id: int; old_building: str
    old_specific_part: str; new_specific_part: str

@dataclass(frozen=True)
class Conflict:
    kind: Literal["specific_part", "tuple"]     # 标识（casefold）重复 / 四元组重复
    key: str                                    # 冲突的新标识或四元组文本
    unit_ids: tuple[int, ...]

@dataclass(frozen=True)
class RelocationPlan:
    total_units: int
    candidates: int                              # 类型为车位且楼层为负层（含已在目标楼栋）
    already_target: int
    moves: tuple[Move, ...]
    conflicts: tuple[Conflict, ...]
    old_building_counts: dict[str, int]          # 被改记录的旧楼栋写法分布（Q-SF-02b-1）
    parking_floor_spellings: dict[str, tuple[int, bool]]   # 车位类全部楼层写法 -> (记录数, 是否被识别为负层)（Q-SF-02b-2）
    negative_floor_non_parking: int              # 负层但类型不是车位的记录数（不会改，仅提示）
    other_building_negative_parking: int         # 非 "1/1栋" 楼栋下的被改记录数（Q-SF-02b-3）

@dataclass(frozen=True)
class Counts:
    units: int; owners: int; phones: int; active_memberships: int

def is_negative_floor(floor: str | None) -> bool: ...                          # IFC-294：parse_integer_text(floor,"层") < 0
def plan_relocation(rows: Iterable[UnitRow]) -> RelocationPlan: ...            # IFC-294：纯函数，无库访问
def load_rows() -> list[UnitRow]: ...                                          # 只读，iterator(chunk_size=1000)
def read_counts() -> Counts: ...                                               # 只读
def unaffected_fingerprint(exclude_ids: set[int]) -> str: ...                  # sha256(id,四级取值,标识,类型,面积) 排序后摘要
def write_backup(path: Path, plan: RelocationPlan, rows: list[UnitRow], counts: Counts) -> "BackupInfo": ...
def verify_backup(path: Path) -> "BackupInfo": ...                             # 校验头部、行数与末行 sha256
def apply_relocation(plan: RelocationPlan, backup: "BackupInfo", expected_changes: int) -> "ApplyResult": ...
def restore_from_backup(path: Path, apply: bool) -> "RestoreResult": ...
```

> `BackupInfo(path: Path, records: int, counts: Counts, sha256: str)`、`ApplyResult(moved: int, before: Counts, after: Counts)`、`RestoreResult(restored: int, differences: int, before: Counts, after: Counts)` 为对应的 frozen dataclass；`plan_relocation` 之外的函数都访问数据库。

#### IFC-294 规则与执行函数契约
- **识别**：`unit_type == "PARKING"` 且 `is_negative_floor(floor)`；`building == TARGET_BUILDING` 的计入 `already_target`、不进入 `moves`（幂等，AC-188-04）。
- **新标识**：`new_specific_part = build_specific_part(TARGET_BUILDING, unit_no, floor, room)`（`registry/models.py:47-56`，同一函数，不复制规则）。
- **冲突预演（最终状态）**：被改记录取新值、其余记录取旧值；检查 (a) `specific_part.casefold()` 重复、(b) `(building, unit_no, floor, room)` 重复。任一 → `conflicts` 非空；`apply_relocation` 遇冲突直接抛错、不写入（AC-188-03）。
- **`apply_relocation`**：要求 `expected_changes == len(plan.moves)`；`transaction.atomic()` 内 `select_for_update` 锁定候选行并重算计划，数量或 id 集合与备份不一致则抛 `RelocationAborted`；逐行 `RegistryUnit.objects.filter(id=…, building=old_building).update(building=TARGET_BUILDING, specific_part=new, updated_at=now)`，每条必须恰好影响 1 行；同事务内写一条审计 `AuditService.record(actor=AuditActor("SYSTEM", None, "management_command"), action="REGISTRY_UNIT_CHANGED", object_type="registry", object_id="underground_relocation", result="SUCCESS", detail={"change": "underground_relocation", "moved": N})`；提交前核对 `Counts` 前后相等、被改记录 `building` 均为目标值、`unaffected_fingerprint` 前后相等，任一不符抛 `RelocationVerifyError`（回滚）。
- **`restore_from_backup`**：先 `verify_backup`；对备份中每条记录检查"当前行存在且 `building == TARGET_BUILDING`"，否则列出并中止；`apply=True` 时事务内把备份的全部列（含 `updated_at`）原值写回（`QuerySet.update`），再核对 `Counts` 与头部一致、逐记录与备份差异为 0；`apply=False` 只报告。
- 异常类型：`RelocationConflict`、`RelocationAborted`、`RelocationVerifyError`、`BackupError`（均继承 `Exception`，由命令外壳翻译为退出码）。

#### IFC-295 命令 `python manage.py relocate_underground_parking`（CLI）
```
relocate_underground_parking                                  # dry-run（默认，只读）
relocate_underground_parking --apply --backup PATH --expect-changes N
relocate_underground_parking --restore PATH                   # 还原 dry-run（只读）
relocate_underground_parking --restore PATH --apply           # 实际还原
        [--list-limit N]                                      # 明细最多输出条数，1~100000，缺省 50
```
- **鉴权**：无 HTTP 鉴权；只能在目标机 shell 里以部署用户执行 `manage.py`；是否允许执行由用户"另行授权"（C-51、AUTH-02），画像 P9 规定子代理不得 ssh，由主会话在授权后执行。命令**不接受**任何隐式写入路径（没有 `--apply` 一律只读）。
- **输入校验**：`--apply` 必须同时给 `--backup` 与 `--expect-changes`（非负整数），缺任一 → `CommandError`（退出码 1）；`--backup` 路径已存在 → 退出码 3 且不触库；`--apply` 与 `--restore` 的组合只允许 `--restore PATH --apply`；`--list-limit` 越界 → `CommandError`；`--restore` 的备份校验失败 → 退出码 3。
- **退出码**：0 正常（含"无需修改"）；1 参数错误；2 存在冲突、`--expect-changes` 与计划不符、事务内核对失败（均已回滚，库保持修正前状态）；3 备份/还原文件问题。
- **输出（stdout，`key=value` 与 `明细|…` 行，沿用 `registry_specific_part_preview` 风格）**：`total_units`、`candidates`、`already_target`、`would_change`、`conflicts`、`old_building|<值>|<数>`、`floor|<写法>|<数>|<recognized|unrecognized>`、`negative_floor_non_parking`、`other_building_negative_parking`、`conflict|<kind>|<key>|<id,id…>`、`move|<id>|<旧标识>|<新标识>`（受 `--list-limit` 限）；apply/restore 额外输出 `before_*`/`after_*`（units、owners、phones、active_memberships）与 `differences`。**不输出姓名、手机号**（C-55）。
- 日志同样只含计数与记录 id。
- 备份文件格式（JSON Lines，UTF-8）：第 1 行头 `{"format","created_at","records","counts"}`；之后每行一条被改记录（`UnitRow` 全字段）；末行 `{"sha256": "<前面全部行字节的摘要>"}`；权限 0600，`O_EXCL` 创建，写完 `fsync` 并回读校验后才允许触库。建议路径：目标机 `/home/yangyang/ocap/snapshots/underground-<TS>.jsonl`（目录见画像 P7）。

**依赖**：MOD-104（`parse_integer_text`、`UNDERGROUND_BUILDING`）、`registry.models`（`RegistryUnit`、`RegistryOwner`、`RegistryPhone`、`build_specific_part`）、`core.audit`。读取"有效认证绑定数"需要 `apps.residency.models.Membership`：在函数内延迟导入（与 `registry/views.py:83` 既有做法相同），模块级不引入 `registry → residency` 依赖。

---

### MOD-110 清册导出文件生成（AUTH-01）

**文件**：`backend/apps/registry/exporting.py`（新建）、`backend/apps/registry/management/commands/export_registry_import_file.py`（新建）、`backend/apps/registry/import_template.py`（修改：只新增函数，`build_csv`/`build_xlsx` 不动，保证既有模板测试不受影响）。测试：`backend/tests/unit/test_registry_export_rows.py`、`backend/tests/integration/test_registry_export_cmd.py`。

```python
# registry/import_template.py（新增）
def build_data_xlsx(rows: list[list[str]]) -> bytes: ...     # IFC-298：单个工作表"清册导入"，表头=IMPORT_COLUMNS；A/B/C/D/H 列整列文本格式 "@"（沿用 _TEXT_COLUMNS）；无填写说明页
def build_data_csv(rows: list[list[str]]) -> bytes: ...      # UTF-8 带 BOM，表头=IMPORT_COLUMNS

# registry/exporting.py
@dataclass(frozen=True)
class ExportCounts:
    units: int                      # 专有部分记录数
    owners_named: int               # 有名业主数
    phones_distinct: int            # 手机号数（全清册去重）

@dataclass(frozen=True)
class ExportGaps:                   # 模板无法表达的记录（不含个人信息）
    units_without_named_owner: tuple[int, ...]    # 专有部分 id
    unnamed_owners: int                            # name 为 NULL 的业主数

@dataclass(frozen=True)
class ExportBundle:
    rows: list[list[str]]           # 每行 8 列，顺序 = IMPORT_COLUMNS
    db_counts: ExportCounts
    gaps: ExportGaps
    relocated_units: int            # 文件中楼栋被改为目标楼栋的专有部分数（库内尚未改的）
    relocated_owners: int
    relocated_phones: int
    conflicts: tuple["Conflict", ...]      # 来自 underground.plan_relocation

@dataclass(frozen=True)
class VerifyReport:
    file_counts: ExportCounts
    diff: dict[str, int]            # units/owners_named/phones_distinct 的 文件-库 差
    rows_failed: int                # plan_import 预检失败行数
    imported: int; updated: int; owners_created: int; phones_created: int
    expected_imported: int          # == relocated_units
    ok: bool

def build_export_bundle() -> ExportBundle: ...                                 # IFC-296：在 transaction.atomic() 内只读
def render_file(bundle: ExportBundle, file_name: str) -> bytes: ...            # 扩展名 .xlsx / .csv 决定格式；其他 → ValueError
def verify_export(content: bytes, file_name: str, bundle: ExportBundle) -> VerifyReport: ...   # read_rows + plan_import（只读）+ 计数比对
def write_export_file(path: Path, content: bytes, overwrite: bool = False) -> None: ...        # 原子写
```

#### IFC-296 导出行与自检规则
- **行生成**：遍历全部专有部分及其业主；每位**有名**业主一行：楼栋、单元、楼层、户号按库内原值；类型为 `unit_type` 的中文标签，`NULL` 输出空；面积按库内值格式化为字符串（`NULL` 输出空；两位小数原样，不改写）；业主姓名；手机号为该业主全部手机号以英文 `;` 连接（无手机号输出空）。被识别记录（ADR-102 同一识别函数 `underground.plan_relocation`）的楼栋输出 `UNDERGROUND_BUILDING`，其余行逐单元格等于库内值；已在目标楼栋下的记录原样输出（因此 AUTH-02 之前或之后导出，文件相同）。
- **冲突**：`plan_relocation(...).conflicts` 非空 → 不生成文件（改后两条记录会合并成同一专有部分）。
- **gaps**：存在 `units_without_named_owner` 或 `unnamed_owners > 0` → 默认不生成文件；`--allow-gaps` 时继续，文件不含这些记录，报告写出差异。
- **自检（`verify_export`）**：对 `render_file` 的字节执行 `read_rows` → `plan_import`（只读，`Deadline` 预算取 600 秒），要求：`rows_failed == 0`（AC-187-03）；`imported == expected_imported`（AUTH-02 之前 = 被改专有部分数；之后 = 0，AC-187-05）；`owners_created`、`phones_created` 与被改记录的业主/手机号数一致（之后为 0）；`updated == 0`；文件重算的 `units`、`owners_named`、`phones_distinct` 与库内计数的差为 0（REQ-NFUNC-032）；字节数 ≤ `MAX_FILE_BYTES`、数据行数 ≤ `MAX_DATA_ROWS`（`import_spec.py:13-14`）。
- 前导零/长数字：xlsx 为文本列、行内字符串原样写入；csv 不加任何转换；自检用 `read_rows` 回读，对"含前导零的楼层/户号/手机号样本"逐值比对（AC-187-04）。

#### IFC-297 命令 `python manage.py export_registry_import_file`（CLI）
```
export_registry_import_file --output PATH [--overwrite] [--allow-gaps]
```
- **鉴权**：同 IFC-295（目标机 shell；须用户另行授权 AUTH-01；子代理不得 ssh）。命令**全程只读**：不调用 `save/create/update/delete/bulk_*`，不写审计。
- **输入校验**：`--output` 必填，扩展名须为 `.xlsx` 或 `.csv`（否则 `CommandError`，退出码 1）；父目录须已存在；目标已存在且无 `--overwrite` → 退出码 3，不触库。
- **退出码**：0 成功；1 参数错误；2 存在冲突 / 存在模板无法表达的记录且未 `--allow-gaps` / 自检不通过 / 文件超限（均不落盘）；3 目标文件问题。失败时清除 `.part` 临时文件，已有同名文件保持原样（AC-187-08）。
- **落盘**：同目录 `<output>.part`，`os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600)` → 写入 → `fsync` → `os.replace(part, output)`。
- **输出（stdout）**：`db_units`、`db_owners_named`、`db_phones_distinct`、`file_units`、`file_owners_named`、`file_phones_distinct`、`diff_*`、`relocated_units`、`gaps_units`、`gaps_unnamed_owners`、`precheck_rows_failed`、`precheck_would_create_units`、`precheck_would_create_owners`、`precheck_would_create_phones`、`output_bytes`、`output=<路径>`；明细只含专有部分 id/标识。**不输出姓名、手机号**（C-55）。
- 建议文件名：`registry_import_underground_parking.xlsx`（取回后放仓库根，Q-SF-13=B；取回与是否提交不属于本设计）。

**依赖**：MOD-109（只调用纯函数 `plan_relocation`/`load_rows`，不调用 `apply_relocation`，两条命令互不触发）、`registry.importing`（`read_rows`、`plan_import`、`Deadline`）、`registry.import_spec`（`IMPORT_COLUMNS`、`UNIT_TYPE_LABELS`、`MAX_*`）、`registry.import_template`、`registry.models`、`openpyxl`（已有，`backend/requirements.txt`）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-173 | US-183、US-192 | MOD-104、MOD-105 |
| REQ-FUNC-174 | US-183、US-184（AC-184-03）、US-186 | MOD-104、MOD-105 |
| REQ-FUNC-175 | US-184 | MOD-104、MOD-105（服务端单点；客户端无改动，由契约/集成测试守护） |
| REQ-FUNC-176 | US-185 | MOD-105（地下车位作为普通楼栋值）、MOD-104（排序保留名）；数据由 MOD-109 修正 |
| REQ-FUNC-177 | US-186 | MOD-105（既有跳级机制）、MOD-104（负层排序） |
| REQ-FUNC-178 | US-187 | MOD-110（依赖 MOD-109 的识别规则） |
| REQ-FUNC-179 | US-188 | MOD-109 |
| REQ-FUNC-180 | US-189、US-191 | MOD-107、MOD-108 |
| REQ-FUNC-181 | US-190 | MOD-107（`q` 行为不变）、MOD-108 |
| REQ-FUNC-182 | US-189、US-190 | MOD-107 |
| REQ-FUNC-183 | US-191 | MOD-108 |
| REQ-FUNC-184 | US-192 | MOD-104、MOD-106 |
| REQ-NFUNC-032 | US-187、US-188 | MOD-109（计数核对、备份还原）、MOD-110（导出计数一致） |
| REQ-NFUNC-033 | US-189 | MOD-107（`IsAdmin`）、MOD-108 |
| C-51 / C-56 | US-187、US-188 | MOD-109、MOD-110（独立命令、默认只读、不进部署流程） |
| C-52 | US-188 | MOD-109（只改 `building`/`specific_part`，不触碰 `Membership`） |
| C-55 | US-187 | MOD-110（输出只写计数；文件落盘策略见 architecture_design OQ-03） |

REQ-FUNC-173~184 共 12 条均被覆盖，无空行。

## 依赖关系

```
MOD-105 → MOD-104（natural_key / sorted_values，IFC-285/287）
MOD-106 → MOD-104（unit_sort_key，IFC-286）
MOD-107 → MOD-104（sorted_values，IFC-292 排序）
MOD-108 → IFC-291、IFC-292（HTTP，经 MOD-107）
MOD-109 → MOD-104（parse_integer_text、UNDERGROUND_BUILDING，IFC-287）；→ registry.models；→ core.audit
MOD-110 → MOD-109（仅 plan_relocation / load_rows，IFC-294）；→ registry.importing（read_rows、plan_import）；→ registry.import_spec；→ registry.import_template
```

跨 app 导入方向：`identity.services`、`residency.housing → registry.ordering`；`registry.* → core`；`registry.underground → residency.models`（仅函数内延迟导入，同 `registry/views.py:83`）。`registry.ordering` 无项目内导入。**已检查：无循环依赖**（MOD-109 与 MOD-110 之间只有 110 → 109 单向，且不涉及命令入口互相调用）。

## 数据迁移

**无。** 不新增字段、表、索引，不修改 `registry/models.py`，不新增迁移文件，画像 P6 不触发。`makemigrations --check --dry-run` 应保持无漂移（画像 P4）。

**测试环境数据变更不通过迁移**：地下车位归属修正（AUTH-02）由 `relocate_underground_parking` 命令执行，原因见 ADR-101（迁移会在每次部署的 `migrate --noinput` 中自动执行，违反"另行授权、不得自动执行"）。该操作的可逆性与数据风险：

| 项 | 内容 |
|---|---|
| 变更内容 | 仅 `RegistryUnit.building`、`specific_part`（及 `updated_at`）三列，且仅限"类型为车位且楼层为负层且楼栋非地下车位"的记录；不改业主、手机号、认证绑定 |
| 可逆性 | 可逆：`--restore PATH [--apply]` 按备份原值写回，差异 0；备份在 apply 前强制生成并回读校验 |
| 数据风险 | (1) 标识冲突 → 写入前预演，冲突整批停止，库不变；(2) 负层写法未被识别（如 `B1`）→ 漏改，dry-run 列出全部车位楼层写法供核对（OQ-02）；(3) 执行期间并发导入 → 唯一约束报错使整个事务回滚；(4) 备份文件不含个人信息，仍按 0600 保存在目标机本地 |
| 执行前提 | 用户当轮明确授权（AUTH-02）；apply 须 `--backup`、`--expect-changes` |

## 受影响的运行单元 / 构建

| 运行单元（画像 P7） | 动作 |
|---|---|
| `ocap-backend`（gunicorn 127.0.0.1:9000，systemd） | 部署新代码并重启；**无迁移**；两条命令随代码一起到目标机但**不会被自动执行** |
| Web 前端（`npm run build -- --base=/ocap/`） | 重新构建并替换 `/home/yangyang/ocap/web`（`AdminRegistry.vue`、`api.js` 变化） |
| 小程序（uni-app） | 无源码改动，不需重新构建；顺序变化由后端接口生效 |
| nginx `ocap` 站点（8090） | 不变 |
| `ocap-run-due-jobs` timer | 不变 |
| 一次性操作（非常驻） | AUTH-02：目标机 `backend/` 下 `venv/bin/python manage.py relocate_underground_parking …`；AUTH-01：同目录 `export_registry_import_file …`；各自须用户当轮单独授权，均不属于部署步骤 |
| Freeark 服务、端口、目录、库 | 不触碰（画像 P7/P8） |
| 需要重新烧录的固件 / FPGA | 不适用 |

### 既有测试影响（GROUP_C 须复核，保持零新增失败）

| 测试 | 影响 |
|---|---|
| `backend/tests/integration/test_identity_display.py:118-125` | 期望 `/me` 房屋顺序 `[unit_a, unit_b]`（原按 `specific_part` 文本序）；新口径按数字自然顺序，须核对夹具楼栋/户号后同步断言 |
| `backend/tests/remote/remote_cases.py:77-83` | 远程用例已要求 `/me/housing` 与 `/me` 顺序一致；本批使其成立（DEF-A 排序部分）；文案"户主"部分与 DEF-B 不在本批 |
| `backend/tests/integration/test_registry_import_api.py`、`test_residency_api.py:15-21`、`tests/e2e/test_registry_import_journeys.py:76-92`、`test_frontend_contract.py:436-450` | `/units/options` 的字段与结构不变，仅顺序变；如有断言依赖旧文本序须同步 |
| `backend/tests/integration/test_frontend_contract.py:30-97` | 新增路径需能 `resolve`，且仅 `IsAdmin` |
| `frontend/tests/*.spec.js` | `git grep AdminRegistry\|registryUnits -- frontend/tests` 无结果，现有前端测试不受影响；新增 `registry_filters.spec.js` |

### 测试规划（路径遵守画像 P3；全部用 SQLite 测试库与合成数据，不连接测试机数据库）

| 文件 | 内容（关联 AC） |
|---|---|
| `backend/tests/unit/test_registry_ordering.py` | `parse_integer_text`/`natural_key`：1/2/10/11、101/902/1001、A2/A10/5、负二/负一/-1/负1/1/2、地下车位排最后、空值、带后缀 "1栋"（AC-183-01~06、AC-184-03） |
| `backend/tests/integration/test_registry_sort_options.py` | `/units/options` 四级顺序、地下车位跳单元、无地下车位不出现（AC-183、185、186） |
| `backend/tests/integration/test_unit_sort_filters_me.py` | `/me` 与 `/me/housing` 同序、认证时间相反、刷新 5 次不变、户主+同住人仍两行、游客空（AC-192-01~04） |
| `backend/tests/integration/test_admin_registry_filters.py` | 各过滤器精确/包含、组合、`q` 组合、空结果、清空、非管理员 403/401、非法参数 400、`filter-options` 顺序与鉴权（AC-189、190） |
| `backend/tests/unit/test_underground_rules.py`、`backend/tests/integration/test_underground_relocation_cmd.py` | 识别规则；dry-run 零写（`CaptureQueriesContext`）；冲突（标识、四元组）整批停止；备份内容无姓名手机号；apply 前后计数/绑定/未受影响指纹相等；重复执行 0 改动；`--restore` 差异 0；缺参数/路径已存在的退出码（AC-188-01~06） |
| `backend/tests/unit/test_registry_export_rows.py`、`backend/tests/integration/test_registry_export_cmd.py` | 行生成（含前导零、多手机号、多业主）；被改行楼栋；计数相等；预检通过；AUTH-02 前后文件一致；零写；gaps/冲突退出码；失败不落盘、无残留 `.part`（AC-187-01~08） |
| `frontend/tests/registry_filters.spec.js` | 六个过滤器参数映射、重置、占位文字不含 "select"（不区分大小写）、`empty-text` 中文、无"楼层"过滤（AC-189-09、191） |
| 前后端契约 | `backend/tests/integration/test_frontend_contract.py` 自动覆盖 `registryFilterOptions`；E2E critical path 须覆盖"后台过滤请求参数 → 后端过滤结果"（画像 P5） |

## 领域与外部依赖出处

画像 P11 有条目，但本批**不新增、不改变对任何闭源 / 外部 API 的调用**（微信、阿里云短信、邮件均不涉及）。下表登记接口契约引用的现有代码事实。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-285~287、IFC-288 | 现有楼栋/单元文本序、户号 `order_by("room")`、楼层 `_floor_sort_key` 只认 "负/-"+阿拉伯数字 | [CODE: backend/apps/registry/services.py:9-19,51-59,68] |
| IFC-289 | `/me` 按 `(specific_part, unit_id)` 排序，按专有部分去重取最高角色 | [CODE: backend/apps/identity/services.py:42-48] |
| IFC-290 | `/me/housing` 按 `certified_at, id` 取 memberships，`identity_view` 取最高身份与入参顺序无关 | [CODE: backend/apps/residency/housing.py:41]、[CODE: backend/apps/accounts/directory.py:20-33] |
| IFC-291 | `AdminUnitListView` 现有 `q`（≤64）、`unit_type` 参数与 `IsAdmin`；分页上限 100 | [CODE: backend/apps/registry/views.py:74-90]、[CODE: backend/apps/core/serializers.py:4-13] |
| IFC-293 | `registryUnits` 现为 `adminHttp.get('/admin/registry/units', { params })`；契约测试解析规则 | [CODE: frontend/src/shared/api.js:141]、[CODE: backend/tests/integration/test_frontend_contract.py:30-97] |
| IFC-294 | `specific_part` 由 `build_specific_part` 生成，非纯数字值（如"地下车位"）不补后缀；`specific_part` 唯一、四元组唯一 | [CODE: backend/apps/registry/models.py:23-31,47-56,65,71-74] |
| IFC-294 | 审计动作 `REGISTRY_UNIT_CHANGED` 已在白名单；`AuditActor("SYSTEM", None, …)` 的既有用法 | [CODE: backend/apps/core/audit.py:11-15]、[CODE: backend/apps/claims/services.py:25] |
| IFC-296/297 | 导入模板 8 列、文本列、`read_rows`/`plan_import` 只读预检、手机号 `;` 分隔解析、行数/体积上限 | [CODE: backend/apps/registry/import_spec.py:13-14,27-36]、[CODE: backend/apps/registry/import_template.py:17,32-51]、[CODE: backend/apps/registry/importing.py:236,342-392,395] |
| IFC-295/297 | management command 先例（只读预览、`key=value` 输出） | [CODE: backend/apps/registry/management/commands/registry_specific_part_preview.py] |
| ADR-101 | 部署流程每次执行 `manage.py migrate --noinput`；测试环境 `MIGRATION_MODULES` 置空 | [CODE: .claude/skills/ocap-deploy/SKILL.md:149]、画像 P4 |
