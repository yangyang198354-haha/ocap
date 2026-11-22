<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T19:52:51+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — ocap_approval_flow

## 摘要

- 执行时间：2026-11-22 19:46–19:52（Asia/Shanghai）
- 环境：vitest 2.1.9 + @vue/test-utils；Element Plus 2.8.7
- 命令：`frontend/npm test`、`miniprogram/npm test`
- 新写单元用例：total = pass + fail + skip + blocked + not_testable = 4 = 4 + 0 + 0 + 0 + 0
- 通过率 = 4 / (4 + 0 + 0) = 100%
- 判定模式：INCREMENTAL baseline；**本层门控：PASSED**

## 执行输出

```
frontend: Test Files 52 passed (52) / Tests 581 passed (581)
miniprogram: Test Files 21 passed (21) / Tests 151 passed (151)
```

## 分项结果

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-1301 | AC-316-01 | StepsEditor 按顺序展示步骤名称与策略（输入值） | PASS | — |
| TC-UNIT-1302 | AC-325-01 | StepsEditor 下移发出 move(0,1) | PASS | — |
| TC-UNIT-1303 | AC-316-01、AC-318-01 | AdminFlows 展示步骤数并以嵌套 steps 提交 | PASS | — |
| TC-UNIT-1312 | AC-328-01 | 三端步骤/动作文案取值一致 | PASS | — |

## 与基线对比（baseline 模式）

- 前端基线 568 tests → 本次 581 tests，新增 13 条（本批新写 5 条 + 既有套件内新计数），0 失败。
- 小程序基线 138 tests → 本次 151 tests，新增 13 条（本批新写 3 条 + 项目既有增量），0 失败。
- 新增失败：0。

## 失败汇总（需路由给开发）

无。
