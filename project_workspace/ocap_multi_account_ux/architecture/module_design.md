<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-24T22:22:09+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>0.1.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/requirements/requirements_spec.md</file><file>project_workspace/ocap_multi_account_ux/requirements/user_stories.md</file><file>project_workspace/ocap_multi_account_ux/architecture/architecture_design.md</file><file>backend/apps/ledger/views.py</file><file>backend/apps/ledger/services.py</file><file>backend/apps/ledger/models.py</file><file>backend/apps/ledger/historical.py</file><file>backend/apps/ledger/apps.py</file><file>backend/apps/ledger/urls.py</file><file>backend/apps/income/views.py</file><file>backend/apps/claims/views.py</file><file>backend/apps/approval/services.py</file><file>frontend/src/shared/api.js</file><file>frontend/src/portal/Reports.vue</file><file>frontend/src/portal/ReportDetailDialog.vue</file><file>frontend/src/portal/AccountCard.vue</file><file>frontend/src/portal/Income.vue</file><file>frontend/src/portal/Claims.vue</file><file>frontend/src/portal/HistoricalExpenses.vue</file><file>frontend/src/admin/AdminAccounts.vue</file><file>miniprogram/pages/claims/index.vue</file><file>miniprogram/utils/api.js</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-202 | 报表按账户聚合服务 | 修改 `backend/apps/ledger/services.py` | 对一批报表按账户一次性汇总收入/支出 | REQ-FUNC-360；US-348 | — |
| MOD-203 | 报表列表账户视角接口 | 修改 `backend/apps/ledger/views.py` | 列表接收 `account_id`，使用 MOD-202 结果覆盖返回金额 | REQ-FUNC-360；US-348 | MOD-202 |
| MOD-204 | 账户选择共享组件 | 新建 `frontend/src/shared/AccountSelect.vue` | 加载启用账户、默认选中默认账户、空态提示 | REQ-FUNC-352～356；US-340～344 | — |
| MOD-205 | 财务报表页账户卡片与列表联动 | 修改 `frontend/src/portal/Reports.vue`、`frontend/src/portal/AccountCard.vue` | 卡片横向均分/滚动、选中态、选中账户驱动列表 | REQ-FUNC-358～360、REQ-NFUNC-074；US-346～348 | MOD-203、MOD-204、MOD-206 |
| MOD-206 | 报表详情跟随账户与收支分色 | 修改 `frontend/src/portal/ReportDetailDialog.vue`、`frontend/src/portal/Reports.vue` | 删除浮层账户下拉，接收页面账户，收支分色 | REQ-FUNC-361/362、REQ-NFUNC-076；US-349/350 | —（复用既有详情接口） |
| MOD-207 | 历史支出审批模型与迁移 | 修改 `backend/apps/ledger/models.py`；新建 `backend/apps/ledger/migrations/0008_historical_expense_approval.py` | 批次/行增加账户、审批实例、状态机字段 | REQ-FUNC-356/357/363；US-344/345/351 | — |
| MOD-208 | 历史支出导入审批服务与回调 | 修改 `backend/apps/ledger/historical.py`、`backend/apps/ledger/apps.py`、`backend/apps/approval/services.py` | 生成待审批批次、审批通过回调入账、驳回/撤回处理、去重纳入待审批批次 | REQ-FUNC-357/363、C-386/C-387；US-345/351 | MOD-207 |
| MOD-209 | 历史支出导入与撤回 API | 修改 `backend/apps/ledger/views.py`、`backend/apps/ledger/urls.py`、`frontend/src/shared/api.js` | 导入接收账户/审批流程；批次视图补充字段；新增撤回端点 | REQ-FUNC-356/357/363；US-344/345/351 | MOD-207、MOD-208 |
| MOD-210 | 历史支出导入页面 | 修改 `frontend/src/portal/HistoricalExpenses.vue` | 账户/审批流程选择、状态展示、撤回/作废入口、文案更新 | REQ-FUNC-356/357/363；US-344/345/351 | MOD-204、MOD-209 |
| MOD-211 | 收入录入与导入账户选择 | 修改 `frontend/src/portal/Income.vue`、`backend/apps/income/views.py` | 逐条录入与批量导入选择账户；导入写入 account；返回账户字段 | REQ-FUNC-352/353；US-340/341 | MOD-204 |
| MOD-212 | 报销/备用金 Web 账户选择 | 修改 `frontend/src/portal/Claims.vue`、`backend/apps/claims/views.py` | 报销/备用金表单账户选择；返回账户字段 | REQ-FUNC-354/355；US-342/343 | MOD-204 |
| MOD-213 | 管理端账户操作可读性 | 修改 `frontend/src/admin/AdminAccounts.vue` | 操作列改用高对比度按钮，禁用态可区分 | REQ-FUNC-351、REQ-NFUNC-075；US-339 | — |
| MOD-214 | 小程序报销/备用金账户选择 | 修改 `miniprogram/pages/claims/index.vue`、`miniprogram/utils/api.js` | 小程序账户 picker、默认账户与必填校验、提交带 account_id | REQ-FUNC-364/365、REQ-NFUNC-078；US-352/353 | —（复用既有后端） |

