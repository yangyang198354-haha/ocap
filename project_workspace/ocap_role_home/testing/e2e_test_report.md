<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-25T13:04:30+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/testing/test_plan.md</file>
    <file>project_workspace/ocap_role_home/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_role_home/testing/integration_test_report.md</file>
    <file>frontend/tests/home_role.spec.js</file>
    <file>miniprogram/tests/home_role.spec.js</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — ocap_role_home

## 摘要

critical path 口径：替代（前端组件级多步用例 TC-WEB-601~606、TC-INT-601~603；项目无浏览器 E2E 框架）

- 执行时间：2026-11-25 12:56–13:03（最后一次全量回归 13:03:56）；环境：vitest（Web jsdom + 小程序 uni-app 桩）。
- E2E 替代用例：total = pass + fail + skip + blocked + not_testable = 9 = 9 + 0 + 0 + 0 + 0。
- critical path 覆盖率 = 6 / 6 = 100%（Must Have US-354~359 均有真实执行用例）。
- critical path 通过率 = 9 / 9 = 100.0%。
- 本层门控：PASSED。

## 全量回归

```
$ cd frontend && npx vitest run
Test Files  58 passed (58)
     Tests  613 passed (613)

$ cd miniprogram && npm test
Test Files  23 passed (23)
     Tests  157 passed (157)
```

- 基线（GROUP_C 门控）：Web 57 files / 607 tests；小程序 22 files / 154 tests。
- 相对基线新增失败数：0（新增 Web 6 例 / 小程序 3 例；无失败、无 skip）。PM 门控复核：`npx vitest run tests/home_role.spec.js tests/layout_contract.spec.js` → 12 passed；`npx vitest run tests/home_role.spec.js tests/approval_flow_contract.spec.js` → 6 passed。

## 用户旅程

### TC-E2E-601: 游客首屏（Web 与小程序）

- 关联：US-354 / AC-354-01/02/03；实现于 TC-WEB-601、TC-INT-601。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 以无房屋身份打开首页 | 身份显示“游客”，欢迎卡含“去认证” | 一致 | PASS |
| 2 | 检查模块 | 公开决议→投票→信息公开→财务；无房屋/任务/管理 | 一致（两端） | PASS |
| 3 | 检查请求 | 不请求 `/me/housing`、`/approval/tasks` | 一致 | PASS |
| 4 | 查看财务 | 仅 `¥100.00` 合计与报表入口，无逐账户明细 | 一致 | PASS |
| 5 | 查看决议来源 | 带“业委会决议”标签 | 一致 | PASS |

- 结论：PASS

### TC-E2E-602: 业主代表“待我表决”与公开决议

- 关联：US-357 / AC-357-01/02/03；实现于 TC-WEB-602、TC-INT-602、TC-WEB-606。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 代表打开首页（2 条 OPEN REP_VOTE） | “待我表决 · 2”，逐条标题/截止/已投票/未投票 | 一致 | PASS |
| 2 | 检查参与率 | 不出现“参与率” | 一致 | PASS |
| 3 | 检查详情请求 | 仅 `/polls/21`、`/polls/22`（有上界） | 一致 | PASS |
| 4 | 混入普通调查 | 不出现在待我表决，仅在“投票与调查” | 一致 | PASS |
| 5 | 查看已截止 REP_VOTE | 进入公开决议，带“业主代表决议”来源 | 一致 | PASS |
| 6 | 检查无权限模块 | 无“待办审批”“管理快捷”，不请求 `/approval/tasks` | 一致 | PASS |

- 结论：PASS

### TC-E2E-603: 业委会委员兼户主工作台

- 关联：US-358、US-359 / AC-358-01/02/03、AC-359-01；实现于 TC-WEB-603、TC-INT-603。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 委员兼户主打开首页（4 项审批、2 条待审） | “待办审批 · 4”与“待我处理 · 2” | 一致 | PASS |
| 2 | 检查待办列表 | 最多 3 条并出现“全部”入口 | 3 条 + 全部 | PASS |
| 3 | 检查顺序 | 待办审批→待我处理→财务公开→管理快捷 | 一致（两端） | PASS |
| 4 | 检查管理快捷 | 收入表、报销/备用金、历史支出导入 | 一致（Web） | PASS |
| 5 | 检查计数与卡片 | 数量只在标题出现一次；仅一张“待我处理” | 一致 | PASS |

- 结论：PASS

### TC-E2E-604: 同住人与产权业主同版式

- 关联：US-355 / AC-355-01/02/03；实现于 TC-WEB-604。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 同住人打开首页 | 我的房屋（只读）→投票→决议→信息→财务 | 一致 | PASS |
| 2 | 检查房屋卡 | 无邀请同住人/变更户主操作 | 一致 | PASS |
| 3 | 检查任务 | 无“待我处理”，不请求 `/me/housing` | 一致 | PASS |
| 4 | 查看财务与来源 | 保留逐账户明细；决议含业主代表来源 | 一致 | PASS |

- 结论：PASS

### TC-E2E-605: 业主代表兼户主 + 空态/0 隐藏

- 关联：US-359 / AC-359-02/03；实现于 TC-WEB-606、TC-WEB-605。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 代表兼户主打开首页（1 条待审） | 待我表决→待我处理 · 1→投票→决议→财务→信息 | 一致 | PASS |
| 2 | 检查重复 | “待我处理”只出现一张卡 | 一致 | PASS |
| 3 | 待审数置 0 | 不显示“待我处理”，无 0 占位卡 | 一致 | PASS |
| 4 | 投票/决议/信息为空 | 保留空态文案（暂无进行中的投票/暂无公开决议/暂无公告） | 一致 | PASS |

- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| 无 | — | 本轮未发现产品缺陷 | — | — | — |

说明：CR-004（Web 与小程序各存一份模块顺序常量）为已接受 MINOR 风险（ADR-200），本轮双向顺序用例未发现漂移，不升级为缺陷。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-360-01 / TC-UNIT-940 | 在霓虹玻璃、极光 Bento、赛博终端三主题下，分别以 1280px 与 768px 宽度打开同一角色首页 | 三主题模块顺序与栅格占位一致，仅颜色/圆角/动效不同；≥768px 无横向滚动 | Chrome 桌面浏览器 | 否（Should Have） |
| M-02 | AC-360-02 / TC-INT-601~603 | 微信开发者工具或真机打开小程序首页，逐角色浏览 | 单列卡片流；底部 Tab 为“首页/决议/投票/我的”；无统计卡宫格 | 微信开发者工具 / 真机 | 否（Should Have） |
| M-03 | AC-358-02（DEV-2） | 委员在小程序首页查看“管理快捷” | 仅“报销/备用金”与“待我审批”两项，文案正确（已批准偏差：不提供收入表/历史支出页） | 微信开发者工具 | 否 |
| M-04 | 契约补跑 | 在测试环境执行 `python manage.py test tests.integration.test_frontend_contract --settings=config.test_settings` | 双端 `api.js` 全部调用解析到 Django 路由；首页字段契约通过 | 已安装 Django 的测试环境 | 否 |
