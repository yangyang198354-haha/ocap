<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T00:11:53+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>requirements/product_review.md</file>
    <file>architecture/architecture_design.md</file>
    <file>../ocap_user_directory/architecture/module_design.md</file>
    <file>../ocap_admin_polish/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：产品评审修正（INCREMENTAL）

> 编号接续全仓：MOD-074 起、IFC-261 起（ADR 见 architecture_design.md，ADR-078 ~ 096）。路径相对仓库根；`B/` = `backend/apps/`，`W/` = `frontend/src/`，`M/` = `miniprogram/`；HTTP 路径省略 `/api/v1`；错误体统一 `{code, message, details?}`（`B/core/errors.py`）。
> 只写签名与契约，不含函数体。Python 类型注解、TypeScript 类型即契约。
> 引用基线旧接口时写 `批次名/IFC-NNN`（user_directory 与 admin_polish 的 IFC-243 ~ 246 在旧文档中重复，不改旧文档）。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-074 | 身份汇总与房屋聚合（后端） | **新建** `B/residency/housing.py`；**修改** `B/residency/views.py`（新增 `MyHousingView`）、`B/residency/urls.py`、`B/identity/services.py`（`IdentityService.me`）、`B/committee/services.py`（`identity_labels`） | `/me` 增 `summary`/`role_label`、任期口径；`/me/housing` 聚合 | REQ-FUNC-143/145/146/149/157；US-151/153/154/157/166 | 既有 `accounts.directory`、`residency`、`committee` 模型 |
| MOD-075 | 申请/申诉状态与注销关闭（后端） | **修改** `B/residency/models.py`、`B/residency/views.py`、`B/residency/services.py`、`B/identity/services.py`（`cancel`）、`B/core/audit.py`；**新建** `B/residency/migrations/0002_closed_status.py` | `CLOSED` 终态、关闭服务、已关闭记录的处理错误 | REQ-FUNC-144/148/155；US-152/156/164 | 无（`cancel` 调用本模块服务） |
| MOD-076 | 发起权限、金额上限与规则限制（后端） | **修改** `B/claims/views.py`、`B/income/views.py`、`B/core/config.py`、`B/core/views.py`、`B/core/urls.py`；**新建** `B/core/limits.py` | 报销/备用金仅委员；金额上限可配置并生效；`/system/limits` | REQ-FUNC-146/161/163/164；US-154/170/172/173 | 无 |
| MOD-077 | 小程序会话（后端） | **修改** `B/accounts/views.py`（`_session_kind` 与三个登录视图） | `client` 字段 → 7 天会话 | REQ-FUNC-147；US-155 | `core.config` |
| MOD-078 | 版式模板管理（后端） | **修改** `B/content/styles.py`、`B/content/views_admin.py` | 列表补 `id`/`usage_count`；被引用禁删 | REQ-FUNC-153；US-162 | 无 |
| MOD-079 | 报表明细脱敏（后端） | **修改** `B/ledger/views.py` | 支出行 `summary` 按配置脱敏 | REQ-FUNC-159；US-168 | `core.config` |
| MOD-080 | 现行规则固化 | **修改** `B/polls/views.py`（常量改引用）；其余规则不改代码，仅测试固化 | 常量收拢，行为不变 | REQ-FUNC-162/163/164/165/166；US-171 ~ 175 | MOD-076（`core.limits`） |
| MOD-081 | E2E 夹具命令 | **新建** `B/jobs/management/commands/e2e_fixture.py`、`B/jobs/e2e_fixture.py` | 本地/测试机夹具创建与清理（`e2e_` 数据） | 画像 P4-1；Q-PR-05；US-150 ~ 178 的 [E2E] 前置 | 既有各 app 模型（只读清册） |
| MOD-082 | Web 公共件 | **新建** `W/shared/labels.js`、`W/shared/confirm.js`、`W/shared/usePaging.js`、`W/portal/parts/UnitCascader.vue`、`W/portal/parts/AuthImage.vue`；**修改** `W/shared/api.js`、`W/shared/format.js`、`W/stores/auth.js` | 中文映射、确认封装、分页组合函数、房屋选择器、鉴权图片、API 入口、入口可见性 getter | REQ-FUNC-142/150/152/156/157/158 | MOD-074 ~ 079（经 IFC） |
| MOD-083 | Web 用户端页面 | **修改** `W/portal/{Units,Me,Home,PortalLayout,Claims,Login,Polls,PollDetail,Resolutions,ResolutionDetail,Income,Reports,Tasks,InfoDetail}.vue`（Units.vue 实质重写） | 用户端各故事的界面 | REQ-FUNC-142 ~ 145/148 ~ 150/152/154 ~ 160/163；US-150 ~ 169/172 | MOD-082、MOD-074/075/076/079 |
| MOD-084 | Web 管理端页面 | **新建** `W/admin/parts/UserPicker.vue`、`W/admin/AdminStyleTemplates.vue`；**修改** `W/admin/{AdminSeats,AdminFlows,AdminUsers,AdminMemberships,AdminAppeals,AdminFinance,AdminRegistry,AdminLayout}.vue`、`W/router/index.js` | 用户选择器、翻页、确认、模板管理页、金额上限配置卡 | REQ-FUNC-150/151/152/153/158/161；US-158 ~ 162/167/170 | MOD-082、MOD-076/078 |
| MOD-085 | 小程序 | **新建** `M/utils/{labels,confirm,paging}.js`、`M/components/UnitPicker.vue`、`M/pages/reports/detail.vue`；**修改** `M/utils/api.js`、`M/pages.json`、`M/store/auth.js`、`M/pages/{units,me,index,claims,resolutions,polls}/index.vue`、`M/pages/login/index.vue`（不改，登录函数在 `api.js`） | 同住人链路、身份展示、报表明细、入口可见性、加载更多、7 天会话请求体 | REQ-FUNC-142 ~ 149/150/152/157/159；US-150 ~ 157/161/166/168 | MOD-074/075/076/077/079（经 IFC） |
| MOD-086 | 测试同步与新增（GROUP_D 实现） | 见 MOD-086 详情（位置遵守画像 P3） | 既有断言同步；新增单元/集成/E2E/契约/远程用例；文档扫描 | REQ-NFUNC-026/027/028；US-175 ~ 178 及全部故事 | 以上全部（无模块反向依赖） |

## 模块详情

### MOD-074 身份汇总与房屋聚合（后端）

**职责**：让两端用同一口径显示身份；为"我的房屋"与首页提供产权业主所需的同住人名单与待审数量。不写库。

#### IFC-261：GET /me/housing（新增）

- 视图：`class MyHousingView(APIView)`（`B/residency/views.py`），路由 `path("me/housing", MyHousingView.as_view())`（`B/residency/urls.py`）。
- 鉴权：`IsMember`（`B/core/permissions.py:28`）。未登录 401；管理员令牌 403（既有语义）。
- 请求：无参数、无请求体。输入校验：不适用（无输入）。
- 响应 200：

```ts
type IdentityCode = 'CHAIR' | 'VICE_CHAIR' | 'MEMBER' | 'REPRESENTATIVE' | 'HEAD' | 'OWNER' | 'RESIDENT' | 'GUEST'
interface HousingResident { user_id: number; nickname: string | null; account_no: string; joined_at: string /* ISO8601 */ }
interface HousingUnit {
  unit_id: number
  specific_part: string
  role: 'HEAD' | 'OWNER' | 'RESIDENT'
  role_label: '户主' | '产权业主' | '同住人'
  certified_at: string
  residents: HousingResident[]          // 仅 role ∈ {HEAD, OWNER} 时填充，否则 []
  pending_application_count: number     // 仅 role ∈ {HEAD, OWNER} 时统计 PENDING 申请，否则 0
}
interface HousingResponse {
  summary: { code: IdentityCode; label: string }
  units: HousingUnit[]                  // 当前有效 Membership，按 certified_at, id 升序；无则 []
  pending_review_count: number          // = Σ pending_application_count
}
```

- 错误类型：无业务错误；沿用全局错误体。
- 查询数：固定（Membership + select_related unit；Seat；同住人 Membership + select_related user；待审计数一条 `GROUP BY`），不随房屋数或同住人数增长。
- 隐私（C-42、ADR-095）：不含手机号、邮箱；`residents` 仅对该专有部分产权业主返回。

#### IFC-273：`HousingService.housing_view`（内部契约，`B/residency/housing.py`，新建）

```python
class HousingResident(TypedDict):
    user_id: int
    nickname: str | None
    account_no: str
    joined_at: datetime

class HousingUnit(TypedDict):
    unit_id: int
    specific_part: str
    role: str
    role_label: str
    certified_at: datetime
    residents: list[HousingResident]
    pending_application_count: int

class HousingPayload(TypedDict):
    summary: IdentityView                      # 来自 apps.accounts.directory.IdentityView
    units: list[HousingUnit]
    pending_review_count: int

def housing_view(user: User) -> HousingPayload: ...
```

- 汇总身份：`accounts.directory.identity_view(memberships=..., seats=...)`（`B/accounts/directory.py:19-33`，业委会职务 > 户主 > 产权业主 > 同住人 > 游客；过期席位不计）。
- 依赖方向：`residency.housing → accounts.directory → residency.models / committee.models`；`residency.models` 不导入 `housing`，无循环。

#### IFC-262：GET /me（既有端点，响应增量，`IdentityService.me`，`B/identity/services.py:19`）

- 鉴权：`IsMember`，不变。输入：无。
- 变更：
  - `identities.summary: { code: IdentityCode; label: string }`（新增，来自 `identity_view`）。
  - `identities.units[].role_label: string`（新增）；其余键（`unit_id`、`specific_part`、`role`）不变。
  - `identities.committee`：由"`status="ACTIVE"` 的首个席位"改为 `CommitteeQuery.active_seat(user.id)`（校验 `term_end >= 今天`，`B/committee/services.py:31-35`）；键与类型不变：`{ position: string, term_end: string } | null`（ADR-082）。
  - `identities.labels: string[]`：结构不变（`[职务?, 房屋身份?]` 或 `["游客"]`），房屋身份由"取第一条"改为"按 `ROLE_RANK` 取最高"（见 IFC-274）。
  - `identities` 键集合变为 `{is_guest, units, committee, labels, summary}`。