## 模块详情

### MOD-202 报表按账户聚合服务

- 职责：给定一页报表与一个账户，返回每张报表在该账户口径下的（收入合计、支出合计），供列表序列化使用。
- 文件：修改 `backend/apps/ledger/services.py`（在 `_aggregate`/`_opening_balance` 旁新增模块级函数；`views.py` 现有导入行 `from .services import AccountService, LedgerService, _aggregate, _opening_balance, _period_range` 增加该函数）。
- IFC-418：
  ```python
  def _totals_by_period(
      reports: Sequence["LedgerReport"],
      account: "LedgerAccount",
  ) -> dict[int, tuple[Decimal, Decimal]]:
      """返回 {report.id: (total_income, total_expense)}；只统计 status=ACTIVE 的台账记录。"""
  ```
  - 鉴权：内部函数，不对外暴露。
  - 输入校验：`reports` 为空返回 `{}`；账户必须已由调用方校验存在。
  - 错误：不抛业务错误；数据库异常交给上层统一处理。
  - 实现约束：只允许 1 次 `LedgerEntry` 查询（范围取所有报表 `_period_range` 的最小 start 与最大 end，过滤 `account`、`status="ACTIVE"`），在 Python 中按报表周期分桶；同一笔流水可同时计入重叠周期（年报表 + 季报表）。
- 依赖：无。
- 外部依赖：无。

### MOD-203 报表列表账户视角接口

- 职责：`GET /ledger/reports` 增加可选 `account_id`；存在时返回该账户口径的收入/支出/结余，`legacy=false`。
- 文件：修改 `backend/apps/ledger/views.py`（`LedgerReportListView`、`ReportSerializer`、`report_summary`）。
- IFC-419：HTTP `GET /api/v1/ledger/reports`
  - 鉴权：沿用 `IsMember`（与现状一致）。
  - 查询参数：`period_type?: "QUARTER"|"YEAR"`、`year?: int`、`page?`、`page_size?`、`account_id?: int`。
  - 成功 `200`：分页结构不变；`results[]` 字段集不变（`id/period_type/year/quarter/total_income/total_expense/balance/opening_balance/closing_balance/legacy/stale/generated_at`）。
    - 未传 `account_id`：保持现状（读取 `LedgerReport` 存储值）。
    - 传 `account_id`：`total_income/total_expense/balance` 使用 IFC-418 结果；`opening_balance/closing_balance` 沿用报表存储值（列表不展示期初期末，避免额外查询）；`legacy=false`。
  - 错误：
    - `account_id` 非整数 → `400 INVALID_VALUE "account_id 不合法"`。
    - 账户不存在 → `404 NOT_FOUND "账户不存在"`。
  - 输入校验：`year` 非整数保持现状抛 `INVALID_VALUE`；`page_size` 由 `page_response` 控制。
- 依赖：MOD-202（IFC-418）。
- 外部依赖：无。

### MOD-204 账户选择共享组件

