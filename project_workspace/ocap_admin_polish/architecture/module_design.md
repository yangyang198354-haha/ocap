<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:45:48+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (1.1.0 DRAFT)</file>
    <file>phase_status.md (Q-B1=B)</file>
    <file>../ocap_registry_import/architecture/module_design.md (基线，至 MOD-038 / IFC-163)</file>
    <file>../ocap_ui_theme/architecture/module_design.md (基线，至 MOD-029 / IFC-151)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：管理端打磨（INCREMENTAL）

> 编号接续全项目：MOD-064 起、IFC-243 起（ADR 见 architecture_design.md，ADR-064~077）。
> 模块 = 本次新建/修改的代码单元，路径相对仓库根 `/root/myproject/ocap`；后端路径前缀 `backend/apps/`；HTTP 路径省略 `/api/v1`；错误体统一 `{code, message, details?}`（`backend/apps/core/errors.py:25-31`）。
> 只写签名与契约，不含函数体。风格 key 格式沿用基线：`^[a-z][a-z0-9_-]{1,31}$`（`accounts/services.py:24`）。
> **1.1.0 定向修订（Q-B1=B，ADR-075 1.1.0）**：仅改 MOD-070 的 IFC-256（触发器标记约定）、MOD-071 的 IFC-258（样式契约，新增管理端 B 风格渐变顶栏/高亮/焦点环规则与对比度项）与 MOD-073 的守护测试条目；其余模块、IFC 编号、依赖图、迁移与运行单元不变。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-064 | 专有部分规则与单条判重 | **修改** `registry/models.py`（`build_specific_part`，原位替换）、`registry/views.py`（`AdminUnitListView.post` 预检查，`:115`） | 新拼接规则的唯一实现；单条新增判重经同一函数 | REQ-FUNC-123/124/126/127/128；NFUNC-23；US-132/133/135/136/137 | 无 |
| MOD-065 | 存量标识重新生成迁移 | **新建** `registry/migrations/0005_regenerate_specific_part.py` | 冻结规则 + 冲突检测 + 两阶段更新 + 可逆 + 核对清单输出 | REQ-FUNC-125；NFUNC-19/23；C-31；US-134 | 无（刻意不依赖 MOD-064，ADR-066） |
| MOD-066 | 核对预览命令 | **新建** `registry/management/__init__.py`、`registry/management/commands/__init__.py`、`registry/management/commands/registry_specific_part_preview.py` | 只读：按当前规则预估变化、冲突、省略楼层段、非纯数字户号清单；上线前预检与上线后幂等核对 | REQ-FUNC-125；US-134（AC-134-03/04/05） | MOD-064 |
| MOD-067 | 导入说明与模板同步 | **修改** `registry/import_spec.py`、`registry/import_template.py` | 规则文案与示例（含实算标识）单一来源；模板示例行 | REQ-FUNC-129；US-138 | MOD-064 |
| MOD-068 | 管理员风格偏好（后端） | **修改** `accounts/models.py`（`AdminAccount`）、`accounts/services.py`、`accounts/views.py`、`accounts/urls.py`；**新建** `accounts/migrations/0003_adminaccount_theme_key.py` | 管理员账号级风格偏好，仅管理员令牌可读写 | REQ-FUNC-130/131/132/134；C-33；US-139~141、143 | 无（复用 `core.permissions.IsAdmin`、`core.errors.ApiError`） |
| MOD-069 | 前端风格核心与管理端 store | **新建** `frontend/src/theme/core.js`、`frontend/src/theme/adminStore.js`；**修改** `frontend/src/theme/store.js`、`frontend/src/theme/apply.js`、`frontend/src/shared/api.js` | 共享工具；管理端 store（设备记忆/对账/选择）；用户端 store 去除强制 B；管理端 API 入口 | REQ-FUNC-130/131/132/134/135；NFUNC-22；US-139~141、143、144 | MOD-068（经 IFC-251） |
| MOD-070 | 管理端风格接线 | **修改** `frontend/index.html`、`frontend/src/router/index.js`、`frontend/src/admin/AdminLogin.vue`（登录对账）、`frontend/src/admin/AdminLayout.vue`；**新建** `frontend/src/theme/AdminThemeSwitcher.vue` | 首屏脚本分键、路由守卫、登录/登出对账、顶栏入口 | REQ-FUNC-130/131/132/134/135；NFUNC-22；US-139~141、143、144 | MOD-069、MOD-071 |
| MOD-071 | 管理端主题化样式 | **修改** `frontend/src/shared/style.css`、`themes/bento.web.css`、`themes/bento.theme.json`、生成物 `frontend/src/theme/generated/themes.css`（脚本重新生成）；管理端页面按下文清单 | 管理端顶栏/导航/登录页类名、管理端作用域覆盖、对比度项、完成口径守护 | REQ-FUNC-133；NFUNC-21；US-142 | 无 |
| MOD-072 | 导入对话框说明 | **修改** `frontend/src/admin/RegistryImportDialog.vue` | 说明区与示例读取 spec 接口新字段，删除硬编码示例 | REQ-FUNC-129；US-138 | MOD-067（经 IFC-246） |
| MOD-073 | 测试同步与新增守护测试 | **新建/修改**：见 MOD-073 详情 | 既有旧格式/"管理端固定 B"断言同步更新；新规则、迁移、偏好、一致性、主题化守护用例 | REQ-NFUNC-20；US-144（AC-144-04）及全部故事回归 | 以上全部（无模块反向依赖） |

## 模块详情

### MOD-064 专有部分规则与单条判重

**文件**：`backend/apps/registry/models.py`（修改）、`backend/apps/registry/views.py`（修改一处）。

**IFC-243 `build_specific_part`（内部函数契约；不对外暴露 HTTP）**

```python
# registry/models.py —— 同名同签名，原位替换（旧版 :16-18）
def build_specific_part(building: str, unit_no: str, floor: str, room: str) -> str: ...

# 模块私有（不导出）：
_SUFFIXES: tuple[str, str, str, str] = ("栋", "单元", "层", "号")   # 楼栋、单元、楼层、户号
_PURE_NUMBER: re.Pattern[str]    # r"(?:负)?[0-9]+"，使用 fullmatch；仅 ASCII 数字
def _segment(value: str, suffix: str) -> str: ...   # strip；空→""；已以 suffix 结尾→原样；纯数字/负+数字→补 suffix；其他→原样
def _floor_is_implied_by_room(floor: str, room: str) -> bool: ...   # 规则（5），见 ADR-064 第 4 点
```