#### IFC-274：`identity_labels` 与最高身份（内部契约）

```python
# B/committee/services.py（修改；签名与返回类型不变）
class CommitteeQuery:
    @staticmethod
    def identity_labels(user_id: int) -> list[str]: ...
    # 房屋身份由 MembershipService.list_active(user_id) 的第一条，改为按 residency.services.ROLE_RANK 最高者；
    # 同级取 certified_at 最早。只在函数内延迟导入 apps.residency.services（现状已如此），不导入 accounts。
```

- 影响：写入报销 `applicant_labels`、决议 `initiator_labels`、收入 `creator_labels` 的新快照，多户且角色不同的用户可能与旧快照不同（ADR-080）；旧记录不回填。
- 依赖：`apps.residency.services.ROLE_RANK`（`B/residency/services.py:8`）。

- 外部依赖：无。

---

### MOD-075 申请/申诉状态与注销关闭（后端）

**职责**：新增 `CLOSED` 终态；注销时在同一事务内关闭本人待处理的同住人申请与产权申诉；对已关闭记录给出明确错误。

**文件与改动**：

- `B/residency/models.py`（修改）：`Appeal.STATUSES`、`ResidentApplication.STATUSES` 各追加 `("CLOSED", "已关闭")`；字段 `max_length=8` 不变；约束不变（`pending_slot` 置 `None` 释放唯一槽）。
- `B/residency/migrations/0002_closed_status.py`（**新建，手写**，文件头注明"手写迁移（画像 P6）"，不含 "Generated by Django"）：依赖 `("residency", "0001_initial")`；`operations = [AlterField(Appeal.status…choices 含 CLOSED), AlterField(ResidentApplication.status…choices 含 CLOSED)]`；字段其余属性与 0001 一致（`max_length=8, default="PENDING"`）。
- `B/core/audit.py:10`（修改）：`AUDIT_ACTIONS` 追加 `"RESIDENT_APPLICATION_CLOSED"`、`"APPEAL_CLOSED"`（否则 `AuditService.record` 抛 `ValueError`，`B/core/audit.py:64-65`）。
- `B/identity/services.py:105`（修改 `IdentityService.cancel`）：在既有 `transaction.atomic()` 内、`AccountService.tombstone(user)` 之前调用 IFC-277；其余步骤与顺序不变。

#### IFC-263：GET /resident-applications/mine、GET /appeals/mine（既有，契约微调）

- 鉴权：`IsMember`，不变。输入：无。
- 响应仍为**数组、不分页**（Q-B-05）：

```ts
type ApplicationStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CLOSED'
interface UnitRef { unit_id: number; specific_part: string }
interface MyApplication { id: number; unit: UnitRef; status: ApplicationStatus; created_at: string; decided_at: string | null }
interface MyAppeal { id: number; unit: UnitRef; status: ApplicationStatus; submitted_at: string; decided_at: string | null; reject_reason: string | null }
```

- 变更：状态取值增加 `CLOSED`；服务端 `[:100]` 限制最近 100 条（按提交时间倒序，沿用现有排序）。`reject_reason` 仅管理员驳回时有值，`CLOSED` 时为 `null`。

#### IFC-264：POST /resident-applications/<id>/decision、POST /admin/appeals/<id>/decision（既有，错误增量）

- 鉴权：不变（前者 `IsMember` 且须为该专有部分产权业主，`B/residency/views.py:221-228`；后者 `IsAdmin`，`:134-135`）。输入校验不变（`decision ∈ {APPROVE, REJECT}`；驳回申诉须 `reject_reason` 1 ~ 500 字）。
- 变更：当记录 `status == "CLOSED"` 时返回 `409`，`code = "ALREADY_CLOSED"`，`message = "该申请已关闭"` / `"该申诉已关闭"`；先于 `ALREADY_DECIDED`（已通过/已驳回）判断；不产生任何房屋关系。申请决议的原子更新语句 `filter(id, status="PENDING").update(...)` 返回 0 行时，需再读一次状态以区分 `ALREADY_CLOSED` 与 `ALREADY_DECIDED`。

#### IFC-277：`PendingRequestService.close_for_cancelled_user`（内部契约，`B/residency/services.py`）

```python
class ClosedCounts(TypedDict):
    resident_applications: int
    appeals: int

class PendingRequestService:
    @staticmethod
    def close_for_cancelled_user(user: User) -> ClosedCounts: ...
```

- 语义：把 `applicant == user` 且 `status == "PENDING"` 的 `ResidentApplication`、`user == user` 且 `status == "PENDING"` 的 `Appeal` 置 `status="CLOSED"`、`decided_at=now`、`pending_slot=None`；不改 `decided_by*`、不改 `reject_reason`；已处理的历史记录不动（AC-164-03）。
- 审计：每条被关闭记录各写一条（AC-164-01 "新增两条关闭记录"），动作 `RESIDENT_APPLICATION_CLOSED` / `APPEAL_CLOSED`，`actor=AuditActor("MEMBER", user.id, f"用户{user.account_no}")`，`object_type="resident_application"|"appeal"`，`object_id=str(记录 id)`，`detail={"reason": "ACCOUNT_CANCELLED", "unit_id": <id>}`；无待处理项时不写任何记录（AC-164-04）。
- 调用约束：必须在调用方的事务内；本函数自身不开新事务。
- 依赖：`AuditService`、`Appeal`、`ResidentApplication`。外部依赖：无。

---

### MOD-076 发起权限、金额上限与规则限制（后端）

**职责**：报销/备用金发起权限；金额上限读配置；公开当前生效的限制值。

#### IFC-265：POST /claims/reimbursements、POST /claims/advances（既有，权限与校验变更）

- 鉴权：`IsMember` → `IsCommitteeMember`（`B/claims/views.py:84,111`；`B/core/permissions.py:28`）。非成员 → `403 FORBIDDEN "需要业委会成员身份"`；业主代表、席位已到期者同样 403（`CommitteeQuery.is_member`，`B/committee/services.py:37-39`）；未登录 401；管理员令牌 401（`IsCommitteeMember` 对非 `User` 主体统一 401，由原 403 变更，属已知语义变化）。
- 请求/响应字段不变（沿用 `B/claims/views.py` 现有：`amount`、`reason`、`occurred_on` / `expected_usage`、`expected_settle_on`、`invoice_ids`、`approval_flow_id`；响应 `claim_view`）。
- 输入校验变更（金额）：

```python
# B/claims/views.py（签名变更，保持对旧调用兼容：limit 缺省时读配置）
def _parse_amount(raw: object, limit: Decimal | None = None) -> Decimal: ...
```

  - 范围：`0.01 ≤ amount ≤ limit`，`limit` 缺省取 `SystemConfig.amount_max()`（IFC-267）；超限 → `400 INVALID_VALUE`，`message = "金额须在 0.01~{limit} 之间（当前上限 {limit} 元）"`，`details = {"max_amount": "<两位小数字符串>"}`；小数位 > 2、非数字 → `400 INVALID_VALUE`（文案不变）。
  - 删除模块常量 `MAX_AMOUNT`（`B/claims/views.py:24`）；`tests/unit/test_domain_rules.py:10` 以 `_parse_amount as parse_claim_amount` 导入并按旧签名调用，因 `limit` 有缺省值而继续可用。
  - 日期与数量规则不变（见 MOD-080 / REQ-FUNC-165）。
- 核销 `POST /claims/settlements`（`IsIncomeMember`）、撤回、重提、列表、详情：不变。

#### IFC-266：POST /admin/income/sheets（逐条录入）、POST /admin/income/sheets/import（既有，金额校验变更）

- 鉴权：`IsIncomeMember`，不变（`B/income/views.py`）。
- 变更：`_parse_amount(raw: object, limit: Decimal | None = None) -> Decimal`（抛 `ValueError`，文案 `金额须为正数、最多两位小数且不超过 {limit}`）；`_record_row(values: dict, line_no: int = 1, *, limit: Decimal | None = None) -> dict`；`_parse_rows(rows: list[list], *, limit: Decimal | None = None) -> dict`。视图在**每个请求开始处读取一次** `SystemConfig.amount_max()` 并向下传递，导入 5000 行时不逐行查库；缺省 `None` 时函数自行读取一次（保持 `tests/unit/test_domain_rules.py:12` 的 `_parse_rows(rows)` 调用兼容）。删除 `MAX_AMOUNT`（`B/income/views.py:28`）。
- 逐条录入超限 → 整体拒绝（沿用 `INCOME_RECORD_INVALID 400`，`details.errors[*].detail` 含当前上限）；批量导入超限的行按既有规则作为 `INVALID_FIELD` 行错误跳过。行数规则（5000 行、500 条）与文案不变（REQ-FUNC-164）。

#### IFC-267：GET /admin/system-config、PUT /admin/system-config/<key>（既有，增加可编辑键）

- 鉴权：`IsAdmin`（`B/core/views.py:43-44`）；非管理员 403，未登录 401。
- `EDITABLE_KEYS`（`B/core/config.py:8`）追加 `"claim.amount_max"`；`DEFAULTS["claim.amount_max"]`（`:37`）由 `None` 改为 `"1000000.00"`。
- `GET /admin/system-config` 响应：`{ "audit.retention_months": number, "claim.amount_max": string }`（增键，既有键不变）。
- `PUT /admin/system-config/claim.amount_max`，请求 `{ "value": string | number }`；校验：