- 职责：Web 端唯一账户选择控件；只列启用账户，自动默认选中默认账户，空列表显示"暂无可用账户"。
- 文件：新建 `frontend/src/shared/AccountSelect.vue`。
- IFC-420：Vue 组件契约
  ```ts
  props: {
    modelValue: number | null
    disabled?: boolean        // 默认 false
    placeholder?: string      // 默认 "请选择入账账户"
    size?: "small" | "default" // 默认 "default"
  }
  emits: {
    "update:modelValue": (id: number | null) => true
    "loaded": (payload: { accounts: AccountOption[]; defaultId: number | null }) => true
  }
  type AccountOption = { id: number; name: string; is_default: boolean }
  ```
  - 数据来源：`accountApi.summary({ status: "ENABLED", recent: 0 })`（`frontend/src/shared/api.js` 既有方法，响应含 `accounts[{id,name,status,is_default,balance,recent_entries}]`）。
  - 行为：挂载后加载；若 `modelValue` 为空且存在默认账户，`emit("update:modelValue", defaultId)` 并 `emit("loaded", ...)`；账户列表为空时下拉展示"暂无可用账户"，不 emit 默认值。
  - 鉴权：依赖页面既有登录态，组件自身不发额外鉴权请求。
  - 输入校验：`modelValue` 必须为启用账户 id 或 `null`；不合法时按空处理。
- 依赖：无。
- 外部依赖：账户汇总接口（既有 IFC-409）。

### MOD-205 财务报表页账户卡片与列表联动

- 职责：账户卡片按宽度均分/横向滚动，支持选中；选中账户驱动下方报表列表；保留"账户余额合计"固定。
- 文件：修改 `frontend/src/portal/Reports.vue`、`frontend/src/portal/AccountCard.vue`。
- IFC-421：组件与页面契约
  ```ts
  // AccountCard.vue
  props: { account: AccountSummary; selected: boolean }
  emits: { select: (id: number) => void }
  // 根元素：<article role="button" tabindex="0" :aria-pressed="selected"
  //          @click="$emit('select', account.id)"
  //          @keydown.enter.prevent="$emit('select', account.id)"
  //          @keydown.space.prevent="$emit('select', account.id)">
  ```
  - `Reports.vue` 状态：`selectedAccountId: number | null`。
  - 账户加载成功后：若 `selectedAccountId` 不在启用账户列表内 → 设为 `accounts.find(a => a.is_default)?.id ?? accounts[0]?.id ?? null`。
  - 列表请求：`ledgerApi.reports({ ...filters, account_id: selectedAccountId })`；切换账户时调用 `resetAndLoad()`（页码归 1，保留周期筛选）。
  - 布局：账户卡片容器 `display:flex; gap:12px; overflow-x:auto`，子项 `flex:1 1 0; min-width:280px`；"账户余额合计"标题与金额位于滚动容器之外。
  - 空账户：`selectedAccountId === null` 时不请求列表，显示既有空态。
  - 鉴权：沿用页面既有 `IsMember` 报表读取权限。
  - 输入校验：点击只传当前卡片账户 id；已停用账户不在列表，无法被选中（AC-418-03）。
- 依赖：MOD-203（IFC-419）、MOD-204（IFC-420，页面账户加载可复用其接口但不强制使用组件）、MOD-206（IFC-422 传参）。
- 外部依赖：无。

### MOD-206 报表详情跟随账户与收支分色

- 职责：移除浮层内账户下拉；详情以页面选中账户加载；明细方向与指标数值按收入/支出分色。
- 文件：修改 `frontend/src/portal/ReportDetailDialog.vue`、`frontend/src/portal/Reports.vue`（传参）。
- IFC-422：组件契约
  ```ts
  props: {
    modelValue: boolean
    reportId: number | null
    accountId: number | null   // 页面当前选中账户，必传
  }
  emits: { "update:modelValue": (v: boolean) => void }
  ```
  - 数据请求：`ledgerApi.reportDetail(reportId, accountId)`（既有接口 `GET /ledger/reports/{id}?account_id=`）。
  - UI：删除"全部账户/各账户"下拉及其账户加载逻辑（AC-420-01）。
  - 颜色：明细"方向"文字与金额加 `is-income` / `is-expense` 类；指标卡"本期收入""本期支出"数值加同类；CSS 复用 `--success` / `--danger`（与 `AccountCard.vue` 同源）。
  - 空态：无明细时保持既有"本期暂无收支明细"。
  - 鉴权：`IsMember`（既有详情接口）。
  - 输入校验：`accountId` 为空时按全局详情加载（仅兜底，正常路径页面必选账户）。
- 依赖：无新增（复用既有详情 IFC-413）。
- 外部依赖：无。

### MOD-207 历史支出审批模型与迁移

