<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T17:25:22+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/requirements/requirements_spec.md</file><file>project_workspace/ocap_history_expense_import/requirements/user_stories.md</file><file>project_workspace/ocap_history_expense_import/architecture/architecture_design.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 模块设计（增量）

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-192 | 历史支出导入批次 | `backend/apps/ledger/models.py`（修改） | 保存批次文件信息、统计、状态与作废信息 | REQ-FUNC-346/338/341；US-334/324/325 | — |
| MOD-193 | 历史支出导入行 | `backend/apps/ledger/models.py`（修改） | 保存每行原始字段、处理结果与关联台账 | REQ-FUNC-344~347；US-334/324 | MOD-192、LedgerEntry |
| MOD-194 | 历史支出导入服务 | `backend/apps/ledger/historical.py`（新建） | 模板生成、文件解析、行校验、重复判定、事务写入与作废 | REQ-FUNC-342~346/341；US-333/334/336 | MOD-192/193、LedgerService |
| MOD-195 | 历史支出 API | `backend/apps/ledger/views.py`、`urls.py`（修改） | 模板下载、导入、批次列表/详情、整批作废 | REQ-FUNC-342~350；US-333~338 | MOD-194、IsIncomeMember、AuditService |
| MOD-196 | 历史支出前端页面 | `frontend/src/portal/HistoricalExpenses.vue`（新建）、`shared/api.js`、`router/index.js`、`layout/menus.js`（修改） | 模板下载、上传、批次列表/明细、作废 | REQ-FUNC-342~350；US-333~338 | MOD-195 |
| MOD-197 | 报表联动 | 现有 `backend/apps/ledger/services.py`、`frontend/src/portal/Reports.vue`（不改代码） | 历史支出写入台账后由现有报表逻辑汇总；作废触发报表过期 | REQ-FUNC-348；US-337 | MOD-194、LedgerService |

## 模块详情

### MOD-192 历史支出导入批次（`HistoricalExpenseBatch`）

- 职责：记录一次导入的文件、操作人、统计与作废状态。
- 字段：
  - `id: int`
  - `file_name: str`（≤255）
  - `imported_by: User`（PROTECT）
  - `status: Literal["IMPORTED","VOIDED"]`，默认 `IMPORTED`
  - `total_rows: int`、`imported_rows: int`、`skipped_rows: int`、`failed_rows: int`
  - `total_amount: Decimal(14,2)`（仅成功行合计）
  - `created_at: datetime`
  - `voided_by: User | None`（SET_NULL）、`voided_at: datetime | None`、`void_reason: str`（≤200）
- 索引：`(status, created_at)`。
- 覆盖：REQ-FUNC-346/338/341。

### MOD-193 历史支出导入行（`HistoricalExpenseRow`）

- 职责：保留每个输入行的原始值与处理结果，成功行关联台账。
- 字段：
  - `batch: HistoricalExpenseBatch`（CASCADE，related_name="rows"）
  - `line_no: int`
  - `occurred_on: date | None`
  - `amount: Decimal(14,2) | None`
  - `category: str`（≤32）、`purpose: str`（≤200）、`remark: str`（≤200）
  - `status: Literal["IMPORTED","DUPLICATE","ERROR"]`
  - `error_message: str`（≤200，空表示无）
  - `ledger_entry: LedgerEntry | None`（SET_NULL，OneToOne）
- 约束：`UniqueConstraint(batch, line_no)`；索引 `(batch, status)`。
- 覆盖：REQ-FUNC-344/336/337/338。

### MOD-194 历史支出导入服务（`HistoricalExpenseService`）

- 文件：`backend/apps/ledger/historical.py`（新建）。
- 常量：`TEMPLATE_COLUMNS: tuple[str, ...] = ("日期","金额","支出类别","用途/事由","备注")`；`MAX_ROWS=5000`；`MAX_FILE_BYTES=5*1024*1024`。
- 类型：
  ```python
  @dataclass(frozen=True)
  class ParsedRow:
      line_no: int
      occurred_on: date
      amount: Decimal
      category: str
      purpose: str
      remark: str

  @dataclass(frozen=True)
  class RowError:
      line_no: int
      reason: Literal["INVALID_FIELD","DUPLICATE"]
      detail: str
  ```
