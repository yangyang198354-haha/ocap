<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-10T22:02:14+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.2.0 DRAFT)</file>
    <file>../ocap/architecture/module_design.md (基线，至 MOD-022 / IFC-141)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：业主清册导入增强（INCREMENTAL）

> 编号接续全仓最大值：MOD-030 起、IFC-152 起（ADR 见 architecture_design.md，ADR-034~044）。
> 模块 = 本次新建/修改的代码单元，路径相对仓库根 `/root/myproject/ocap`。后端路径前缀 `backend/apps/`。
> 0.2.0：已写入用户对 Q1~Q6 的答复（architecture_design"已答复问题"）；Q1 的落地口径（无名业主 + 吸收规则）为 PM 口径、待用户确认，不阻断开发。
> 所有 HTTP 路径省略前缀 `/api/v1`。错误体统一为 `{code, message, details?}`（`backend/apps/core/errors.py:25-31`）。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-030 | 清册数据模型与迁移 | **修改** `registry/models.py`、`registry/serializers.py`；**新建** `registry/migrations/0002_owner_type_area.py`、`0003_backfill_legacy_owners.py`、`0004_phone_owner_required.py` | 专有部分类型/面积/可空层级、业主表、手机号归属业主、既有数据回填 | REQ-FUNC-087/088/089/090/091/094/098；NFUNC-011；US-095~098、101 | core |
| MOD-031 | 导入规格与导入引擎 | **新建** `registry/import_spec.py`、`registry/importing.py`、`registry/import_template.py` | 列/取值/限制常量（单一来源）；文件解析；计划（校验+合并）；批量应用；模板生成 | REQ-FUNC-083/084/085/086/092/093；NFUNC-013/014/015；US-092~094、096、099、100 | MOD-030 |
| MOD-032 | 清册管理端 API | **修改** `registry/views.py`、`registry/urls.py` | 列表/新增/修改专有部分、owners 全量替换、导入、模板与说明下载；审计 | REQ-FUNC-083~085/087~090/093/095；NFUNC-011/014/015；US-092~097、100 | MOD-030、MOD-031、core |
| MOD-033 | 清册查询服务 | **修改** `registry/services.py` | 用户端逐级选项（跳空层级、类型面积）；按手机号查专有部分；既有 `phone_registered/get_unit` 保持 | REQ-FUNC-091/097；NFUNC-012；US-098、103 | MOD-030 |
| MOD-034 | 自动绑定服务 | **新建** `residency/auto_bind.py`；**修改** `residency/services.py`（`certify_owner` 增加 `origin` 参数） | 依据已验证手机号把用户认证为清册中命中的各专有部分的产权业主 | REQ-FUNC-096；NFUNC-012/014；C-25/C-26；US-102 | MOD-033、core |
| MOD-035 | 自动绑定触发点 | **修改** `accounts/views.py`（`RegisterView`）、`identity/views.py`（`PhoneBindView`） | 注册/首次绑定手机号成功后调用自动绑定，响应加 `auto_bound` | REQ-FUNC-096；US-102 | MOD-034 |
| MOD-036 | Web 管理端清册页 | **修改** `frontend/src/admin/AdminRegistry.vue`、`frontend/src/shared/api.js`；**新建** `frontend/src/admin/RegistryImportDialog.vue`、`frontend/src/admin/registryImport.js` | 说明、模板下载、预检→确认→结果、处理中/超时提示、错误清单下载、类型/面积/业主编辑与筛选 | REQ-FUNC-083~085/088~090/093/095/098；NFUNC-015；US-092~101 | IFC-153~158 |
| MOD-037 | Web 用户端 | **修改** `frontend/src/portal/Units.vue`、`Register.vue`、`Me.vue` | 动态跳级选择、显示类型面积、无手机号指引、自动绑定提示 | REQ-FUNC-091/096/097/098；US-098、102~104 | IFC-152、160、161 |
| MOD-038 | 小程序 | **修改** `miniprogram/pages/units/index.vue`、`miniprogram/pages/phone/index.vue`、`miniprogram/utils/api.js`（注释） | 同 MOD-037 的小程序对应页面（小程序无注册页） | REQ-FUNC-091/096/097；US-098、102、103 | IFC-152、161 |

## 模块详情

### MOD-030 清册数据模型与迁移

**文件**：`backend/apps/registry/models.py`（修改）、`serializers.py`（修改）、`migrations/0002~0004`（新建，手写）。

**模型契约（字段定义，非实现）**：

```python
# registry/models.py
UNIT_TYPE_CHOICES: list[tuple[str, str]]   # [("RESIDENCE","住宅"),("APARTMENT","公寓"),("SHOP","商铺"),("PARKING","车位"),("OTHER","其他")]

def build_specific_part(building: str, unit_no: str, floor: str, room: str) -> str: ...
    # 只拼非空段，以 "-" 连接；已有四级完整记录结果与旧规则相同（AC-098-05）

class RegistryUnit(models.Model):
    building: CharField(max_length=32)
    unit_no: CharField(max_length=32, blank=True, default="")      # 空层级存 ""，不存 NULL（ADR-035）
    floor: CharField(max_length=32, blank=True, default="")        # 16 -> 32
    room: CharField(max_length=32)                                  # 16 -> 32
    specific_part: CharField(max_length=140, unique=True)           # 100 -> 140
    unit_type: CharField(max_length=10, choices=UNIT_TYPE_CHOICES, null=True, blank=True)   # NULL = 未登记
    area: DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)              # 平方米；NULL = 未登记
    created_at / updated_at                                         # 不变
    # Meta.constraints 保留 uniq_registry_unit(building, unit_no, floor, room)；ordering 不变
    # save() 调用 build_specific_part()

class RegistryOwner(models.Model):                                  # 新建
    unit: ForeignKey(RegistryUnit, CASCADE, related_name="owners")
    name: CharField(max_length=64, null=True, blank=True)           # NULL 仅用于迁移回填的既有记录（ADR-037）；新增/导入/单条编辑一律非空（REQ-FUNC-090）
    created_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
    # Meta.constraints: UniqueConstraint(fields=["unit","name"], name="uniq_registry_owner_name")

class RegistryPhone(models.Model):
    unit: ForeignKey(RegistryUnit, CASCADE, related_name="phones")  # 保留；须等于 owner.unit
    owner: ForeignKey(RegistryOwner, CASCADE, related_name="phones")   # 新增；0002 为 null=True，0004 收紧为非空
    phone: CharField(max_length=11)
    # 保留 uniq_registry_phone(unit, phone)、Index(phone)
```

**序列化器契约**（`registry/serializers.py`）：

