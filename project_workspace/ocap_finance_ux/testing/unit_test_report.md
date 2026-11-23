<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T23:30:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/testing/test_plan.md</file>
    <file>backend/tests/unit/test_ledger_accounts_unit.py</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — ocap_finance_ux

## 摘要

- 执行时间：2026-11-23 23:28（Asia/Shanghai）；环境：Django 6.0.6 / DRF 3.17.1 / SQLite 内存库（`config.test_settings`）。
- 命令：`python manage.py test tests.unit.test_ledger_accounts_unit tests.unit.test_rework_rules --settings=config.test_settings`
- 计数：total = pass + fail + skip + blocked + not_testable = 14 = 14 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 14/14 = 100.0%。
- 判定模式：INCREMENTAL baseline（零新增失败）；**本层门控：PASSED**。

## 执行输出

```
Ran 14 tests in 0.582s
OK
```

## 分项结果（新增 7 例）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-1401 | AC-405-01/02 | 余额只计有效收入−支出 | PASS |
| TC-UNIT-1402 | AC-409-03/04/05 | 最近流水排序、上限 10、排除作废 | PASS |
| TC-UNIT-1403 | AC-406-01/02、AC-407-01 | 默认账户兜底归属 | PASS |
| TC-UNIT-1406 | AC-407-04 | 不存在/停用账户不可用 | PASS |
| TC-UNIT-1404 | AC-403-01/02/03/06 | 季度/年度链式期初期末 | PASS |
| TC-UNIT-1405 | AC-403-05 | 作废标记后续期间并级联重算 | PASS |
| TC-UNIT-1407 | AC-403-06 | legacy 报表期初期末为 NULL | PASS |

现有相关用例：`tests.unit.test_rework_rules` 7 例全部 PASS（报表 stale 行为回归）。

## 与基线对比

基线为 0 失败；本层 0 新增失败。

## 失败汇总

无。
