<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T10:08:03.0867713+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>testing/integration_test_report.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告

## 摘要

critical path 口径：替代（Vitest + jsdom 挂载真实页面、`api.js`、Pinia 与内存路由；HTTP 层为有状态替身，无浏览器 E2E 框架）。

- 执行时间：2026-11-27 09:55:19～09:59:09（Asia/Shanghai）。
- `total = pass + fail + skip + blocked + not_testable = 83 + 0 + 0 + 0 + 0 = 83`。
- critical path 覆盖率 = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = `4/4 = 100%`（US-370～373）。
- critical path 通过率 = `2/2 = 100%`；新写 2 条全部通过，零新增失败；**本层门控：PASSED**。
- 分层命令：
  - `backend/`：`$env:DJANGO_SECRET_KEY='test-only'; python manage.py test tests.e2e --settings=config.test_settings`
  - `frontend/`：`npx vitest run tests/approval_history_e2e.spec.js tests/layout_e2e.spec.js --passWithNoTests`
- 分层输出：后端 `Ran 78 tests in 13.955s / OK`；前端 `Test Files 2 passed (2) / Tests 5 passed (5)`。

## 全量回归

| 范围 | 命令 | 最终计数 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | `$env:DJANGO_SECRET_KEY='test-only'; python manage.py test --settings=config.test_settings` | `Ran 1266 tests in 83.215s`；`OK (skipped=2)`；1264 pass + 0 fail + 2 skip | 0 |
| 前端全量 | `npx vitest run --passWithNoTests` | `Test Files 64 passed (64)`；`Tests 639 passed (639)` | 0 |
| Web 构建 | `$env:VITE_API_BASE='/ocap/api/v1'; npm run build -- --base=/ocap/` | `1887 modules transformed`；`✓ built in 10.53s` | 0；仅既有大 chunk 警告 |

全量失败清单为空；既有 Element Plus/Vue 警告不导致失败。最终全量执行晚于全部测试文件最后一次编辑。

## 用户旅程

### TC-E2E-2301：审批待办 → 同意并留意见 → 已处理 → 只读审批过程

- 关联：US-370、US-371 / AC-370-01、AC-370-02、AC-371-02；环境：真实 `Tasks.vue`、`ApprovalTimeline.vue`、`api.js`，有状态 HTTP 替身。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 打开两步决议待办 | 显示第 1 步与同意入口 | 显示“更换电梯”“财务初审” | PASS |
| 2 | 输入“同意，预算清晰”并确认 | POST 动作与意见；待办移除 | POST 仅 1 次；显示“暂无待办” | PASS |
| 3 | 切到“已处理” | 每实例一次；显示本人动作/意见、整单审批中、当前第 2 步 | 1 条记录，全部文案符合，无同意/拒绝按钮 | PASS |
| 4 | 打开“审批过程” | 两步、审批人、动作、时间、意见、整单状态完整且只读 | 全字段出现；未新增 POST | PASS |

- 结论：PASS。

### TC-E2E-2302：同住人待审 → 通过 → 已通过记录 → 申请人本人记录

- 关联：US-372、US-373 / AC-372-01、AC-372-02、AC-373-01、AC-373-02；环境：真实 `UnitsReview.vue`、`UnitsApplicationRecords.vue`、Store 与 `api.js`，有状态 HTTP 替身。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 产权人打开同住人审核 | 待审与既有通过记录分区显示；不显示拒绝/他房记录 | “小王”“其他申请人”可见；“王拒绝”“B房”不可见 | PASS |
| 2 | 通过小王的申请 | 待审移除；通过记录含房屋、申请人、实名、时间、状态、备注且只读 | 全部符合，历史卡无操作按钮 | PASS |
| 3 | 切为无产权申请人并打开本人记录 | 无需产权即可看本人通过结果、处理时间与备注 | “处理结果：已通过”“处理备注：已核实”等完整 | PASS |
| 4 | 核对他人记录 | 只返回/显示本人申请 | 仅 1 条；不含“其他申请人/李其他” | PASS |

- 结论：PASS。

## 缺陷

无。首次 E2E 执行中 TC-E2E-2302 的测试数据把同单元拒绝记录也归给本人，与“申请人既有本人记录均可见”冲突；修正测试数据归属后最终通过，不属于产品缺陷。

## 人工验证清单

以下为替代 E2E 的补充浏览器视觉复核，不是未覆盖的行为 AC，也不改变上述自动化通过率。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-AH-01 | AC-370-01、02 / TC-E2E-2301 | 在真实 Web 浏览器处理一条两步审批并切到已处理、打开审批过程 | 无遮挡/横向异常；审批中与当前步骤清晰；历史只读 | 测试环境、两名审批人 | 否（行为已由替代 E2E 覆盖） |
| M-AH-02 | AC-372-01 / TC-E2E-2302 | 在真实 Web 浏览器通过同住人申请并核对两个列表及申请人记录 | 卡片布局正常、字段完整；申请人只见本人记录 | 测试环境、产权人和申请人账号 | 否（行为已由替代 E2E 覆盖） |