```python
class RegistryOwnerSerializer(serializers.Serializer):
    id: int
    name: str | None
    phones: list[str]            # 管理员完整手机号（PlainPhoneField，仅 /admin/registry/** 使用，core/masking.py:29-30）

class RegistryUnitAdminSerializer(serializers.ModelSerializer):
    fields = ["id","specific_part","building","unit_no","floor","room",
              "unit_type","unit_type_label","area","owners"]
    # unit_type_label: str | None；area: "89.50" | None（DRF 默认 Decimal -> 字符串）
    # 移除旧的扁平 phones 字段
```

**迁移（详见"数据迁移"节）**。

**依赖**：Django、`apps.core`。**外部依赖**：无。

---

### MOD-031 导入规格与导入引擎

**文件**：`registry/import_spec.py`、`registry/importing.py`、`registry/import_template.py`（均新建）。测试建议位置（画像 P3）：`backend/tests/unit/test_registry_import_engine.py`、`backend/tests/integration/test_registry_import_api.py`。

**1. `import_spec.py`——单一来源**

```python
MAX_FILE_BYTES: int = 5 * 1024 * 1024
MAX_DATA_ROWS: int = 20000
TIME_BUDGET_SECONDS: int          # 取 settings.REGISTRY_IMPORT_TIME_BUDGET_SECONDS，缺省 60（测试可 override_settings）
MAX_AREA: Decimal = Decimal("99999999.99")
COLUMN_BUILDING, COLUMN_UNIT, COLUMN_FLOOR, COLUMN_ROOM, COLUMN_TYPE, COLUMN_AREA, COLUMN_OWNER, COLUMN_PHONE: str
    # "楼栋","单元","楼层","户号","专有部分类型","专有部分面积（平方米）","业主姓名","手机号"
IMPORT_COLUMNS: list[str]                         # 上述 8 列，顺序即模板顺序
UNIT_TYPE_LABELS: dict[str, str]                  # 中文标签 -> 代码；反向映射同源于 UNIT_TYPE_CHOICES

@dataclass(frozen=True)
class ColumnSpec: name: str; required: str; allowed: str; example: str   # required 为展示文案，如 "必填"/"选填"/"仅车位必填"
def column_specs() -> list[ColumnSpec]: ...
def spec_payload() -> dict: ...                   # IFC-159 的响应体
def validate_unit_fields(*, building: str, unit_no: str, floor: str, room: str) -> str | None: ...
    # 返回首个错误文案或 None；单条接口与导入共用
def parse_area(text: str) -> tuple[Decimal | None, str | None]: ...      # (值, 错误文案)
def parse_unit_type(text: str) -> tuple[str | None, str | None]: ...     # (代码, 错误文案)
```

校验规则与文案（括号内为需求依据；**同一行出现多个问题时只报首个，顺序：楼栋 → 户号 → 单元/楼层长度与 `-` → 类型 → 面积 → 姓名 → 手机号**）：

| 字段 | 规则 | 文案（`reason`） | 依据 |
|---|---|---|---|
| 楼栋 | 必填、≤32、不含 `-` | "缺少楼栋" / "楼栋过长（最多 32 字符）" / "楼栋不得含“-”" | AC-098-04 |
| 户号 | 必填、≤32（可含 `-`） | "缺少户号" / "户号过长（最多 32 字符）" | AC-098-04、AC-098-01/06 |
| 单元、楼层 | 可空、≤32、不含 `-` | "单元过长…" / "楼层过长…" / "单元不得含“-”" 等 | AC-098-04 |
| 专有部分类型 | 新专有部分的行必填；取值只能是 住宅/公寓/商铺/车位/其他（去首尾空格，中文标签原样） | "专有部分类型为空" / "专有部分类型不在允许范围内（住宅、公寓、商铺、车位、其他）" | AC-096-02/03 |
| 面积 | 空则按类型规则；非空须匹配 `^\d+(\.\d+)?$` 且 > 0、小数位 ≤ 2、≤ MAX_AREA | "专有部分面积须为大于 0 的数值" / "专有部分面积最多 2 位小数" / "专有部分面积超出可登记范围" | AC-096-04 |
| 车位面积 | 最终类型为车位而面积为空 | "车位的专有部分面积不能为空" | AC-096-07、A-1 |
| 业主姓名 | 必填，去首尾空格后 1~64 字符 | "业主姓名不能为空" / "业主姓名过长（最多 64 字符）" | AC-094-09、REQ-FUNC-090 |
| 手机号 | 可空；按英文 `;` 拆分、去空格、去重；每个须匹配 `PHONE_RE`（`core/masking.py:6`） | "手机号格式不正确" | AC-100-04、AC-094-03 |
| 同专有部分类型冲突 | 同一专有部分各合法行非空类型不唯一 | "同一专有部分的类型不一致" | AC-096-05 |
| 同专有部分面积冲突 | 各合法行非空面积（按数值比较）不唯一 → 这些行全部失败 | "同一专有部分的面积不一致" | Q2=A |
| 手机号占用 | 手机号已登记给该专有部分内另一位姓名不同的业主 | "手机号已登记给同一专有部分的另一位业主" | AC-099-07、C-24 |
| 标识冲突 | 标识命中已有记录但四级取值不同 | "专有部分标识与已有记录冲突" | ADR-035 |

**2. `importing.py`——解析、计划、应用**

