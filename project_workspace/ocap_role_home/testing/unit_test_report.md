<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-25T13:02:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/testing/test_plan.md</file>
    <file>frontend/tests/auth.store.spec.js</file>
    <file>frontend/tests/product_review_core.spec.js</file>
    <file>miniprogram/tests/store.spec.js</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — ocap_role_home

## 摘要

- 执行时间：2026-11-25 12:59（Asia/Shanghai）；环境：Node + vitest 3（Web 与小程序各一套配置）。
- 命令：
  - `cd frontend && npx vitest run tests/auth.store.spec.js tests/product_review_core.spec.js`
  - `cd miniprogram && npx vitest run tests/store.spec.js`
- 计数：total = pass + fail + skip + blocked + not_testable = 18 = 18 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 18/18 = 100.0%。
- 判定模式：INCREMENTAL baseline（零新增失败）；**本层门控：PASSED**。

## 执行输出

```
✓ tests/product_review_core.spec.js (8 tests) 167ms
✓ tests/auth.store.spec.js (8 tests) 12ms
Test Files  2 passed (2)
     Tests  16 passed (16)

Test Files  1 passed (1)
     Tests  2 passed (2)
```

## 分项结果

本层本次**无新增用例**：MOD-215/MOD-218 新增的能力 getter（`isRepresentative`、`ownerUnits`、`hasOwnerUnit`、`residentUnits`、`hasResidentUnit`、`isGuest`）为纯派生 getter，行为由前端集成用例 TC-WEB-601~606、TC-INT-601~603 直接断言；本层执行相关既有单测作为回归：

| 范围 | 用例数 | 结果 | 说明 |
|---|---|---|---|
| `frontend/tests/auth.store.spec.js` | 8 | PASS | 登录态/身份仓库既有契约（未被本次改动破坏） |
| `frontend/tests/product_review_core.spec.js` | 8 | PASS | labels / usePaging / 入口可见性等纯逻辑 |
| `miniprogram/tests/store.spec.js` | 2 | PASS | 小程序 auth 仓库既有契约 |

## 与基线对比（baseline 模式）

基线为 GROUP_C 门控时的零失败；本层 18 例全部 PASS，新增失败 0。

## 失败汇总（需路由给开发）

无。
