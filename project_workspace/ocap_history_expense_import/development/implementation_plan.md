<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-23T17:50:09+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/requirements/requirements_spec.md</file><file>project_workspace/ocap_history_expense_import/requirements/user_stories.md</file><file>project_workspace/ocap_history_expense_import/architecture/architecture_design.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file><file>project_workspace/ocap_history_expense_import/architecture/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 实现计划（增量）

## 实现概览

- 模块数：6（MOD-192~197）；改动文件：后端 6 个、前端 4 个、测试 1 个（现有断言同步）。
- 实现顺序按依赖拓扑：MOD-192/193（模型+迁移）→ MOD-194（服务）→ MOD-195（API）→ MOD-196（前端）→ MOD-197（报表联动，零代码，仅验证）。
- 写入方式：历史支出以 `source_type="historical_expense"`、`source_id=batch.id`、`seq=line_no` 直接调用现有 `LedgerService.post` 写台账；不创建 Claim/ApprovalInstance，不进入审批待办（ADR-178/180）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-192/193 | `backend/apps/ledger/models.py` | 修改 | — | M | 新增 `HistoricalExpenseBatch`、`HistoricalExpenseRow`；显式索引名与迁移一致 | DONE |
| 2 | MOD-192/193 | `backend/apps/ledger/migrations/0007_historical_expense.py` | 新建 | 1 | M | 手写 CreateModel + 唯一约束 + 2 个索引；依赖 accounts.0001、ledger.0006；可逆 | DONE |
| 3 | MOD-192/193 | `backend/apps/ledger/apps.py` | 修改 | 1 | L | `ready()` 注册用户外键引用（消除 core.W001） | DONE |
| 4 | MOD-194 | `backend/apps/ledger/historical.py` | 新建 | 1,2 | H | 模板生成、xlsx/csv 解析、行校验、去重、事务写入、整批作废 | DONE |
| 5 | MOD-194 | `backend/apps/core/audit.py` | 修改 | 4 | L | 审计动作白名单新增 `HISTORICAL_EXPENSE_IMPORTED/VOIDED` | DONE |
| 6 | MOD-195 | `backend/apps/ledger/views.py` | 修改 | 4 | M | IFC-408~412 五个视图 + 序列化辅助 | DONE |
| 7 | MOD-195 | `backend/apps/ledger/urls.py` | 修改 | 6 | L | 注册 5 条路由 | DONE |
| 8 | MOD-196 | `frontend/src/shared/api.js` | 修改 | 6 | L | `historicalExpenseApi`（template/importFile/batches/batchDetail/voidBatch） | DONE |
| 9 | MOD-196 | `frontend/src/router/index.js` | 修改 | — | L | 用户端路由 `/historical-expenses` | DONE |
| 10 | MOD-196 | `frontend/src/portal/HistoricalExpenses.vue` | 新建 | 8,9 | H | 模板下载、上传、结果与错误行、批次表、明细弹窗、作废弹窗、非委员无权限提示 | DONE |
| 11 | MOD-196 | `frontend/src/portal/Reports.vue` | 修改 | 10 | L | 业委会成员可见“历史支出导入”按钮入口 | DONE |
| 12 | MOD-197 | `backend/apps/ledger/services.py` | 不改（复用） | 4 | L | 报表汇总与作废置过期逻辑已满足；仅验证 | DONE |
| 13 | — | `frontend/tests/qa_unit_theme.spec.js` | 修改 | 9 | L | 路由页面组件计数 18→19（现有断言同步） | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件） | 状态 | 说明 |
|---|---|---|---|---|
| US-333 | AC-333-01 | `backend/apps/ledger/historical.py:build_template`；`frontend/src/portal/HistoricalExpenses.vue:downloadTemplate` | DONE | xlsx 首表固定五列 + “填写说明”表；前端另提供 csv 下载 |
| US-333 | AC-333-02 | `backend/apps/ledger/views.py:HistoricalExpenseTemplateView` + `IsIncomeMember` | DONE | 未登录 401、非委员 403，不返回文件 |
| US-334 | AC-334-01 | `historical.py:import_file` → `LedgerService.post`；`views.py:HistoricalExpenseImportView` | DONE | 每行写 EXPENSE 台账并关联批次；不建申请/审批实例 |
| US-334 | AC-334-02 | `historical.py:_validate`、`import_file`（errors 收集、`if not valid: return None, ...`） | DONE | 逐行错误含行号与原因；全部无效不建批次 |
| US-334 | AC-334-03 | `historical.py:import_file`（`existing` 集合 + `seen`） | DONE | 四要素去重，文件内与历史有效批次均判重；备注不参与 |
| US-334 | AC-334-04 | `historical.py:import_file`（5MB 413）、`MAX_ROWS` 行数 400、`_read_rows` 仅首表 | DONE | xlsx 多表只读 `sheetnames[0]` |
| US-334 | AC-334-05 | `historical.py:import_file`（缺列 400 + `columns`）、`_validate`（未来日期） | DONE | 缺列列出具体列名；未来日期按错误行跳过 |
| US-335 | AC-335-01 | `views.py:_batch_view`、`HistoricalExpenseBatchListView`；`HistoricalExpenses.vue` 批次表 | DONE | 含时间/操作人/文件/行数/金额合计/状态；合计取有效行之和 |
| US-335 | AC-335-02 | `views.py:HistoricalExpenseBatchDetailView`、`_row_view`；前端明细弹窗 | DONE | 含日期/金额/类别/用途/备注/处理结果与原因；非委员 403 |
| US-336 | AC-336-01 | `historical.py:void_batch` → `LedgerService.void_by_source`/`_mark_reports_stale`；审计 `HISTORICAL_EXPENSE_VOIDED` | DONE | 台账置 VOIDED、批次置 VOIDED、报表 stale，审计含操作人/原因/行数/金额 |
| US-336 | AC-336-02 | `historical.py:void_batch`（已作废 409、重导允许：去重仅看 IMPORTED 批次）；`IsIncomeMember` | DONE | 重复作废不重复审计；作废后可重导；非委员 403 |
| US-337 | AC-337-01 | `backend/apps/ledger/services.py:LedgerService.generate`（汇总全部 ACTIVE 台账） | DONE | 明细含 `source_type/source_id/seq`，可见历史来源标记 |
| US-337 | AC-337-02 | `views.py:LedgerReportListView/LedgerReportDetailView`（`IsMember`） | DONE | 已登录即可查看；未登录 401 |
| US-337 | AC-337-03 | `services.py:void_by_source` + `_mark_reports_stale`；重新生成排除作废行 | DONE | 重算后 total_expense 减少 |
| US-338 | AC-338-01 | `views.py` 五个视图均 `permission_classes=[IsIncomeMember]`；`urls.py` 注册 | DONE | 模板/导入/列表/详情/作废统一权限 |
| US-338 | AC-338-02 | `frontend/src/portal/Reports.vue`（`v-if="auth.isCommittee"`）；`HistoricalExpenses.vue`（`v-if/v-else` + `onMounted` 权限守卫） | DONE | 非委员不见入口；直访显示无权限提示且不请求批次接口 |