- 语义（逐条对应 AC，详见 ADR-064）：每段 strip；空段跳过；已带后缀原样；`[0-9]+` 或 `负[0-9]+` 补后缀；含其他内容（"3.0""-1""B1""1F""整栋""A-088"）原样；楼层非空、`stem = 楼层去末尾"层"` 非空且户号以 `stem+"层"` 开头 → 省略楼层段；四段直接连接。
- 示例（来自需求，供 GROUP_D 取金标，不是实现）：`("1栋","1单元","1","101") → "1栋1单元1层101号"`；`("1栋","","负1","924") → "1栋负1层924号"`；`("10栋","","1","1") → "10栋1层1号"`；`("建设南路146号","","","整栋") → "建设南路146号整栋"`；`("圣灯路155号","","1","1层") → "圣灯路155号1层"`；`("建设南路160号","","2","1层") → "建设南路160号2层1层"`；`("车库","","","A-088") → "车库A-088"`；`("1栋","","","101") → "1栋101号"`（AC-133-07，首尾空格先去除）。
- 调用点（全部为既有，不改调用方式）：`models.py:39`（`save()`）、`importing.py:389`（解析）、`views.py:157`（单条编辑判重）。
- **变更 1（`views.py:115`）**：`AdminUnitListView.post` 的重复检查由 `RegistryUnit.objects.filter(**fields).exists()` 改为 `RegistryUnit.objects.filter(specific_part=build_specific_part(**fields)).exists()`，使"楼层 `1` 与 `1层`、户号 `101` 与 `101号` 视为同一专有部分"在 409 `UNIT_EXISTS` 处拦截（AC-136-02），而不是落到库层 `IntegrityError`。`:119-120` 的 `IntegrityError` 兜底保留。
- 对外接口（既有，契约不变、行为随规则变化，见 IFC-260）：`GET/POST /admin/registry/units`、`PATCH/DELETE /admin/registry/units/<id>`、`POST /admin/registry/import`（`dry_run` 预检同一入口）。鉴权：均为 `IsAdmin`（`views.py:75,126`）；输入校验：沿用 `validate_unit_fields`（楼栋/户号必填、各段 ≤32、楼栋/单元/楼层不含"-"，`import_spec.py:105-126`），错误类型 `INVALID_VALUE` 400 / `UNIT_EXISTS` 409，均不变（C-32）。
- 性能：纯字符串运算，预编译正则；20000 行规模增量可忽略（REQ-NFUNC-23 后半）。
- 依赖：无。外部依赖：无。

---

### MOD-065 存量标识重新生成迁移

**文件**：`backend/apps/registry/migrations/0005_regenerate_specific_part.py`（新建，手写；文件头注明"手写迁移（画像 P6）；规则为冻结副本，禁止随运行时规则修改"，不含 "Generated by Django"）。依赖：`("registry", "0004_phone_owner_required")`；**不 import `apps.registry.models`、`importing`、`views` 等应用代码**，只用 `apps.get_model("registry", "RegistryUnit")` 的历史模型。

**IFC-244 迁移函数契约（可被测试以 `importlib.import_module("apps.registry.migrations.0005_regenerate_specific_part")` 直接调用）**

```python
def _frozen_rule_v1(building: str, unit_no: str, floor: str, room: str) -> str: ...    # 新规则冻结副本（语义同 ADR-064）
def _frozen_legacy_rule(building: str, unit_no: str, floor: str, room: str) -> str: ... # 旧规则：非空段以 "-" 连接（不 strip）

@dataclass(frozen=True)
class UnitRow: id: int; building: str; unit_no: str; floor: str; room: str; specific_part: str

@dataclass(frozen=True)
class RegenPlan:
    changes: list[tuple[int, str, str]]            # (id, 旧标识, 新标识)，仅值会变化的行
    conflicts: list[tuple[list[int], str]]         # (同组记录 id 列表, casefold 后的最终值)
    review: list[tuple[UnitRow, str]]              # 户号非纯数字的记录与其新标识（AC-134-05）

def plan_regeneration(rows: Iterable[UnitRow], rule: Callable[[str, str, str, str], str]) -> RegenPlan: ...
    # 最终值 = 改动行取 rule(...)、未改动行取原值；按 casefold 分组，组内>1 即冲突

def regenerate_specific_parts(apps, schema_editor) -> None: ...      # RunPython forward
def restore_legacy_specific_parts(apps, schema_editor) -> None: ...  # RunPython reverse（用 _frozen_legacy_rule，对称处理）

PLACEHOLDER_PREFIX: str = "~regen~"       # 占位值 f"{PLACEHOLDER_PREFIX}{id}"；执行前断言库中无以此开头的值
BATCH_SIZE: int = 200                     # bulk_update 批大小（SQLite 变量上限）
```

- `Migration.operations = [migrations.RunPython(regenerate_specific_parts, restore_legacy_specific_parts)]`。
- 执行步骤（forward）：① 读全表 `(id, building, unit_no, floor, room, specific_part)`；② `plan_regeneration`；③ `conflicts` 非空 → 向 stderr 逐行输出 `id|旧标识|新标识|楼栋|单元|楼层|户号`，抛 `RuntimeError("专有部分标识重新生成存在 N 条冲突记录，整批未生效")`，**此时未写任何数据**；④ 无冲突 → `with transaction.atomic(using=schema_editor.connection.alias)`：阶段 1 把 `changes` 中的行置为占位值，阶段 2 置为新值（均 `bulk_update(["specific_part"], batch_size=200)`）；⑤ 向 stdout 输出摘要（总数、变化数、非纯数字户号清单行数及明细 `id|旧标识|新标识|楼栋|单元|楼层|户号`）。
- 幂等：已是新格式时 `changes` 为空，不执行任何写入，第二次执行"被修改记录数 = 0"（AC-134-03）。
- 不变量：只写 `specific_part`；不触碰楼栋/单元/楼层/户号、类型、面积、业主、手机号、房屋关系、申诉、席位（C-31、REQ-NFUNC-19）；不刷新 `updated_at`（OQ-05）。
- 鉴权/输入：无 HTTP/CLI 入口；随 `python manage.py migrate` 在目标机由部署流程执行。
- 外部依赖：无。

---

### MOD-066 核对预览命令

**文件**：`backend/apps/registry/management/__init__.py`、`.../commands/__init__.py`、`.../commands/registry_specific_part_preview.py`（均新建）。

**IFC-245 CLI：`python manage.py registry_specific_part_preview [--limit N]`**