```python
# B/core/config.py
EDITABLE_VALIDATORS: dict[str, Callable[[object], object]]   # key → 校验并规范化后的值；失败抛 ApiError
def validate_amount_max(value: object) -> str: ...            # 规范化为两位小数字符串
class SystemConfigService:
    @staticmethod
    def amount_max() -> Decimal: ...                           # 读 claim.amount_max；缺失/损坏回退 Decimal("1000000.00")
```

  - 规则：`bool`/`None`/非数字 → `400 INVALID_VALUE`，`message = "上限须为正数且最多两位小数"`；`≤ 0` 同；小数位 > 2 同；`> 999999999999.99` → `400 INVALID_VALUE`（超出金额列范围）；不允许清空（Q-PR-01=A）。
  - 成功：保存规范化字符串，写既有审计 `SYSTEM_CONFIG_CHANGED`（`detail.before/after`，`B/core/views.py:60-65`），响应 `{ key, value }`。已提交记录不受影响（只在提交时读取）。
  - `PUT` 对 `audit.retention_months` 的既有分支（`B/core/views.py:52-59`）保持不变，改为经 `EDITABLE_VALIDATORS` 分派时须保持其错误码与文案（`RETENTION_TOO_SHORT`、`RETENTION_TOO_LONG`、`INVALID_VALUE`）不变。

#### IFC-272：GET /system/limits（新增）

- 视图：`class SystemLimitsView(APIView)`（`B/core/views.py`），`path("system/limits", …)`（`B/core/urls.py`）。
- 鉴权：`IsMember`（仅登录普通用户；管理员令牌 403）。输入：无。
- 响应 200：

```ts
interface SystemLimits {
  claim_amount_max: string            // 两位小数，当前 claim.amount_max
  poll_max_questions: number          // 配置 poll.max_questions，默认 50
  poll_options_min: number            // 常量 2
  poll_options_max: number            // 常量 10
  vote_min_window_minutes: number     // 配置 vote.min_window_minutes，默认 60
  income_import_max_rows: number      // 常量 5000
  income_manual_max_records: number   // 常量 500
}
```

#### `B/core/limits.py`（新建，常量模块）

```python
POLL_OPTIONS_MIN: int = 2
POLL_OPTIONS_MAX: int = 10
INCOME_IMPORT_MAX_ROWS: int = 5000
INCOME_MANUAL_MAX_RECORDS: int = 500
def current_limits() -> dict[str, object]: ...   # 组装 SystemLimits 响应（读配置）
```

- 依赖：`core.config`、`core.models`。外部依赖：无。

---

### MOD-077 小程序会话（后端）

#### IFC-268：POST /auth/login/code、/auth/login/password、/auth/login/email（既有，请求体增量）

- 鉴权：无需鉴权（登录入口，沿用现状）。
- 请求体新增可选字段 `client?: 'web' | 'miniapp'`（缺省 `'web'`）。
- 输入校验：`client` 非字符串或不在 `{web, miniapp}` → `400 INVALID_VALUE`（`message = "client 不合法"`）；其余字段校验不变。
- 行为（`B/accounts/views.py:42` 的 `_session_kind`）：

```python
def _session_kind(payload: Mapping[str, object], *, default: str = "IDLE") -> str: ...
# 返回 "EXTENDED" 当 payload.get("remember_me") 为真，
#   或 payload.get("client") == "miniapp" 且 SystemConfig.get("session.miniapp_extended") 为真；否则 default。
```

- 响应不变：`{ token, user, is_new }`。`EXTENDED` 的 7 天上限与"满 7 天 401"沿用 `AccountService.authenticate_token`（`B/accounts/services.py:275-296`）。
- 不改：管理员登录 `POST /admin/auth/login`（仍拒绝 `remember_me`，`B/accounts/views.py:319`）；`POST /auth/wechat/miniapp`（已固定 `EXTENDED`，`:160`）；`POST /auth/wechat/web/exchange`（Web，不传 `client`）。
- 依赖：`core.config.SystemConfig`。

---

### MOD-078 版式模板管理（后端）

#### IFC-269：GET /admin/content/style-templates、POST /admin/content/style-templates（既有，响应增量）

- 鉴权：`AdminOnly`（`B/content/views_admin.py` 现状，管理员令牌）。
- 列表响应元素类型：

```ts
interface StyleTemplateItem {
  key: string                  // 'builtin:classic' | 'builtin:notice' | 'builtin:formal' | `custom:${number}`
  name: string
  builtin: boolean
  tokens: Record<string, string | number>
  id?: number                  // 仅 custom（新增）
  usage_count?: number         // 仅 custom（新增）：ContentPost.style_key == key 的记录数，含草稿/已发布/已下线
}
```

- `POST` 响应同类型（`usage_count: 0`）。输入校验不变（名称必填且 ≤ 64、唯一；`tokens` 经 `validate_tokens` 白名单与范围，`B/content/styles.py:66-85`）；错误 `STYLE_NAME_REQUIRED 400`、`STYLE_NAME_EXISTS 409`、`STYLE_INVALID 400`。

```python
# B/content/styles.py
class StyleService:
    @staticmethod
    def list_all() -> list[dict]: ...              # 自定义项追加 id、usage_count（单条 GROUP BY 聚合）
    @staticmethod
    def usage_count(template_id: int) -> int: ...  # ContentPost.objects.filter(style_key=f"custom:{template_id}").count()
    @staticmethod
    def delete(template_id: int) -> None: ...      # 引用数 > 0 → ApiError("STYLE_IN_USE", …, 409, {"count": n})
```

#### IFC-270：DELETE /admin/content/style-templates/<int:template_id>（既有，行为变更）

- 鉴权：`AdminOnly`。路径参数 `template_id: int`（Django `<int:>`）。
- 成功 204；不存在 `404 NOT_FOUND`；被内容引用 `409 STYLE_IN_USE`，`message = "该模板被 {n} 条内容使用，不能删除"`，`details = {"count": n}`。
- 内置模板无数值 id，对其 PUT/DELETE 路径不存在（路由层 404），内置模板不可被改、不可被删（AC-162-05）。`PUT` 行为不变。

---

### MOD-079 报表明细脱敏（后端）

#### IFC-271：GET /ledger/reports/<int:report_id>（既有，响应值变更）

- 鉴权：`IsMember`，不变（`B/ledger/views.py:54-55`）。
- 变更：`report_detail(report)`（`B/ledger/views.py:77`）对 `detail[*]` 中 `direction == "EXPENSE"` 的元素，当 `SystemConfig.get("report.show_expense_reason")` 为假（默认 False，`B/core/config.py:41`）时 `summary` 置 `null`；元素其余字段（`direction`、`occurred_on`、`entry_type`、`amount`、`source_type`、`source_id`、`seq`）不变；收入行不变；列表接口与合计字段不变。

```python
def report_detail(report: LedgerReport) -> dict: ...   # 同名同签名；内部对 detail 做按需拷贝脱敏，不写回数据库
```

- 依赖：`core.config`。[ASSUMPTION：Q-B-01]

---

### MOD-080 现行规则固化

**职责**：不改行为，收拢常量并以测试固化。

- `B/polls/views.py`（修改）：`2 <= len(options) <= 10`（`:97-98`）改引用 `core.limits.POLL_OPTIONS_MIN/MAX`；题数上限 `SystemConfig.get("poll.max_questions")`、窗口 `vote.min_window_minutes`（`:51-53`）不变。
- `B/income/views.py`：`len(rows) > 5001`（`:79`）、`1 <= len(rows) <= 500`（`:218`）改引用 `core.limits` 常量（与 MOD-076 同一文件，改动互不重叠）；文案不变（"文件行数超过 5000"、"records 须为 1~500 条"）。
- 不改代码、仅测试固化的规则：半数分母（`B/resolutions/services.py:73-76`，`result.denominator` 已写入）、任期开始日（`B/committee/views.py:67`）、报销发生日期/备用金核销日期/核销 50 张（`B/claims/views.py:95,123,151`）、重复申请（`B/residency/views.py:79,186`）、模板示例 6 行（`B/registry/import_spec.py:42-49`）。具体用例见 MOD-086。
- 外部依赖：无。

---

### MOD-081 E2E 夹具命令

**职责**：为 GROUP_D 本地 E2E 与 E2 部署后 HTTP E2E 创建/清理 `e2e_` 数据；不改 `RegistryUnit`/`RegistryOwner`/`RegistryPhone`。

**文件**：`B/jobs/management/commands/e2e_fixture.py`（命令入口，沿用 `create_admin.py`、`run_due_jobs.py` 所在目录）、`B/jobs/e2e_fixture.py`（创建/清理逻辑，便于单测直接调用）。

#### IFC-278：CLI `python manage.py e2e_fixture {setup|status|cleanup}`

```python
class Command(BaseCommand):
    help: str
    def add_arguments(self, parser: CommandParser) -> None: ...
    # 子命令 action: Literal["setup", "status", "cleanup"]
    #   setup:   --units INT(默认 3，范围 3~10)  --bulk-users INT(默认 0，范围 0~60)
    #            --bulk-resolutions INT(默认 0，范围 0~60)
    #   status:  无参数
    #   cleanup: --execute（缺省为 dry-run，只列出将删除的行数）
    def handle(self, *args, **options) -> None: ...

# B/jobs/e2e_fixture.py
E2E_PREFIX: str = "e2e_"
E2E_PHONE_PREFIX: str = "1990000"                 # 预留号段，后 4 位序号
class SetupReport(TypedDict):
    accounts: list[dict[str, object]]             # {key, kind: "member"|"admin", account_no|username, nickname, phone_masked, roles}
    units: list[dict[str, object]]                # {key: "U1"|"U2"|"U3", unit_id, specific_part}
    flows: list[dict[str, object]]                # {id, scope, name}
    registry_counts: dict[str, int]               # RegistryUnit/RegistryOwner/RegistryPhone 行数
def setup(*, units: int, bulk_users: int, bulk_resolutions: int, password: str) -> SetupReport: ...
def status() -> dict[str, object]: ...            # 现存 e2e 数据计数 + registry_counts + claim.amount_max 当前值
def cleanup(*, execute: bool) -> dict[str, object]: ...
```