```python
@dataclass(frozen=True)
class RawRow: row_no: int; cells: dict[str, str]           # row_no 为文件物理行号（表头=1）；cells 键为 IMPORT_COLUMNS

class ImportFileError(ApiError): ...                       # code 见 IFC-157
class ImportTimeout(ApiError): ...                         # 504 IMPORT_TIMEOUT
class ImportConflict(ApiError): ...                        # 409 IMPORT_CONFLICT

class Deadline:
    def __init__(self, seconds: float, started: float | None = None) -> None: ...
    def check(self, stage: str) -> None: ...               # 超出抛 ImportTimeout(details={"limit_seconds", "stage"})

def read_rows(name: str, raw: bytes, deadline: Deadline) -> list[RawRow]: ...
    # name 决定 csv/xlsx；校验表头（缺列抛 IMPORT_COLUMNS_MISSING）；
    # 数据行 > MAX_DATA_ROWS 抛 IMPORT_FILE_INVALID "文件行数超过 20000"；全空行跳过；xlsx 单元格经 cell_text()

def cell_text(value: object) -> str: ...                   # ADR-039 第 2 点

@dataclass
class RowError: row: int; field: str | None; reason: str

@dataclass
class PlannedPhoneMove: phone_id: int; to_owner_ref: str     # to_owner_ref 为已有业主 id 或本次计划内业主键

@dataclass
class UnitChange: specific_part: str; fields: list[str]    # 取值 "unit_type" / "area"

@dataclass
class ImportPlan:
    rows_total: int
    errors: list[RowError]                                 # 按 row 升序
    units_to_create: list["PlannedUnit"]
    units_to_update: list["PlannedUnitUpdate"]
    owners_to_create: list["PlannedOwner"]
    phones_to_create: list["PlannedPhone"]
    owner_names_to_fill: list["PlannedNameFill"]           # 无名业主被吸收时写入姓名（ADR-037）
    phone_moves: list["PlannedPhoneMove"]                  # 被吸收的其他无名业主名下手机号并入目标业主
    owners_to_delete: list[int]                            # 吸收后已无手机号的无名业主 id
    changes: list[UnitChange]
    def summary(self) -> dict: ...                         # IFC-157 响应体中除 elapsed_ms / dry_run 外的字段

def plan_import(rows: list[RawRow], deadline: Deadline) -> ImportPlan: ...
    # 纯计算 + 只读 DB（分批读已有专有部分、业主、手机号）。不写库。
    # 预检与正式导入都调用它；两者的差别只在是否调用 apply_plan。

def apply_plan(plan: ImportPlan, deadline: Deadline) -> None: ...
    # 单个 transaction.atomic()；批量写入顺序见 architecture_design 性能方案；
    # 每个批次后 deadline.check("apply")；IntegrityError -> ImportConflict；任何异常都使事务回滚
```

`plan_import` 步骤（顺序即规则优先级）：
1. 行级规范化与校验（见上表），失败行记 `RowError`，不进入后续步骤。
2. 以 `build_specific_part()` 的 `casefold()` 为键分组，分批读取已有专有部分及其业主、手机号。
3. 专有部分级：类型冲突与面积冲突（Q2=A）→ 该组全部合法行转为失败；标识冲突 → 该行失败；车位最终面积检查（A-1）。
4. 按文件顺序逐行处理业主：以去首尾空格后的姓名（`casefold()`，A-3）在该专有部分的"已有 + 本次已计划"**有名**业主中匹配，得到目标业主：
   - 匹配到有名业主 N → 目标 = N；否则若行内某手机号被本专有部分的**无名业主**持有（迁移遗留，ADR-037）→ 目标 = 其中第一位（给它补上姓名，记 `owner_names_to_fill`）；否则新建业主。
   - 对行内每个手机号：已属目标 → 跳过；被其他**无名业主**持有 → 并入目标（`phone_moves`），该无名业主若因此无手机号则进 `owners_to_delete`；被其他**有名业主**持有 → **整行失败**"手机号已登记给同一专有部分的另一位业主"；无人持有 → 新建手机号。
   - 先对整行做全部检查、再登记计划，保证行级原子（失败行任何内容都不应用）。
   - 无名业主不会被姓名匹配到；没有手机号命中无名业主的行不影响它们（统一上传文件中未列出的无名业主保持原状，不删除）。
5. 统计：专有部分仅在至少有一行最终成功时计为新增/更新；`changes` 记录已有专有部分被改的 `unit_type`/`area`（文件非空值与库值不同才算改）；超过 1000 条截断并置 `changes_truncated`。

`apply_plan` 约束：`bulk_create` 之后按 `specific_part` / `(unit_id,name)` 回查主键（MySQL 不回填）；`bulk_update` 显式写 `updated_at`；吸收相关写入顺序：补名（`bulk_update` owner.name）→ 手机号改属（`bulk_update` phone.owner）→ 删除已空的无名业主 → 新建业主/手机号，避免撞 `(unit,name)` 与 `(unit,phone)` 约束；`RegistryPhone.unit` 与 `owner.unit` 必须一致。

**3. `import_template.py`**

```python
def build_template_xlsx() -> bytes: ...
    # 工作表1 "清册导入"：表头 + 示例行；8 列均设文本格式 "@"，类型列加下拉数据验证
    # 工作表2 "填写说明"：由 column_specs() 与限制常量生成，首行提示"请先删除示例行再填写"
def build_template_csv() -> bytes: ...                     # UTF-8 带 BOM，表头 + 示例行
SAMPLE_ROWS: list[list[str]]                                # 3 行同一专有部分（含 1 位无手机号业主）+ 1 个车位（单元楼层空）；每行重复类型与面积
```

**依赖**：MOD-030；`openpyxl`（已有，`backend/requirements.txt:5`）、标准库 `csv`、`decimal`、`time`。**外部依赖**：无闭源 API。

---

### MOD-032 清册管理端 API

**文件**：`registry/views.py`（修改）、`registry/urls.py`（修改）。`AdminUnitPhonesView` 及其路由**删除**（A-6）。

**新增/变更路由**：

```python
urlpatterns = [
    path("units/options", UnitOptionsView.as_view()),                              # IFC-152（修改）
    path("admin/registry/units", AdminUnitListView.as_view()),                     # IFC-153 GET / IFC-154 POST
    path("admin/registry/units/<int:unit_id>", AdminUnitDetailView.as_view()),     # IFC-155 PATCH；DELETE 不变
    path("admin/registry/units/<int:unit_id>/owners", AdminUnitOwnersView.as_view()),   # IFC-156（新）
    path("admin/registry/import", AdminRegistryImportView.as_view()),              # IFC-157（修改）
    path("admin/registry/import/template", AdminRegistryTemplateView.as_view()),   # IFC-158（新）
    path("admin/registry/import/spec", AdminRegistrySpecView.as_view()),           # IFC-159（新）
]
```

#### IFC-153 `GET /admin/registry/units`（修改）
- 鉴权：`IsAdmin`（沿用 `core/permissions.py:19-24`；非管理员 403 `FORBIDDEN`，未登录 401 `UNAUTHORIZED`）。
- 查询：`page: int = 1`、`page_size: int = 20（1~100，沿用 core/serializers.py:6-9）`、`q: str ≤64`（`specific_part` 包含，沿用）、`unit_type: str`，取值为五个代码之一或 `UNSET`（未登记）；其他取值 → `400 INVALID_QUERY`。
- 响应 200：`{count: int, page: int, page_size: int, results: [RegistryUnitAdminSerializer]}`，`owners` 内含姓名与完整手机号（REQ-FUNC-095）；视图须 `prefetch_related("owners__phones")`，避免 N+1。
- 排序：`id`（沿用）。

