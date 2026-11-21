<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-21T12:11:30+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>frontend/tests/layout_contract.spec.js</file>
    <file>frontend/src/portal/UserProfile.vue</file>
    <file>miniprogram/pages/me/index.vue</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

执行时间 2026-11-21T12:06；环境 Windows / vitest。
命令：`frontend: npx vitest run tests/layout_contract.spec.js`
total = pass + fail + skip + blocked + not_testable = 6 = 6 + 0 + 0 + 0 + 0；通过率 = 100%。
判定模式：baseline；**本层门控：PASSED**。

## 执行输出

```
frontend  Tests  6 passed (6)
```

## 分项结果

| 集成边界 | 用例 | 结果 |
|---|---|---|
| 客户端调用 → 后端路由契约 | TC-INT-1501（meApi.userProfile → GET /users/{id}/profile）等 6 条 | PASS |

本批未新增 API 调用：Web 仍用 `meApi.userProfile`；小程序复用既有 `api.profile()`（`GET /me/profile`），路径与后端路由均由既有契约测试覆盖。

## 与基线对比

无失败，无新增失败。

## 失败汇总

无。

## 备注

后端无改动，未运行后端测试；既有后端测试基线不在本次回归范围。