```python
class Command(BaseCommand):
    help: str
    def add_arguments(self, parser) -> None: ...   # --limit: int，默认 50，范围 1~100000
    def handle(self, *args, **options) -> None: ... # 只读：仅 SELECT；不写库、不写文件
```

- 行为：读全表，用**当前** `build_specific_part`（IFC-243）计算新值，向 stdout 输出：`total`、`would_change`（存储值 ≠ 新值）、`conflicts`（按 `casefold` 分组，>1）及其明细、`floor_omitted`（新值省略了非空楼层段的条数）、`review`（户号非纯数字的条数）及前 `--limit` 条明细（`id|存储标识|新标识|楼栋|单元|楼层|户号`）。迁移前运行 = 上线预检（"冲突 0"复核）；迁移后运行 `would_change = 0` 即幂等证据。
- 鉴权：无应用级鉴权；等同于服务器 shell + `.env` 数据库凭据的访问权限（与 `create_admin.py`、`run_due_jobs.py` 一致）；输出不含业主姓名与手机号（只有标识与四个字段原值）。
- 输入校验：`--limit` 非整数或超出范围 → `CommandError`（退出码 1）。
- 依赖：MOD-064（IFC-243）。外部依赖：无。
- 说明：本命令不执行于测试机的动作由 GROUP_E1 / PM 只读 ssh 决定（画像 P9）；测试用 `call_command` 在 SQLite 上覆盖。

---

### MOD-067 导入说明与模板同步

**文件**：`backend/apps/registry/import_spec.py`、`backend/apps/registry/import_template.py`（修改）。

**IFC-247 示例与实算标识（`import_spec.py`，示例行由 `import_template.py:8-13` 迁入）**

```python
EXAMPLE_ROWS: list[list[str]]    # 列顺序 = IMPORT_COLUMNS；至少含：
    # ["1栋","1单元","3","301","住宅","89.50","张三","13800000001"] × 3 行（李四、王芳，王芳无手机号）
    # ["车库","","","A-088","车位","12.50","赵云",""]
    # ["1栋","","负1","924","车位","12.50","钱七",""]
    # ["10栋","","1","1","商铺","60.00","孙八",""]
def example_identifiers() -> list[dict[str, str]]: ...   # [{"fields": "1栋 / 1单元 / 3 / 301", "specific_part": "1栋1单元3层301号"}, ...]，由 build_specific_part 实算，同一专有部分去重
SUFFIX_RULES: list[str]          # 说明文案（后缀补全、纯数字与"负1"补后缀、含其他文字原样、户号以"楼层值+层"开头省略楼层段）
```

- `column_specs()` 的 `楼栋/单元/楼层/户号` 四列 `allowed` 追加"可带或不带后缀（栋/单元/层/号），系统自动补全"（AC-138-01）；`spec_payload()` 的 `notes` 增加 `SUFFIX_RULES`；示例列 `example` 保持字段原值。
- 模板：`build_csv()` / `build_xlsx()` 的签名不变，示例行读 `EXAMPLE_ROWS`；`_NOTES` 增加规则文案；文本列设置不变（`_TEXT_COLUMNS`，`import_template.py:24`）。
- **IFC-246 `GET /admin/registry/import/spec` 响应扩展（既有端点，只增字段）**

```ts
// 既有字段不变：file_types, max_file_mb, max_rows, excel_sheet_note, time_budget_seconds, unit_types, columns, notes
interface SpecPayloadAdded {
  suffix_rules: string[]                                   // 后缀规则说明，逐条
  examples: Array<{ fields: string; specific_part: string }>  // 示例及实算标识
}
```

- 鉴权：沿用 `IsAdmin`（`views.py:343-347`）。输入：无参数。状态码：200；非管理员 401/403（沿用）。
- 模板下载端点不变：`GET /admin/registry/import/template?file_type=xlsx|csv`（`IsAdmin`，非法 `file_type` → 400 `INVALID_QUERY`，`views.py:325-328`）。
- 依赖：MOD-064（IFC-243）。外部依赖：`openpyxl`（沿用 `backend/requirements.txt:5`）。

---

### MOD-068 管理员风格偏好（后端）

**文件**：`backend/apps/accounts/models.py`（`AdminAccount` 增字段）、`services.py`、`views.py`、`urls.py`（修改）；`backend/apps/accounts/migrations/0003_adminaccount_theme_key.py`（新建，手写）。

```python
# accounts/models.py —— 紧随 created_by_admin_id（:50）
class AdminAccount(models.Model):
    theme_key: CharField(max_length=32, null=True, blank=True)    # NULL = 未选择（客户端解释为默认 bento）
```

**IFC-250 服务**（`accounts/services.py`，`AccountService`，紧随 `set_theme`（:333））

```python
@staticmethod
def set_admin_theme(admin: AdminAccount, theme: object) -> AdminAccount: ...
    # 校验同 set_theme：str 且匹配 THEME_KEY_RE；否则 ApiError("INVALID_VALUE", "风格标识不合法")；save(update_fields=["theme_key"])
```

**IFC-248 `GET /admin/me/theme`**
- 鉴权：`permission_classes = [IsAdmin]`；无令牌 → 401 `UNAUTHORIZED`；普通用户令牌 → 403 `FORBIDDEN`（`core/permissions.py:19-25`）。只作用于 `request.user`，无 id 参数。
- 输入：无。响应 200：`{"theme": string | null}`（单对象）。

**IFC-249 `PUT /admin/me/theme`**
- 鉴权：同上 `IsAdmin`。请求体：`{"theme": string}`，必填。
- 输入校验：非 JSON 对象、缺失、非字符串、不匹配 `^[a-z][a-z0-9_-]{1,31}$` → 400 `INVALID_VALUE` "风格标识不合法"；不校验是否属于启用集合（ADR-025）；不接受 `null`。
- 响应 200：`{"theme": string}`。副作用：仅更新本人 `theme_key`，不写审计、不影响令牌。
- 路由：`accounts/urls.py` 追加 `path("admin/me/theme", AdminThemePreferenceView.as_view())`；`AdminThemePreferenceView(APIView)` 新建于 `views.py`（含 `get`/`put`，紧随 `ThemePreferenceView`（:255））。
- 隔离证明（C-33）：`/me/theme` 仍为 `IsMember`，管理员令牌访问 403（既有用例 `tests/integration/test_theme_preference_api.py:11-14` 保持通过）；`/admin/me/theme` 为 `IsAdmin`，用户令牌 403。契约测试要求管理端调用只能对应 `IsAdmin` 视图（`test_frontend_contract.py:84-87`）——满足。
- 迁移：见"数据迁移"。依赖：无。外部依赖：无。