#### IFC-154 `POST /admin/registry/units`（修改）
- 鉴权：`IsAdmin`。
- 请求：`{building: str, unit_no?: str, floor?: str, room: str, unit_type: "RESIDENCE"|"APARTMENT"|"SHOP"|"PARKING"|"OTHER", area?: str | number | null}`。
- 校验：层级字段经 `validate_unit_fields`；`unit_type` 缺失或非法 → `400 INVALID_VALUE`"请选择专有部分类型"；`area` 经 `parse_area`（拒绝布尔、非数值、≤0、>2 位小数）→ `400 INVALID_VALUE`"专有部分面积格式不正确"；类型为车位而无面积 → `400 INVALID_VALUE`"车位须填写专有部分面积"（AC-097-07）；类型为住宅等而无面积允许（AC-097-08）。
- 响应：`201` 单个 `RegistryUnitAdminSerializer`；标识已存在 → `409 UNIT_EXISTS`"专有部分已存在"（修复现有重复新增 500 的隐患：当前 `views.py:54` 直接 `create`，撞唯一约束抛 `IntegrityError`）。
- 审计：`REGISTRY_UNIT_CHANGED`，`detail={"change": "create"}`（沿用 `views.py:212-215`）。

#### IFC-155 `PATCH /admin/registry/units/<unit_id>`（修改）
- 鉴权：`IsAdmin`。可含字段：`building, unit_no, floor, room, unit_type, area`（均可选）。
- 校验：同 IFC-154；`unit_type` 出现时必须是合法代码（不可置空）；`area` 出现时可为 `null`（清除），但**合并后的**最终类型为车位时最终面积不得为空；仅修改业主、不带类型字段的请求不受影响（AC-101-04）；改动层级字段导致标识与其他记录重复 → `409 UNIT_EXISTS`；专有部分不存在 → `404 NOT_FOUND`。
- 响应 200：序列化器；审计 `change="update"`。已认证身份不受影响（AC-097-06，沿用不触碰 `Membership`）。
- DELETE 行为不变（`views.py:79-89`），级联删除业主与手机号。

#### IFC-156 `PUT /admin/registry/units/<unit_id>/owners`（新，取代 `/phones`）
- 鉴权：`IsAdmin`。
- 请求：`{owners: [{id?: int, name?: str | null, phones: [str]}]}`——对该专有部分的业主做**全量替换**：
  - 请求中出现的 `id` 必须属于本专有部分，否则 `400 INVALID_VALUE`；缺 `id` 为新建；库中存在而请求未出现的业主被删除（其手机号随之删除）。
  - `name`：去首尾空格后须 1~64 字符，否则 `400 INVALID_VALUE`"业主姓名不能为空"（AC-095-07）/ 过长；仅当该条带 `id` 且指向库中姓名为 `NULL` 的业主（迁移遗留）时，`name` 可省略或为 `null`（保留未登记姓名，使仅改其他信息的编辑不被迫补名）；新建业主一律要求姓名。
  - 姓名（`casefold()`）在请求内重复 → `400 OWNER_NAME_DUPLICATE`，`details={"index": int}`。
  - `phones`：每项须匹配 `PHONE_RE`，否则 `400 INVALID_VALUE`"手机号格式不正确"（AC-095-03）；单个业主内去重；同一手机号出现在两位不同业主 → `400 PHONE_DUPLICATE_IN_UNIT`"手机号已登记给同一专有部分的另一位业主"，`details={"index": int}`。
  - **不设业主数量上限**（REQ-FUNC-087）；请求体大小受 Django 默认 `DATA_UPLOAD_MAX_MEMORY_SIZE`（2.5 MB）限制，足够数千位业主。
- 事务：`transaction.atomic()` + 锁该专有部分行；改名对换不得因 `(unit,name)` 唯一约束失败（实现提示：先将待改名者置 `NULL` 再赋值）；校验失败时原有业主不变（AC-095-03、-07）。
- 响应 200：该专有部分的序列化器；`404 NOT_FOUND` 专有部分不存在。
- 审计：`REGISTRY_UNIT_CHANGED`，`detail={"change": "owners", "owner_count": int}`（不含姓名、手机号）。已认证身份不撤销（C-22、AC-095-05），代码上不触碰 `Membership`。

#### IFC-157 `POST /admin/registry/import`（修改）
- 鉴权：`IsAdmin`；`parser_classes = [MultiPartParser, FormParser]`（沿用）。
- 请求：multipart 字段 `file`（必填）；`dry_run` 取 query（`1`/`true`）或表单字段（沿用 `views.py:143-145`）。
- 输入校验与错误（按此顺序）：

| 条件 | 响应 |
|---|---|
| 缺 `file` | `400 FILE_REQUIRED`"缺少文件" |
| `file.size > 5 MB` | `413 FILE_TOO_LARGE`"文件超过 5 MB" |
| 扩展名（不区分大小写）不是 `.csv`/`.xlsx` | `400 IMPORT_FILE_INVALID`"仅支持 xlsx 或 csv" |
| 解析失败 | `400 IMPORT_FILE_INVALID`"文件无法解析" |
| 数据行 > 20000 | `400 IMPORT_FILE_INVALID`"文件行数超过 20000" |
| 缺列 | `400 IMPORT_COLUMNS_MISSING`，`message="缺少列：…，请使用新模板"`，`details={"columns": [缺的列名]}`（旧 5 列文件缺 3 列，AC-093-06） |
| 超过软期限 | `504 IMPORT_TIMEOUT`，`details={"limit_seconds": 60, "stage": "parse"|"plan"|"apply"}` |
| 写入时撞唯一约束（并发导入） | `409 IMPORT_CONFLICT`"有其他导入正在进行，请稍后重试" |
| `openpyxl` 缺失 | `503 IMPORT_UNAVAILABLE`（沿用） |

  所有拒绝类错误发生时清册不变（AC-092-03/04/05、AC-093-06）。
- 响应 200：

```python
class ImportResult(TypedDict):
    dry_run: bool
    rows_total: int          # 非空数据行数
    rows_ok: int
    rows_failed: int
    imported: int            # 新增专有部分数（沿用旧字段名；预检为"将新增"）
    updated: int             # 更新（已存在）专有部分数
    owners_created: int
    phones_created: int
    failed: int              # 等于 rows_failed（沿用旧字段名）
    errors: list[dict]       # {"row": int, "field": str | None, "reason": str}，按 row 升序，全量
    changes: list[dict]      # {"specific_part": str, "fields": ["unit_type"|"area", ...]}，最多 1000
    changes_truncated: bool
    owners_named: int        # 无名业主被补名的数量（迁移遗留业主被统一上传补名）
    elapsed_ms: int
```
  `dry_run=True` 时不写库，数字为"将会"的结果，且与同一份文件随后正式导入的结果一致（AC-100-03）。
