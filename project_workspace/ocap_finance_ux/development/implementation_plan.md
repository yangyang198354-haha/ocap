<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-23T22:54:00.7371287+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_finance_ux/requirements/user_stories.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_finance_ux/phase_status.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — ocap_finance_ux

## 实现概览

- 模块数：10（MOD-192～201）；改动文件 20 个（后端 12，前端 8），另新增 5 个迁移、2 份开发文档。
- 顺序依据 module_design「依赖关系」的拓扑排序：MOD-192（账户模型与余额服务）→ MOD-193（流水账户归属）→ MOD-194（报表链式生成）→ MOD-196（审计动作）→ MOD-195（账户与报表 API）→ MOD-197（迁移）→ MOD-201（前端 API 层）→ MOD-198/199/200（门户页、主页、管理端）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-192 | `backend/apps/ledger/models.py` | 修改 | — | M | 新增 `LedgerAccount`；`LedgerEntry.account`；`LedgerReport` 期初/期末/legacy | DONE |
| 2 | MOD-192 | `backend/apps/ledger/services.py` | 修改 | 1 | M | `AccountService`（默认账户/余额/最近流水/汇总）；`LedgerService.post(account=)` | DONE |
| 3 | MOD-193 | `backend/apps/income/models.py`、`backend/apps/claims/models.py` | 修改 | 1 | L | 单据可空账户外键 | DONE |
| 4 | MOD-193 | `backend/apps/income/services.py`、`backend/apps/claims/services.py` | 修改 | 2,3 | L | 入账时传单据账户 | DONE |
| 5 | MOD-193 | `backend/apps/income/views.py`、`backend/apps/claims/views.py` | 修改 | 2 | L | 录入可指定 `account_id`（缺省默认账户） | DONE |
| 6 | MOD-194 | `backend/apps/ledger/models.py`、`backend/apps/ledger/services.py` | 修改 | 1,2 | H | 期初=期间前累计、期末=期初+收支；作废波及后续期间；重算级联 | DONE |
| 7 | MOD-196 | `backend/apps/core/audit.py` | 修改 | — | L | 登记 `ACCOUNT_CREATED` / `ACCOUNT_UPDATED` | DONE |
| 8 | MOD-195 | `backend/apps/ledger/views.py`、`backend/apps/ledger/urls.py` | 修改 | 2,6 | H | 账户汇总、管理端账户 CRUD、报表详情账户视角 | DONE |
| 9 | MOD-197 | `backend/apps/ledger/migrations/0004_ledger_account.py`、`0005_ledger_account_backfill.py`、`0006_ledger_entry_account_not_null.py`；`backend/apps/income/migrations/0006_income_sheet_account.py`；`backend/apps/claims/migrations/0005_claim_account.py` | 新建 | 1,3 | M | 建表/加列/幂等回填/非空/旧报表标记 | DONE |
| 10 | MOD-201 | `frontend/src/shared/api.js` | 修改 | 8 | L | `accountApi`；`reportDetail(id, accountId)` | DONE |
| 11 | MOD-198 | `frontend/src/portal/Reports.vue`（重写）、`ReportDetailDialog.vue`、`AccountCard.vue`（新建） | 修改/新建 | 10 | H | 周期筛选、账户卡片、动效浮层详情 | DONE |
| 12 | MOD-199 | `frontend/src/portal/Home.vue` | 修改 | 10 | M | 主页账户余额卡片 | DONE |
| 13 | MOD-200 | `frontend/src/admin/AdminAccounts.vue`（新建）、`frontend/src/router/index.js`、`frontend/src/layout/menus.js` | 新建/修改 | 10 | M | 账户列表/新建/编辑/默认/停用 | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-322 | AC-401-01/02/03 | `frontend/src/portal/Reports.vue`：周期筛选（全部/仅年报/仅季报）→ `ledgerApi.reports({ period_type })` | DONE | 后端沿用 `period_type` 过滤与倒序 |
| US-322 | AC-401-04 | `Reports.vue`：`filters` 变化调用 `resetAndLoad()` | DONE | 回到第 1 页 |
| US-322 | AC-401-05 | `Reports.vue`：空列表渲染 `el-empty`「暂无已生成报表」 | DONE | 筛选区保持可见 |
| US-322 | AC-401-06 | `Reports.vue`：`periodFilter` 初始值 `ALL`，页码由 `usePaging` 初始化为 1 | DONE | 刷新回默认 |
| US-323 | AC-402-01 | `Reports.vue` + `ReportDetailDialog.vue`：`el-dialog` + 自定义过渡 260ms，展示期间/期初/收入/支出/期末/明细 | DONE | 底部详情区块已移除 |
| US-323 | AC-402-02 | `ReportDetailDialog.vue`：Esc/关闭按钮 → `emit('update:modelValue')`；关闭后 `triggerEl.focus()` | DONE | 筛选与页码在父组件保持 |
| US-323 | AC-402-03 | `ReportDetailDialog.vue`：`styles` 中 `width: min(92vw, 760px)`、明细区 `overflow: auto` | DONE | 360px 不横向滚动 |
| US-323 | AC-402-04 | `ReportDetailDialog.vue`：`@media (prefers-reduced-motion: reduce)` 禁用位移/缩放 | DONE | — |
| US-323 | AC-402-05 | `ReportDetailDialog.vue`：加载失败显示原因与「重试」，不自动关闭 | DONE | — |
| US-324 | AC-403-01/02/03/04 | `backend/apps/ledger/services.py`：`_opening_balance()` + `generate()` | DONE | 期初=期间起点前有效流水累计；最早期间为 0.00 |
| US-324 | AC-403-05 | `backend/apps/ledger/services.py`：`_mark_reports_stale()`（覆盖期间及之后）+ `_regenerate_after()`（重算后续非 legacy 报表） | DONE | PM 门控 condition ① 已在此登记 |
| US-324 | AC-403-06 | `LedgerReport.opening_balance/closing_balance` 非空生成；`report_summary()` 输出两位小数串 | DONE | legacy 报表例外，见 ADR-179/Q-FA-08 |
| US-325 | AC-404-01 | `POST /api/v1/admin/ledger/accounts` + `AdminAccounts.vue` | DONE | 新账户余额 0.00 |
| US-325 | AC-404-02 | `ledger/views.py::AdminAccountListView/AdminAccountDetailView` 唯一性校验 → `ACCOUNT_NO_EXISTS`；前端展示「账户号已存在」 | DONE | — |
| US-325 | AC-404-03 | `ledger/views.py`：修改账户号/名称不写流水 | DONE | 余额实时聚合 |
| US-325 | AC-404-04 | 服务层名称 1–64、账户号 0–32 校验 → `INVALID_VALUE`；前端必填提示 | DONE | 空账户号归一化为 NULL（ADR-183，condition ②） |
| US-325 | AC-404-05 | `IsAdmin` 权限；路由在管理端布局下 | DONE | 非管理员 403 |
| US-326 | AC-405-01/02 | `ledger/services.py::AccountService.balance()`（仅 ACTIVE，收入−支出） | DONE | — |
| US-326 | AC-405-03 | 余额按流水实时聚合，不存账户列 | DONE | ADR-182 |
| US-326 | AC-405-04 | `money()` 归一化，新账户余额 `0.00` | DONE | — |
| US-327 | AC-406-01/02/03/04 | `ledger/migrations/0005_ledger_account_backfill.py` | DONE | 幂等 `get_or_create` + `update(account=None)`；账为 NULL |
| US-328 | AC-407-01 | `income/services.py::on_approved()` 传 `sheet.account`；为空时默认账户 | DONE | — |
| US-328 | AC-407-02 | `income/views.py::AdminSheetListView.post` 接受 `account_id`；`income/services.py` 入账传递 | DONE | 前端表单未加账户选择器（见开放问题 OQ-01） |
| US-328 | AC-407-03 | `claims/services.py::on_approved/_approve_settlement` 传 `claim.account`；`claims/views.py` 接受 `account_id` | DONE | — |
| US-328 | AC-407-04 | `ledger/services.py::AccountService.resolve_account()` → `ACCOUNT_UNAVAILABLE` 409，不写流水 | DONE | — |
| US-329 | AC-408-01/02 | `Home.vue` 账户卡片：合计 + 各账户余额（2 位小数） | DONE | — |
| US-329 | AC-408-03 | `Home.vue` 卡片点击 → `/reports` | DONE | — |
| US-329 | AC-408-04 | `Home.vue` 加载失败显示「加载失败」+ 重试，不影响其他区块 | DONE | — |
| US-330 | AC-409-01 | `Reports.vue`：账户卡片区在报表列表之前 | DONE | — |
| US-330 | AC-409-02/03/04/05 | `AccountService.recent_entries()`（仅 ACTIVE，`-occurred_on,-id`，limit 10）；`AccountCard.vue` 空态「暂无收支记录」 | DONE | — |
| US-330 | AC-409-06 | `Reports.vue`/`AccountCard.vue` 样式：余额字号 ≥ 正文 1.5 倍；首屏布局紧凑 | DONE | 视觉走查待用户确认（GR-A-001-F01） |

