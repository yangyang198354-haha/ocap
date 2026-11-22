<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T19:52:51+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — ocap_approval_flow

## 摘要

critical path 口径：替代（多步 API 端到端旅程 + 三端契约/界面用例）

- 新写 E2E 用例：total = pass + fail + skip + blocked + not_testable = 1 = 1 + 0 + 0 + 0 + 0
- critical path 覆盖率 = 有已执行端到端级用例的 Must Have 故事 / Must Have 故事总数 = 11 / 11 = 100%
- critical path 通过率 = 1 / 1 = 100%
- **本层门控：PASSED**

## 全量回归

| 命令 | 结果 | 相对基线新增失败 |
|---|---|---|
| `backend/python manage.py test --settings=config.test_settings` | `Ran 1186 tests in 35.327s`；`FAIL: test_tc_int_964_register_and_bind_response_field_registry_match` | 0（该失败为预存在） |
| `frontend/npm test` | `Test Files 52 passed (52)`；`Tests 581 passed (581)` | 0 |
| `miniprogram/npm test` | `Test Files 21 passed (21)`；`Tests 151 passed (151)` | 0 |

预存在失败依据：`tests/integration/test_phone_match_contract.py` 读取 `miniprogram/pages/phone/index.vue` 中的旧 `registry_match` 标记，而该文件自提交 f7316cb（上一批次）起已是 PhonePane 包装页；`git log -1 -- miniprogram/pages/phone/index.vue` 显示本批次未修改该文件。

## 用户旅程

### TC-E2E-1330: 提交 → 第 1 步通过 → 第 2 步通过 → 整单通过

- 关联：US-315 / AC-323-01、AC-322-01；环境：Django test client + SQLite
- 位置：`backend/tests/integration/test_approval_flow_steps.py::TwoStepSequentialTests::test_two_steps_approved_end_to_end`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理员创建 2 步流程（初审/终审） | 201，step_count=2 | 201 | PASS |
| 2 | 发起人提交决议 | 201，实例 PENDING，current_step_order=1 | 201 | PASS |
| 3 | 第 2 步审批人查询待办 | count=0 | 0 | PASS |
| 4 | 第 1 步审批人通过 | 200，current_step_order=2，决议仍 PENDING | 符合 | PASS |
| 5 | 第 2 步审批人通过 | 200，实例 APPROVED，决议 APPROVED | 符合 | PASS |
| 6 | 发起人查看时间线 | 2 步均 APPROVED，含审批人与时间 | 符合 | PASS |

### 三端覆盖（端到端级替代）

- Web 管理后台：TC-UNIT-1303（创建流程提交 steps）+ TC-INT-1316（客户端路径契约）。
- Web 用户端：TC-INT-1305（待办 → 备注 → 决策）、TC-INT-1304（时间线渲染）。
- 小程序：TC-INT-1310/1311（页面注册、api 路径、文案一致）。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| DEF-001 | MAJOR | 时间线组件模板引用未定义常量，渲染崩溃 | TC-INT-1304 | `frontend/src/portal/ApprovalTimeline.vue` |

DEF-001 已修复并复跑通过（修复说明见 code_review_report“缺陷修复”）。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | REQ-NFUNC-064 | 两名审批人同时点击“同意”（同一或签步骤） | 仅产生一个步骤判定，无重复推进，动作记录与决策一致 | 测试环境树莓派 + MySQL；两名委员账号 | 否 |
| MV-02 | AC-331-01 | 微信开发者工具打开小程序审批详情并通过 | 状态与 Web 一致，备注正确显示 | 微信开发者工具/体验版 | 否 |
