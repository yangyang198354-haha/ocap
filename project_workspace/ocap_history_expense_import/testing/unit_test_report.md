<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T18:02:30+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/testing/test_plan.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（历史支出导入）

## 摘要

- 执行时间：2026-11-23 17:55~17:56；环境：`/tmp/ocap-venv`（Django 5.2，`config.test_settings`）+ vitest/jsdom。
- 命令：`manage.py test tests.unit.test_history_expense_rules --settings=config.test_settings`；`npx vitest run tests/historical_expenses.spec.js`。
- total = pass + fail + skip + blocked + not_testable = 17 = 17 + 0 + 0 + 0 + 0。
- 通过率 = 17/(17+0+0) = 100%；判定模式：baseline（零新增失败）；**本层门控：PASSED**。
- 说明：后端 12 条为新写纯函数用例；前端 5 条为新写页面用例（页面挂载 + HTTP mock，属单模块）。

## 执行输出

```
$ cd /workspace/backend && /tmp/ocap-venv/bin/python manage.py test tests.unit.test_history_expense_rules --settings=config.test_settings
Ran 12 tests in 0.283s
OK
Found 12 test(s).

$ cd /workspace/frontend && npx vitest run tests/historical_expenses.spec.js
 Test Files  1 passed (1)
      Tests  5 passed (5)
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-2101 | AC-334-02/05 | 日期解析：ISO/斜杠/date/datetime；空、非法、不存在日期拒绝 | PASS | — | — |
| TC-UNIT-2102 | AC-334-02 | 金额解析：正数/千分位；0、负数、三位小数、非数字拒绝 | PASS | — | — |
| TC-UNIT-2102 | AC-334-02/05 | 行校验：合法行、未来日期、类别/用途/备注超长、空日期 | PASS | — | — |
| TC-UNIT-2103 | AC-333-01 | xlsx/csv 模板列顺序、说明表、非法类型拒绝、5MB 常量 | PASS | — | — |
| TC-UNIT-2104 | AC-334-03 | ParsedRow.duplicate_key 仅含日期+金额+类别+用途 | PASS | — | — |
| TC-UNIT-2105 | AC-338-02 | 非委员直访：显示无权限、不发批次请求 | PASS | — | — |
| TC-UNIT-2106 | AC-335-01 | 委员：批次列表显示文件/行数/金额/状态 | PASS | — | — |
| TC-UNIT-2107 | AC-333-01 | 委员：下载 xlsx 模板请求参数与本地保存 | PASS | — | — |
| TC-UNIT-2108 | AC-335-02 | 委员：明细弹窗显示用途与重复原因 | PASS | — | — |
| TC-UNIT-2109 | AC-336-01 | 委员：填写原因并确认作废，调用接口并刷新 | PASS | — | — |

## 与基线对比（baseline 模式）

- 新增用例 17 条全部通过；未改动既有单元用例，无新增失败。
- 无既有失败新增。

## 失败汇总（需路由给开发）

无。
