<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T19:52:51+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/requirements/user_stories.md</file>
    <file>project_workspace/ocap_approval_flow/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — 审批流程多步化与或/与签（ocap_approval_flow）

## 测试策略

- 被测改动：审批步骤模型与迁移、ANY/ALL 判定引擎、流程配置/待办/决策/时间线接口、Web 管理后台步骤编辑、Web 用户端待办与时间线、小程序审批页面。
- In scope：REQ-FUNC-316~332 的全部 AC；三端接口契约；历史流程兼容。
- Out of scope：半数同意（HALF_MAJORITY）投票链路（本次未改）、真实微信环境、真实 MySQL 并发压测。
- 环境：后端 Django test runner + `config.test_settings`（SQLite 内存库）；前端 vitest + @vue/test-utils；小程序 vitest。
- 判定模式：INCREMENTAL baseline（相对基线零新增失败，新写用例全部通过）。
- 基线：后端全量 1167 tests，其中 `test_tc_int_964_register_and_bind_response_field_registry_match` 预存在失败（phone 页面自 f7316cb 起为包装页，被测文件本批次未修改）；前端 51 files / 568 tests 全绿；小程序 20 files / 138 tests 全绿。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-316-01 | TC-UNIT-1301、TC-INT-1310 | UNIT/INT | 自动 | 新写 | `frontend/tests/approval_steps_ui.spec.js`、`backend/tests/integration/test_approval_flow_steps.py::AdminFlowStepsTests` | 管理员已登录 | 创建含 2 步的流程 | 步骤名称/策略按序返回 | 2 名委员 |
| AC-317-01 | TC-INT-1310 | INT | 自动 | 新写 | 同上 `test_reject_empty_step_name` | 管理员 | 提交空步骤名 | 422 INVALID_STEPS | 空名称 |
| AC-318-01 | TC-INT-1310 | INT | 自动 | 新写 | `test_reject_step_without_approver` | 管理员 | 步骤无审批人 | 422 INVALID_STEPS | 空数组 |
| AC-318-02 | TC-INT-1310 | INT | 自动 | 新写 | `test_reject_non_member_step_approver` | 存在非委员用户 | 指定其为审批人 | 422 APPROVER_NOT_COMMITTEE_MEMBER | 普通用户 |
| AC-325-01 | TC-UNIT-1302 | UNIT | 自动 | 新写 | `approval_steps_ui.spec.js` StepsEditor | 2 步 | 点击下移 | 发出 move(0,1) | — |
| AC-326-01 | TC-INT-1311 | INT | 自动 | 新写 | `test_config_change_does_not_affect_inflight` | 实例在办 | 管理员改步骤 | 实例步骤状态不变 | 原 2 步 |
| AC-327-01 | TC-INT-1315 | INT | 自动 | 新写 | `test_legacy_flow_becomes_single_step` | 仅 FlowApprover 的旧流程 | 提交审批 | 生成 1 步 ANY | 1 名委员 |
| AC-327-02 | TC-INT-1315 | INT | 自动 | 新写 | 同上 | 在办旧实例 | 决策 | 按原快照通过 | 1 名委员 |
| AC-320-01 | TC-INT-1312 | INT | 自动 | 新写 | `AnyStrategyTests::test_any_one_passes_step` | 或签 2 人 | 1 人通过 | 推进到第 2 步 | 2 名委员 |
| AC-320-02 | TC-INT-1312 | INT | 自动 | 新写 | `test_partial_reject_does_not_end` | 或签 2 人 | 1 人拒绝 | 仍 PENDING/第 1 步，备注入时间线 | 备注“金额需核实” |
| AC-320-03 | TC-INT-1312 | INT | 自动 | 新写 | `test_all_reject_fails_instance` | 或签 2 人 | 2 人都拒绝 | 整单 REJECTED | — |
| AC-321-01 | TC-INT-1313 | INT | 自动 | 新写 | `AllStrategyTests::test_partial_approve_still_pending` | 会签 2 人 | 1 人通过 | 仍 ACTIVE | — |
| AC-321-02 | TC-INT-1313 | INT | 自动 | 新写 | `test_all_approve_advances` | 会签 2 人 | 2 人通过 | 推进第 2 步 | — |
| AC-321-03 | TC-INT-1313 | INT | 自动 | 新写 | `test_any_reject_fails_step` | 会签 2 人 | 1 通过 1 拒绝 | 整单 REJECTED | — |
| AC-322-01 | TC-INT-1311、TC-INT-1305 | INT | 自动 | 新写 | `test_tasks_only_for_current_step`、`approval_steps_ui.spec.js` Tasks | 2 步实例 | 查询待办 | 仅当前步骤审批人可见 | — |
| AC-323-01 | TC-E2E-1330 | E2E（替代：多步 API 旅程） | 自动 | 新写 | `test_two_steps_approved_end_to_end` | 2 步流程 | 两步均通过 | 决议 APPROVED | — |
| AC-324-01 | TC-INT-1312/1313 | INT | 自动 | 新写 | 两个拒绝用例 | 第 1/2 步失败 | 查询实例 | 后续步骤不激活、动作保留 | — |
| AC-324-02 | 现有 TC | INT | 自动 | 现有 | `test_approval_finality.py` | 已拒绝单据 | 原单重提 | 409 不可重提 | — |
| AC-328-01 | TC-INT-1304、TC-INT-1314 | INT | 自动 | 新写 | `ApprovalTimeline.vue` 测试、`test_timeline_permissions` | 进行到第 2 步 | 打开时间线 | 步骤名/到达时间/动作/备注 | — |
| AC-328-02 | TC-INT-1304 | INT | 自动 | 新写 | `approval_steps_ui.spec.js` | 第 2 步未到达 | 渲染 | 显示“未开始” | — |
| AC-328-03 | TC-INT-1304 | INT | 自动 | 新写 | 同上 | 备注 300 字 | 渲染 | 备注完整展示 | — |
| AC-329-01 | TC-INT-1314 | INT | 自动 | 新写 | `test_timeline_permissions` | 历史审批人 | GET 时间线 | 200 | — |
| AC-329-02 | TC-INT-1314 | INT | 自动 | 新写 | 同上 | 无关成员 | GET 时间线 | 403 FORBIDDEN | — |
| AC-330-01 | TC-INT-1305、TC-INT-1311 | INT | 自动 | 新写 | Tasks 测试、`test_tasks_only_for_current_step` | 第 2 步审批人 | 看待办 | 列表中无该单据 | — |
| AC-330-02 | TC-INT-1314 | INT | 自动 | 新写 | `test_timeline_permissions` | 管理员/成员 | GET 时间线 | 字段一致 | — |
| AC-331-01 | TC-INT-1310（小程序契约） | INT | 自动 | 新写 | `miniprogram/tests/approval_flow_contract.spec.js` | 小程序 api | 检查 decision 路径与 comment | 路径与字段存在 | — |
| AC-331-02 | TC-INT-1311（小程序契约） | INT | 自动 | 新写 | 同上 | 页面注册 | 检查 pages.json 与文案引用 | 页面可达、文案一致 | — |
| AC-332-01 | TC-INT-1314 | INT | 自动 | 新写 | `test_comment_length_limit` | 审批人 | 提交 501 字备注 | 400 INVALID_VALUE；500 字通过 | 500/501 字符 |
| AC-332-02 | TC-INT-1305 | INT | 自动 | 新写 | Tasks 测试 | 审批人不填备注 | 提交 | decide 收到空串 | — |

## 测试数据需求

- 业委会成员若干（CHAIR + 3 MEMBER + 1 无关成员），由 `tests/support.py` 工厂生成。
- 无 `[DATA_REQUIRED]`；不依赖外部服务。

## 不可测项

| AC | 原因 |
|---|---|
| — | 无 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-311 | TC-UNIT-1301/1302/1303、TC-INT-1310 | UNIT/INT |
| US-312 | TC-INT-1311、TC-INT-1315 | INT |
| US-313 | TC-INT-1312、TC-INT-1305 | INT |
| US-314 | TC-INT-1313 | INT |
| US-315 | TC-E2E-1330、TC-INT-1311 | E2E/INT |
| US-316 | TC-INT-1312/1313 | INT |
| US-317 | TC-INT-1304、TC-INT-1314 | INT |
| US-318 | TC-INT-1314 | INT |
| US-319 | TC-INT-1305、TC-INT-1311 | INT |
| US-320 | TC-INT-1310/1311（小程序契约）、TC-UNIT-1312 | INT/UNIT |
| US-321 | TC-INT-1314、TC-INT-1305 | INT |