- 职责：为批次增加账户与审批实例信息，扩展批次/行状态。
- 文件：修改 `backend/apps/ledger/models.py`；新建 `backend/apps/ledger/migrations/0008_historical_expense_approval.py`。
- IFC-423：模型契约
  ```python
  class HistoricalExpenseBatch(models.Model):
      STATUSES = [
          ("PENDING", "审批中"), ("IMPORTED", "已入账"), ("REJECTED", "已驳回"),
          ("WITHDRAWN", "已撤回"), ("VOIDED", "已作废"),
      ]
      account = models.ForeignKey("ledger.LedgerAccount", null=True, blank=True,
                                  on_delete=models.PROTECT,
                                  related_name="historical_expense_batches")
      approval_instance_id = models.BigIntegerField(null=True, blank=True)
      decided_at = models.DateTimeField(null=True, blank=True)
      status = models.CharField(max_length=10, choices=STATUSES, default="PENDING")

  class HistoricalExpenseRow(models.Model):
      STATUSES = [
          ("PENDING", "待入账"), ("IMPORTED", "成功"),
          ("DUPLICATE", "重复"), ("ERROR", "错误"),
      ]
  ```
  - `max_length=10` 可容纳全部状态值（最长 `WITHDRAWN` = 9）。
  - `imported_rows/total_amount` 语义：有效行数与有效金额（`PENDING` + `IMPORTED` 行），审批前后不重算。
  - 鉴权：模型无鉴权，API 沿用 `IsIncomeMember`。
  - 输入校验：`account` 允许空仅用于旧批次；新批次由 API 强制解析（缺省回退默认账户，ADR-192）。
- 依赖：无。
- 外部依赖：无。

### MOD-208 历史支出导入审批服务与回调

- 职责：把"解析 + 去重 + 建批次"与"审批后入账"拆开；注册审批回调；支持撤回；去重覆盖待审批批次。
- 文件：修改 `backend/apps/ledger/historical.py`、`backend/apps/ledger/apps.py`、`backend/apps/approval/services.py`（`subject_title` 增加分支）。
- IFC-424：服务契约
  ```python
  def create_pending_batch(
      *, file_name: str, raw: bytes, user, account, flow_id: int
  ) -> tuple[HistoricalExpenseBatch | None, list[dict], int]:
      """解析并校验文件，创建 PENDING 批次与行（PENDING/DUPLICATE/ERROR），
      提交审批后返回 (batch, errors, total_rows)。无有效行时返回 (None, errors, total_rows)，不建批次。"""
  ```
  - 事务：创建批次、行、`ApprovalEngine.submit(scope="INCOME", subject_type="historical_expense_batch", subject_id=batch.id, flow_id=flow_id, submitter=user)`、回写 `approval_instance_id` 在同一 `transaction.atomic()` 内完成（OQ-B-01）。
  - 去重键：`HistoricalExpenseRow.objects.filter(status__in=("PENDING", "IMPORTED"), batch__status__in=("PENDING", "IMPORTED")).values_list("occurred_on", "amount", "category", "purpose")`；被驳回/撤回批次的待入账行不占用去重键。
  - 入账：仅 `on_approved` 中执行 `LedgerService.post(direction="EXPENSE", amount=..., occurred_on=..., entry_type=..., summary=..., account=batch.account, source_type=SOURCE_TYPE, source_id=batch.id, seq=line_no)`，成功后行置 `IMPORTED` 并写 `ledger_entry`；重复/错误行保持原状。
- IFC-425：审批回调（注册于 `LedgerConfig.ready()`）
  ```python
  ApprovalEngine.register_callbacks(
      "historical_expense_batch",
      on_approved=historical.on_approved,
      on_rejected=historical.on_rejected,
      on_withdrawn=historical.on_withdrawn,
  )

  def on_approved(subject_id: int) -> None: ...   # PENDING → IMPORTED，逐行入账
  def on_rejected(subject_id: int) -> None: ...   # PENDING → REJECTED，写 decided_at
  def on_withdrawn(subject_id: int) -> None: ...  # PENDING → WITHDRAWN，写 decided_at
  ```
  - 幂等：入账前检查批次状态必须为 `PENDING` 且行状态为 `PENDING`，重复回调不重复入账。
- IFC-426：撤回服务
  ```python
  def withdraw_batch(batch_id: int, *, user) -> HistoricalExpenseBatch:
      """批次必须 PENDING 且 approval_instance_id 非空；调用 ApprovalEngine.withdraw 触发回调；
      非提交人由引擎返回 403。"""
  ```
  - 错误：批次不存在 `404`；状态非 `PENDING` → `409 INVALID_STATE`；无审批实例 → `409 INVALID_STATE`。