- **鉴权/护栏**（命令行入口，无 HTTP）：必须设置环境变量 `OCAP_E2E_FIXTURE=1`，否则 `CommandError`；`setup` 需环境变量 `OCAP_E2E_PASSWORD`（经 `validate_password`，`B/accounts/services.py` 现有密码规则），不接受命令行明文密码、不输出密码、不写文件；输出为 stdout JSON（`SetupReport`，手机号一律 `mask_phone`）。
- **输入校验**：`--units` 非整数或超范围、`--bulk-*` 超范围 → `CommandError`（退出码 1）；可选单元不足（无有效房屋关系的住宅类 `unit_type="RESIDENCE"` 专有部分少于 `--units`）→ `CommandError`；预留号段已有未归属 `e2e_` 的用户占用 → `CommandError`。
- **选房规则**：只读查询 `RegistryUnit`：按 id 升序，取前 `--units` 条满足"无任何有效 `Membership`（`ended_at is null`）、无 PENDING 申诉/同住人申请、`unit_type == "RESIDENCE"`"的专有部分，记为 U1、U2、U3 …；**不写** `RegistryUnit` 及其业主、手机号表。
- **创建的数据（全部带 `e2e_` 标识）**：

| key | 类型 | 标识 | 关系 / 用途 |
|---|---|---|---|
| e2e_admin | `AdminAccount` | username `e2e_admin` | 管理端操作：申诉审核、用户搜索、版式模板、清册预检（`dry_run`） |
| e2e_owner_a | `User` | 昵称 `e2e_owner_a`，手机 `1990000 0001` | U1 户主（`Membership` role `HEAD`，`source="APPEAL"`） |
| e2e_owner_b | `User` | 昵称 `e2e_owner_b`，`…0002` | U1 产权业主（role `OWNER`） |
| e2e_resident | `User` | `e2e_resident`，`…0003` | U1 同住人（role `RESIDENT`，`source="APPLICATION"`） |
| e2e_applicant | `User` | `e2e_applicant`，`…0004` | 无房屋；同住人申请/申诉的申请人 |
| e2e_guest | `User` | `e2e_guest`，`…0005` | 游客；非成员权限断言 |
| e2e_other_head | `User` | `e2e_other_head`，`…0006` | U2 户主（"其他房屋的户主"） |
| e2e_multi | `User` | `e2e_multi`，`…0007` | U3 户主 + U2 同住人（AC-157-01 多房屋身份） |
| e2e_member | `User` + `Seat` | `e2e_member`，`…0008` | U3 产权业主 + 委员席位（发起报销/备用金、可见待办） |
| e2e_member2 | `User` + `Seat` | `e2e_member2`，`…0009` | U3 产权业主 + 委员席位（审批人） |
| e2e_rep | `User` + `Seat` | `e2e_rep`，`…0010` | U2 产权业主 + 业主代表席位（AC-154-03） |
| e2e_flow_expense | `ApprovalFlow`+`FlowApprover` | name `e2e_flow_expense`，scope `EXPENSE`，`DESIGNATED`，审批人 `e2e_member2` | 报销/备用金发起前置 |
| e2e_flow_resolution | 同上 | scope `RESOLUTION` | 决议发起前置（可选） |
| e2e_bulk_NN | `User` | 昵称 `e2e_bulk_NN`，`…1001+` | `--bulk-users`：使注册用户总数超过 20（AC-160-01） |
| e2e_决议NN | `Resolution` | `title` 以 `e2e_` 开头，`initiator=e2e_member`，`status="APPROVED"`，`approval_mode="DESIGNATED"` | `--bulk-resolutions`：使公开决议总数超过 20（AC-161-01）；仅此一类直接写决议行 |

  - 席位：`Seat(position, term_start=今天, term_end=今天+12 个月, status="ACTIVE", granted_by_admin_id=<e2e_admin id>)`，不经过人数上限校验；`Membership`/`Seat` 仅为 `e2e_` 用户创建；`Membership.source` 取 `"APPEAL"`/`"APPLICATION"`（≤ 12 字符，M-SA-006）。
  - `account_no` 沿用 `accounts/services._new_account_no` 的生成方式；密码均取自 `OCAP_E2E_PASSWORD`（哈希存储）。
  - 幂等：`setup` 重复执行时已存在的 `e2e_` 行不重复创建、不重置密码（需重置请先 `cleanup`）。
- **cleanup 规则**：
  - 只删除同时满足 "昵称以 `e2e_` 开头 且 手机号以 `1990000` 开头" 的 `User`、`username` 以 `e2e_` 开头的 `AdminAccount`、`name` 以 `e2e_` 开头的 `ApprovalFlow`、`name` 以 `e2e_` 开头且 `created_by_admin_id` 为 e2e 管理员的 `StyleTemplate`、标题以 `e2e_` 开头且 `initiator` 为 e2e 用户的 `Resolution`；任一待删行不满足双条件即中止并报错。
  - 删除顺序（先依赖后主体，避开 `PROTECT` 外键：`Claim.submitter`、`ApprovalInstance.submitter`、`ApprovalAction.actor`、`IncomeSheet.submitted_by`、`Poll.creator`、`Resolution.initiator`）：`AuthToken` → 附件（`owner` 为 e2e 用户）→ `ApprovalAction`/`ApprovalInstance`（`submitter` 为 e2e 用户）→ `Claim`（`submitter`）→ `IncomeSheet`（`submitted_by`）→ `Poll`（`creator`）→ `Vote`/`Resolution` → `Appeal`/`ResidentApplication`/`Membership`/`Seat` → `FlowApprover`/`ApprovalFlow` → `StyleTemplate` → `User` → `AdminAccount`。分批（每批 ≤ 200 行）。
  - **不删除**：`AuditLog`（审计保留）；任何 `RegistryUnit`/`RegistryOwner`/`RegistryPhone`；`SystemConfig` 行。
  - 账本保护：若存在 `source_type` 为 `claim`/`income_record` 且来源行属于 e2e 用户的 `LedgerEntry`（即 e2e 用例把申请推进到了审批通过），退出码 2 并列出，**不删除任何数据**，由 E2 人工处理（因账本分录会影响真实季度/年度报表）。E2E 用例因此约定：不得把 e2e 报销/备用金/收入表推进到审批通过。
  - 清理后 `status` 应显示 e2e 计数全 0、`registry_counts` 与 `setup` 报告一致。
- 副作用提示：夹具占用 U1 ~ U3 的"户主"槽位（`head_slot`），期间真实业主认证这些房屋只能成为产权业主；清理后恢复。委员席位期间计入"在任人数"（半数分母），故默认仅 2 名委员。

---

### MOD-082 Web 公共件

**文件**：

- `W/shared/labels.js`（新建）：

```ts
export const ROLE_LABELS: Record<'HEAD' | 'OWNER' | 'RESIDENT', string>            // 户主 / 产权业主 / 同住人
export const POSITION_LABELS: Record<'CHAIR' | 'VICE_CHAIR' | 'MEMBER' | 'REPRESENTATIVE', string>
export const IDENTITY_LABELS: Record<IdentityCode, string>                         // 含 GUEST → 游客
export const APPLICATION_STATUS_LABELS: Record<'PENDING' | 'APPROVED' | 'REJECTED' | 'CLOSED', string>
//   申请：待审批 / 已通过 / 已拒绝 / 已关闭（申请人已注销）；申诉：待审核 / 已通过 / 已驳回 / 已关闭（申请人已注销）→ 由 kind 区分
export function statusLabel(kind: 'application' | 'appeal' | 'poll' | 'seat' | 'account', code: string): string
export function yesNo(value: boolean | null | undefined): '是' | '否' | ''
```

  键集合与 `M/utils/labels.js` 一致（测试守护，ADR-092）。
- `W/shared/confirm.js`（新建）：

```ts
export type ConfirmKey = 'revokeMembership' | 'revokeSeat' | 'deleteUnit' | 'deleteFlow' | 'voidIncome'
  | 'withdrawResolution' | 'withdrawClaim' | 'withdrawIncome' | 'removeResident' | 'leaveUnit' | 'cancelAccount'
export function confirmDanger(key: ConfirmKey, vars?: Record<string, string>): Promise<boolean>
//   内部 ElMessageBox.confirm；取消/关闭 → resolve(false)；确认 → resolve(true)。后果文案按 key 固定；cancelAccount 列出 4 项（户主身份将由他人接任、业委会席位失效、待处理的申请与申诉被关闭、账号不可恢复）
```

- `W/shared/usePaging.js`（新建）：

```ts
export function usePaging<T, F extends object>(opts: {
  fetch: (params: F & { page: number; page_size: number }) => Promise<{ count: number; results: T[] } | T[]>
  filters?: Ref<F>
  pageSize?: number            // 默认 20，范围 1~100
}): { items: Ref<T[]>; total: Ref<number>; page: Ref<number>; pageSize: Ref<number>; loading: Ref<boolean>;
      reload(): Promise<void>; goto(page: number): Promise<void>; resetAndLoad(): Promise<void> }
// 返回数组（旧接口）时 total = 数组长度；筛选变化调用 resetAndLoad() 回到第 1 页；翻页保持 filters
```

- `W/portal/parts/UnitCascader.vue`（新建）：Props `{ modelValue: number | null }`；Emits `update:modelValue`、`change: { unit_id: number; specific_part: string; label: string }`；内部调用 `unitApi.options`（`GET /units/options`），逻辑自 `W/portal/Units.vue:60-170` 抽出，含"跳过空层级/未划分"提示；无任何内部编号输入框（AC-150-01）。
- `W/portal/parts/AuthImage.vue`（新建）：Props `{ src: string | null; alt?: string; size?: number }`；`src` 形如 `/api/v1/attachments/<uuid>/download`，经 `attachmentApi.download` 取 blob → `URL.createObjectURL`，卸载与 `src` 变化时 `revokeObjectURL`；取不到时显示占位。
- `W/shared/format.js`（修改）：沿用 `formatDateTime`（`:11-14`）；新增 `export function moneyText(value: string | number | null): string`（两位小数展示，非必要不改现有函数）。
- `W/stores/auth.js`（修改）：新增 getter `identitySummary: (s) => s.me?.identities?.summary ?? { code: 'GUEST', label: '游客' }`；`isCommittee` 保持（读 `committee.position`，由 IFC-262 保证与接口权限一致）。
- `W/shared/api.js`（修改）→ IFC-281。