- 审计：`REGISTRY_IMPORTED`，`detail={imported, updated, failed, rows_total, owners_created, phones_created, dry_run}`，不含姓名、手机号、文件名（AC-094-06、REQ-NFUNC-014）。超时/冲突不记成功审计。
- 性能：REQ-NFUNC-015，见 architecture_design 对应节。

#### IFC-158 `GET /admin/registry/import/template`（新）
- 鉴权：`IsAdmin`（AC-093-05）。
- 查询：`file_type: "xlsx" | "csv" = "xlsx"`；其他值 → `400 INVALID_QUERY`。**不得使用 `format` 作参数名**（DRF 渲染器后缀冲突）。
- 响应 200：二进制附件，用 `HttpResponse`（绕过 DRF JSON 渲染器）。xlsx 的 `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`；csv 为 `text/csv; charset=utf-8`。`Content-Disposition: attachment; filename="registry_import_template.xlsx"`（或 `.csv`）。

#### IFC-159 `GET /admin/registry/import/spec`（新）
- 鉴权：`IsAdmin`。无参数。
- 响应 200：

```python
class ImportSpec(TypedDict):
    file_types: list[str]                  # [".csv", ".xlsx"]
    max_file_mb: int                       # 5
    max_rows: int                          # 20000
    excel_sheet_note: str                  # "仅读取第一个工作表"
    time_budget_seconds: int               # 60
    unit_types: list[dict]                 # {"code": str, "label": str}
    columns: list[dict]                    # {"name": str, "required": str, "allowed": str, "example": str}
    notes: list[str]                       # 多位业主怎么填、同名视为同一业主、无手机号业主只能走申诉、请使用 UTF-8 CSV 等
```

**依赖**：MOD-030、MOD-031；`apps.core`（`AuditService`、`ApiError`、`IsAdmin`、`page_response`、`PHONE_RE`）。

---

### MOD-033 清册查询服务

**文件**：`registry/services.py`（修改）；`options()` 的视图在 `registry/views.py:UnitOptionsView`（MOD-032 文件，职责归本模块）。

```python
class RegistryService:
    @staticmethod
    def phone_registered(unit_id: int, phone: str) -> bool: ...        # 不变（registry/services.py:7-8）
    @staticmethod
    def get_unit(unit_id: int) -> RegistryUnit | None: ...             # 不变
    @staticmethod
    def units_by_phone(phone: str) -> list[RegistryUnit]: ...          # IFC-162（新）：该手机号登记的全部专有部分，按 id 升序去重
    @staticmethod
    def options(*, building: str | None = None, unit_no: str | None = None,
                floor: str | None = None) -> dict: ...                 # IFC-152
```

#### IFC-152 `GET /units/options`（修改，用户端）
- 鉴权：`IsMember`（沿用 `registry/views.py:28`）；未登录 `401`（AC-103-04）。
- 查询：`building?: str`、`unit_no?: str`、`floor?: str`，各 ≤32 字符，超长 → `400 INVALID_QUERY`。**参数"存在但为空串"表示"该层选了'无'"**（旧实现用真值判断，`views.py:34-37`，须改为 `is not None`）。参数只能自上而下出现：有 `unit_no` 必须有 `building`、有 `floor` 必须有 `unit_no`，否则 `400 INVALID_QUERY`"缺少上级参数"（沿用）。
- 响应 200：

```python
class OptionsResponse(TypedDict):
    level: Literal["building", "unit_no", "floor", "room"]    # 本次要选择的层级
    skipped: list[Literal["unit_no", "floor"]]                 # 本次自动跳过的层级（候选在该层全为空）；客户端后续请求须以空串回传
    has_empty: bool                                            # level 为 unit_no/floor 时，同级另有"该层为空"的专有部分
    options: list[dict]
    # level != "room":  {"value": str}                            （只含非空值，字典序）
    # level == "room":  {"value": str, "unit_id": int, "unit_type": str | None,
    #                    "unit_type_label": str | None, "area": str | None, "label": str}
    #                   label 例 "301（住宅 89.50 ㎡）"；仅有其一时只显示其一；都无时只显示户号；不得出现 "null"/空括号/姓名/手机号
```
- 算法：已给出的参数筛选候选集；依次对 `unit_no`、`floor` 中**尚未给出**的第一个层级取候选值集合：若集合恰为 `{""}` → 加入 `skipped`、继续下一层；若同时含 `""` 与非空值 → 返回非空值并 `has_empty=true`；否则返回该层。两层都解决后返回 `room` 列表（按 `room` 排序）。
- 客户端约定：`has_empty=true` 时追加一项"无单元/无楼层"，选中则下一次请求带该层空串（AC-098-03）；`skipped` 的层级后续请求以空串回传。
- 隐私：响应只含房屋属性，不含姓名、手机号（REQ-NFUNC-012、AC-103-03）。

**依赖**：MOD-030。

---

### MOD-034 自动绑定服务

**文件**：`residency/auto_bind.py`（新建）、`residency/services.py`（修改）。测试建议：`backend/tests/integration/test_registry_autobind.py`。

```python
# residency/auto_bind.py
@dataclass(frozen=True)
class AutoBound:
    unit_id: int
    specific_part: str
    role: Literal["HEAD", "OWNER"]

class AutoBindService:
    @staticmethod
    def bind_by_phone(user) -> list[AutoBound]: ...                # IFC-163
```
- 前置：调用方保证 `user.phone` 刚通过验证码校验（C-25）；`user.phone` 为空返回 `[]`。
- 行为：`RegistryService.units_by_phone(user.phone)` → 对每个专有部分：已是该专有部分产权业主（`MembershipService.is_owner_of`）则跳过；否则 `MembershipService.certify_owner(user.id, unit.id, "REGISTRY", origin="REGISTRY_AUTO")`；捕获 `ApiError("ALREADY_CERTIFIED")` 视为跳过；其他异常记录日志并停止后续（已成功的保留）；整体不向外抛异常。每个专有部分独立事务（`certify_owner` 自带，`residency/services.py:15`）。
- 户主：由 `certify_owner` 的 `head_slot` 逻辑决定（先到先得，AC-102-01/03），同住人升级为产权业主（AC-102-07）。

```python
# residency/services.py（修改）
@staticmethod
def certify_owner(user_id: int, unit_id: int, source: str, origin: str | None = None) -> str: ...   # IFC-164
```
- `origin` 缺省 `None`：行为、审计 detail 与现状完全相同。`origin == "REGISTRY_AUTO"` 时，`CERTIFY_BY_REGISTRY` 审计的 detail 追加 `{"origin": "REGISTRY_AUTO", "origin_label": "清册自动绑定"}`（REQ-NFUNC-014、AC-102-08）；`Membership.source` 仍为 `"REGISTRY"`（`residency/models.py:9,16`，列长 12 放不下新值）。
- 手动认证路径 `CertificationView`（`residency/views.py:29-52`）与申诉通过路径不传 `origin`，不改动。

