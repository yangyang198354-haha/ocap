<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-23T23:16:20.1124833+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.1</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_finance_ux/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — ocap_finance_ux（GROUP_C）

## 摘要

- 改动文件：17 个修改 + 8 个新增（3 个前端组件、5 个迁移），共约 +644 / −104 行（`git diff --stat`，不含 `project_workspace` 文档与既有无关改动）。
- 五维平均分：7.9 / 10（Correctness 8.4、Security 9.2、Performance 6.6、Maintainability 7.6、Testability 7.8）。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 1（Open）/ MINOR 4（Open 3，Fixed 1）。
- 自验证：后端 `Ran 1188 tests … OK (skipped=2)`；前端 `Test Files 52 passed (52)`。

## 文件 → MOD/IFC 映射

| 文件 | MOD | IFC |
|---|---|---|
| `backend/apps/ledger/models.py` | MOD-192/194 | ADR-178/180/183 |
| `backend/apps/ledger/services.py` | MOD-192/193/194 | IFC-417 |
| `backend/apps/ledger/views.py`、`urls.py` | MOD-195 | IFC-409~414 |
| `backend/apps/income/{models,services,views}.py` | MOD-193 | — |
| `backend/apps/claims/{models,services,views}.py` | MOD-193 | — |
| `backend/apps/core/audit.py` | MOD-196 | REQ-NFUNC-071 |
| `backend/apps/ledger/migrations/0004~0006`、`income/0006`、`claims/0005` | MOD-197 | ADR-181 |
| `frontend/src/shared/api.js` | MOD-201 | IFC-409~413 |
| `frontend/src/portal/Reports.vue`、`ReportDetailDialog.vue`、`AccountCard.vue` | MOD-198 | REQ-FUNC-333/334/341 |
| `frontend/src/portal/Home.vue` | MOD-199 | REQ-FUNC-340 |
| `frontend/src/admin/AdminAccounts.vue`、`router/index.js`、`layout/menus.js` | MOD-200 | IFC-410~412 |

## 自验证结果

| 命令 | 输出尾部 |
|---|---|
| `python -m compileall -q backend` | 退出码 0，无输出 |
| `python manage.py test tests.unit.test_rework_rules tests.integration.test_finance_polls_api --settings=config.test_settings` | `OK`（含报表 stale/重算用例） |
| `python manage.py test tests.integration.test_frontend_contract tests.integration.test_product_review_ac tests.integration.test_product_review_api tests.integration.test_rework_cr011_024 tests.integration.test_e2e_fixture_command tests.integration.test_ui_theme_qa tests.integration.test_admin_appeals_regression tests.e2e.test_rework_journeys tests.e2e.test_journeys --settings=config.test_settings` | `OK` |
| `python manage.py test --settings=config.test_settings` | `Ran 1188 tests in 46.604s` / `OK (skipped=2)` |
| `npx vitest run`（frontend） | `Test Files 52 passed (52)` |

未验证项：无（前后端命令均在本机实测执行）。性能阈值（REQ-NFUNC-070：报表页 P95 ≤ 2 s、详情 ≤ 500 ms）未做压测，记为遗留风险 CR-002。

## 按模块评审

### MOD-192 账户模型与余额服务

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 7/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MINOR | `backend/apps/ledger/services.py:AccountService.summary` | 每个账户各做一次余额聚合与一次最近流水查询（N+1）；账户少时可接受，账户增多需一次聚合或缓存（ADR-182 已记风险） | OPEN |
| CR-005 | MINOR | `backend/apps/ledger/services.py:AccountService.default_account` | 并发首次调用可能创建多个同名账户（名称非唯一）；迁移已保证默认账户存在，风险低 | OPEN |

### MOD-193 流水账户归属

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MAJOR | `frontend/src/portal/Income.vue`、`Claims.vue` | 录入表单未新增账户选择器，当前一律使用默认账户；后端已支持 `account_id` 并在账户停用/不存在时返回 `ACCOUNT_UNAVAILABLE`。module_design 未分配该前端改动，待用户确认（OQ-01 / F01/F02） | OPEN |

### MOD-194 报表链式生成

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 6/10 | 7/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `services.py:_mark_reports_stale`、`_regenerate_after` | 逐条报表计算期间范围；报表数量按年/季增长，量级小，后续可改单条 SQL 条件更新 | OPEN |
| CR-006 | MINOR | `services.py:generate` | 级联重算在同一事务内按期间升序全量重算受影响报表，未做变更检测（仅在期间受影响时执行） | OPEN |

### MOD-195 账户与报表 API

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 6/10 | 7/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MINOR | `views.py:AdminAccountListView.get` | 列表每行单独聚合余额（N+1）；管理端账户数少，接口分页默认小 | OPEN |
| CR-007 | MINOR | `views.py:LedgerReportDetailView.get` | 账户视角返回 `legacy=False`（实时计算），与父报表 `legacy` 标签不同，建议交接表单中说明 | OPEN |

### MOD-196 审计动作登记

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

无问题。

### MOD-197 数据迁移

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-008 | MINOR | `ledger/migrations/0005_ledger_account_backfill.py` | 反向迁移为 noop，回退需数据库快照（ADR-181/C-375 已声明）；迁移在测试库全量重放通过 | FIXED（按设计保留） |

### MOD-198/199/200/201 前端

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MINOR | `Reports.vue` / `ReportDetailDialog.vue` | 账户卡片与报表列表分别请求，首屏两次网络往返；数据量小，未合并接口 | OPEN |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

| CR | 原因 | 建议处理时机 |
|---|---|---|
| CR-004 | 收入/报销表单的账户选择器不在 module_design 的 MOD-193/198 范围内，属需求确认项（Q-FA-05 的 UI 落点、F01/F02）；后端契约已就绪，补 UI 属增量小改 | 用户确认 OQ-01 后，作为 GROUP_C 缺陷回流或下一迭代处理 |

## 缺陷修复

| DEF | 级别 | 位置 | 根因 | 修改说明 |
|---|---|---|---|---|
| DEF-001（GROUP_D 回流，PM 授权最小修复） | MAJOR | `frontend/src/portal/Reports.vue`、`frontend/src/portal/ReportDetailDialog.vue` | `usePaging` 对 `filters` 只做 `unref`，传入函数时被展开为空对象，导致「仅年报/仅季报」请求缺少 `period_type`；`el-option` 绑定 `null` 触发 Element Plus 属性类型告警 | `filters` 改为 `computed`；「全部账户」选项 value 改为空串，请求层 `accountId || null` 归一化；修复后 TC-WEB-1401~1405 与全量回归通过 |

## 现有测试调整

| 测试 | 调整 | 原因 |
|---|---|---|
| `frontend/tests/layout_menus.spec.js` | 财务二级项期望由 2 项改为 3 项（新增「账户管理」），标题同步 | 管理端「财务」分组按 ADR-185 新增入口 |
| `frontend/tests/qa_unit_theme.spec.js` | 管理端路由组件数 17→18 | 新增 `AdminAccounts.vue` 路由 |