- 接口：
  - `build_template(file_type: Literal["xlsx","csv"]) -> bytes`：首行固定列；xlsx 含“填写说明”Sheet。
  - `parse_rows(file_name: str, raw: bytes) -> list[dict]`：只读第一个工作表；CSV UTF-8。
  - `validate_row(values: dict, line_no: int, amount_limit: Decimal) -> ParsedRow | RowError`
  - `import_file(*, file_name: str, raw: bytes, user) -> HistoricalExpenseBatch`
    - 事务内：创建批次 → 逐行解析/校验 → 重复判定 → 成功行创建 `HistoricalExpenseRow` 并调用 `LedgerService.post(direction="EXPENSE", amount=..., occurred_on=..., entry_type=category or "历史支出", summary=purpose, source_type="historical_expense", source_id=batch.id, seq=line_no)` → 更新统计。
    - 全部行为错误/重复时不创建批次，返回 `batch=None`。
  - `void_batch(batch_id: int, *, user, reason: str) -> HistoricalExpenseBatch`：校验状态；调用 `LedgerService.void_by_source("historical_expense", batch.id)`；置 `VOIDED` 与作废信息；写审计。
- 重复判定：与已有 `HistoricalExpenseRow(status="IMPORTED")` 同批/跨批比较 `(occurred_on, amount, category, purpose)`；以及同文件内已出现的四元组。作废批次的行不参与重复判定。
- 覆盖：REQ-FUNC-342~346/341。

### MOD-195 历史支出 API

| IFC | 方法/路径 | 权限 | 请求 | 成功响应 | 错误 |
|---|---|---|---|---|---|
| IFC-408 | `GET /api/v1/admin/ledger/historical-expenses/template` | `IsIncomeMember` | `file_type` = `xlsx`/`csv`（默认 xlsx） | 200 二进制（xlsx/csv），`Content-Disposition` | 400 `INVALID_VALUE`；401/403 |
| IFC-409 | `POST /api/v1/admin/ledger/historical-expenses/import` | `IsIncomeMember` | multipart `file`（≤5MB，≤5000 行） | 201 `{batch: BatchView|null, errors: RowError[]}`；全部无效时 200 `{batch:null,...}` | 400 `FILE_REQUIRED`/`IMPORT_FILE_INVALID`/`IMPORT_COLUMNS_MISSING`（`details.columns`）；413 `FILE_TOO_LARGE`；409 `IMPORT_IN_PROGRESS`（可选，本期不做并发锁） |
| IFC-410 | `GET /api/v1/admin/ledger/historical-expenses/batches` | `IsIncomeMember` | `page`、`page_size` | 200 分页 `{count,results:[BatchSummary]}` | 401/403 |
| IFC-411 | `GET /api/v1/admin/ledger/historical-expenses/batches/{batch_id}` | `IsIncomeMember` | — | 200 `BatchDetail`（含 `rows:[RowView]`） | 404 `NOT_FOUND`；401/403 |
| IFC-412 | `POST /api/v1/admin/ledger/historical-expenses/batches/{batch_id}/void` | `IsIncomeMember` | `{reason: str}`（1~200） | 200 `BatchDetail`（status=VOIDED） | 404 `NOT_FOUND`；409 `ALREADY_VOIDED`；400 `INVALID_VALUE`；401/403 |

类型（响应字段）：
```ts
type BatchSummary = {
  id: number; fileName: string; importedBy: number; importedByLabel: string;
  status: "IMPORTED" | "VOIDED"; totalRows: number; importedRows: number;
  skippedRows: number; failedRows: number; totalAmount: string;
  createdAt: string; voidedAt: string | null; voidReason: string;
}
type RowView = {
  lineNo: number; occurredOn: string | null; amount: string | null;
  category: string; purpose: string; remark: string;
  status: "IMPORTED" | "DUPLICATE" | "ERROR"; errorMessage: string;
}
```
输入校验：文件类型/大小/行数；日期 `YYYY-MM-DD` 或 `YYYY/MM/DD` 且 ≤今天；金额 >0、≤`SystemConfig.amount_max()`、最多两位小数；类别 ≤32、用途 ≤200、备注 ≤200；表头必须含五列（缺少返回 `details.columns`）。

### MOD-196 历史支出前端页面