#### IFC-279：Web 工具函数契约（上述 labels / confirm / usePaging / format）
#### IFC-280：Web 组件契约（UnitCascader / AuthImage / UserPicker，签名见本节与 MOD-084）

#### IFC-281：`W/shared/api.js` 变更（画像 P6，与 IFC-283 同步）

```ts
// meApi 增加
housing: () => get('/me/housing')                                   // GET /me/housing → HousingResponse
limits: () => get('/system/limits')                                 // GET /system/limits → SystemLimits   （放在 meApi 或新 limitsApi）
// attachmentApi 增加
download: (id: string) => http.get(`/attachments/${id}/download`, { responseType: 'blob' })   // 返回 Blob
// admin 增加（管理端令牌）
systemConfigAll: () => adminHttp.get('/admin/system-config')        // GET → { 'audit.retention_months': number, 'claim.amount_max': string }
// 既有函数改为可带分页参数（签名兼容）：
admin.seats: (params?) => adminHttp.get('/admin/committee/seats', { params })
approvalApi.tasks: (scope, params?) => get('/approval/tasks', { scope, ...params })
// 既有、本批开始被页面使用（无需改签名）：
unitApi.myAppeals / myResidentApplications / residentApplicationsToReview / decideResidentApplication / removeResident / leaveUnit / createResidentApplication
admin.styleTemplates / createStyleTemplate / updateStyleTemplate / deleteStyleTemplate
admin.users({ q, page, page_size })                                  // 用户选择器与账号页翻页
```

- 契约守护约束（`test_frontend_contract.py:30-97`，M-SA-007）：路径为字面量或模板字符串，不带 `?`；`admin.*` 调用的视图只能是 `IsAdmin` 族，用户端调用的只能是 `IsMember`/`IsCommitteeMember`/`IsIncomeMember`/`IsChairOrVice`；`download` 的 `GET /attachments/<id>/download` 为 `IsMemberOrAdmin`，对用户端令牌成立。
- `GET /me/housing`、`GET /system/limits` 在后端均已登记（IFC-261、IFC-272），契约测试可解析。

#### IFC-282：Web 入口可见性（`auth.isCommittee`、`auth.identitySummary`）见上。

- 外部依赖：Element Plus（既有）、axios（既有，`W/shared/http.js`）。

---

### MOD-083 Web 用户端页面

逐文件改动（均修改现有文件）：

| 文件 | 改动 | REQ / US |
|---|---|---|
| `W/portal/Units.vue` | 重写页面结构：①"我的身份与房屋"（汇总身份 + 房屋列表：房屋名、身份中文名；产权业主展开同住人名单与"移除"，同住人显示"退出"）；②"待我审批的同住人申请"（数量徽标，通过/拒绝）；③"选择房屋"（`UnitCascader`），其下三个动作：认证、提交申诉、申请成为同住人；④"我的同住人申请"（`myResidentApplications`）；⑤"我的申诉"（`myAppeals`，已驳回显示原因）。删除手输"专有部分 ID"与"说明"输入框（`:41`）；认证成功提示用 `ROLE_LABELS`（`:175`）。移除/退出经 `confirmDanger('removeResident'|'leaveUnit')`。无申请/申诉时显示"暂无同住人申请"/"暂无申诉" | REQ-FUNC-142 ~ 145/148/149/150/158；US-150 ~ 153/156/157 |
| `W/portal/Home.vue` | 对产权业主（`auth.me.identities.units` 含 HEAD/OWNER）请求 `meApi.housing()`，在首页显示"待审批同住人申请：N"并链接到 `/units#review`；无待审则不显示；失败静默（`catch` 后不显示，不影响首页其他区块与既有测试 mock）；`quick` 中"待办""报销/备用金"仅 `auth.isCommittee` 显示；"当前身份"显示 `identitySummary.label` | REQ-FUNC-143/146/149/157；US-151/154/166 |
| `W/portal/PortalLayout.vue` | `navItems` 中"报销/备用金""待办"仅 `auth.isCommittee`（`:36-45`） | REQ-FUNC-146/157；US-154/166 |
| `W/portal/Me.vue` | 新增"身份"卡（汇总身份 + 逐房屋身份，数据取 `auth.me` 与 `meApi.housing()`）；资料卡增加生日（`el-date-picker`，`value-format="YYYY-MM-DD"`，可空）；头像用 `AuthImage` 显示、上传前提示"jpg/png，不超过 2 MB"、`accept=".jpg,.jpeg,.png"` 并在前端预校验大小；"注销"前调用 `confirmDanger('cancelAccount')`（`:235`）；"常用入口"按身份显示 | REQ-FUNC-149/150/156/157；US-157/158/165/166 |
| `W/portal/Claims.vue` | "新建申请"按钮对非成员隐藏（`:7`，`v-if="auth.isCommittee"`）；撤回前 `confirmDanger('withdrawClaim')`（`:303`）；列表接入 `usePaging`；金额输入处显示 `limits.claim_amount_max` 提示 | REQ-FUNC-146/150/152/161；US-154/158/161/170 |
| `W/portal/Login.vue` | 密码框占位符改为"账号或手机号"（`:16`） | REQ-FUNC-154；US-163 |
| `W/portal/Polls.vue`、`PollDetail.vue` | 发起表单顶部显示"最多 {poll_max_questions} 道题；单选/多选题选项 {min} ~ {max} 个；表决窗口不少于 {vote_min_window_minutes} 分钟"（取自 `/system/limits`）；状态与截止时间用 `statusLabel`/`formatDateTime`（`:15`）；列表接入 `usePaging` | REQ-FUNC-152/158/163；US-161/167/172 |
| `W/portal/Resolutions.vue`、`ResolutionDetail.vue` | 列表 `usePaging`；撤回前 `confirmDanger('withdrawResolution')`（`ResolutionDetail.vue:95`）；发起半数同意决议处显示最短窗口提示 | REQ-FUNC-150/152/163 |
| `W/portal/Income.vue` | 列表 `usePaging`；作废、撤回前 `confirmDanger('voidIncome'|'withdrawIncome')`（`:180`）；导入/录入处显示行数/条数与金额上限提示 | REQ-FUNC-150/152/161/164 |
| `W/portal/Reports.vue` | 列表 `usePaging`；报表详情增加明细表（日期、类型 `entry_type`、方向、金额；不显示 `summary`），与合计相等 | REQ-FUNC-152/159；US-161/168 |
| `W/portal/Tasks.vue` | 列表 `usePaging`（后端已内存分页） | REQ-FUNC-152；US-161 |
| `W/portal/InfoDetail.vue` | `infoApi.detail` 失败（404 或任意错误）→ 显示"内容不存在或已下线"与"返回列表"链接（`router-link` 到 `/info`）；不得空白（`:28-33`） | REQ-FUNC-160；US-169 |

- 约束：不得在 `portal/**/*.vue` 出现 `data-theme`、风格 key 字面量或 `current ===` 比较（`frontend/tests/ui_blocks.spec.js:98` 守护）；新增 `portal/parts/` 子目录组件同样遵守；`portal/` 顶层 `.vue` 文件数与路由 import 数不变（`qa_unit_theme.spec.js:273` 的 17 保持）。
- 依赖：MOD-082（公共件）、IFC-261/262/263/264/265/266/271/272。

---

### MOD-084 Web 管理端页面

| 文件 | 改动 | REQ / US |
|---|---|---|
| `W/admin/parts/UserPicker.vue`（新建） | Props `{ modelValue: number \| null; placeholder?: string }`；Emits `update:modelValue`、`change: AdminUserCandidate \| null`；输入关键词（≤ 32 字符，防抖）→ `admin.users({ q, page, page_size: 10 })`；候选项显示 `nickname`、`real_names`（有则）、`account_no`、`phone`（后端已脱敏）、`identity_label`；无匹配显示"无匹配用户"；超过一页可翻页；选中后以所选对象渲染"昵称 + 身份"供确认；页面不含"用户 ID"输入框 | REQ-FUNC-151；US-159 |
| `W/admin/AdminSeats.vue` | 赋予席位对话框用 `UserPicker` 替换手输 `form.user_id`（`:40`）；提交仍发 `user_id`；撤销前 `confirmDanger('revokeSeat')`（`:130-138`）；列表翻页（`admin.seats({page,page_size})`）；状态/启用显示中文（`:22`） | REQ-FUNC-150/151/152/158；US-158/159/160/167 |
| `W/admin/AdminFlows.vue` | 审批人用多选的 `UserPicker` 替换"逗号分隔用户 ID"（`:36`），保存时仍提交 `approver_ids: number[]`（沿用 `B/approval/views.py:28-71` 契约）；删除前 `confirmDanger('deleteFlow')`（`:88`）；列表翻页 | REQ-FUNC-150/151/152；US-158/159/160 |
| `W/admin/AdminUsers.vue` | 注册用户列表接入 `usePaging`（搜索关键词与翻页保持，`:71-81`）；状态列显示中文"启用/停用"、布尔显示"是/否"（`:11,28`） | REQ-FUNC-152/158；US-160/167 |
| `W/admin/AdminMemberships.vue` | 撤销前 `confirmDanger('revokeMembership')`（`:49-57`，后果含户主接任与席位可能失效）；列表翻页 | REQ-FUNC-150/152；US-158/160 |
| `W/admin/AdminAppeals.vue` | 列表翻页；状态显示含"已关闭（申请人已注销）"（`:45`） | REQ-FUNC-152/155；US-160/164 |
| `W/admin/AdminFinance.vue` | 列表翻页（`:43`）；新增"金额上限"配置卡：读取 `admin.systemConfigAll()`，保存调 `admin.updateSystemConfig('claim.amount_max', value)`，非法输入显示后端 `INVALID_VALUE` 文案，原值不变 | REQ-FUNC-152/161；US-160/170 |
| `W/admin/AdminRegistry.vue` | 删除专有部分前 `confirmDanger('deleteUnit')`（`:253-260`）；中文显示 | REQ-FUNC-150/158；US-158/167 |
| `W/admin/AdminStyleTemplates.vue`（新建） | "我的版式模板"页：列表（名称、被引用数、内置/自定义）、新建/改名/编辑样式项（沿用内容编辑器现有 `tokens` 项与范围：`font_family_key`、`font_size 12~24`、`line_height 1.2~2.4`、`paragraph_spacing 0~32`、`page_chars 200~20000`、五个颜色）、删除（先 `ElMessageBox` 确认；`STYLE_IN_USE` 时显示"被 N 条内容引用"）；名称为空前端先拦并提示"模板名称不能为空"；内置项无编辑/删除入口 | REQ-FUNC-153；US-162 |
| `W/admin/AdminLayout.vue` | `navItems` 追加"版式模板"（`/admin/content/styles`） | REQ-FUNC-153 |
| `W/router/index.js` | 增加 `{ path: 'content/styles', component: () => import('@/admin/AdminStyleTemplates.vue') }`（挂在 `/admin` 子路由下，`:35-49` 一带） | REQ-FUNC-153 |