---

### MOD-069 前端风格核心与管理端 store

**文件**：新建 `frontend/src/theme/core.js`、`frontend/src/theme/adminStore.js`；修改 `frontend/src/theme/store.js`、`frontend/src/theme/apply.js`、`frontend/src/shared/api.js`。

**IFC-252 `theme/core.js`（从 `store.js:7-18` 抽出，用户端与管理端共享）**

```ts
export const KEY_RE: RegExp                                  // ^[a-z][a-z0-9_-]{1,31}$
export const sortedThemes: ReadonlyArray<ThemeMeta>          // THEMES 按 order 排序（来自 generated/registry）
export function findTheme(key: string): ThemeMeta | undefined
export function resolveKey(key: unknown): string             // 非字符串/格式不符/不在注册表 → DEFAULT_THEME
export function readDevice(deviceKey: string): string | null  // 存储不可用时返回 null，不抛
export function writeDevice(deviceKey: string, key: string): void   // 存储不可用时忽略
```

**IFC-253 `useAdminThemeStore`（`theme/adminStore.js`，Pinia，id `adminTheme`）**

```ts
export const ADMIN_DEVICE_KEY = 'ocap_admin_theme'
function useAdminThemeStore(): {
  current: string; ready: boolean; reconciled: boolean
  list: ReadonlyArray<ThemeMeta>                  // 即风格注册表，按 order；新增风格自动出现（AC-139-03）
  initFromDevice(): void                          // 读 ADMIN_DEVICE_KEY，非法/缺失/未注册 → DEFAULT_THEME；应用（surface 'admin'）
  enter(): void                                   // 进入管理端路由：!ready → initFromDevice()；否则重新应用 current
  reconcile(): Promise<void>                      // GET /admin/me/theme：账号值权威（有效→应用并写设备记忆；null/未注册→bento 并写设备记忆）；失败静默保持当前，不清设备记忆；成功置 reconciled=true
  select(key: string): Promise<void>              // 乐观应用 + 写设备记忆 + PUT /admin/me/theme；失败回滚并抛出，调用方提示"保存失败"；key 不在注册表 → 抛 Error('风格不存在')
  resetSession(): void                            // 登出：reconciled=false，保留设备记忆
}
```

- `store.js`（用户端，修改）：改用 `core.js`；**删除 `forAdminRoute()`**（`:58-61`，ADR-076）；其余方法与行为不变；`_apply` 调 `applyTheme(key, scheme, 'portal')`。
- **IFC-259 `apply.js`**：`applyTheme(key: string, scheme: 'dark'|'light', surface?: 'admin'|'portal'): void`——除既有 `data-theme`、`dark` 类外，设置 `html[data-surface]`（缺省 `'portal'`）；`detectLowEnd()` 不变。
- **IFC-251 `shared/api.js` 追加**（画像 P6 契约同步；字面量路径、无查询串，满足 `test_frontend_contract.py:30-37` 的解析规则）：

```ts
// 追加到 admin 对象（`api.js:126`）
theme: () => adminHttp.get('/admin/me/theme')                                   // → { theme: string | null }
setTheme: (theme: string) => adminHttp.put('/admin/me/theme', { theme })        // → { theme: string }
```

- 依赖：MOD-068（IFC-248/249）；`generated/registry.js`（既有）。外部依赖：Pinia、axios（沿用）。

---

### MOD-070 管理端风格接线

**文件**：修改 `frontend/index.html`、`frontend/src/router/index.js`、`frontend/src/admin/AdminLogin.vue`、`frontend/src/admin/AdminLayout.vue`；新建 `frontend/src/theme/AdminThemeSwitcher.vue`。

**IFC-254 `index.html` 首屏内联脚本契约**（替换 `:8-14`）

```ts
// 同步执行于样式解析前；任何异常都回落 bento
const admin = location.pathname.indexOf('/admin') !== -1
const saved = localStorage.getItem(admin ? 'ocap_admin_theme' : 'ocap_theme')
const key = (saved && /^[a-z][a-z0-9_-]{1,31}$/.test(saved)) ? saved : 'bento'
document.documentElement.setAttribute('data-theme', key)
document.documentElement.setAttribute('data-surface', admin ? 'admin' : 'portal')
```

**IFC-255 `router.afterEach` 契约**（修改 `router/index.js:65-73`）

```ts
// to.meta.admin 为真：adminTheme.enter(); 若 getToken(true) 且 !adminTheme.reconciled → adminTheme.reconcile()（不 await）
// 否则：沿用基线用户端分支（!theme.ready || from.meta.admin → theme.initFromDevice(); 有令牌且未对账 → theme.reconcileAfterLogin()）
```
`beforeEach`（登录守卫，`:56-62`）不改；管理端令牌缺失仍跳 `/admin/login`。

**IFC-257 管理端登录/登出对账契约**
- `AdminLogin.vue`：`admin.login` 成功并 `setToken(token, true)` 之后，`await useAdminThemeStore().reconcile()`，再 `router.replace('/admin')`（保证登录后首屏已是账号风格，AC-141-01/04）；`reconcile` 失败不阻断登录（AC-140-03）。登录页不渲染任何风格入口（AC-139-05）。
- `AdminLayout.vue` 登出：`setToken('', true)` 后调用 `useAdminThemeStore().resetSession()`，再跳 `/admin/login`；设备记忆保留（AC-141-05）。

**IFC-256 `AdminThemeSwitcher.vue`**

```ts
// 无 props；内部使用 useAdminThemeStore()
// 渲染：el-dropdown，触发器显示当前风格名；菜单项 = store.list（色块 swatch 三色 + name），当前项带"已选"，每项点击区域 ≥ var(--hit-min)
// 触发器标记约定（1.1.0，供 IFC-258 的样式选择器使用）：<button type="button" class="admin-theme-trigger">，内含风格名文本与一个下拉箭头 SVG
//   （SVG 的 stroke/fill 只用 currentColor，不写颜色字面量）；高度 ≥ var(--hit-min)；组件自身不写任何颜色，颜色全由 .admin-theme-trigger 的样式规则决定
// 组件必须渲染在 AdminLayout 的 .admin-bar 内（样式规则按 .admin-bar 限定）；下拉菜单 Teleport 到 body，不在 .admin-bar 内，使用 Element Plus 默认菜单样式
// 点击：key === store.current 时无操作；否则 await store.select(key)；catch → ElMessage.error('保存失败，已恢复原风格，请稍后重试')
```

