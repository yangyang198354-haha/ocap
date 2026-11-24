<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-24T23:21:23+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/testing/test_plan.md</file><file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

## 摘要

- 执行时间：2026-11-24 23:15（Asia/Shanghai）
- 环境：Windows / Python 3.14.6 / Django 6.0.6 / `config.test_settings`（SQLite 内存库，模型直建表、不执行迁移）
- 命令：`python manage.py test tests.unit --settings=config.test_settings`（工作目录 `backend/`）
- 计数：total = pass + fail + skip + blocked + not_testable = 259 + 0 + 1 + 0 + 0 = 260
- 通过率 = pass/(pass+fail+blocked) = 259/259 = 100.00%
- 判定模式：INCREMENTAL / baseline（零新增失败）；**本层门控：PASSED**
- 新写用例：5（TC-UNIT-2001～TC-UNIT-2004），全部通过；既有用例 255（含 1 个既有 skip）。

## 执行输出

```
python manage.py test tests.unit --settings=config.test_settings
Found 260 test(s).
System check identified no issues (0 silenced).
Ran 260 tests in 2.909s
OK (skipped=1)
Destroying test database for alias 'default'...
```

定向核验新写用例：

```
python manage.py test tests.unit.test_multi_account_ux_rules tests.integration.test_multi_account_ux_api tests.integration.test_multi_account_ux_contract tests.e2e.test_multi_account_ux_journey --settings=config.test_settings
Ran 18 tests in 0.631s
OK
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-2001 | AC-419-01 | `_totals_by_period` 按报告区间与账户分桶，排除 VOIDED 与其他账户 | PASS | — | — |
| TC-UNIT-2002 | AC-416-01、AC-422-02 | 导入生成 PENDING 批次/PENDING 行、不写台账、approval_instance 非空；去重按账户隔离 | PASS | — | — |
| TC-UNIT-2003 | AC-416-02、AC-416-03 | 审批通过后按批次账户入账，行置 IMPORTED、decided_at 写入、余额正确；驳回/撤回无台账 | PASS | — | — |
| TC-UNIT-2004 | AC-416-03 | 审批中批次作废返回 INVALID_STATE/409；撤回经审批引擎置 WITHDRAWN，重复撤回 409 | PASS | — | — |

## 与基线对比（baseline 模式）

- 基线：本批开发阶段记录为“无已知单元失败”；本次全量 `tests.unit` 260 用例 `OK (skipped=1)`。
- 新增失败：0。
- 既有失败：0（1 个既有 skip 与基线条目一致，非本次引入）。

## 失败汇总（需路由给开发）

无。