- 其他修改：`build_template` 填写说明增加"导入后提交审批，审批通过后才入账"。
- 依赖：MOD-207。
- 外部依赖：`ApprovalEngine`（既有）。

### MOD-209 历史支出导入与撤回 API

- 职责：导入接口接收账户与审批流程；批次视图补充账户/审批字段；新增撤回端点。
- 文件：修改 `backend/apps/ledger/views.py`、`backend/apps/ledger/urls.py`、`frontend/src/shared/api.js`。
- IFC-427：HTTP `POST /api/v1/admin/ledger/historical-expenses/import`（`multipart/form-data`）
  - 鉴权：`IsIncomeMember`（沿用）。
  - 请求：`file`（必填，≤5MB，xlsx/CSV，≤5000 行）、`account_id?: int`（缺省回退默认账户）、`approval_flow_id: int`（必填）。
  - 成功：有有效行 `201 {batch, errors[], total_rows}`；全部重复/错误 `200 {batch: null, errors[], total_rows}`。
  - 错误：`FILE_REQUIRED 400`、`FILE_TOO_LARGE 413`、`IMPORT_FILE_INVALID 400`、`IMPORT_COLUMNS_MISSING 400`、`INVALID_VALUE 400`（`account_id`/`approval_flow_id` 非法）、`ACCOUNT_UNAVAILABLE 409`（账户不存在/停用）、`FLOW_NOT_FOUND 404` / `FLOW_INVALID 400`（沿用审批引擎错误码）。
  - 输入校验：`approval_flow_id` 必须为整数且属于 `scope="INCOME"` 的启用流程（由 `ApprovalEngine.submit` 校验）。
- IFC-428：HTTP `POST /api/v1/admin/ledger/historical-expenses/batches/{id}/withdraw`
  - 鉴权：`IsIncomeMember`；仅提交人可撤回（引擎校验）。
  - 成功 `200`：批次视图 + `rows[]`（`status=WITHDRAWN`）。
  - 错误：`404 NOT_FOUND`、`409 INVALID_STATE`、`403 FORBIDDEN`。
- IFC-429：批次视图契约（`_batch_view` 扩展，列表/详情/导入/撤回共用）
  ```text
  id, file_name, imported_by, imported_by_label, status,
  total_rows, imported_rows, skipped_rows, failed_rows, posted_rows,
  total_amount, created_at, voided_at, void_reason,
  account_id: int|null, account_name: str|null,
  approval_instance_id: int|null, decided_at: str|null
  ```
  - `posted_rows`：`rows.filter(status="IMPORTED").count()`；`imported_rows` 保持"有效行数"。
  - 既有 `HistoricalExpenseBatchVoidView`：仅 `IMPORTED` 可作废；`PENDING` 调用 → `409 INVALID_STATE "审批中的批次请先撤回"`。
- 前端 API（`frontend/src/shared/api.js`）：
  ```js
  export const historicalExpenseApi = {
    // 既有 list/detail/template/void 不变
    importFile: (file, { accountId, flowId } = {}) => { /* FormData 追加 account_id、approval_flow_id */ },
    withdrawBatch: (id) => http.post(`/admin/ledger/historical-expenses/batches/${id}/withdraw`, {}),
  }
  ```
- 依赖：MOD-207、MOD-208。
- 外部依赖：无。

### MOD-210 历史支出导入页面

- 职责：页面提供账户与审批流程选择，按状态展示批次并提供撤回/作废入口，更新导入说明。
- 文件：修改 `frontend/src/portal/HistoricalExpenses.vue`。
- IFC-430：页面行为契约
  - 顶部导入区：`<AccountSelect v-model="accountId" />` + 审批流程 `el-select`（`approvalApi.flows("INCOME")`，沿用既有方法）+ 上传。
  - 必填：`accountId` 或 `flowId` 为空时提示"请选择入账账户"/"请选择审批流程"并直接返回，不调用上传接口（AC-415-03）。
  - 批次表新增"账户"列；状态标签：`PENDING=审批中(warning)`、`IMPORTED=已入账(success)`、`REJECTED=已驳回(danger)`、`WITHDRAWN=已撤回(info)`、`VOIDED=已作废(info)`。
  - 操作：明细（全部）、撤回（`PENDING` 且提交人本人）、作废（仅 `IMPORTED`）。
  - 结果提示：成功后提示"已提交审批，审批通过后入账"；详情展示账户与审批信息。
  - 文案：上传区说明由"导入即入账"改为"导入后提交审批，审批通过后入账"。
  - 鉴权：页面沿用现有路由与角色；按钮不替代后端权限。
  - 输入校验：文件与账户/流程校验在发请求前完成。