- `AdminLayout.vue`（修改）：导航由内联 13 个 `<router-link>` 改为数据驱动数组 `navItems: Array<{label: string; to: string}>`（顺序与文案保持原样：业主清册、申诉、房屋关系、业委会席位、审批流程、财务、账号、信息公开、素材库、AI 服务、平台账户、内容参数、审计/配置），每项 `active-class="is-active"`；品牌 `<strong>` 改为 `<span class="brand">`；根元素加 `class="admin-shell"`；退出按钮前渲染 `<AdminThemeSwitcher />`。既有路由与权限不变。
- 依赖：MOD-069、MOD-071。外部依赖：Element Plus（沿用）。

---

### MOD-071 管理端主题化样式

**IFC-258 样式契约**

1. `frontend/src/shared/style.css`（风格无关的中性骨架，只用语义变量）：`.admin-bar` 与 `.topbar` 共享"粘性顶栏 + `var(--overlay)` 背景 + `var(--line)` 下边框"（现 `:43,56` 两处）；`.admin-bar .topnav { flex-wrap: wrap }`；**窄屏规则 `.topbar .topnav { display:none }`（`:60`）不得作用于 `.admin-bar`**（管理导航在窄屏保持可见，OQ-09）；新增 `.admin-login`（承接 `AdminLogin.vue:2` 的 `max-width:420px; padding-top:80px` 内联样式）；**1.1.0 新增** `.admin-theme-trigger`（`display:inline-flex; align-items:center; gap:6px; min-height:var(--hit-min); padding:0 12px; background:transparent; color:var(--text); border:1px solid var(--line); border-radius:var(--radius-btn); cursor:pointer; font:inherit`），作为 neon/terminal（及任何未覆盖风格）下触发器的默认外观。
2. `themes/bento.web.css` 追加（**只作用于管理端 B 风格**；下文 `S` 代表前缀 `html[data-theme="bento"][data-surface="admin"]`，实际文件中每个逗号分隔的选择器都要写出完整前缀，以满足 `build.mjs:125-154,207` 的作用域校验；颜色只用语义变量，唯一的字面量是叠加层 `rgba(17,18,26,.22)`，与 `bento.web.css:10` 同为 `#11121A` 色系）。**规则的书写顺序即层叠顺序，不得调换"悬停"与"高亮"两条**（二者特异性相同，靠后者胜出）：
   | 选择器 | 声明（只列契约，不含其他） | 对应口径 |
   |---|---|---|
   | `S .el-button--primary` | `--el-button-bg-color / -hover-bg-color / -active-bg-color / -border-color / -hover-border-color / -active-border-color: var(--accent)`；文字仍 `var(--on-accent)`（沿用 1.0.0） | AC-142-03 |
   | `S .admin-bar` | `background: var(--hero)`；`color: var(--on-hero)`；`border-bottom: 0` | Q-B1=B(a) |
   | `S .admin-bar .brand` | `color: var(--on-hero)` | Q-B1=B(a) |
   | `S .admin-bar .topnav` | `background: rgba(17,18,26,.22)`；`border-radius: var(--radius-lg)`；`box-shadow: none`；`padding: 4px` | ADR-075 决定 2 |
   | `S .admin-bar .topnav a` | `color: var(--on-hero)` | Q-B1=B(a) |
   | `S .admin-bar .topnav a:hover` | `background: rgba(17,18,26,.22)` | 同上 |
   | `S .admin-bar .topnav a.is-active` | `background: var(--surface)`；`color: var(--accent-text)`；`font-weight: 650` | Q-B1=B(b)；覆盖 `bento.web.css:12` 的黑色胶囊与 `style.css:51-52` |
   | `S .admin-bar .admin-theme-trigger` | `color: var(--on-hero)`；`border-color: var(--on-hero)` | Q-B1=B(a) |
   | `S .admin-bar .admin-theme-trigger:hover` | `background: rgba(17,18,26,.22)` | 同上 |
   | `S .admin-bar .el-button` | `--el-button-bg-color / -hover-bg-color / -active-bg-color`：`transparent`；`--el-button-text-color / -hover-text-color / -active-text-color / -border-color / -hover-border-color / -active-border-color`：`var(--on-hero)` | Q-B1=B(a) 退出按钮 |
   | `S .admin-bar .el-button:hover` | `background: rgba(17,18,26,.22)` | 同上 |
   | `S .admin-bar :focus-visible` | `outline-color: var(--on-hero)` | ADR-075 决定 5 |
   - 用户端规则 `bento.web.css:10-12`（`.topnav` 胶囊、`a.is-active` 黑色胶囊）**不得修改**。管理端高亮靠特异性覆盖：`S .admin-bar .topnav a.is-active` 的特异性为 5 个类级 + 2 个元素，高于 `:12` 与 `style.css:52` 的 `.topnav a[aria-current="page"]`；管理端导航项均带 `active-class="is-active"`（MOD-070），`is-active` 规则的特异性（5 类级）高于 `S .admin-bar .topnav a`（4 类级），故后者的 `--on-hero` 文字色不会盖掉高亮文字色；`aria-current="page"` 只出现在已带 `is-active` 的项上（精确匹配是前缀匹配的子集），不会出现"有 aria-current 而无 is-active"的情形。
   - `neon`/`terminal` 不新增任何规则；它们的 `.el-button--primary`、`.topnav a.is-active` 等既有规则不变。
3. `themes/bento.theme.json` 的 `contrast` 数组追加两项（格式同既有项，`fg` 为 token 名、`bg` 为 `#RRGGBB`，`min` ≥4.5 且不高于实测值）：
   - `{ "fg": "onAccent", "bg": "#4F46E5", "min": 6.2, "label": "管理端主按钮文字 / 强调色" }`（1.0.0；实测 6.29）
   - `{ "fg": "onHero", "bg": "#7C3AED", "min": 5.6, "label": "管理端顶栏白字 / 渐变中段" }`（1.1.0 新增；实测 5.70）
   - 既有项 `onHero / #DB2777`（min 4.59，"Hero 白字 / 渐变亮端"）与 `onHero / #4F46E5`（min 4.5，"Hero 白字 / 渐变起点"）保持不变，现在同时守护管理端顶栏；高亮胶囊文字沿用既有项 `accentText / #FFFFFF`（min 6.2，"强调色 / 白卡"）。
   - **渐变的校验口径**：`build.mjs`/`schema.mjs:68` 只接受单色 `#RRGGBB` 背景，`hero` 在 `TOKEN_SPEC` 中是自由字符串（`schema.mjs:10` 的 `hero: 'str'`），不被解析。因此构建期口径 = "渐变各色停点逐一建项，取最差值"（三个停点最差为 `#DB2777` 的 4.60）；两停点之间的插值色由 MOD-073 的守护测试对 `tokens.hero` 解析后采样断言（实测最小 4.592）。不改 `build.mjs`、`schema.mjs`。
