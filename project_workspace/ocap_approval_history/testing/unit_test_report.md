<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T10:08:03.0867713+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

- 执行时间：2026-11-27 09:55:57～09:56:01（Asia/Shanghai）。
- 环境：Python 3.14.6 / Django 6.0.6 / `config.test_settings` / SQLite 隔离测试库；Vitest 2.1.9 / jsdom。
- 命令：
  - `backend/`：`$env:DJANGO_SECRET_KEY='test-only'; python manage.py test tests.unit --settings=config.test_settings`
  - `frontend/`：`npx vitest run tests/approval_history_unit.spec.js --passWithNoTests`
- `total = pass + fail + skip + blocked + not_testable = 261 + 0 + 1 + 0 + 0 = 262`。
- 通过率 = `pass/(pass+fail+blocked) = 261/261 = 100%`；INCREMENTAL baseline 模式，零新增失败且 2 条新写用例全部通过。
- **本层门控：PASSED**。

## 执行输出

后端：

```text
Ran 260 tests in 4.324s
OK (skipped=1)
```

前端：

```text
Test Files 1 passed (1)
Tests 2 passed (2)
```

## 分项结果

| TC | AC | 模块/描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-2301 | AC-371-01 | `approvalApi.tasks` 原样转发 `handled`、`scope` 与分页参数 | PASS | — | — |
| TC-UNIT-2302 | AC-372-01 | `approvedResidentApplications` 仅 GET 固定端点，不发 POST | PASS | — | — |
| 既有后端单元套件 | 回归 | 260 条，259 通过、1 条 Windows 非 POSIX 权限位既有跳过 | PASS/SKIP | — | 环境差异，非本批失败 |

## 与基线对比

失败 0；相对开发门控及既有单元基线新增失败 0。唯一跳过为既有 Windows 权限位用例，不属于本批新用例。

## 失败汇总（需路由给开发）

无。
