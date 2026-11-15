<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T17:47:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/requirements/user_stories.md</file>
    <file>project_workspace/ocap_identity_display/development/implementation_plan.md</file>
    <file>project_workspace/ocap_identity_display/development/code_review_report.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：用户端身份显示与认证房屋信息

## 测试策略

- 被测改动：MOD-101 后端身份/房屋聚合、MOD-102 Web 主页、MOD-103 小程序首页与“我的”。
- 范围 in：REQ-FUNC-136~141、REQ-NFUNC-024~026 对应 26 组 AC。
- 范围 out：管理端用户目录、历史决议/收入/报销中的已落库标签、微信真机渲染。
- 环境：Python 3.14.6 + Django 6.0.6（`config.test_settings`，SQLite 内存库）；Node 20 + vitest 2.1.9（jsdom）。
- 判定模式：baseline（INCREMENTAL，零新增失败）。
- 基线来源：改动前后端 561 项通过；本次新增 14 项测试（8 INT / 3 E2E / 3 客户端），并将 11 项旧口径断言按需求更新，最终后端 572 项通过。
- 分层：单元/组件 = 后端 `tests.unit`+`tests.smoke`、`frontend/tests`、`miniprogram/tests`；集成 = `backend/tests/integration`；E2E = `backend/tests/e2e`（多步 API 旅程，替代浏览器 E2E）。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 预期 |
|---|---|---|---|---|---|
| AC-145-01 | TC-INT-501、TC-WEB-502、TC-MP-502 | INT/组件 | 新写 | `test_identity_display.py::test_tc_int_501...`、`identity_display.spec.js` | 游客、units 空、数量 0 |
| AC-145-02 | TC-INT-502、TC-E2E-501、TC-WEB-501 | INT/E2E/组件 | 新写 | 同上、`test_identity_display_journey.py` | 产权业主、不出现“户主” |
| AC-145-03 | TC-INT-503 | INT | 新写 | `test_tc_int_503_appeal_owner_shows_owner` | 申诉来源显示产权业主 |
| AC-145-04 | TC-INT-504、TC-E2E-502 | INT/E2E | 新写 | 同上 | 同住人 |
| AC-145-05 | TC-INT-504 | INT | 新写 | 同上 | 产权业主优先 |
| AC-145-06 | TC-INT-507 | INT | 新写 | `test_tc_int_507_ended_membership_is_excluded` | 关系结束后显示游客 |
| AC-145-07 | TC-INT-505、TC-E2E-503 | INT/E2E | 新写 | `test_tc_int_505...` | 主任/副主任优先 |
| AC-145-08 | TC-INT-505 | INT | 新写 | 同上 | 委员/业主代表 |
| AC-145-09 | TC-INT-505 | INT | 新写 | 同上 | 职务失效回落产权业主 |
| AC-145-10 | TC-INT-502/504 | INT | 新写 | 同上 | labels 恰好 1 个元素 |
| AC-146-01 | TC-INT-502、TC-E2E-501、TC-WEB-501、TC-MP-501 | INT/E2E/组件 | 新写 | 同上 | 名称/住宅/89.50 ㎡ |
| AC-146-02 | TC-INT-506 | INT | 新写 | `test_tc_int_506...` | 按名称排序 |
| AC-146-03 | TC-INT-505 | INT | 新写 | 同上 | 车位类型与面积 |
| AC-146-04 | TC-INT-506 | INT | 新写 | 同上 | 类型“未登记” |
| AC-146-05 | TC-INT-506 | INT | 新写 | 同上 | 面积“未登记” |
| AC-146-06 | TC-INT-501、TC-WEB-502、TC-MP-502 | INT/组件 | 新写 | 同上 | 空状态 |
| AC-146-07 | TC-INT-507 | INT | 新写 | 同上 | 撤销后不显示 |
| AC-146-08 | TC-INT-504、TC-E2E-502、TC-WEB-501、TC-MP-501 | INT/E2E/组件 | 新写 | 同上 | 同住人标注 |
| AC-146-09 | TC-INT-506 | INT | 新写 | 同上 | 同 unit 去重、数量=行数 |
| AC-147-01 | TC-WEB-503 | 组件 | 新写 | `identity_display.spec.js` | 加载中不显示游客/0 |
| AC-147-02 | TC-WEB-504 | 组件 | 新写 | 同上 | 失败提示 + 重试 |
| AC-147-03 | TC-INT-507 | INT | 新写 | 同上 | 已结束关系不计入 |
| AC-148-01 | TC-E2E-501、TC-MP-503、TC-WEB-501 | E2E/组件 | 新写 | 同上 | 两端身份文案一致 |
| AC-148-02 | TC-WEB-501、TC-MP-501 | 组件 | 新写 | 同上 | 两端房屋字段一致 |
| AC-148-03 | TC-WEB-502、TC-MP-502 | 组件 | 新写 | 同上 | 空态一致 |
| AC-148-04 | [NOT_TESTABLE: 需两台真实登录端] | — | — | 人工验证清单 | 切换端后即时显示新身份 |
| REQ-FUNC-141（跨端契约） | TC-INT-508 | INT | 新写 | `test_frontend_contract.py::test_me_unit_display_fields_read_by_both_clients` | 两端源码读取 4 个字段 |

## 测试数据需求

| 数据 | 来源 |
|---|---|
| 专有部分：1栋1单元9层902号，住宅，89.50 ㎡ | 测试内创建 |
| 专有部分：2栋1单元3层301号，公寓，面积缺失 | 测试内创建 |
| 专有部分：车位 D001，12.00 ㎡ | 测试内创建 |
| 委员/业主代表/过期职务 | `make_seat` + 日期更新 |
| 清册手机号（唯一） | `next_phone()` |

## 不可测项

| AC | 原因 |
|---|---|
| AC-148-04 | 需要真实 Web 与小程序两端登录同一账号并即时切换，自动化环境无小程序运行时 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-145 | TC-INT-501~505、TC-E2E-501~503 | INT / E2E |
| US-146 | TC-INT-502、TC-INT-504~507、TC-E2E-501/502、TC-WEB-501、TC-MP-501 | INT / E2E / 组件 |
| US-148 | TC-INT-508、TC-WEB-501/502、TC-MP-501~503 | INT / 组件 |