4. 重新运行 `node scripts/themes/build.mjs`，提交生成物 `frontend/src/theme/generated/themes.css`（`--check` 通过；`registry.js` 无变化，`bento.theme.json` 的 `swatch`/`tokens` 不变）。
5. 选择器必须以 `html[data-theme="bento"]` 开头，满足构建脚本的作用域校验（`scripts/themes/build.mjs:207`）；`S` 前缀已满足。不得为绕开该校验而把规则放进 `style.css` 之外的其他文件或使用无前缀选择器。
6. **低端设备与减少动态效果**：`html[data-perf="low"]` 只替换 `--blur/--surface/--glass`（`build.mjs:176`），不影响 `--hero`、`--on-hero`；高亮胶囊的 `var(--surface)` 在低端设备上变为 `--glass-low-end`（bento 为 `#FFFFFF`，与 `--surface` 同值），对比度不变。新规则不含动画与过渡，减少动态效果无额外处理。

**管理端 15 页 + 布局的改动清单（含核对依据）**

| 文件（`frontend/src/admin/`） | 现状核实 | 本次改动 |
|---|---|---|
| `AdminLayout.vue` | 固定写法的 13 个导航、`<strong>` 品牌、无高亮、无切换入口 | **改**（见 MOD-070）；移除内联结构 |
| `AdminLogin.vue` | 3 处内联样式（宽度/外边距，无颜色） | **改**：外层内联样式 → `.admin-login`；加登录对账（IFC-257） |
| `AdminRegistry.vue`（20 处内联）、`AdminContentEditor.vue`（14）、`AdminPlatforms.vue`（10）、`AdminAiServices.vue`（9）、`AdminAudit.vue`（5）、`AdminContentPosts.vue`（5）、`AdminFlows.vue`（5）、`AdminSeats.vue`（5）、`AdminUsers.vue`（5）、`AdminAppeals.vue`（4）、`AdminMedia.vue`（4）、`AdminContentSettings.vue`（1）、`AdminFinance.vue`（2）、`AdminMemberships.vue`（1） | 内联样式全部为 `margin/width/justify-content/max-width/padding`，**无颜色类属性**（`git grep -n 'style="'` 逐条核对）；`<style scoped>` 仅 `AdminContentEditor.vue:420`、`AdminMedia.vue:79` 且无颜色；页面使用 `.page/.card/.title/.row/.muted/.list-item` 与 Element Plus | **不需要改**（口径 1~3 的守护测试证明合规）；若守护测试日后发现违规，按违规处理 |
| `RegistryImportDialog.vue` | 14 处内联（无颜色）；`:33` 硬编码示例 | 由 MOD-072 修改 |
| `editor/MediaPicker.vue`、`editor/Toolbar.vue`、`editor/RichEditor.vue` | 无页面级颜色；`editor/colors.js` 为富文本调色板数据（内容颜色，非界面颜色，`.js`） | 不改 |

- 完成口径（7 项，含自动与人工）：见 architecture_design ADR-075 的表；GROUP_D 据此编写 `frontend/tests/admin_theme.spec.js` 与人工走查清单。
- 依赖：无。外部依赖：无新增。

---

### MOD-072 导入对话框说明

**文件**：`frontend/src/admin/RegistryImportDialog.vue`（修改）。
- 说明区读取 `spec.suffix_rules` 与 `spec.examples`（IFC-246）渲染"后缀规则"与"示例：字段 → 生成的专有部分"，**删除 `:33` 的硬编码示例行**（含旧写法）；预检/结果的"被修改项"继续显示后端返回的 `specific_part`（新格式，无前端处理）。
- `registryImport.js`、`api.js:141-148` 的导入/模板/说明调用不变。
- 鉴权：沿用管理员令牌（`adminHttp`）。依赖：MOD-067。

---

### MOD-073 测试同步与新增守护测试（测试位置遵守画像 P3）

