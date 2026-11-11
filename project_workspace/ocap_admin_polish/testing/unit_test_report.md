<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T23:32:38.0156563+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_admin_polish/testing/test_plan.md</file>
    <file>project_workspace/ocap_admin_polish/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

- 执行时间：2026-11-11 23:26（Asia/Shanghai）；环境：Windows / Python 3.14.6 / Django 6.0.6 / SQLite 内存库。
- 命令：`cd backend; python manage.py test tests.unit --settings=config.test_settings`
- `total = pass + fail + skip + blocked + not_testable = 142 + 0 + 3 + 0 + 0 = 145`
- 通过率 = 142 / (142 + 0 + 0) = 100%；判定模式 baseline；**本层门控：PASSED**。
- 新增单元用例：7 个（`tests/unit/test_specific_part_rule.py`），全部通过；既有单元用例同步 2 个文件（`test_registry_import_rules.py`、`test_registry_import_smoke.py`）。

## 执行输出

```
Creating test database for alias 'default'...
..........................................................................sss....................................................................
----------------------------------------------------------------------
Ran 145 tests in 0.573s

OK (skipped=3)
Destroying test database for alias 'default'...
Found 145 test(s).
System check identified no issues (0 silenced).
```

`python -m compileall -q backend` → `COMPILE_OK`（静态检查，不计入用例数）。

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-201 | AC-132-01/04 | 四级齐全直接连接并补后缀 | PASS | — | — |
| TC-UNIT-202 | AC-132-02/03 | 空段跳过（车位/商铺） | PASS | — | — |
| TC-UNIT-203 | AC-133-01/02 | 已带后缀与纯数字一致 | PASS | — | — |
| TC-UNIT-204 | AC-133-03/05/06 | 非数字取值原样 | PASS | — | — |
| TC-UNIT-205 | AC-133-04/08/09 | 楼层省略规则 | PASS | — | — |
| TC-UNIT-206 | AC-133-07 | strip 与 "3.0" | PASS | — | — |
| TC-UNIT-207 | ADR-069 | 规则单点定义 / 无旧式 join | PASS | — | — |
| TC-UNIT-110 | AC-138-02/03 | 模板 BOM、8 列、6 行示例 | PASS | — | — |
| TC-UNIT-106 | AC-132-01~03 | 旧金标已同步为新规则 | PASS | — | — |
| 其余既有单元用例（131 个） | — | 账号/清册/权限等 | PASS / SKIP 3 | — | 既有 skip |

## 与基线对比（baseline 模式）

- 基线：530 tests OK (skipped=9) 为全量；单元层基线为 138 tests OK（3 skipped）。
- 本次单元层 145 tests（+7），skip 仍为 3，失败 0；无新增失败。
- 既有 skip 3 个：由既有测试条件跳过，非本次引入（原因见各用例原有 skip 标记）。

## 失败汇总（需路由给开发）

无。
