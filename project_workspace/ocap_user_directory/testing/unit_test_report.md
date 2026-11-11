<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T22:46:57.2524963+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 单元测试报告

## 摘要

- 执行时间：2026-11-11 22:44 ~ 22:46（Asia/Shanghai）；环境：Windows 开发机，后端 Django test runner + SQLite 内存库，前端 vitest + jsdom。
- 命令：
  - 后端：`python manage.py test tests.unit --settings=config.test_settings`
  - 前端：`npx vitest run tests/admin_users.spec.js`
- 后端计数：total 138 = pass 135 + fail 0 + skip 3 + blocked 0 + not_testable 0；通过率 = 135 / (135 + 0 + 0) = 100%。
- 前端新增计数：total 2 = pass 2 + fail 0 + skip 0；通过率 100%。
- 合并计数：total 140 = pass 137 + fail 0 + skip 3 + blocked 0 + not_testable 0；通过率 137 / 137 = 100%。
- 判定模式：baseline（零新增失败、新写用例全部通过）；**本层门控：PASSED**。

## 执行输出

```
> python manage.py test tests.unit --settings=config.test_settings
Ran 138 tests in 0.413s
OK (skipped=3)

> npx vitest run tests/admin_users.spec.js
✓ tests/admin_users.spec.js (2 tests) 72ms
Test Files  1 passed (1)
     Tests  2 passed (2)
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-410 | AC-134-01、AC-134-04 | `formatDateTime` 输出 `YYYY-MM-DD HH:mm`，空值为空串 | PASS | — | — |
| TC-UNIT-411 | AC-134-02、AC-135-01 | 四列渲染、手机号脱敏、空值“未认证/—/从未登录” | PASS | — | — |

## 与基线对比（baseline 模式）

- 既有后端单元用例：138 个，0 失败，与基线一致。
- 前端新增 2 个用例全部通过；无既有前端单元用例因本次改动失败。
- 新增失败：0。

## 失败汇总（需路由给开发）

无。
