<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T11:01:52+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — 申诉与同住人申请记录中心

## 摘要

- 执行时间：2026-11-22 10:53–10:59（Asia/Shanghai；本轮为 DEF-AC-01 修复后的 GROUP_D-2 复跑）
- 环境：Node/vitest + jsdom，真实页面组件 + 真实 store/api，仅 mock HTTP 层。
- 命令：`npm --prefix frontend test`
- total = pass + fail + skip + blocked + not_testable = 568 + 0 + 0 + 0 + 0 = 568
- 通过率 = 568 / (568 + 0 + 0) = 100%
- 判定模式：baseline（基线 562 通过）→ 新增 6 条全部通过，既有 562 条零失败。**本层门控：PASSED**

## 执行输出

```
 Test Files  50 passed (50)
      Tests  568 passed (568)
   Duration  328.11s
```

新增用例文件：`frontend/tests/appeal_center_flow.spec.js`（6 条）
- TC-UNIT-1532 / AC-292-01、AC-293-02/03、AC-294-01/03/04：记录字段与操作按钮显隐
- TC-UNIT-1533 / AC-294-01：撤回确认后 POST /appeals/{id}/withdraw
- TC-UNIT-1534 / AC-297-01/02：实名校验与提交体
- TC-UNIT-1535 / AC-291-02/03、AC-294-03：默认 Tab、节点不重建、重新提交回填
- TC-UNIT-1536 / AC-295-01/02：同住申请双 Tab 与表单不重建
- TC-UNIT-1537 / AC-298-02/03：同住人实名与“—”占位

## 分项结果

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-1532 | 292-01/293-02/03/294-01/03/04 | 申诉记录展示与按钮显隐 | PASS | — |
| TC-UNIT-1533 | 294-01 | 撤回交互调用正确接口 | PASS | — |
| TC-UNIT-1534 | 297-01/02 | 实名必填、长度与提交体 | PASS | — |
| TC-UNIT-1535 | 291-02/03、294-03 | Tab 保持与重新提交回填 | PASS | — |
| TC-UNIT-1536 | 295-01/02 | 同住申请双 Tab | PASS | — |
| TC-UNIT-1537 | 298-02/03 | 身份页实名与占位 | PASS | — |
| 既有 562 条 | — | 全量回归 | PASS | — |

## 与基线对比

- 基线 562 通过；本次 568 通过（+6 新写）。
- 新增失败：0。

## 失败汇总（需路由给开发）

无。