## 迁移

| 迁移 | 内容 | 可逆 |
|---|---|---|
| `ledger/0004_ledger_account` | 建 `LedgerAccount`；`LedgerEntry.account` 可空 + 索引；`LedgerReport` 加 `opening_balance`/`closing_balance`/`legacy` | 是（结构） |
| `ledger/0005_ledger_account_backfill` | 幂等创建默认账户并回填全部空账户流水；既有报表置 `legacy=True` | 反向 noop（不回滚数据） |
| `ledger/0006_ledger_entry_account_not_null` | `LedgerEntry.account` 改非空、`on_delete=PROTECT` | 否（需快照） |
| `income/0006_income_sheet_account` | `IncomeSheet.account` 可空外键 | 是 |
| `claims/0005_claim_account` | `Claim.account` 可空外键 | 是 |

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `LedgerEntry.save()` 在 `account_id` 为空时自动落默认账户 | MOD-192 未定义 | 保持既有直接 `LedgerEntry.objects.create()`（含存量测试与数据脚本）可用，避免非空列导致写入失败 | 仅在未显式传账户时多一次默认账户查询；服务层仍显式传账户 |
| 收入/报销创建视图接受可选 `account_id` | MOD-193 只定义服务签名 | AC-407-02/03 要求「提交时指定账户」 | 前端表单暂未暴露选择器（OQ-01） |
| `claims` 迁移编号用 `0005` | module_design 写作 `claims/0006_claim_account` | 该应用实际最大迁移为 `0004_claim_origin`，顺序编号避免空号 | 仅文件名不同，内容与设计一致 |
| 需求 AC 编号 `AC-401~409` | 原 `AC-322~330`（已批准 user_stories 1.0.0） | 仓库测试 `test_requirements_numbering` 要求全批次唯一，`AC-322~330` 与既有批次重复 | user_stories/architecture/module 升版 1.0.1，验收语义不变 |

