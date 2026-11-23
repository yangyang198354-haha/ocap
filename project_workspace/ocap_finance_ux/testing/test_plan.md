<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T23:26:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/requirements/user_stories.md</file>
    <file>project_workspace/ocap_finance_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_finance_ux/development/code_review_report.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — ocap_finance_ux（GROUP_D）

## 测试策略

- 被测改动：账户实体与余额、流水账户归属、报表期初/期末链式生成与级联、账户/报表 API、门户财务报表页与主页卡片、管理端账户管理。
- 范围：in scope = 本次 10 个 MOD 与 IFC-409~417；out of scope = 微信小程序、部署环境、历史旧报表的具体数值（标记旧口径）。
- 环境：Python 3.14.6 + Django 6.0.6 + DRF 3.17.1；`--settings=config.test_settings`（SQLite 内存库，表由模型直建、**不执行迁移**）；前端 vitest + Vue Test Utils + Element Plus。
- 判定模式：INCREMENTAL baseline（零新增失败）。基线 = GROUP_C 门控时全量：后端 `Ran 1188 tests OK (skipped=2)`、前端 `Test Files 52 passed`。
- 分层：目录分层——`backend/tests/unit/`（服务/模型）、`backend/tests/integration/`（DRF + ORM + 路由）、`backend/tests/e2e/`（多步 API 旅程）、`frontend/tests/*.spec.js`（组件 + HTTP 替身）。
- critical path 口径：替代（多步 API 旅程 TC-E2E-1401 + 前端组件用例），项目无浏览器 E2E 框架。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-405-01/02 | TC-UNIT-1401 | 单元 | auto | 新写 | `tests/unit/test_ledger_accounts_unit.py::AccountServiceTests::test_balance_only_counts_active_entries` | 默认账户 + 有效/作废流水 | 计算余额 | 100−30=70.00，作废不计 | 100/30/999 |
| AC-409-03/04/05 | TC-UNIT-1402 | 单元 | auto | 新写 | 同上 `::test_recent_entries_order_limit_and_status` | 同账户 12 条 + 1 条作废 | 取最近 10 条 | 10 条、日期倒序、同日 id 倒序、排除作废 | 12 条 + 作废 |
| AC-406-01/02、AC-407-01 | TC-UNIT-1403 | 单元 | auto | 新写 | 同上 `::test_default_account_and_implicit_assignment` | 默认账户 | 直接 create 流水 | 自动归入默认账户且唯一 | — |
| AC-407-04 | TC-UNIT-1406 | 单元 | auto | 新写 | 同上 `::test_resolve_account_rejects_disabled_or_missing` | 不存在/停用账户 | resolve | `ACCOUNT_UNAVAILABLE` | id=10^6、DISABLED |
| AC-403-01/02/03/06 | TC-UNIT-1404 | 单元 | auto | 新写 | `tests/unit/test_ledger_accounts_unit.py::ReportChainTests::test_quarter_and_year_chain` | Q1~Q4 + 年度 | 逐期生成 | Q1 期初 0；Q2 期初=Q1 期末；年度对齐 Q1 期初/Q4 期末；差额=收支差 | 2025 年 |
| AC-403-05 | TC-UNIT-1405 | 单元 | auto | 新写 | 同上 `::test_void_marks_later_periods_and_cascade` | Q1~Q3 已生成 | Q2 补录支出后重生成 Q2 | Q2/Q3 stale，Q3 期初=Q2 期末 | 2025 年 |
| AC-403-06 | TC-UNIT-1407 | 单元 | auto | 新写 | 同上 `::test_legacy_report_has_null_open_close` | legacy 报表 | 读取字段 | 期初/期末为 NULL | 2024 |
| AC-405-04、AC-409-01/02 | TC-INT-1407 | 集成 | auto | 新写 | `tests/integration/test_finance_accounts_api.py::AccountApiTests::test_summary_permissions_shape_and_totals` | 成员/匿名/管理员令牌 | GET 汇总 | 成员 200，合计/余额/结构正确；匿名 401，管理员 403 | 100/20 |
| AC-405-04、AC-409-04 | TC-INT-1408 | 集成 | auto | 新写 | 同上 `::test_summary_enabled_filter_and_recent_zero` | 含停用账户 | GET ?status=ENABLED&recent=0 | 过滤停用；明细为空 | DISABLED 账户 |
| AC-404-01/02/04/05 | TC-INT-1409 | 集成 | auto | 新写 | 同上 `::test_admin_account_crud_validation_and_audit` | 管理员/成员令牌 | 创建 + 重复 + 空名 + 非管理员 | 201 余额 0.00；409 ACCOUNT_NO_EXISTS；400 INVALID_VALUE；403 | ZJ-001 |
| AC-404-02/03、AC-405-01 | TC-INT-1410 | 集成 | auto | 新写 | 同上 `::test_patch_name_account_no_status_and_default_transfer` | 两个账户 + 流水 | PATCH 改名/设默认/停用 | 默认唯一、流水与余额不变、停用保留 | B-001 |
| AC-401-01/02、AC-403-01/06 | TC-INT-1411 | 集成 | auto | 新写 | `ReportChainApiTests::test_report_list_filters_and_chain_fields` | 季/年报表 | GET 列表按 period_type | 仅返回对应类型，含期初期末 | 300.00 |
| AC-402-05、AC-403-03 | TC-INT-1412 | 集成 | auto | 新写 | 同上 `::test_report_detail_account_perspective` | 两账户流水 | 详情带/不带 account_id | 组织口径 200/120；账户口径 0/80；不存在 404 | 200/80 |
| AC-403-06 | TC-INT-1413 | 集成 | auto | 新写 | 同上 `::test_legacy_report_detail_keeps_nulls` | legacy 报表 | GET 详情 | legacy=true，期初期末 null | 2024 |
| AC-407-01/02 | TC-INT-1414 | 集成 | auto | 新写 | `PostingAccountApiTests::test_income_sheet_uses_selected_account` | 收入流程 + 审批人 | 带 account_id 建表→提交→审批 | 流水归属所选账户 | 66.00 |
| AC-407-04 | TC-INT-1415 | 集成 | auto | 新写 | 同上 `::test_income_sheet_rejects_disabled_account` | 停用账户 | 提交收入表 | 409 ACCOUNT_UNAVAILABLE，无流水 | 1.00 |
| AC-407-03 | TC-INT-1416 | 集成 | auto | 新写 | 同上 `::test_advance_uses_selected_account` | 备用金流程 | 带 account_id 申请→审批 | 支出条目归属所选账户 | 50.00 |
| AC-401/403/405/407/408/409 | TC-E2E-1401 | E2E（替代） | auto | 新写 | `tests/e2e/test_finance_accounts_journey.py::test_account_report_journey` | 管理员 + 业委会 + 审批人 | 建账户→收入生效→汇总→生成链式报表→过滤/详情→作废→级联→停用 | 各步数值与状态断言全部成立 | 2025 年、100.00 |
| AC-409-01/03 | TC-WEB-1401 | 集成（前端） | auto | 新写 | `frontend/tests/finance_accounts_ui.spec.js` 财务报表页第 1 例 | mock HTTP | 挂载 Reports | 展示合计、账户名、¥100.00、报表条目 | SUMMARY |
| AC-401-01/04 | TC-WEB-1402 | 集成（前端） | auto | 新写 | 同上第 2 例 | mock HTTP | 点击「仅年报」 | 请求参数含 `period_type=YEAR` | — |
| AC-402-01/02 | TC-WEB-1403 | 集成（前端） | auto | 新写 | 同上第 3 例 | mock HTTP | 点击报表 → 关闭浮层 | 请求详情、浮层含期初/期末、关闭后列表仍在 | DETAIL |
| AC-408-01/03 | TC-WEB-1404 | 集成（前端） | auto | 新写 | 同上 主页用例 | mock HTTP | 挂载 Home + 点击卡片 | 余额与账户名、跳转 `/reports` | SUMMARY |
| AC-404-04 | TC-WEB-1405 | 集成（前端） | auto | 新写 | 同上 管理端用例 | mock adminHttp | 新建账户空表单保存 | 提示「请填写账户名称」且不 POST | — |