**依赖**：MOD-033（`units_by_phone`）、`apps.core`。**不依赖** `accounts`、`identity`。

---

### MOD-035 自动绑定触发点

**文件**：`accounts/views.py`（`RegisterView.post`，当前 `:85-96`）、`identity/views.py`（`PhoneBindView.post`，当前 `:35-45`，及 `_merge_response` `:16-25`）。

#### IFC-160 `POST /auth/register`（响应扩展）
- 鉴权：无需鉴权（注册入口，沿用）；输入校验不变（手机号格式、6 位数字验证码，`accounts/views.py:88-93`）。
- 时机：`register_by_phone` 成功（验证码已通过、用户已创建）之后调用 `AutoBindService.bind_by_phone(user)`；验证码错误/过期时注册失败，不产生任何身份（AC-102-05）。
- 响应 201 在原有 `{token, user, is_new}` 上增加：`auto_bound: [{"unit_id": int, "specific_part": str, "role": "HEAD"|"OWNER"}]`（无命中为空数组，AC-102-04）。

#### IFC-161 `POST /me/phone/bind`（响应扩展）
- 鉴权：`IsMember`（沿用）；输入校验不变。
- 时机：`IdentityService.bind_phone` 返回 `merged == False` 后调用自动绑定（含微信登录用户，AC-102-06；非微信用户，AC-102-10）。`merged == True` 不触发（Q4=A 已确认）；`/me/phone/change`、验证码登录不触发。
- 响应 200 在原有 `{merged, phone, token?, user?}` 上增加 `auto_bound`（同上结构，`merged==True` 时恒为 `[]`）。

**依赖**：MOD-034。依赖方向：`accounts.views → residency.auto_bind`、`identity.views → residency.auto_bind`；`residency` 不导入 `accounts`/`identity`。`registry` 不导入 `residency`（仅保留既有的 `views.py:83` 函数内延迟导入）。

---

### MOD-036 Web 管理端清册页

**文件**：`frontend/src/admin/AdminRegistry.vue`（修改）、`frontend/src/shared/api.js`（修改）、`frontend/src/admin/RegistryImportDialog.vue`（新建）、`frontend/src/admin/registryImport.js`（新建）。测试建议：`frontend/tests/registryImport.spec.js`（vitest，画像 P3 位置）。

**`api.js` 契约变更**（`admin` 对象，当前 `frontend/src/shared/api.js:131-140`）：

```js
registryUnits: (params) => adminHttp.get('/admin/registry/units', { params }),               // params 增 unit_type
createRegistryUnit: (data) => adminHttp.post('/admin/registry/units', data),                   // data 增 unit_type, area
updateRegistryUnit: (id, data) => adminHttp.patch(`/admin/registry/units/${id}`, data),
deleteRegistryUnit: (id) => adminHttp.delete(`/admin/registry/units/${id}`),
registryUnitOwners: (id, owners) => adminHttp.put(`/admin/registry/units/${id}/owners`, { owners }),  // 取代 registryUnitPhones（删除）
registryImportSpec: () => adminHttp.get('/admin/registry/import/spec'),
registryImportTemplate: (fileType) =>
  adminHttp.get('/admin/registry/import/template', { params: { file_type: fileType }, responseType: 'blob' }),
importRegistry: (file, { dryRun = false } = {}) => { /* FormData(file)；dryRun 时 POST /admin/registry/import?dry_run=1 */
  // 必须在该请求上单独设置 { timeout: 100000 }（http.js:25 全局为 15000）
},
```
注意：响应拦截器 `resp => resp.data`（`http.js:27`）对 blob 同样返回 Blob；错误响应若为 blob 需转文本再解析 JSON（`error.response.data` 在 `responseType:'blob'` 时是 Blob）。契约测试 `backend/tests/integration/test_frontend_contract.py:35-37` 的正则会解析上述字面路径并 `resolve()`，所以路径必须写成字符串字面量。

**页面行为**：
- 列表：列"专有部分 / 类型（未登记）/ 面积（未登记）/ 业主（人数；展开见姓名与完整手机号；姓名为空显示"（未登记姓名）"）/ 操作（编辑、业主、删除）"；顶部类型筛选（含"未登记"）。
- 新增/编辑对话框：楼栋、单元（选填）、楼层（选填）、户号、类型（必选）、面积（车位必填，提示）。
- "业主"对话框：可增删任意多行 {姓名, 手机号（可多个，逗号/换行分隔，选填）}，无数量限制；提示"未登记手机号的业主只能通过产权申诉认证"（REQ-FUNC-098）。
- 导入：按钮"下载模板"（xlsx / csv 下拉）、"格式说明"（折叠面板，数据来自 IFC-159）、"批量导入"。流程 选择文件 → 预检 → 展示结果（新增/更新专有部分、业主数、手机号数、失败行数、被修改项列表）→ "确认导入" → 结果。结果与错误以表格呈现，错误表最多渲染 200 行，其余通过"下载错误清单"获得（`registryImport.js: errorsToCsv(errors): Blob`，UTF-8 BOM）。
- 处理中与超时：见 architecture_design 第 4 节；`IMPORT_REQUEST_TIMEOUT_MS = 100000`；处理期间禁用全部导入相关按钮，并在对话框显示已等待秒数；按错误码/状态分流提示（`IMPORT_TIMEOUT`、`IMPORT_CONFLICT`、502/504/`ECONNABORTED`、`IMPORT_COLUMNS_MISSING`）。

**依赖**：IFC-153~159。

---

### MOD-037 Web 用户端

**文件**：`frontend/src/portal/Units.vue`（修改，当前固定四个下拉 `:6-20`）、`Register.vue`（修改，`submit` 当前 `:49-62`）、`Me.vue`（修改，`afterPhoneChange` 当前 `:165-174`）。`api.js` 的 `unitApi.options`、`authApi.register`、`meApi.bindPhone` 路径不变（`frontend/src/shared/api.js:9,31,38`），只在注释里补充响应新字段。

