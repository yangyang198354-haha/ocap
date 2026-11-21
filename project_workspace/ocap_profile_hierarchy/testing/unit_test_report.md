<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-21T12:11:30+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>frontend/tests/profile_ux.spec.js</file>
    <file>miniprogram/tests/identity_display.spec.js</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

执行时间 2026-11-21T12:10；环境 Windows / vitest 2.1.9 / jsdom。
命令：`frontend: npx vitest run tests/profile_ux.spec.js`；`miniprogram: npx vitest run tests/identity_display.spec.js`。
total = pass + fail + skip + blocked + not_testable = 18 = 18 + 0 + 0 + 0 + 0；通过率 = 18/(18+0+0) = 100%。
判定模式：baseline，零新增失败；**本层门控：PASSED**。

## 执行输出

```
frontend  Tests  13 passed (13)
miniprogram  Tests  5 passed (5)
```

## 分项结果

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-1509 | AC-273-01/274-01/275-01/275-02 | Web 实名可见：昵称 → 实名+徽章 → 身份，身份标签独立 | PASS |
| TC-UNIT-1510 | AC-273-02/274-02 | Web 无实名：不渲染实名与徽章 | PASS |
| TC-UNIT-1511 | AC-273-03 | Web 昵称为空：显示“未设置昵称”且在身份前 | PASS |
| TC-UNIT-1512 | AC-275-01/275-02 | Web 实名与身份的样式规则不同（`var(--text)`/650 vs 独立 muted 规则） | PASS |
| TC-MP-504 | AC-276-01 | 小程序实名可见：顺序与认证徽章 | PASS |
| TC-MP-505 | AC-276-02/276-03 | 小程序无实名/接口失败：无徽章且静默降级 | PASS |
| 其余 12 条 | — | 同文件既有用例（profile 页、身份展示）回归 | PASS |

## 与基线对比

本层两个测试文件无失败；无新增失败。

## 失败汇总

无。