- 依赖：MOD-082、IFC-267/269/270、既有 `GET /admin/users`（`ocap_user_directory/IFC-243`，旧文档编号重复，故带批次前缀）。
- 约束：`admin/**/*.vue` 不含风格专属判断（`ui_blocks.spec.js:98`）；`admin/` 路由页组件数 16 → 17（`qa_unit_theme.spec.js:273` 同步为 17）；"无默认风格/新增风格"文案扫描（`qa_unit_theme.spec.js:265-268`）不得被新页文案触发。

---

### MOD-085 小程序

#### IFC-283：`M/utils/api.js` 变更（与 IFC-281 同步）

```ts
loginByCode: (phone: string, code: string) => http.post('/auth/login/code', { phone, code, client: 'miniapp' })
loginByPassword: (identifier: string, password: string) => http.post('/auth/login/password', { identifier, password, client: 'miniapp' })
housing: () => http.get('/me/housing')
myResidentApplications: () => http.get('/resident-applications/mine')
createResidentApplication: (data: { unit_id: number }) => http.post('/resident-applications', data)
residentApplicationsToReview: () => http.get('/resident-applications/to-review')
decideResidentApplication: (id: number, decision: 'APPROVE' | 'REJECT') => http.post(`/resident-applications/${id}/decision`, { decision })
removeResident: (unitId: number, userId: number) => http.delete(`/units/${unitId}/residents/${userId}`)
leaveUnit: (unitId: number) => http.post(`/units/${unitId}/leave`, {})
myAppeals: () => http.get('/appeals/mine')
limits: () => http.get('/system/limits')
report: (id: number) => http.get(`/ledger/reports/${id}`)
reports: (params?: { page?: number; page_size?: number }) => http.get('/ledger/reports', params)
claims: (params) => http.get('/claims', params)                   // 已有，调用处补 page/page_size
polls: (params?) => http.get('/polls', params)
resolutions: (scope, params?) => http.get('/resolutions', { scope, ...params })
tasks: (params?) => http.get('/approval/tasks', params)
```

- `M/utils/http.js` 已有 `http.get/post/put/patch/delete`（`M/utils/http.js` 末尾 `export const http`），`removeResident` 直接用 `http.delete`；`http.get(url, data)` 的 `data` 即查询参数。
- 契约测试：所有调用为字面量路径、无 `?`，对应后端路由与方法均存在（`/units/<id>/residents/<id>` DELETE、`/units/<id>/leave` POST 已在 `B/residency/urls.py:19-20`）。

#### IFC-284：小程序工具与组件契约

```ts
// M/utils/labels.js：键集合与 W/shared/labels.js 一致
export function statusLabel(kind: 'application' | 'appeal' | 'poll' | 'seat' | 'account', code: string): string
// M/utils/confirm.js
export function confirmDanger(key: ConfirmKey, vars?: Record<string, string>): Promise<boolean>   // uni.showModal，后果用换行拼接
// M/utils/paging.js
export function usePaging<T>(opts: { fetch: (params: { page: number; page_size: number }) => Promise<{ count: number; results: T[] } | T[]>; pageSize?: number }):
  { items: Ref<T[]>; total: Ref<number>; hasMore: ComputedRef<boolean>; loading: Ref<boolean>; loadMore(): Promise<void>; reset(): Promise<void> }
// M/components/UnitPicker.vue：Props { modelValue: number | null }；Emits 'update:modelValue' | 'change'（同 UnitCascader）；逻辑自 M/pages/units/index.vue:5-20,43-100 抽出
```

**页面改动**：

| 文件 | 改动 | REQ / US |
|---|---|---|
| `M/pages/units/index.vue` | 用 `UnitPicker`；新增"申请成为同住人"（调用 `createResidentApplication`）、"我的同住人申请"、"我的申诉"（含驳回原因）、"待我审批"列表（通过/拒绝）、房屋列表（产权业主可移除同住人、同住人可退出；均经 `confirmDanger`）；提示"暂无同住人申请/暂无申诉" | REQ-FUNC-142 ~ 145/148/149/150；US-150 ~ 153/156/157 |
| `M/pages/index/index.vue` | 对产权业主显示"待审批同住人申请：N"并进入"我的房屋"待审批区；`quick` 中"报销"仅委员显示；待办卡片"加载更多"；身份取 `summary.label`；失败静默 | REQ-FUNC-143/146/152/157；US-151/154/161/166 |
| `M/pages/me/index.vue` | 身份显示汇总 + 房屋列表；"报销 / 备用金"按钮仅委员显示；财务报表行可点击进入 `pages/reports/detail?id=`；报表列表"加载更多" | REQ-FUNC-146/149/152/157/159；US-154/157/161/166/168 |
| `M/pages/reports/detail.vue`（新建，需在 `M/pages.json` 登记，标题"报表明细"） | `onLoad(options.id)` → `api.report(id)`；显示合计、结余及收入/支出明细（日期、类型、金额；不显示 `summary`），合计与 Web 报表详情相等；无报表显示"暂无已生成报表"由列表页承担 | REQ-FUNC-159；US-168 |
| `M/pages/claims/index.vue`、`resolutions/index.vue`、`polls/index.vue` | 列表 `usePaging`（"加载更多"、"没有更多了"、总数）；状态用 `statusLabel`；报销页对非委员不可进入时给出文案（入口已隐藏，直接进入时 403 提示"需要业委会成员身份"） | REQ-FUNC-146/152/158；US-161 |
| `M/store/auth.js` | 新增 getters `isCommittee`（读 `me.identities.committee.position`）、`identitySummary` | REQ-FUNC-146/157 |
| `M/pages.json` | 增加 `pages/reports/detail` | REQ-FUNC-159 |

- 依赖：IFC-261/262/263/264/268/271/272；`MOD-077`（登录 `client`）。
- 约束：不新增 tabBar 项（Q125 暂定 4 项不变）；小程序本批不补设密码、注销、收入表（C-44）。

---

### MOD-086 测试同步与新增（由 GROUP_D 实现，设计清单）

**位置（画像 P3）**：后端 `backend/tests/{unit,integration,e2e}/`、远程 `backend/tests/remote/`；前端 `frontend/tests/*.spec.js`；小程序 `miniprogram/tests/*.spec.js`。

**既有用例必须同步更新（P-SA-013，git grep 核实）**：

| 既有用例 | 位置 | 原因 | 更新方式 |
|---|---|---|---|
| `/me` identities 键集合 | `backend/tests/integration/test_frontend_contract.py:140`（`assertEqual(set(identities), {"is_guest","units","committee","labels"})`） | 新增 `summary` | 键集合加 `summary`；另断言 `units[*].role_label` |
| 管理端路由页组件数 | `frontend/tests/qa_unit_theme.spec.js:273`（`admin/` 数 16） | 新增 `AdminStyleTemplates` 路由页 | 16 → 17，注释"16 页 + AdminLayout" |
| TC-INT-311 | `backend/tests/integration/test_registry_import_xlsx_defects.py:118` | US-175 AC-175-03 | 期望 `(6, 0)` 且新增专有部分 4 个（已知基线失败，改后应通过） |
| 非成员发起报销/备用金的既有用例 | `backend/tests/e2e/test_journeys.py`、`test_rework_journeys.py`、`integration/test_finance_polls_api.py`、`test_gap_must_have.py`、`test_rework_cr011_024.py`、`test_frontend_contract.py`（共 16 处 `claims/reimbursements|advances`） | 创建视图改 `IsCommitteeMember` | GROUP_C 逐处复核：发起人须有有效委员席位（`make_seat`）；以非成员发起的断言改为 403 |
| 报表详情 `detail[*].summary` | `backend/tests/` 内对 `/ledger/reports/<id>` 的断言（`git grep '"detail"' backend/tests` 以实跑为准） | ADR-091 脱敏 | 支出行 `summary` 期望 `null` |
| 小程序登录请求体 | `miniprogram/tests/api.spec.js:78,80` | ADR-083 请求体加 `client` | 断言 `{ ..., client: 'miniapp' }` |
| Web 页面挂载用例 | `frontend/tests/pages.spec.js`（Home、Claims、Me）、`ui_blocks.spec.js`（Home、Claims，`openCreate`）、`qa_int_theme.spec.js:241`（PortalLayout） | 新增 `/me/housing`、`/system/limits` 请求；入口按身份显示 | mock 路由表补默认返回；页面对未登记路由须容错；`ME` 夹具补 `committee`/`summary` |
| 小程序页面用例 | `miniprogram/tests/pages.spec.js`、`qa_e2e_*.spec.js` | units/me/index 页面结构改动 | 对应更新 |