**新增**：
- `backend/tests/unit/test_specific_part_rule.py`：IFC-243 金标表（AC-132-01~05、AC-133-01~09 逐条）；`models.py` 内无第二处拼接。
- `backend/tests/integration/test_specific_part_regeneration.py`：IFC-244——迁移文件自带冻结金标表（不引用应用函数）；PM 样例（`10栋-3单元-10-1001`→`10栋3单元10层1001号` 等 AC-134-01 全部样例）；冲突（`楼层 1 + 户号 101` 与 `楼层 1层 + 户号 101号`）→ 整批不生效且数据不变、stderr 含冲突清单；交叉情形（P=(车库,"","","A-088")、Q=(车库A,"","","088")）无冲突且成功；幂等（第二次 `changes` 为空）；字段原值与子表条数不变（AC-134-02）；反向还原旧格式；5742 条合成数据耗时断言（SQLite，阈值取需求的 60 秒）。
- `backend/tests/integration/test_specific_part_consistency.py`：模型保存/批量导入/单条新增/单条编辑四路径 `specific_part == build_specific_part(...)`；AST 扫描无第二个同名定义、`apps/registry` 无 `"-".join(`；搜索 `1栋1单元` 命中、`1栋-1单元` 不命中（AC-135-03/04）；单条新增 `1`/`1层`、`101`/`101号` → 409 `UNIT_EXISTS`（AC-136-02）；导入 `1`/`1层` 合并为一个专有部分（AC-137-02/03）；模板示例行预检失败 0 且标识与 `spec.examples` 一致（AC-138-03）；管理员/用户令牌越权 401/403（AC-136-03、AC-137-04）。
- `backend/tests/integration/test_admin_theme_preference_api.py`：IFC-248/249——未登录 401、用户令牌 403（读与写）、初值 null、往返、非法值 400、已下线 key 可存；用户偏好与管理员偏好互不影响（AC-141-03、AC-143-01/03）。
- `backend/tests/integration/test_registry_specific_part_preview.py`：IFC-245（`call_command`，SQLite）。
- `frontend/tests/admin_theme.spec.js`：ADR-075 完成口径 1~6。**1.1.0 新增守护条目（口径 5、6，读取源文件 `themes/bento.web.css`、`themes/bento.theme.json`、生成物 `themes.css`，不依赖浏览器渲染；解析方式沿用 `theme_build.spec.js:6-7` 的做法，`contrastRatio`/`mix` 取自 `scripts/themes/schema.mjs`，期望值另行独立手算，不用被测输出生成期望，参考 `qa_unit_theme.spec.js:28` 的独立实现）**：
  1. 作用域：`bento.web.css` 中凡含 `.admin-bar` 的选择器，逐个（按逗号拆分）都以 `html[data-theme="bento"][data-surface="admin"]` 开头；`neon.web.css`、`terminal.web.css` 不含 `.admin-bar`；生成物中 `html[data-theme="neon"]`/`html[data-theme="terminal"]` 段落不含 `.admin-bar`。
  2. 渐变顶栏：生成物含 `html[data-theme="bento"][data-surface="admin"] .admin-bar` 规则块，`background` 为 `var(--hero)`、`color` 为 `var(--on-hero)`；`.admin-bar .brand`、`.admin-bar .topnav a`、`.admin-bar .admin-theme-trigger`、`.admin-bar .el-button` 规则块的文字色取 `var(--on-hero)`（`.el-button` 为 `--el-button-text-color` 系列）。
  3. 高亮：`… .admin-bar .topnav a.is-active` 规则块 `background` 为 `var(--surface)`、`color` 为 `var(--accent-text)`，块内不含 `#11121A`/`#fff`；该规则在源文件中位于 `… .admin-bar .topnav a:hover` 规则之后（层叠顺序，IFC-258 第 2 条）。
  4. 零回归：`bento.web.css` 含原样的 `html[data-theme="bento"] .topnav a.is-active, html[data-theme="bento"] .tabbar a.is-active { background: #11121A; color: #fff; }` 与 `html[data-theme="bento"] .topnav { background: var(--surface); border-radius: 999px; …}`；`bento.web.css` 中不带 `[data-surface="admin"]` 的既有规则数量与改动前相同（以改动前基线的规则选择器清单作对照）。
  5. 对比度（停点）：`bento.theme.json` 的 `contrast` 含 `fg=onHero` 对 `#4F46E5`、`#7C3AED`、`#DB2777` 三项，含 `fg=accentText` 对 `#FFFFFF`、`fg=onAccent` 对 `#4F46E5`；且每个 `tokens.hero` 中出现的停点色（正则取 `#RRGGBB`）都对应一个 `onHero` 项（防止日后改渐变漏建项）。
  6. 对比度（插值）：解析 `tokens.hero` 的 `linear-gradient` 停点与位置，在各停点之间按 sRGB 线性插值取 ≥1000 个采样点，`onHero` 对每个采样色 ≥4.5（当前实测最小 4.592）。
  7. 叠加层：`.admin-bar` 相关规则里出现的全部 `rgba(` 取值，RGB 三元组只能是 `17,18,26`（只许深色叠加，保证文字对比度不低于渐变本身）。
  8. 结构（组件挂载，沿用 `qa_int_theme.spec.js:228-237` 的挂载方式）：`AdminLayout` 渲染 `.admin-bar .brand`、13 个带 `active-class` 的导航链接、`.admin-theme-trigger`（`AdminThemeSwitcher`）与退出按钮，且均位于 `.admin-bar` 内；当前路由对应的链接带 `is-active`。
  9. `build.mjs --check` 通过；`run(themesDir)` 对仓库 `themes/` 返回 `errors` 为空（作用域与对比度校验均通过）。
  - 既有且必须继续通过的相关用例（不改动，用于证明零回归）：`theme_build.spec.js:30-46`（对比度实测不低于声明且 ≥4.5，`FLOOR` 按 label 取项，新增项不影响）、`qa_unit_theme.spec.js:64-83`（独立复算 ≥ `min`）、`qa_unit_theme.spec.js:55-62`（样式源不含 `prefers-color-scheme`）、`ui_blocks.spec.js:85-95`（三份 web.css 的 `.home-*` 布局规则）、`theme.spec.js:34-45`（`.vue` 无颜色字面量）、`ui_blocks.spec.js:97` 起（`portal`/`admin` 的 `.vue` 不含 `data-theme`/风格 key 字面量；`AdminLayout.vue` 不得出现 `data-surface`/`bento`）。
- `frontend/tests/admin_theme_store.spec.js`：IFC-253——对账优先级（账号值权威、null→bento、已下线→bento 不写库、读取失败保持当前、选择失败回滚、登出保留记忆）；与用户端 store 互不影响（AC-143-01/02/03）；`index.html` 内联脚本在 `vm` 沙箱按路径选键（AC-141-02/05、AC-143-02）。
- 前端契约：`frontend/tests/api.spec.js` 追加 `admin.theme/setTheme`；后端 `test_frontend_contract.py` 无需改动，自动解析 `adminHttp.get/put('/admin/me/theme')` 并校验 `IsAdmin`。

**需同步更新的既有用例**（AC-144-04、REQ-NFUNC-20，单列说明，不计新增失败）：
- 旧标识断言（`git grep -n specific_part -- backend/tests` 核实）：`tests/e2e/test_registry_import_journeys.py:92,111`、`tests/e2e/test_registry_import_scale_journeys.py:127`、`tests/integration/test_gap_must_have.py:284-285`（取值随规则，核对）、`tests/integration/test_registry_import_enhancement.py:300,432,473,479,493,530,636`、`tests/integration/test_registry_import_query_bounds.py:47`（手写旧格式键 `B-1-1-{i}`，须改为经规则生成）、`tests/integration/test_registry_import_xlsx_defects.py:65`、`tests/unit/test_registry_import_rules.py:91-95`（旧规则金标，改为新规则金标）、`tests/unit/test_registry_import_smoke.py:30`、`tests/unit/test_domain_rules.py:198,207`、`tests/support.py:31`（`next_specific_part` 辅助）。
- "管理端固定 B"断言：`frontend/tests/theme.spec.js:121-133`、`qa_unit_theme.spec.js:150-156,250-256`、`qa_int_theme.spec.js:48-63`、`qa_e2e_theme.spec.js:147-156`；`qa_unit_theme.spec.js:262` 的管理端页数断言（16）保持不变（`AdminThemeSwitcher.vue` 位于 `theme/`，不是路由页）。
- 以上清单按基线实跑逐个核对，GROUP_C 修改后以"改动前后零新增失败"为准。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-123 | US-132 | MOD-064 |
| REQ-FUNC-124 | US-133 | MOD-064 |
| REQ-FUNC-125 | US-134 | MOD-065、MOD-066 |
| REQ-FUNC-126 | US-135 | MOD-064（规则与写入点）、MOD-073（一致性守护）；输出/搜索代码零改动（ADR-069，IFC-260） |
| REQ-FUNC-127 | US-136 | MOD-064 |
| REQ-FUNC-128 | US-137 | MOD-064 |
| REQ-FUNC-129 | US-138 | MOD-067、MOD-072 |
| REQ-FUNC-130 | US-139 | MOD-068、MOD-069、MOD-070 |
| REQ-FUNC-131 | US-140 | MOD-068、MOD-069 |
| REQ-FUNC-132 | US-141 | MOD-068、MOD-069、MOD-070 |
| REQ-FUNC-133 | US-142 | MOD-071、MOD-070 |
| REQ-FUNC-134 | US-143 | MOD-068、MOD-069、MOD-070 |
| REQ-FUNC-135 | US-144 | MOD-069、MOD-070、MOD-073 |
| REQ-NFUNC-19 | US-134 | MOD-065 |
| REQ-NFUNC-20 | 全部 | MOD-073 |
| REQ-NFUNC-21 | US-142 | MOD-071 |
| REQ-NFUNC-22 | US-139、US-141 | MOD-070 |
| REQ-NFUNC-23 | US-134、US-137 | MOD-064、MOD-065 |

