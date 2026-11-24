<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-24T22:55:00+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>0.1.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file><file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file></input_files>
  <phase>PHASE_06</phase>
  <status>DRAFT</status>
</file_header>

## 摘要

- 改动：13 个 MOD；后端 10 文件（含新建迁移 1）、前端 10 文件（含新建 `AccountSelect.vue`）、小程序 2 文件、测试调整 7 文件。`git diff --stat`：34 files changed, 594 insertions(+), 163 deletions(-)；另有 2 个新增文件（`backend/apps/ledger/migrations/0008_historical_expense_approval.py`、`frontend/src/shared/AccountSelect.vue`）。
- 五维平均分：8.8 / 10。
- 问题统计：CRITICAL 2（已修复 2）/ MAJOR 1（已修复 1）/ MINOR 7（已修复 5，遗留 2）。
- 说明：`git diff --stat` 中 `.trae/sdlc/project_profile.md`、`project_workspace/_kb_inbox.jsonl`、`ocap_appeal_center`、`ocap_navigation_ia` 与 `registry_import_投票权清单.xlsx` 为本任务开始前已存在的改动，未触碰。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| backend/apps/ledger/models.py、migrations/0008_*.py | MOD-207 / IFC-419 |
| backend/apps/ledger/historical.py、apps.py | MOD-208 / IFC-419、IFC-422 |
| backend/apps/core/audit.py | MOD-208 / IFC-419 |
| backend/apps/approval/services.py | MOD-208 / IFC-419 |
| backend/apps/ledger/views.py、urls.py | MOD-203/209 / IFC-418、IFC-419、IFC-422 |
| backend/apps/ledger/services.py | MOD-202 / IFC-418 |
| backend/apps/income/views.py | MOD-211 / IFC-420、IFC-421 |
| backend/apps/claims/views.py | MOD-212 / IFC-423 |
| frontend/src/shared/AccountSelect.vue | MOD-204 / IFC-420 |
| frontend/src/portal/Reports.vue、AccountCard.vue | MOD-205 / IFC-418 |
| frontend/src/portal/ReportDetailDialog.vue | MOD-206 / IFC-418 |
| frontend/src/portal/Income.vue、shared/api.js | MOD-209/211 / IFC-420、IFC-421 |
| frontend/src/portal/Claims.vue | MOD-212 / IFC-423 |
| frontend/src/portal/HistoricalExpenses.vue、shared/confirm.js | MOD-210 / IFC-422 |
| frontend/src/admin/AdminAccounts.vue | MOD-213 / IFC-417 |
| miniprogram/utils/api.js、pages/claims/index.vue | MOD-214 / IFC-424 |

## 自验证结果