- 依赖：MOD-204（IFC-420）、MOD-209（IFC-427/428/429）。
- 外部依赖：无。

### MOD-211 收入录入与导入账户选择

- 职责：收入逐条录入与批量导入均可选择账户，导入批次写入所选账户，返回账户信息。
- 文件：修改 `frontend/src/portal/Income.vue`、`backend/apps/income/views.py`。
- IFC-431：HTTP `POST /api/v1/admin/income/sheets/import`（`multipart/form-data`）
  - 鉴权：`IsIncomeMember`（沿用）。
  - 请求新增：`account_id?: int`；缺省回退默认账户（ADR-192）。
  - 成功 `201`：`sheet_view` 增加 `account_id`、`account_name`。
  - 错误：`account_id` 不存在/停用 → `ACCOUNT_UNAVAILABLE 409`（沿用 `AccountService.resolve_account`）。
- IFC-432：HTTP `POST /api/v1/admin/income/sheets`（逐条录入建草稿）
  - 请求既有 `account_id` 不变；成功响应 `sheet_view` 增加 `account_id`、`account_name`。
  - 缺省仍回退默认账户（ADR-192）。
- 前端行为（`Income.vue`）：
  - 工具栏增加 `<AccountSelect v-model="accountId" />`，未选账户时"批量导入"仅提示"请先选择入账账户"，不发请求（AC-412-02）。
  - "逐条录入"对话框增加 `<AccountSelect v-model="form.account_id" />`，打开时默认选中默认账户；无启用账户时提示"暂无可用账户"且"保存为草稿"禁用（AC-411-01/03）。
  - 列表/明细展示账户名（依赖 `account_name`）。
  - `incomeApi.importFile(file, accountId)` 在 FormData 追加 `account_id`。
- 依赖：MOD-204（IFC-420）。
- 外部依赖：无。

### MOD-212 报销/备用金 Web 账户选择

- 职责：Web 报销与备用金表单选择账户，列表/详情展示账户。
- 文件：修改 `frontend/src/portal/Claims.vue`、`backend/apps/claims/views.py`。
- IFC-433：`claim_view` 增加 `account_id: int|null`、`account_name: str|null`（列表与详情的既有字段不变）。
  - 创建接口既有 `account_id` 解析不变（缺省回退默认账户，ADR-192）。
  - 鉴权：沿用现有 claims 权限。
- 前端行为：
  - 报销/备用金对话框增加 `<AccountSelect v-model="form.account_id" />`；默认选中默认账户；未选时提示"请选择入账账户"并阻止提交（AC-413-01、AC-414-02）。
  - 核销（SETTLEMENT）表单不加账户选择（Q-10）。
  - 列表/详情展示账户名。
- 依赖：MOD-204。
- 外部依赖：无。

### MOD-213 管理端账户操作可读性

- 职责：账户管理表格"编辑""设为默认"清晰可辨，禁用态可区分。
- 文件：修改 `frontend/src/admin/AdminAccounts.vue`。
- IFC-434：UI 契约
  - 操作列由 `el-button link` 改为带可见边框/浅底的小尺寸 `el-button`（非 `link`）。
  - "设为默认"在 `is_default=true` 时 `disabled`，保留禁用态样式；不得以隐藏按钮替代（AC-410-02）。
  - 颜色取自现有主题变量（`--text`/`--line`/`--muted`），不新增主题或依赖。
  - 窄屏：表格允许横向滚动（Element Plus 默认）。
- 依赖：无。
- 外部依赖：无。

### MOD-214 小程序报销/备用金账户选择

