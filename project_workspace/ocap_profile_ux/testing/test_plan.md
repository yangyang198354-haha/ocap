<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-19T00:32:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/requirements/user_stories.md</file>
    <file>project_workspace/ocap_profile_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_profile_ux/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — ocap_profile_ux

## 测试策略

- 被测改动：MOD-153～163（资料字段、公开 profile、默认头像、5 MB 头像、席位表格与过滤、审批流程详情/编辑、房屋关系过滤/搜索）。
- 范围 in：REQ-FUNC-255～263、REQ-NFUNC-051/052；out：微信小程序（I-1）、真实微信/短信 API（使用 fakes）。
- 环境：Python 3.14 + Django 测试配置 `config.test_settings`（SQLite 内存库）；前端 vitest 2.1.9 + jsdom；命令取画像 P4。
- 判定模式：INCREMENTAL / baseline——每层相对基线零新增失败且新写用例全部通过；critical path 通过率 1.00。
- 基线来源：GROUP_C 实跑记录（后端 6 个 Windows 文件权限类失败；前端 TC-UNIT-873、qa TC-UNIT-103、theme_build 为既有失败；两个路由 spec 在满载并行下超时、单跑通过）。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 |
|---|---|---|---|---|---|---|---|
| AC-261-01/02、AC-262-01/02 | TC-UNIT-1506 | unit | 新写 | `frontend/tests/profile_ux.spec.js` | 用户无头像 | 挂载右上角菜单 | 触发器中存在 `img.auth-image`，alt=默认头像 |
| AC-263-01/02/03 | TC-INT-1502 | integration | 新写 | `backend/tests/integration/test_profile_ux_api.py::AvatarLimitTests` | 注册用户 | 上传 4.9MB / 5.1MB / gif | 201 / 413 FILE_TOO_LARGE / 400 |
| AC-263-02/03 | 既有 TC-INT-901、TC-UNIT-531（已按 5MB 更新） | unit | 现有调整 | `frontend/tests/layout_pages.spec.js`、`product_review_ui.spec.js` | 选择文件 | beforeUpload | 超 5MB 拒绝且文案含 5 MB |
| AC-264-01/02/03 | TC-INT-1503、TC-UNIT-1504 | integration/unit | 新写 | `test_profile_ux_api.py::SeatListProfileUxTests`、`profile_ux.spec.js` | 管理员 + 待绑定/已绑定席位 | 列表/表格渲染 | holder_detail 8 键齐全；表格 10 列；电话脱敏 |
| AC-265-01/02/03/04 | TC-INT-1503 | integration | 新写 | 同上 | admin/普通用户 | bucket=active/ended、非法 bucket、普通用户 | 默认仅 ACTIVE；ended 命中 REVOKED；400/403 |
| AC-266-01 | TC-INT-1504 | integration | 新写 | `test_profile_ux_api.py::FlowDetailTests` | 流程含审批人 | 列表读取 | approvers 项含 id/nickname/identity_label |
| AC-267-01/02 | TC-INT-1504 | integration | 新写 | 同上 | 管理员 | PUT 改名与换审批人 | 200，名称/审批人更新 |
| AC-268-01/02/03 | TC-INT-1505 | integration | 新写 | `test_profile_ux_api.py::MembershipFilterTests` | 一条关系 | building/unit_no/floor 过滤 | count=1；错误楼层=0 |
| AC-269-01/02/03/04 | TC-INT-1505、TC-UNIT-1505 | integration/unit | 新写 | 同上 + `profile_ux.spec.js` | 关系数据 | name/phone/q 搜索 | 命中 1；前端 phone/q 参数正确；非法 phone 400 |
| AC-270-01/02/03/04 | TC-UNIT-1501/1502、TC-INT-1501 | unit/integration | 新写 | `profile_ux.spec.js`、`test_profile_ux_api.py::ProfileFieldsTests` | 他人/本人/未知用户 | 打开 profile | 白名单 8 键；is_self 显示编辑；404；无敏感字段 |
| AC-271-01/02/03/04 | TC-INT-1501（实名部分）、TC-UNIT-1503 | integration/unit | 新写 | 同上 | 业主/非业主 | 开关/公开页 | 默认 false；非业主 403；开启后他人可见；关闭即隐藏 |
| AC-272-01/02/03 | TC-INT-1501、TC-UNIT-1501/1503 | integration/unit | 新写 | 同上 | 用户 | 保存 100 字/超长；空签名；HTML | 200/400；空态文案；插值转义 |
| AC-260-01/02 | 无自动化 | — | — | — | — | — | [NOT_TESTABLE: jsdom 不计算像素与视口布局] |

## 测试数据需求

- 合成手机号（`tests.support.next_phone`）、合成姓名（业主甲/乙/张三/李四）、合成清册单元；无真实个人信息。
- 头像边界文件在内存生成（4.9 MB / 5.1 MB PNG 魔数 + 填充）。

## 不可测项

| AC | 原因 |
|---|---|
| AC-260-01、AC-260-02 | jsdom 不计算像素/布局，控件垂直中心偏差与换行需真实浏览器或人工走查（见 e2e 报告人工验证清单） |
| AC-265-02 的“结束原因（如有）”展示 | 数据层断言 `end_reason` 字段存在；具体文案取决于历史数据，E2E 未构造 |
| AC-270-01 决议参与人入口 | 按偏差 D-03 不在范围（既有隐私契约禁止 participants 返回 user_id） |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-260 | [NOT_TESTABLE] + 人工清单 MV-01 | — |
| US-261 | TC-UNIT-1506、TC-INT-1502 | unit/integration |
| US-262 | TC-UNIT-1506 | unit |
| US-263 | TC-INT-1502、TC-UNIT-901/531（5MB 更新） | integration/unit |
| US-264 | TC-INT-1503、TC-UNIT-1504 | integration/unit |
| US-265 | TC-INT-1503、TC-UNIT-1504 | integration/unit |
| US-266 | TC-INT-1504 | integration |
| US-267 | TC-INT-1504 | integration |
| US-268 | TC-INT-1505、TC-UNIT-1505 | integration/unit |
| US-269 | TC-INT-1505、TC-UNIT-1505 | integration/unit |
| US-270 | TC-UNIT-1501/1502、TC-INT-1501 | unit/integration |
| US-271 | TC-INT-1501、TC-UNIT-1503 | integration/unit |
| US-272 | TC-INT-1501、TC-UNIT-1501/1503 | integration/unit |
