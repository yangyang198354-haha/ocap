<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T18:01:00+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/requirements/user_stories.md</file><file>project_workspace/ocap_history_expense_import/development/implementation_plan.md</file><file>project_workspace/ocap_history_expense_import/development/code_review_report.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 测试计划（增量）

## 测试策略

- 被测改动：MOD-192~197（批次/行模型、导入服务、5 个 API、前端页面与报表联动）。
- 范围：
  - in scope：US-333~338 全部 16 条 AC；前后端契约（新增 5 条 API 调用）。
  - out of scope：小程序（本期无入口）；真实微信/短信外部服务。
- 环境：Python venv `/tmp/ocap-venv`（Django 5.2）；`config.test_settings`（SQLite 内存库，`MIGRATION_MODULES` 置空，外部服务内存替身）；前端 vitest（jsdom）。
- 判定模式：INCREMENTAL / baseline（零新增失败）。基线：后端 1191、前端 54 文件/585、小程序 21/151（画像 P4）；小程序本期无改动，不重跑。
- 执行顺序：单元 → 集成 → E2E → 全量回归（含前后端契约测试）。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 |
|---|---|---|---|---|---|---|---|
| AC-333-01 | TC-UNIT-2103 | unit | 新写 | `tests/unit/test_history_expense_rules.py::HistoricalExpenseTemplateTests` | — | 生成 xlsx/csv 模板 | 五列顺序正确，xlsx 含“填写说明”表 |
| AC-333-01 | TC-INT-2101 | integration | 新写 | `tests/integration/test_history_expense_api.py::TemplateTests::test_ac_333_01_...` | 主任已登录 | GET template（xlsx/csv） | 200 二进制，表头正确 |
| AC-333-01 | TC-UNIT-2107 | unit（Web） | 新写 | `frontend/tests/historical_expenses.spec.js` | 委员，mock 模板响应 | 点击“下载 xlsx 模板” | 请求参数正确并触发保存 |
| AC-333-02 | TC-INT-2102 | integration | 新写 | `...::TemplateTests::test_ac_333_02_template_permissions` | 业主/匿名/管理员 | GET template | 403 / 401 / 403 |
| AC-334-01 | TC-INT-2103 | integration | 新写 | `...::ImportTests::test_ac_334_01_valid_rows_write_expense_ledger_only` | 主任 | 导入 3 行 | 201、3 条 EXPENSE 台账、无 Claim/审批实例、审计存在 |
| AC-334-01 | TC-E2E-2101 | e2e | 新写 | `tests/e2e/test_history_expense_journey.py` | 主任+业主 | 导入→报表→作废→重导 | 全链路一致 |
| AC-334-02 | TC-UNIT-2101/2102 | unit | 新写 | `tests/unit/...::ParseDate/ParseAmount/Validate` | — | 校验日期/金额/长度 | 非法值返回原因 |
| AC-334-02 | TC-INT-2104/2105 | integration | 新写 | `...::test_ac_334_02_mixed...`、`..._all_invalid...` | 主任 | 混合/全错文件 | 合法行导入、错误行含行号；全错不建批次 |
| AC-334-03 | TC-UNIT-2104 | unit | 新写 | `tests/unit/...::test_valid_row_becomes_parsed_row` | — | 构造 ParsedRow | duplicate_key 仅四要素 |
| AC-334-03 | TC-INT-2106 | integration | 新写 | `...::test_ac_334_03_duplicates...` | 已有一批 | 重复导入 | 文件内与历史重复均跳过；备注不同仍判重 |
| AC-334-04 | TC-INT-2107 | integration | 新写 | `...::test_ac_334_04_size_row_limit_and_first_sheet_only` | 主任 | >5MB、5001 行、多表 | 413 / 400 / 仅读首表 |
| AC-334-05 | TC-INT-2108 | integration | 新写 | `...::test_ac_334_05_missing_column_and_future_date` | 主任 | 缺列、未来日期 | 400 列出缺列；未来行报错跳过 |
| AC-335-01 | TC-INT-2109 | integration | 新写 | `...::test_ac_335_01_and_02_batch_list_and_detail` | 已导入 | GET 批次列表 | 字段齐全、金额合计=600.00 |
| AC-335-01 | TC-UNIT-2106 | unit（Web） | 新写 | `frontend/tests/historical_expenses.spec.js` | 委员 | 打开页面 | 显示文件名/行数/金额/状态 |
| AC-335-02 | TC-INT-2109 | integration | 新写 | 同上（详情部分） | 已导入 | GET 批次详情 | 行字段齐全；非委员 403 |
| AC-335-02 | TC-UNIT-2108 | unit（Web） | 新写 | `frontend/tests/historical_expenses.spec.js` | 委员 | 点击“明细” | 弹窗显示用途与重复原因 |
| AC-336-01 | TC-INT-2110 | integration | 新写 | `...::test_ac_336_01_void_batch_ledger_reports_and_audit` | 已导入且已生成报表 | 整批作废 | 台账 VOIDED、批次 VOIDED、报表 stale、审计含原因/行数/金额 |
| AC-336-01 | TC-UNIT-2109 | unit（Web） | 新写 | `frontend/tests/historical_expenses.spec.js` | 委员 | 填原因确认作废 | 调用 void 接口并刷新列表 |
| AC-336-02 | TC-INT-2111 | integration | 新写 | `...::test_ac_336_02_revoid_conflict_reimport_allowed...` | 已作废 | 再作废/重导 | 409 且不重复审计；重导成功；非委员 403 |
| AC-337-01 | TC-INT-2112 | integration | 新写 | `...::test_ac_337_01_03_report_...` | 已导入 | 生成 2022Q3 | total_expense=300.00，明细含历史来源 |
| AC-337-02 | TC-INT-2113 | integration | 新写 | `...::test_ac_337_02_report_visible_to_owner...` | 已生成 | 业主查看/匿名 | 200 / 401 |
| AC-337-03 | TC-INT-2112 | integration | 新写 | 同上（作废后） | 已作废 | 刷新/重算 | stale=True；重算 total_expense=0.00 |
| AC-338-01 | TC-INT-2114 | integration | 新写 | `...::PermissionMatrixTests` | 5 类主体 | 模板/列表/详情/导入 | 委员 200/201；业主/管理员 403；匿名 401 |
| AC-338-02 | TC-UNIT-2105 | unit（Web） | 新写 | `frontend/tests/historical_expenses.spec.js` | 非委员 | 直访页面 | 显示无权限提示，不请求批次 |
| IFC-408~412 契约 | TC-INT-2115 | integration | 现有 | `tests/integration/test_frontend_contract.py::RouteContractTests` | — | 静态扫描 api.js 并 resolve 路由 | 新增 5 条调用全部可解析、方法/权限相容 |

## 测试数据需求

- 后端：内存生成的 xlsx/csv（openpyxl/csv），无外部文件依赖；5001 行 CSV 为程序生成，不落盘。
- 前端：mock HTTP 层（`tests/http.mock.js`），不访问网络。
- [DATA_REQUIRED: 无]

## 不可测项

| AC | 原因 |
|---|---|
| — | 无 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-333 | TC-UNIT-2103、TC-INT-2101/2102、TC-UNIT-2107 | unit + integration |
| US-334 | TC-INT-2103~2108、TC-E2E-2101 | unit + integration + e2e |
| US-337 | TC-INT-2112/2113、TC-E2E-2101 | integration + e2e |
| US-338 | TC-INT-2114、TC-UNIT-2105 | integration + unit（Web） |

> Should Have：US-335（TC-INT-2109、TC-UNIT-2106/2108）、US-336（TC-INT-2110/2111、TC-UNIT-2109、TC-E2E-2101）已覆盖。