- 新页面：`frontend/src/portal/HistoricalExpenses.vue`；路由 `/historical-expenses`；菜单项 `{ key: 'historicalExpenses', label: '历史支出导入', audience: 'committee', match: ['/historical-expenses'], to: '/historical-expenses' }`。
- API 客户端（`frontend/src/shared/api.js`）：
  ```js
  export const historicalExpenseApi = {
    template: (fileType = 'xlsx') => http.get('/admin/ledger/historical-expenses/template', { params: { file_type: fileType }, responseType: 'blob' }),
    importFile: (file) => { const body = new FormData(); body.append('file', file); return http.post('/admin/ledger/historical-expenses/import', body) },
    batches: (params) => http.get('/admin/ledger/historical-expenses/batches', { params }),
    batchDetail: (id) => http.get(`/admin/ledger/historical-expenses/batches/${id}`),
    voidBatch: (id, reason) => http.post(`/admin/ledger/historical-expenses/batches/${id}/void`, { reason })
  }
  ```
- 页面区域：模板下载（xlsx/csv）、上传导入、批次列表（时间/操作人/文件/行数/金额/状态/操作）、批次明细弹窗（逐行结果）、整批作废（原因确认）。
- 与报表页关系：不修改 `Reports.vue` 逻辑；历史支出通过台账自然进入报表。
- 覆盖：REQ-FUNC-342~350；US-333~338。

### MOD-197 报表联动

- 不新增报表代码。`LedgerService.generate` 已按 `status=ACTIVE` 汇总所有 `LedgerEntry`（`backend/apps/ledger/services.py:76-79`），历史支出写入后即可生成历史季度/年度报表。
- 作废通过 `LedgerService.void_by_source` 触发 `_mark_reports_stale`（`backend/apps/ledger/services.py:49-67`），报表重算后排除作废明细。
- 报表明细中的 `entry_type` 显示支出类别（空则“历史支出”），`summary` 显示用途。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-342 | US-322 | MOD-194、MOD-195、MOD-196 |
| REQ-FUNC-343 | US-334 | MOD-194、MOD-195、MOD-196 |
| REQ-FUNC-344 | US-334 | MOD-194、MOD-195 |
| REQ-FUNC-345 | US-334 | MOD-194 |
| REQ-FUNC-346 | US-334 | MOD-192、MOD-193、MOD-194、MOD-197 |
| REQ-FUNC-347 | US-335 | MOD-192、MOD-193、MOD-195、MOD-196 |
| REQ-FUNC-348 | US-337 | MOD-197 |
| REQ-FUNC-349 | US-338 | MOD-195、MOD-196 |
| REQ-FUNC-350 | US-336 | MOD-192、MOD-194、MOD-195、MOD-196、MOD-197 |
| REQ-NFUNC-073 | US-334/324/325 | MOD-194、MOD-195 |

## 依赖关系

- MOD-194 → MOD-192/193（创建批次与行）
- MOD-194 → 现有 `LedgerService.post/void_by_source`（IFC-110/111，`backend/apps/ledger/services.py:31-47`、`:49-59`）
- MOD-195 → MOD-194（调用服务）
- MOD-195 → `IsIncomeMember`（现有权限）
- MOD-196 → MOD-195（HTTP 调用）
- MOD-197 → MOD-194（台账写入间接驱动报表）
- 已检查：无循环依赖。

## 数据迁移

- 新增 `backend/apps/ledger/migrations/0007_historical_expense.py`（手写、单 app）：
  - 创建 `HistoricalExpenseBatch`、`HistoricalExpenseRow` 两表；
  - 创建 `(status, created_at)`、`(batch, status)` 索引与 `(batch, line_no)` 唯一约束；
  - 不改动现有 `LedgerEntry`/`LedgerReport` 表结构与数据。
- 可逆：`migrations.DeleteModel` 可回滚，但会丢失导入批次数据（`[MANUAL_ROLLBACK_REQUIRED]`）。
- 风险：全新表，无存量数据迁移；目标机不生成迁移（画像 P8）。

## 受影响的运行单元 / 构建

- 后端：`ocap-backend.service` 重启；执行 `manage.py migrate`；无新增进程/定时任务。
- 前端：重新构建并以 `VITE_API_BASE=/ocap/api/v1`、`--base=/ocap/` 部署静态产物。
- 数据库：MySQL 库 `ocap` 新增两表；不修改现有表。
- CI：现有测试与构建流程即可，无需新增服务。

## 领域与外部依赖出处

不适用（画像 P11-1/P11-2 为“无”；本需求不调用 P11-3 的微信/短信/邮件外部 API）。