- 职责：小程序报销/备用金表单选择账户并提交 `account_id`。
- 文件：修改 `miniprogram/pages/claims/index.vue`、`miniprogram/utils/api.js`。
- IFC-435：小程序 API 契约
  ```js
  // miniprogram/utils/api.js
  accounts: (params = { status: "ENABLED", recent: 0 }) =>
    http.get("/ledger/accounts/summary", params)
  ```
  - 现有 `createReimbursement/createAdvance` 载荷增加 `account_id`（后端既有字段，无需新端点）。
  - 页面：表单加载时 `api.accounts()`；`accountId` 默认取 `accounts.find(a => a.is_default)?.id ?? accounts[0]?.id ?? null`；`picker` 仅展示启用账户；空列表时展示"暂无可用账户"并禁用提交。
  - 提交前校验：`accountId` 为空 → `uni.showToast("请选择入账账户")`，不调用 API（AC-423-02、AC-424-02）。
  - 核销（SETTLEMENT）与报表页不改（Q-10）。
- 依赖：无。
- 外部依赖：账户汇总接口（既有 IFC-409）、claims 创建接口（既有）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-351 | US-339 | MOD-213 |
| REQ-FUNC-352 | US-340 | MOD-204、MOD-211 |
| REQ-FUNC-353 | US-341 | MOD-204、MOD-211 |
| REQ-FUNC-354 | US-342 | MOD-204、MOD-212 |
| REQ-FUNC-355 | US-343 | MOD-204、MOD-212 |
| REQ-FUNC-356 | US-344 | MOD-204、MOD-207、MOD-209、MOD-210 |
| REQ-FUNC-357 | US-345 | MOD-207、MOD-208、MOD-209、MOD-210 |
| REQ-FUNC-358 | US-346 | MOD-205 |
| REQ-FUNC-359 | US-347 | MOD-205 |
| REQ-FUNC-360 | US-348 | MOD-202、MOD-203、MOD-205 |
| REQ-FUNC-361 | US-349 | MOD-206 |
| REQ-FUNC-362 | US-350 | MOD-206 |
| REQ-FUNC-363 | US-351 | MOD-207、MOD-208、MOD-209、MOD-210 |
| REQ-FUNC-364 | US-352 | MOD-214 |
| REQ-FUNC-365 | US-353 | MOD-214 |
| REQ-NFUNC-074 | US-346 | MOD-205 |
| REQ-NFUNC-075 | US-339 | MOD-213 |
| REQ-NFUNC-076 | US-350 | MOD-206 |
| REQ-NFUNC-077 | US-340～345、348 | MOD-207～212、MOD-214 |
| REQ-NFUNC-078 | US-352/353 | MOD-204、MOD-214 |

## 依赖关系

```text
MOD-203 → MOD-202（IFC-418）
MOD-205 → MOD-203（IFC-419）
MOD-205 → MOD-204（IFC-420）
MOD-205 → MOD-206（IFC-422）
MOD-208 → MOD-207（IFC-423）
MOD-209 → MOD-207、MOD-208（IFC-424～426）
MOD-210 → MOD-204、MOD-209（IFC-420、427～429）
MOD-211 → MOD-204（IFC-420）
MOD-212 → MOD-204（IFC-420）
```
已检查：无循环依赖。MOD-213/214 无内部依赖。

## 数据迁移

- 迁移文件：`backend/apps/ledger/migrations/0008_historical_expense_approval.py`（手写，单 app 范围，符合画像 P6；禁用 `makemigrations` 全量产物）。
- 变更：
  - `HistoricalExpenseBatch` 新增 `account`（FK `ledger.LedgerAccount`，`null=True`，`on_delete=PROTECT`，`related_name="historical_expense_batches"`）。
  - `HistoricalExpenseBatch` 新增 `approval_instance_id`（`BigIntegerField(null=True)`）、`decided_at`（`DateTimeField(null=True)`）。
  - `HistoricalExpenseBatch.status` 默认值 `IMPORTED` → `PENDING`（仅影响新记录），choices 扩展为 5 个状态；`max_length=10` 不变。
  - `HistoricalExpenseRow.status` choices 增加 `PENDING`，默认值保持 `ERROR`。