## 测试数据需求

- 后端：默认账户由 `AccountService.default_account()` 在用例内创建（测试设置不执行迁移，无法依赖 0005 回填）。
- 前后端数值统一 2025 年期间（避免“未来期间”校验），账户号使用固定前缀 `ZJ-001`/`B-001`/`IN-001`，每个用例独立测试库，无跨用例污染。
- 无 `[DATA_REQUIRED]`。

## 不可测项

| AC | 原因 | 处理 |
|---|---|---|
| AC-406-03/04（迁移幂等、总额不变） | 测试设置以模型直建表、`Apply all migrations: (none)`，迁移脚本不执行 | 人工验证清单 M-01：在测试环境 MySQL 快照上执行 0004→0006 并核对总额 |
| AC-401-06（刷新回默认筛选/第 1 页） | 浏览器刷新行为，非组件单测可覆盖 | 人工验证 M-02 |
| AC-402-03（360px 无横向滚动） | 依赖真实布局引擎 | 人工验证 M-03 |
| AC-402-04（减少动态效果） | `prefers-reduced-motion` 媒体查询在 jsdom 不生效 | 人工验证 M-04 |
| AC-408-04（卡片加载失败重试） | 组件已实现 try/catch + 重试按钮，未自动化 | 人工验证 M-05 |
| AC-405-03（不缓存余额列） | 结构性约束 | code_review_report：`LedgerAccount` 无 balance 字段，余额实时聚合 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-322 周期筛选 | TC-WEB-1402、TC-E2E-1401 | 前端集成 / E2E |
| US-323 动效浮层详情 | TC-WEB-1403 | 前端集成 |
| US-324 期初期末链式 | TC-UNIT-1404、TC-UNIT-1405、TC-INT-1411、TC-E2E-1401 | 单元 / 集成 / E2E |
| US-325 多账户管理 | TC-INT-1409、TC-INT-1410、TC-WEB-1405、TC-E2E-1401 | 集成 / 前端 / E2E |
| US-326 账户盈余 | TC-UNIT-1401、TC-INT-1410、TC-E2E-1401 | 单元 / 集成 / E2E |
| US-327 存量迁入默认账户 | [NOT_TESTABLE: 测试设置不执行迁移] → 人工验证 M-01 | — |
| US-328 单据账户归属 | TC-INT-1414、TC-INT-1415、TC-INT-1416、TC-UNIT-1403 | 集成 / 单元 |
| US-329 主页卡片 | TC-WEB-1404、TC-E2E-1401 | 前端集成 / E2E |
| US-330 账户卡片与最近 10 笔 | TC-WEB-1401、TC-UNIT-1402、TC-INT-1407、TC-E2E-1401 | 前端 / 单元 / 集成 / E2E |

## 人工验证清单（摘要，详见 e2e_test_report）

- M-01 迁移回填（对应 US-327 / AC-406-03/04）
- M-02 刷新默认筛选（AC-401-06）
- M-03 360px 浮层布局（AC-402-03）
- M-04 减少动态效果（AC-402-04）
- M-05 主页卡片失败重试（AC-408-04）