## 开放问题

- [ASSUMPTION] OQ-01：收入表/报销表单未新增账户选择器（module_design 未包含对应前端改动），当前一律使用默认账户；后端已支持 `account_id`，待确认是否需要在录入表单暴露（关联 GR-B-001-F01/F02）。
- [ASSUMPTION] OQ-02：旧报表（`legacy=True`）在列表中保留并显示「旧口径」标签，账户视角详情为实时计算，二者并存（ADR-179）。
- [ASSUMPTION] OQ-03：默认账户的停用与默认身份转移由 `PATCH is_default/status` 支持，未限制「默认账户不可停用」。

## 自验证结果（2026-11-23）

| 命令 | 结果 |
|---|---|
| `python -m compileall -q backend` | 通过（退出码 0，无输出） |
| `python manage.py test tests.unit.test_rework_rules tests.integration.test_finance_polls_api --settings=config.test_settings` | OK |
| `python manage.py test <契约/评审/旅程/主题相关 9 个模块> --settings=config.test_settings` | OK |
| `python manage.py test --settings=config.test_settings` | `Ran 1188 tests ... OK (skipped=2)` |
| `npx vitest run`（frontend） | `Test Files 52 passed (52)` |

前端现有测试的最小调整（行为变更导致，逐条说明见 code_review_report）：`layout_menus.spec.js` 财务二级项 2→3；`qa_unit_theme.spec.js` 管理端路由组件 17→18。