- 回填：无。旧批次保持 `status=IMPORTED`、`account=NULL`、行 `status=IMPORTED`，符合 C-389（不回溯补审批）；旧批次列表账户列显示"—"。
- 可逆性：`migrations.RemoveField` 可逆删除新增列；回滚不恢复已迁移的账户/审批关联（数据风险：回滚后新批次账户信息丢失），回滚前需备份。
- 数据风险：低。无唯一约束变更、无索引删除；新增列均可空。`ledger_hist_status_created_idx` 已覆盖按状态列表查询。
- 其他 app：无迁移。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 动作 |
|---|---|---|
| Django 后端（gunicorn / systemd `ocap-backend`） | 新增迁移、审批回调、报表列表参数 | 迁移后重启 |
| Web 前端（Vite 构建产物） | Reports/AccountCard/ReportDetailDialog/Income/Claims/HistoricalExpenses/AdminAccounts/新组件 | 重新构建并替换 nginx `:8090` 静态产物 |
| 微信小程序 | claims 页面与 api.js | `npm run build:mp-weixin` 重新构建；发布需用户当轮授权（RU-4） |
| 定时任务 / 容器 / 端口 | 无 | — |

## 测试文件规划（供 GROUP_D 使用）

| 层 | 路径 | 覆盖 |
|---|---|---|
| 后端集成 | `backend/tests/integration/test_reports_account_view.py`（新建） | IFC-419 正常/非法 account_id/404；AC-419-01 |
| 后端集成 | `backend/tests/integration/test_history_expense_api.py`（修改） | 导入→审批中零台账→通过后入账；驳回/撤回零台账；旧批次不变（AC-415～417、422） |
| 后端 E2E | `backend/tests/e2e/test_history_expense_journey.py`（修改） | 多账户下完整审批入账链路 |
| 后端单元 | `backend/tests/unit/test_history_expense_rules.py`（修改） | 去重覆盖 PENDING 批次、状态机与幂等 |
| 后端集成 | `backend/tests/integration/test_finance_accounts_api.py`（修改） | 账户汇总禁用账户过滤（回归） |
| 前端 | `frontend/tests/finance_accounts_ui.spec.js`（修改） | 卡片选中/布局/详情无下拉 |
| 前端 | `frontend/tests/historical_expenses.spec.js`（修改） | 账户+流程必填、状态标签、撤回/作废 |
| 前端 | `frontend/tests/income_template.spec.js`（修改） | 收入账户选择与导入参数 |
| 前端 | `frontend/tests/claims_account.spec.js`（新建） | 报销/备用金账户选择与校验 |
| 小程序 | `miniprogram/tests/claims_account.spec.js`（新建） | picker 默认/必填/仅启用账户（REQ-NFUNC-078） |

## 领域与外部依赖出处

画像 P11 未声明硬件、闭源 API 或数值算法约束，本次改动为既有业务系统的账户/审批/报表逻辑，不适用 P11 资料。接口事实均取自仓库代码：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| MOD-203 / IFC-419 | 报表列表当前无 account_id；详情支持 account_id 并按账户聚合 | `backend/apps/ledger/views.py:165-176`、`backend/apps/ledger/views.py:205-233` |
| MOD-202 / IFC-418 | 台账聚合只统计 `status="ACTIVE"`，周期分段由 `_period_range` 给出 | `backend/apps/ledger/services.py:17-52` |
| MOD-208 | 审批回调注册方式、subject_type 与 scope 约定 | `backend/apps/income/apps.py`、`backend/apps/income/services.py`、`backend/apps/approval/services.py` |
| MOD-207 | 历史支出批次/行现有字段与状态 | `backend/apps/ledger/models.py:90-135` |
| MOD-208 | 现有导入即入账与去重逻辑 | `backend/apps/ledger/historical.py:149-241` |
| MOD-209 | 历史支出导入/批次/作废路由与权限 | `backend/apps/ledger/views.py:269-319`、`backend/apps/ledger/urls.py` |
| MOD-211 | 收入导入当前不写账户；逐条创建已接受 account_id | `backend/apps/income/views.py:179-237`、`backend/apps/income/views.py:287-288` |
| MOD-212 | claims 创建已接受可选 account_id | `backend/apps/claims/views.py:128/167/202`、`backend/apps/claims/views.py:28-42` |
| MOD-214 | 小程序 claims 提交与 api.js 结构 | `miniprogram/pages/claims/index.vue`、`miniprogram/utils/api.js` |
| MOD-205/206 | 现有报表页/卡片/详情结构与颜色变量 | `frontend/src/portal/Reports.vue`、`frontend/src/portal/AccountCard.vue`、`frontend/src/portal/ReportDetailDialog.vue` |