- `Units.vue`：由 `level`/`skipped`/`has_empty` 驱动的逐级选择（每次选择后用已选的各层（含空串）再请求），不渲染被跳过的层级；末级选项显示服务端 `label`（`filterable`）；认证失败 `PHONE_NOT_IN_REGISTRY` 时在原有申诉卡片旁显示指引"如清册中未登记你的手机号，请提交产权申诉"（AC-104-01，后端文案已存在 `residency/views.py:50`）；`PHONE_REQUIRED` 沿用"请先绑定手机号"（AC-104-03）。
- `Register.vue` / `Me.vue`：响应 `auto_bound` 非空时，显示"已根据你的手机号自动认证为 {specific_part} 的产权业主"（多个则逐个或合并展示）；文案中不含他人信息（AC-102-08）。

**依赖**：IFC-152、160、161。

---

### MOD-038 小程序

**文件**：`miniprogram/pages/units/index.vue`（修改，四个 picker `:5-16` 与 `load/pick*` 方法）、`miniprogram/pages/phone/index.vue`（修改，`done` `:62-70`）、`miniprogram/utils/api.js`（`options`、`bindPhone` 仅更新注释，路径不变，`:18,21`）。测试建议：`miniprogram/tests/units.spec.js`（vitest，画像 P3）。

- `units/index.vue`：与 MOD-037 相同的动态跳级逻辑，picker 数据源为服务端 `options`；`roomLabels` 改用服务端 `label`；`has_empty` 时在 picker 末尾追加"无单元/无楼层"。小程序 picker 无搜索，车库类大列表可用性有限（风险 R9）。
- `phone/index.vue`：`done(result)` 中若 `result.auto_bound?.length`，用 `uni.showModal` 显示"已根据你的手机号自动认证为 …"（toast 会被截断）。
- 小程序没有注册页（`miniprogram/utils/api.js` 无 register 调用），IFC-160 与小程序无关。
- 管理端清册功能不在小程序，无同类页面（已 `grep -rn "units/options\|certif\|/appeals" miniprogram` 核实，仅 `pages/units/index.vue`、`tests/api.spec.js`、`utils/api.js`）。

**依赖**：IFC-152、161。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-083 | US-092、093、094 | MOD-031、032、036 |
| REQ-FUNC-084 | US-092 | MOD-031（import_spec）、032（IFC-159）、036 |
| REQ-FUNC-085 | US-093 | MOD-031（import_template）、032（IFC-158）、036 |
| REQ-FUNC-086 | US-093、094 | MOD-031 |
| REQ-FUNC-087 | US-094、095 | MOD-030、031、032（IFC-156 无上限） |
| REQ-FUNC-088 | US-096、097 | MOD-030、031、032、036 |
| REQ-FUNC-089 | US-096、097 | MOD-030、031、032、036 |
| REQ-FUNC-090 | US-094、095 | MOD-030、031、032 |
| REQ-FUNC-091 | US-098 | MOD-030、033、037、038 |
| REQ-FUNC-092 | US-099 | MOD-031 |
| REQ-FUNC-093 | US-100 | MOD-031、032、036 |
| REQ-FUNC-094 | US-101 | MOD-030（迁移）、036（"未登记"显示） |
| REQ-FUNC-095 | US-095、097 | MOD-032、036 |
| REQ-FUNC-096 | US-102 | MOD-034、035、037、038 |
| REQ-FUNC-097 | US-103 | MOD-033、037、038 |
| REQ-FUNC-098 | US-099、104 | MOD-030、031、032、036、037 |
| REQ-NFUNC-011 | US-094、095 | MOD-030、031、032 |
| REQ-NFUNC-012 | US-095、102、103 | MOD-032（仅管理端返回姓名/手机号）、033、034、035 |
| REQ-NFUNC-013 | US-093 | MOD-031（`cell_text`、模板文本列） |
| REQ-NFUNC-014 | US-094、097、102 | MOD-032、034 |
| REQ-NFUNC-015 | US-094、100 | MOD-031、032、036 + 部署配置（architecture_design"GR-A-001 condition 处理"） |
| C-21~C-26 | — | C-21：MOD-034 不改认证比对；C-22：MOD-032 不触碰 `Membership`；C-23：MOD-030 无证件字段；C-24：MOD-031/032；C-25/26：MOD-034/035 |

REQ-FUNC-083~098 共 16 条均被覆盖，无空行。

## 依赖关系

```
MOD-032 → MOD-031（plan_import / apply_plan / read_rows / build_template_*，经 IFC-157/158/159）
MOD-032 → MOD-030（模型、序列化器）
MOD-031 → MOD-030
MOD-033 → MOD-030
MOD-034 → MOD-033（IFC-162 units_by_phone）；→ residency.services（IFC-164，同 app）
MOD-035 → MOD-034（IFC-163）
MOD-036 → IFC-153~159（HTTP，经 MOD-032）
MOD-037 → IFC-152（MOD-033）、IFC-160/161（MOD-035）
MOD-038 → IFC-152、IFC-161
```

跨 app 导入方向（后端）：`accounts.views`、`identity.views` → `residency.auto_bind` → `registry.services` → `registry.models` → `core`。`residency.models → registry.models` 为既有边（`residency/models.py:4`）。`registry → residency` 仅有既有的函数内延迟导入（`registry/views.py:83`），本次不新增。**已检查：无循环依赖。**

## 数据迁移

**有。** 全部手写，仅限 `registry` 一个 app（画像 P6）；文件头不得含 "Generated by Django"（注：既有 `registry/migrations/0001_initial.py:1` 的头部即是 "Generated by Django 6.0.6"，属 CR-023 已知遗留，本次不动它）；须用 Django 5.2.x 校验（画像 P4）；`makemigrations --check --dry-run` 须无漂移。`residency`、`accounts` 无迁移（`Membership.source` 不变）。

| 迁移 | 内容 | 可逆 |
|---|---|---|
| `registry/0002_owner_type_area` | `AlterField`：`unit_no`（`blank=True, default=""`）、`floor`（max 16→32，`blank=True, default=""`）、`room`（16→32）、`specific_part`（100→140）；`AddField`：`RegistryUnit.unit_type`（可空 `CharField(10)`）、`RegistryUnit.area`（可空 `DecimalField(10,2)`）；`CreateModel RegistryOwner`（含 `uniq_registry_owner_name`）；`AddField RegistryPhone.owner`（`null=True`） | 是（反向删除新增项；加宽列反向缩窄，若已有超长数据则失败） |
| `registry/0003_backfill_legacy_owners` | `RunPython`：对每个 `owner IS NULL` 的 `RegistryPhone`，创建一位 `name=NULL` 的 `RegistryOwner(unit=phone.unit)` 并写回 `phone.owner`（逐条创建以取得主键，量级为既有清册行数；`iterator(chunk_size=1000)`）。**不删除任何既有行**。逻辑放在可被测试直接导入调用的函数里（测试环境 `MIGRATION_MODULES` 置空，不会自动跑迁移，画像 P4）。PM 落地口径（ADR-037，待用户确认） | 是：反向函数删除 `name IS NULL` 的业主（并先把对应手机号的 `owner` 置空） |
| `registry/0004_phone_owner_required` | `AlterField RegistryPhone.owner` 改为非空；执行前断言不存在 `owner IS NULL` 的手机号 | 是（改回可空） |