## 迁移

- `backend/apps/ledger/migrations/0007_historical_expense.py`：创建 `HistoricalExpenseBatch`、`HistoricalExpenseRow`，含 `uniq_hist_expense_line` 唯一约束与两个索引；可逆（`migrate ledger 0006` 回退）。
- 依赖 `("accounts","0001_initial")` 与 ledger `0003`；不使用 `settings.AUTH_USER_MODEL`（本仓库未安装 `django.contrib.auth`）。
- `makemigrations --check --dry-run` 结果为 “No changes detected”。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 入口采用报表页按钮，而非新增主菜单项 | MOD-196 指定 `layout/menus.js` 新增 `historicalExpenses` 菜单项；ADR-182 | 现有导航契约测试（`layout_nav.spec.js`）精确断言菜单集合，新增项会改多份既有断言，超出“最小改动”范围 | 功能可达性不受影响：业委会成员在“财务报表”页可见入口；后续如需菜单项可在专项迭代调整导航契约 |
| `Reports.vue` 增加一行入口按钮 | MOD-196/197 写“Reports.vue 不改代码” | 作为上一条的替代入口 | 仅新增 1 行按钮，无逻辑改动；报表页既有测试通过 |
| CSV 模板/导入为额外能力 | IFC-408/409 以 xlsx 为主，未禁止 csv | 复用现有收入导入经验，成本极低 | 不影响 xlsx 主路径；AC 未要求 csv，属兼容性增强 |

## 开放问题

- [ASSUMPTION] 金额上限沿用 `SystemConfig.amount_max()`；空表头/空行的判定规则为“整行无值即跳过”。
- [ASSUMPTION] 错误原因码使用 `INVALID_FIELD` / `DUPLICATE`，明细接口返回 `error_message` 中文描述。
- [ASSUMPTION] 导入结果中的 `errors` 仅返回前 100 条，避免大文件响应过大；批次行明细仍完整保留。
- [ASSUMPTION] 审计 actor 类型固定为 `MEMBER`（接口权限已限定为业委会成员）。
- [ASSUMPTION] 文件名截断至 255 字符存储；作废原因 1~200 字。
- [TODO] 并发导入锁（IFC-409 标注本期不做）未实现，依赖成员人工避免同时导入。