**新增用例（文件命名，按需求 AC 逐条，GROUP_D 自行细化）**：

- `backend/tests/unit/test_product_review_rules.py`：`validate_amount_max`（正数/两位小数/上限/非法）、`_parse_amount`/`_parse_rows` 带 `limit`、`identity_view` 与 `identity_labels` 一致性（多户取最高、过期席位）、`_session_kind`（`client`）、`PendingRequestService`（只关闭 PENDING）、`current_limits`、`labels` 键集合（Python 侧读取前端文件，沿用 `test_frontend_contract.py` 做法）。
- `backend/tests/integration/test_product_review_api.py`：`/me/housing`（产权业主/同住人/游客；residents 仅产权业主；待审数量；固定查询数）、`/me` 增量字段、申请/申诉 `CLOSED` 与 `ALREADY_CLOSED`、注销关闭与审计条数（AC-164-01 ~ 04）、报销/备用金 403/201（含业主代表、到期席位）、金额上限默认与修改（AC-170-01 ~ 05，含非管理员 403、非法值）、`/system/limits`、小程序 `client` 的 7 天（用 `authenticate_token(now=…)`，AC-155-02）与 Web/管理端不变（AC-155-03）、版式模板（引用禁删 409、内置不可寻址 404、`id`/`usage_count`）、报表脱敏、REQ-FUNC-162 ~ 165 的边界（AC-171-01 ~ 03、172-02 ~ 04、173-01/02、174-01 ~ 05）。
- `backend/tests/integration/test_e2e_fixture_command.py`：`setup` 幂等、不改 `RegistryUnit/Owner/Phone` 行数、`cleanup` dry-run 与 `--execute`、双条件护栏、账本保护退出码 2、未设 `OCAP_E2E_FIXTURE` 拒绝。
- `backend/tests/e2e/test_product_review_journeys.py`：本地旅程（同住人申请 → 审批 → 移除/退出；申诉 → 驳回 → 用户可见原因；注销自动关闭；多房屋身份与管理端一致 AC-157-04；用户搜索与席位赋予 AC-159-01/03/05/06；模板 CRUD AC-162-01 ~ 06；分页 N > 20 AC-160/161）。
- `backend/tests/integration/test_frontend_contract.py`（追加，字段级）：`/me/housing`、`/resident-applications/mine`、`/appeals/mine`、`/system/limits`、`style-templates` 列表的前端读取字段名与后端一致；新增前端调用均能解析（AC-178-02）。
- `backend/tests/integration/test_requirements_numbering.py`（新增，文档类）：扫描全仓 `project_workspace/*/requirements` 的 REQ/US/AC 定义行重复数 = 0；user_directory 对照表条目数（AC-176-01/02）；被注记条目的原文保留（AC-177，按行数）。
- `frontend/tests/product_review_*.spec.js`：`labels`/`confirm`/`usePaging` 单测；`UnitCascader`（无内部编号输入框）、`UserPicker`、`AuthImage`；Units/Me/Home/Claims/PortalLayout/InfoDetail/Login 页面渲染与入口可见性；各确认弹窗"取消不发请求"；`AdminStyleTemplates`；`labels` 与小程序键集合一致。
- `miniprogram/tests/product_review_*.spec.js`：`api` 新增函数的路径/方法/请求体；`paging` 加载更多；`labels`；units/me/index/reports 页面。
- `backend/tests/remote/`（HTTP E2E，P4-1）：见下节。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-142 | US-150 | MOD-082（UnitCascader）、MOD-083、MOD-085 |
| REQ-FUNC-143 | US-151 | MOD-074（IFC-261）、MOD-083、MOD-085 |
| REQ-FUNC-144 | US-152 | MOD-075（IFC-263）、MOD-083、MOD-085 |
| REQ-FUNC-145 | US-153 | MOD-074（IFC-261 residents）、MOD-082（confirm）、MOD-083、MOD-085 |
| REQ-FUNC-146 | US-154 | MOD-076（IFC-265）、MOD-074（IFC-262 任期口径）、MOD-083、MOD-085 |
| REQ-FUNC-147 | US-155 | MOD-077（IFC-268）、MOD-085（IFC-283） |
| REQ-FUNC-148 | US-156 | MOD-075（IFC-263）、MOD-083、MOD-085 |
| REQ-FUNC-149 | US-157 | MOD-074（IFC-261/262/274）、MOD-083、MOD-085 |
| REQ-FUNC-150 | US-158（并见 US-153、US-164） | MOD-082（confirm）、MOD-083、MOD-084、MOD-085 |
| REQ-FUNC-151 | US-159 | MOD-084（UserPicker，复用 `ocap_user_directory/IFC-243`）、MOD-082 |
| REQ-FUNC-152 | US-160、US-161 | MOD-082（usePaging）、MOD-083、MOD-084、MOD-085 |
| REQ-FUNC-153 | US-162 | MOD-078（IFC-269/270）、MOD-084 |
| REQ-FUNC-154 | US-163 | MOD-083（Login.vue） |
| REQ-FUNC-155 | US-164 | MOD-075（IFC-277、IFC-264） |
| REQ-FUNC-156 | US-165 | MOD-082（AuthImage）、MOD-083（Me.vue） |
| REQ-FUNC-157 | US-166 | MOD-074（IFC-262）、MOD-082（auth store）、MOD-083、MOD-085 |
| REQ-FUNC-158 | US-167 | MOD-082（labels）、MOD-083、MOD-084 |
| REQ-FUNC-159 | US-168 | MOD-079（IFC-271）、MOD-083（Reports）、MOD-085（reports/detail） |
| REQ-FUNC-160 | US-169 | MOD-083（InfoDetail.vue） |
| REQ-FUNC-161 | US-170 | MOD-076（IFC-265/266/267/272）、MOD-084（AdminFinance 配置卡）、MOD-083（提示） |
| REQ-FUNC-162 | US-171 | MOD-080（现状固化 + 测试） |
| REQ-FUNC-163 | US-172 | MOD-076（IFC-272）、MOD-080、MOD-083（发起提示） |
| REQ-FUNC-164 | US-173 | MOD-080、MOD-076（IFC-272）、MOD-083（Income 提示） |
| REQ-FUNC-165 | US-174 | MOD-080（现状固化 + 测试） |
| REQ-FUNC-166 | US-175 | MOD-080、MOD-086（TC-INT-311 更新） |
| REQ-NFUNC-026 | US-176 | 文档已由 GROUP_A 交付；MOD-086（编号扫描用例） |
| REQ-NFUNC-027 | US-177 | 文档已由 GROUP_A 交付；MOD-086（注记扫描用例） |
| REQ-NFUNC-028 | US-178 | MOD-086（零回归、字段级契约、IFC-281/283 同步）；所有 MOD 的"只增不改"约束 |

## 依赖关系

- MOD-083 → MOD-082（调用 IFC-279/280/281/282）；MOD-083 → MOD-074（IFC-261、262）；MOD-083 → MOD-075（IFC-263、264）；MOD-083 → MOD-076（IFC-265、266、272）；MOD-083 → MOD-079（IFC-271）
- MOD-084 → MOD-082；MOD-084 → MOD-076（IFC-267）；MOD-084 → MOD-078（IFC-269、270）；MOD-084 → 既有 `ocap_user_directory/IFC-243`
- MOD-085 → MOD-074（IFC-261、262）、MOD-075（IFC-263）、MOD-076（IFC-272）、MOD-077（IFC-268）、MOD-079（IFC-271）
- MOD-082 → MOD-074 ~ MOD-079（仅经 IFC-281 的 HTTP 路径，无代码依赖）
- MOD-074 → 既有 `accounts.directory`、`residency`、`committee`（`residency.housing → accounts.directory → residency.models/committee.models`；`committee.services` 延迟导入 `residency.services`，不导入 `accounts`）
- MOD-075 → 既有 `core.audit`；`identity.services.cancel → residency.services.PendingRequestService`（`identity` 已依赖 `residency`，方向不变）
- MOD-076 → 既有 `committee.services`、`core.config`；MOD-080 → MOD-076（`core.limits`）
- MOD-077 → 既有 `core.config`；MOD-079 → 既有 `core.config`；MOD-078 → 既有 `content.models`
- MOD-081 → 既有各 app 模型（`registry` 仅读）；无其他模块依赖 MOD-081
- MOD-086 → 全部（测试依赖产品代码，无反向依赖）
- 已检查：无循环依赖（模块级与 Python 导入级）。

## 数据迁移

| 项 | 内容 |
|---|---|
| 新字段/表/索引 | **无**。仅 `residency.Appeal.status` 与 `residency.ResidentApplication.status` 的 `choices` 追加 `CLOSED` |
| 迁移文件 | `backend/apps/residency/migrations/0002_closed_status.py`，手写、单 app（residency）、依赖 `0001_initial`；文件头注明"手写迁移（画像 P6）"，不含 "Generated by Django"；不使用 `makemigrations` 产物，不在目标机生成（画像 P6、P8） |
| 迁移方式 | `operations = [AlterField, AlterField]`；MySQL 与 SQLite 上均为无 SQL 的元数据变更（`choices` 不进 DB）；`makemigrations --check --dry-run` 应为"No changes"（用 Django 5.2.x，不得用 6.x，画像 P4） |
| 是否可逆 | 可逆（AlterField 反向即还原 choices，无数据转换）；回滚代码前须确认库中无 `status='CLOSED'` 行，否则旧代码不识别该值（仅影响显示，不影响约束，因 `pending_slot` 已为 NULL） |
| 数据风险 | 无存量数据改写；**不触碰 5742 条清册（RegistryUnit/RegistryOwner/RegistryPhone）与任何现有账号数据**。`SystemConfig` 的 `claim.amount_max` 行在管理员首次保存时才创建（非迁移）；E2E 夹具写入的 `e2e_` 数据由 `cleanup` 清除 |
| 测试库 | 测试以 `MIGRATION_MODULES` 置空运行（画像 P4），迁移文件不被测试执行；GROUP_D 需另以 `manage.py migrate` 在 SQLite 临时库验证一次迁移可正向/反向执行（不连测试机） |