| 命令 | 输出尾部 |
|---|---|
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings`（backend/） | `No changes detected` |
| `python manage.py test --settings=config.test_settings`（backend/） | `Ran 1238 tests in 46.738s` / `OK (skipped=2)` |
| `python manage.py test tests.unit.test_history_expense_rules tests.unit.test_ledger_accounts_unit tests.integration.test_history_expense_api tests.integration.test_finance_accounts_api tests.e2e.test_history_expense_journey tests.e2e.test_finance_accounts_journey --settings=config.test_settings` | `Ran 45 tests` / `OK` |
| `npx vitest run --passWithNoTests`（frontend/） | `Test Files 56 passed (56)` / `Tests 595 passed (595)` |
| `npx vitest run tests/finance_accounts_ui.spec.js tests/pages.spec.js tests/ui_blocks.spec.js tests/approval_finality.spec.js tests/historical_expenses.spec.js` | `Test Files 5 passed (5)` / `Tests 43 passed (43)` |
| `npm run build`（frontend/） | `✓ built in 8.47s`（仅有既有 chunk 体积告警） |
| `npm test`（miniprogram/） | `Test Files 21 passed (21)` / `Tests 151 passed (151)` |
| `$env:UNI_INPUT_DIR=<repo>; npx uni build -p mp-weixin`（miniprogram/） | `DONE Build complete.` |

未验证项：无。说明：`npm run build:mp-weixin` 直接执行会因仓库根布局找不到 `src/manifest.json` 失败；按既有布局设置 `UNI_INPUT_DIR` 后构建通过，未修改构建配置（画像未定义该构建命令）。构建产物已删除。

## 按模块评审

### MOD-202 / MOD-203（报表按账户聚合）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MINOR | ledger/views.py:ReportSerializer / Reports.vue:loadReports | 无可用账户时仍会请求报表列表，与 IF-C418 空态语义不符 | FIXED（selectedAccountId 为空直接返回） |
| CR-007 | MINOR | ledger/services.py:_totals_by_period | 单次扫描后在 Python 中按报表周期分桶为 O(条目数×报表数)；当前 page_size≤100、单账户数据量有限，满足 COND-B-02 的"一次查询"要求 | OPEN（可接受，后续可改 SQL 条件聚合） |

### MOD-207 / MOD-208（历史支出审批）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | CRITICAL | historical.py:create_pending_batch；income/views.py:_existing_duplicate_keys | 去重原先跨账户比较四项键，会误跳过另一账户同日同额同类同说明的合法记录 | FIXED（按目标账户过滤，并兼容 account 为空的历史旧数据） |
| CR-003 | MAJOR | historical.py:void_batch | 旧作废逻辑允许对审批中批次作废，造成状态歧义 | FIXED（非 IMPORTED 返回 409"审批中的批次请先撤回"） |

### MOD-209 / MOD-210（历史支出接口与页面）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | CRITICAL | income/views.py:IncomeImportView.post | 账户解析被放在去重查询之后，导致 UnboundLocalError（导入 500） | FIXED（先解析 account 再去重） |
| CR-008 | MINOR | ledger/views.py:批次列表 | 批次行已入账数需避免 N+1；当前用 annotate(posted_rows) + select_related | FIXED |

### MOD-204 / MOD-205 / MOD-206（账户选择与报表 UI）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MINOR | AccountCard.vue emit | 契约要求 select 事件带 account.id，初版未带参 | FIXED |
| CR-006 | MINOR | Income.vue AC-411-03 | "暂无可用账户"初版仅在空下拉内可见，页面无提示 | FIXED（弹窗内可见提示 + 保存禁用） |

### MOD-211 / MOD-212 / MOD-213（收入、报销、账户管理）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MINOR | AdminAccounts.vue:操作列 | 链接按钮在默认主题下与背景同色，对比度不足 | FIXED（改为带边框 plain 按钮，禁用态可区分） |

### MOD-214（小程序）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-010 | MINOR | miniprogram/pages/claims/index.vue | 账户列表加载失败时仅置空，未提示"暂无可用账户"；提交仍会被校验拦截 | OPEN（可接受，后续可补充提示） |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

本轮无缺陷修复模式（未收到 `<defects>`）。

## 现有测试调整

| 文件 | 调整原因 |
|---|---|
| backend/tests/integration/test_history_expense_api.py | 历史支出导入改为必须携带 `approval_flow_id` 且审批通过后入账；新增 INCOME 审批流程与审批人，`_import_three`/`_import_year` 导入后审批，断言由"导入即入账、无审批实例"改为"PENDING→审批→IMPORTED" |
| backend/tests/e2e/test_history_expense_journey.py | 同上；全链路增加审批步骤，重新导入后需再次审批才统计为已入账 |
| frontend/tests/pages.spec.js | 报销/备用金提交载荷新增 `account_id`；无账户默认值时表单校验会阻止请求 |
| frontend/tests/ui_blocks.spec.js | 同上，并在 mock 路由补充账户摘要 |
| frontend/tests/approval_finality.spec.js | 收入重新发起弹窗新增账户选择，补充账户摘要 mock |
| frontend/tests/finance_accounts_ui.spec.js | 报表详情请求由无参数改为 `{account_id: 1}` |
| frontend/tests/historical_expenses.spec.js | 批次状态文案由"已导入"改为"已入账" |
| miniprogram/tests/pages.spec.js、ui_blocks.spec.js | 报销/备用金提交载荷新增 `account_id`，并补充账户摘要 mock |