- **既有数据的结果**：既有专有部分的四级取值、`specific_part`、`(unit, phone)` 记录原样保留；类型、面积为 `NULL`（管理端显示"未登记"，REQ-FUNC-094）；每个既有手机号对应一位姓名为 `NULL` 的业主。认证仅比对 `RegistryPhone(unit, phone)`，因此结果与上线前一致（AC-101-02）。
- **MySQL 注意**：DDL 不在事务内、不可整体回滚，所以拆为 3 个迁移，每步独立可重试；加宽 `specific_part` 唯一索引列到 140 字符（utf8mb4 下 560 字节）在 InnoDB 索引长度限制内。
- **数据风险**：回填脚本量级取决于现网手机号行数（未知，测试环境）；唯一约束 `(unit, name)` 对 `NULL` 不冲突（MySQL 与 SQLite 一致）。
- **回滚**：`[MANUAL_ROLLBACK_REQUIRED]` 撤销 0002 会删除 `RegistryOwner` 表及类型/面积列，迁移后录入的姓名、类型、面积、新业主全部丢失；执行前必须 `mysqldump` 备份 `registry_registryunit`、`registry_registryphone`、`registry_registryowner` 三表，且须在恢复旧代码**之前**反向迁移（旧代码无新迁移文件，见 ocap-deploy SKILL ROLLBACK-004，`.claude/skills/ocap-deploy/SKILL.md:272-276`）。
- **既有测试影响（GROUP_C 须同步修改，保持零新增失败）**：
  - `backend/tests/support.py:123-129` `make_unit` 直接创建 `RegistryPhone(unit, phone)`，须改为先建 `RegistryOwner` 再建手机号；
  - `backend/tests/smoke/test_flows_smoke.py:59-61` 同上；
  - `backend/tests/integration/test_gap_must_have.py:249`（`unit.phones.create`）与 `:401-442`（`PUT …/phones`）；
  - `backend/tests/integration/test_residency_api.py:24-45`（导入与 `/phones`）；
  - `backend/tests/e2e/test_gap_journeys.py:67-68`（`PUT …/phones`）；
  - `backend/tests/integration/test_residency_api.py:15-21` 的 options 断言（响应新增字段，旧断言仍应成立）。

## 受影响的运行单元 / 构建

| 运行单元（画像 P7） | 动作 |
|---|---|
| `ocap-backend`（gunicorn 127.0.0.1:9000） | 部署新代码 + **执行迁移 `registry` 0002~0004** + 重启；核实/调整 `--timeout`（目标 90 秒）与 worker 数（风险 R1/R2，E1 给核实清单与方案）。迁移前对 3 张 registry 表做 mysqldump |
| nginx `ocap` 站点（8090，仅此站点） | 核实/增加 `client_max_body_size 6m;`、`proxy_read_timeout 90s;`、`proxy_send_timeout 90s;`；改前备份，`nginx -t` 后 `reload`（不 restart）。Freeark nginx 配置**不触碰** |
| 阿里云 VPS nginx(443) + frp、Freeark nginx `^~ /ocap/` 段 | **不在本次范围，已知限制**（Q6=B）：60 秒验收只在内网 `http://192.168.31.51:8090/ocap/` |
| Web 前端（`npm run build -- --base=/ocap/`） | 重新构建并替换 `/home/yangyang/ocap/web` |
| 小程序（uni-app 构建） | 重新构建；发布流程不在画像 P7 内 |
| `ocap-run-due-jobs` timer | 无变化 |
| 需要重新烧录的固件 / FPGA | 不适用 |

## 领域与外部依赖出处

画像 P11 有条目（微信、阿里云短信等），但**本次设计不新增对任何闭源/外部 API 的调用**：自动绑定只使用本系统内已验证的手机号；验证码校验沿用 `AccountService.verify_code`，不改变其调用。下表登记接口契约中引用的、来自现有代码的事实。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-160 | 注册入口校验：手机号 `PHONE_RE`、6 位数字验证码；`register_by_phone` 内完成验证码校验后创建用户 | [CODE: backend/apps/accounts/views.py:85-96]、[CODE: backend/apps/accounts/services.py:168-185] |
| IFC-161 | 绑定手机号：`PHONE_ALREADY_BOUND` 校验、`verify_code(purpose="BIND_PHONE")`、手机号属于他人则合并 | [CODE: backend/apps/identity/services.py:47-63] |
| IFC-164 | `certify_owner` 的审计动作 `CERTIFY_BY_REGISTRY`、户主 `head_slot` 先到先得、同住人升级；`Membership.source` 列长 12 | [CODE: backend/apps/residency/services.py:14-42]、[CODE: backend/apps/residency/models.py:9,16] |
| IFC-157 | 审计动作 `REGISTRY_IMPORTED`、`REGISTRY_UNIT_CHANGED`、`CERTIFY_BY_REGISTRY` 已登记于白名单；`AuditService.record` 对未登记动作抛 `ValueError` | [CODE: backend/apps/core/audit.py:11-15,59-60] |
| IFC-153/156 | `PlainPhoneField` 仅限 `/admin/registry/**` 使用；`page_response` 分页参数与上限 | [CODE: backend/apps/core/masking.py:29-30]、[CODE: backend/apps/core/serializers.py:4-13] |
| ADR-040 | axios 全局超时 15000 ms | [CODE: frontend/src/shared/http.js:25] |
| ADR-040 | nginx `proxy_read_timeout`/`proxy_send_timeout` 默认 60 秒；`client_max_body_size` 默认 1m；gunicorn `timeout` 默认 30 秒 | [WEB: https://nginx.org/en/docs/http/ngx_http_proxy_module.html，2026-11-10]、[WEB: https://nginx.org/en/docs/http/ngx_http_core_module.html，2026-11-10]、[WEB: https://gunicorn.org/reference/settings/，2026-11-10]（gunicorn 默认值经搜索结果摘要获得，未取得官方页面原文 `[UNSOURCED-原文]`） |
| ADR-040 | 目标机 gunicorn 实际参数、nginx 实际超时/体积设置 | **[UNSOURCED]**——不在仓库，P3/SKILL.md 均无；留给 E1/用户核实 |