**IFC-260 既有接口"值格式变化、契约不变"清单**（代码零改动，随存储值自动变为新格式；GROUP_D 契约/回归用例须覆盖）：`GET /admin/registry/units`（`specific_part` 字段与 `q` 搜索，`views.py:83`）、`GET /admin/memberships`（`identity/views.py:81,103`）、`GET /me`（`identity/services.py:22`）、自动绑定响应 `auto_bound[].specific_part`（`residency/auto_bind.py:22,51`）、认证/申诉响应中的 `unit.specific_part`（`residency/views.py:26`）、导入预检/结果的 `changes[].specific_part`（`importing.py:184`）。字段名、类型、分页方式均不变；用户端权限行为不变（AC-135-06）。

## 依赖关系

- MOD-066 → MOD-064（IFC-243）
- MOD-067 → MOD-064（IFC-243）
- MOD-072 → MOD-067（IFC-246）
- MOD-069 → MOD-068（IFC-248/249，经 IFC-251）
- MOD-070 → MOD-069（IFC-252/253/259）、MOD-071（IFC-258 的类名与变量）
- MOD-073 → 以上全部
- MOD-064、MOD-065、MOD-068、MOD-071 无出向依赖。MOD-065 **刻意不**依赖 MOD-064（ADR-066）。

已检查：无循环依赖。

## 数据迁移

| 项 | 内容 |
|---|---|
| `registry/0005_regenerate_specific_part.py`（手写，数据迁移，无结构变化） | 把 `registry_registryunit.specific_part` 按冻结的新规则重新生成。方式：`RunPython`（forward + reverse）；单 app 范围；依赖 `registry.0004`。文件头不含 "Generated by Django"（画像 P6）。不使用 Django 6.x 生成或校验（画像 P4）；本迁移无需 makemigrations，也不影响 `makemigrations --check --dry-run` 的模型状态比对 |
| 更新顺序与冲突 | 先全量检测（`casefold` 分组）→ 有冲突则列出并整批不生效、不写数据 → 无冲突则单事务内"占位值 → 新值"两阶段更新，避免唯一约束在更新中途被违反（ADR-067；交叉情形示例 `车库A-088`） |
| 可重复 | 是。已是新格式则无变化行、不写库 |
| 可逆 | 是。`restore_legacy_specific_parts` 用冻结旧规则对称重算；字段原值未变，所以旧标识可无损推回。例外：迁移后新增的记录在旧规则下互相冲突时，反向整批中止并列出，须人工处理 |
| 回滚顺序（E1 写入 deployment_plan） | 停 `ocap-backend` → `python manage.py migrate registry 0004`（还原旧标识）→ 回退代码 → 启动。迁移前建议 `python manage.py dumpdata registry.registryunit`（不含姓名手机号）存入 `/home/yangyang/ocap/snapshots/` 作为数据级兜底（P7 的回滚快照只含代码） |
| 数据风险 | 低：只改一个派生列；PM 测试环境实测 5742 条、冲突 0、省略楼层段 24 条、非纯数字户号 27 条（phase_status GR-A-002 verification）。上线前须用 MOD-066 在目标环境复核冲突 = 0；规模 5742 条预计 <10 秒 `[ESTIMATE]`（REQ-NFUNC-23，测试环境实测为准）。`updated_at` 不刷新（OQ-05） |
| `accounts/0003_adminaccount_theme_key.py`（手写，加列） | `AddField(AdminAccount.theme_key, CharField(max_length=32, null=True, blank=True))`；可空列，既有管理员无需回填（NULL = 默认 B，REQ-FUNC-131）；可逆（`RemoveField`，丢弃偏好，无业务数据风险）。写法同 `accounts/0002_user_theme_key.py`（手写文件头），依赖 `("accounts", "0002_user_theme_key")` |

## 受影响的运行单元 / 构建

| 运行单元 | 动作 | 说明 |
|---|---|---|
| 后端 `ocap-backend`（systemd，gunicorn） | 须执行迁移 `registry 0005`、`accounts 0003` 并重启 | 代码变更：规则、单条新增预检、spec/模板、管理员偏好接口、预览命令。建议停服务→迁移→启动（OQ-04） |
| Web 前端（`npm run build -- --base=/ocap/` → `/home/yangyang/ocap/web`） | 须重新构建并替换静态文件 | 含 `index.html` 首屏脚本、管理端 store/入口、样式与重新生成的 `themes.css`；nginx 无需改动 |
| 风格构建脚本 `scripts/themes/build.mjs` | 开发机/CI 运行一次并提交生成物；CI 的 `--check` 守护 | 不在目标机运行 |
| 小程序 | 无变化 | ADR-077 |
| `ocap-run-due-jobs` timer、Freeark 服务/端口/目录/库 | 无变化 | P7、P8、C-34 |
| 后端/前端测试 | 后端 `python manage.py test --settings=config.test_settings`；前端 `npx vitest run --passWithNoTests`（画像 P4） | gate_mode=baseline，零新增失败 |

## 领域与外部依赖出处

不适用：画像 P11 列出的外部服务（微信、短信、邮件、内容平台等）本次均不涉及，无新增外部 API、寄存器或算法；"专有部分拼接规则"来自需求文档（REQ-FUNC-123/124 与用户 Q1/Q2/Q-AP-01 答复）而非外部资料；测试环境数据取自 phase_status.md 中 PM 的只读核验记录。