## 受影响的运行单元 / 构建

| 运行单元 | 变更 | 操作 |
|---|---|---|
| `ocap-backend`（gunicorn 127.0.0.1:9000，systemd） | 代码变更（residency/identity/committee/claims/income/core/accounts/content/ledger/jobs）；迁移 residency 0002 | 发布代码 → `python manage.py migrate` → 重启服务 |
| `ocap-run-due-jobs.timer` 触发的 `run_due_jobs` | 无逻辑变更 | 无需操作（下次触发自动使用新代码；`judge_if_due` 行为不变） |
| `ocap-content-worker` | `content/styles.py`、`views_admin.py` 有改动，worker 不依赖其新行为 | 建议随后端一并重启（非必须） |
| Web 前端静态资源 | 用户端与管理端页面、公共件、路由 | `cd frontend && npm run build -- --base=/ocap/` → 发布静态文件（沿用 ocap-deploy skill） |
| 微信小程序包 | 新页面、组件、api.js、pages.json | `cd miniprogram` 重新构建；提交体验版/审核属人工步骤（不由部署自动化执行） |
| E2E 夹具 | 新增管理命令，仅 E2 在测试机、设置 `OCAP_E2E_FIXTURE=1` 后执行 | 部署后 `setup` → HTTP E2E → `cleanup --execute`；不常驻 |
| 数据库 | residency 0002（仅 choices） | 随 `migrate` |
| nginx / Freeark 服务 | 无 | 不触碰（画像 P7、P8） |
| CI（GitHub Actions） | 无工作流改动；新增测试文件被现有命令收集（`tests/remote/` 用例文件不匹配 `test*.py`，默认不收集） | 无 |

## E2E 可测性（供 GROUP_D 本地 E2E 与部署后 HTTP E2E，画像 P4-1）

**原则**：本地 E2E 用 `backend/tests/support.py` 的工厂（`make_owner`、`make_admin`、`make_unit`、`make_seat`、`make_flow`，`backend/tests/support.py:60-160`）造数据，可操控时钟与数据量；部署后 HTTP E2E 只经 `https://ai-freeark.xin/ocap/` 公开入口，只用 MOD-081 创建的 `e2e_` 账号，不直连数据库、不 SSH，测试代码放 `backend/tests/remote/`。

**远程测试的组织**（只给形态，GROUP_D 细化）：

- 文件命名 `remote_*.py`（不匹配默认的 `test*.py`，默认测试命令不收集）；入口命令形态：`python manage.py test tests.remote --pattern="remote_*.py"`，必须由环境变量 `OCAP_E2E_BASE_URL`（缺省拒绝运行）、`OCAP_E2E_PASSWORD` 驱动；HTTP 客户端用 `requests`（已在 `backend/requirements.txt` 中，无新依赖）。
- 登录：`e2e_*` 用户用账号密码登录（`POST /auth/login/password`，`identifier` 为夹具报告中的 `account_no`），管理员 `POST /admin/auth/login`；不走短信（console 替身）。
- 每个远程用例自己创建的数据（申请、申诉、模板）名称带 `e2e_` 前缀，测完自行删除/由 `cleanup` 兜底。

**故事 → 夹具账号映射（远程 E2E）**：

| 故事 AC（[E2E]） | 使用的夹具 | 说明 |
|---|---|---|
| AC-150-01/02/03、152-01/02/03 | `e2e_applicant` 申请 U1（有产权业主）；U 无产权业主的场景用"第 4 个空闲房屋"（`--units 4`，不建立 Membership） | 房屋选择走 `GET /units/options` 逐级到 U1；不手输 ID |
| AC-151-01/02/03 | `e2e_owner_a`/`e2e_owner_b`（U1 产权业主）、`e2e_resident`（反例） | 申请人为 `e2e_applicant` 与第二个申请人（`e2e_bulk_*` 或 `e2e_guest`） |
| AC-153-01/02/03 | `e2e_owner_a` 移除 `e2e_resident`；`e2e_resident` 退出；反例 `e2e_other_head`、`e2e_admin` | 每次操作后用 `e2e_resident` 重新加入需重建：远程用例先通过申请/审批流程重新建立同住人关系，或夹具提供第二个同住人 `e2e_multi`（U2 同住人） |
| AC-154-01/02/03 | 403：`e2e_guest`、`e2e_owner_a`、`e2e_rep`；201：`e2e_member`（流程 `e2e_flow_expense`） | **不得推进到审批通过**（避免账本分录）；用例结束 `withdraw` |
| AC-155-01 | `e2e_applicant` 以 `client: "miniapp"` 登录后等待 31 分钟再请求 | 慢用例，单列为 `slow`，默认不跑；本地用时钟控制代替（AC-155-02） |
| AC-156-01 ~ 04 | `e2e_applicant` 提交申诉（附件经 `POST /attachments` 上传 `e2e_` 文件），`e2e_admin` 驳回/通过 | 通过后 `e2e_applicant` 获得 U1 关系（只写 `Membership`，不改清册） |
| AC-157-01/03/04 | `e2e_multi`（U3 户主 + U2 同住人）、`e2e_guest`；管理员 `GET /admin/users?q=` 对照 | 汇总身份两端一致 |
| AC-158-02 | `e2e_admin` 撤销 `e2e_owner_b` 在 U1 的认证 | 仅对 `e2e_` 用户；撤销后需重建，放在同类用例末尾 |
| AC-159-01/03/05/06 | `e2e_admin` 搜索 `e2e_owner_a`（账号、手机号后四位 `0001`、清册实名：夹具用户无清册实名，实名搜索在远程用例中**不测**，本地测） | 非管理员 `e2e_guest` 请求得 403 |
| AC-160-01/02 | `--bulk-users 25` 使注册用户总数 > 20；管理员翻页核对 `count` 与各页合计 | 若真实用户已很多，也满足 |
| AC-161-01/04 | `--bulk-resolutions 25`；`e2e_guest` 翻页 | 决议为 `e2e_` 前缀，清理时删除 |
| AC-162-01 ~ 06 | `e2e_admin`；模板名 `e2e_模板A/B`；被引用场景需内容：用 `e2e_admin` 创建内容草稿 `e2e_内容`（`POST /admin/content/posts`）引用模板，测完删除内容 | 内置不可寻址：`PUT/DELETE /admin/content/style-templates/builtin:classic` 期望 404 |
| AC-164-01/02 | 用 `e2e_bulk_*` 的一个账号：提交同住人申请与申诉（对未占用房屋须有产权业主，故申请指向 U1）后注销（注销需验证码 → 远程**不测**，本地测） | 远程仅测 `ALREADY_CLOSED` 之外的只读行为 |
| AC-166-02 | `e2e_guest` 请求 `GET /approval/tasks` → 403 | |
| AC-168-01/02 | 系统已有报表时验证；无报表时跳过并标 SKIP 原因 | 报表由定时任务生成，远程不造数据 |
| AC-169-01 | `e2e_admin` 发布再下线 `e2e_内容`，`e2e_guest` 请求详情 → 404 | |
| AC-170-01/04 | 远程仅测：默认上限边界（1,000,000.00 成功 / 1,000,000.01 失败，提交后立即 `withdraw`）与非管理员 403、非法值 400；**"改为 500,000.00"的写全局配置步骤不在远程执行**（Q-B-02） | |
| AC-175-01 | `e2e_admin` 下载模板并 `POST /admin/registry/import?dry_run=1` 预检 | 只读预检，不正式导入（画像 P4-1、P8） |
| AC-178-03 | `e2e_guest` 依次请求 `/auth/login/password`、`/resolutions`、`/me`、`/me/housing`、`/me/profile`，均 200 且既有字段齐全 | |

**本地 E2E 需要但不适合远程**：注销流程（验证码）、实名搜索、7 天会话时钟、全局配置修改、REQ-FUNC-162 ~ 165 的边界（日期、半数分母、行数）、模板被内容引用的数量提示。

**执行与回收（E2 / GROUP_D 约定）**：`setup`（记录 `registry_counts`）→ 跑远程 E2E → `cleanup`（dry-run 先核对）→ `cleanup --execute` → `status` 确认 e2e 计数为 0、`registry_counts` 与 `setup` 一致、`claim.amount_max` 为默认值。夹具命令由 GROUP_C 实现、E2 在测试机执行；执行前须用户当轮确认（画像 P9）。

## 领域与外部依赖出处

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| 全部 IFC / MOD | 本批无新增外部 API 用法：不调用微信、阿里云短信、邮件、内容平台、LLM 接口；`session.miniapp_extended`、`claim.amount_max` 等均为本系统内部配置 | [CODE: backend/apps/core/config.py:36-37]；画像 P11-3（测试只经 `apps/integrations/fakes.py`） |
| IFC-268 | 7 天会话时长与 `EXTENDED` 校验为本系统实现 | [CODE: backend/apps/accounts/services.py:275-296]、[CODE: backend/apps/core/config.py:34-36] |
| MOD-081 | 夹具短信走 console 替身，不触发外部调用；手机号段 `1990000xxxx` 仅用于测试库内唯一键，不发送短信 | 画像 P7（`SMS_GATEWAY_BACKEND=console`）、P4-1 |

画像 P11 不为"无"，但本批 IFC 不涉及任何 P11-3 所列外部 API 的签名、字段或调用顺序，故不需要 P11 出处；上表只登记"确无外部依赖"的核对结论。
