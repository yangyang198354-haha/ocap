<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-25T13:20:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.1</version>
  <input_files><file>project_workspace/ocap_role_home/phase_status.md</file><file>project_workspace/ocap/requirements/requirements_spec.md</file><file>frontend/src/portal/Home.vue</file><file>miniprogram/pages/index/index.vue</file><file>frontend/src/stores/auth.js</file><file>backend/apps/residency/housing.py</file><file>backend/apps/polls/views.py</file><file>backend/apps/ledger/views.py</file></input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 需求规格（增量）

## 执行摘要

用户要求在已完成方案设计的基础上落地“角色化首页”：不同身份进入 Web 或小程序时，只看到自己关心的模块，删除重复统计与重复入口，并保持三套主题与两端一致。功能需求 10 条、非功能需求 1 条；INFERRED 0 条（0 ÷ 11 = 0%）。优先级按“用户明确要求 = Must Have，配套一致性 = Should Have”赋值：Must Have 9 条、Should Have 1 条。

## 现有系统基线

- Web 首页现有模块：Hero（含“审批待办/进行中投票”徽章）、待办、4 张数据卡、账户余额、快捷入口、进行中的投票、最新公开决议 — `frontend/src/portal/Home.vue:4-105`。
- 小程序首页结构相同：徽章 + 待办 + 4 张数据卡 + 认证房屋 + 快捷入口 + 投票 + 最新决议 — `miniprogram/pages/index/index.vue:11-69`。
- 身份数据：`identities.units[].role`（HEAD/OWNER/RESIDENT）、`identities.committee.position`（CHAIR/VICE_CHAIR/MEMBER/REPRESENTATIVE）、`identities.summary` — `frontend/src/stores/auth.js:9-17`；后端 `backend/apps/identity/services.py:54-80`。
- 待审同住人：仅 HEAD/OWNER 房屋统计 `pending_application_count`，首页汇总为 `pending_review_count` — `backend/apps/residency/housing.py:164-174`。
- 现有接口权限：投票/决议/报表为登录用户（`IsMember`），收入/报销为业委会成员（`IsIncomeMember`），审批待办为业委会成员 — `backend/apps/polls/views.py:32`、`backend/apps/resolutions/views.py:151`、`backend/apps/income/views.py:140`、`backend/apps/ledger/views.py`。
- 三主题首页布局：`themes/neon.web.css`、`themes/bento.web.css`、`themes/terminal.web.css`，当前已统一为 4 栏 Bento。

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-366 | 首页根据当前用户的能力（是否户主/产权业主、是否业主代表、是否业委会成员）决定渲染哪些模块；无权限模块不渲染，且不发起对应接口请求 | 用户“因为权限的不同…有些无权限的看不到”“按照不同角色的关注度对卡片重新设计” | Must Have | 变更（固定模块 → 按能力渲染） | 能力判定以现有 `/me` 身份数据为准 |
| REQ-FUNC-367 | 同住人与产权业主使用同一版式与模块顺序；同住人的“我的房屋”为只读，且不显示“待我处理（同住人申请）” | 用户“同住人可以和产权业主看到一样的内容” | Must Have | 新增 | 只读 = 不出现邀请/变更/认证等管理操作 |
| REQ-FUNC-368 | 当用户任一房屋为 HEAD/OWNER 且存在待审同住人申请时，显示一张“待我处理”卡；多套房合并计数；数量为 0 时不显示该卡 | 用户确认“业主代表和委员也可能是户主…会给他们显示吗”→“单独成卡” | Must Have | 新增 | 卡片标题含数量，点击进入同住人审批 |
| REQ-FUNC-369 | 业主代表首页显示“待我表决”卡，仅列业主达标口径的投票，展示标题、截止时间与参与状态；无待表决时不显示 | 用户“业主代表的待我表决，是业主达标口径的投票” | Must Have | 新增 | 不混入财务/决议审批；不展示参与率（Q-RH-01 决策） |
| REQ-FUNC-370 | 业委会成员首页显示“待办审批”卡，仅列当前轮到本人审批的事项，最多 3 条并提供“全部”入口；数量为 0 时不显示列表内容 | 现有首页待办 + 用户“看到自己关心，想看的东西” | Must Have | 变更（保留待办，数量移入标题） | 非业委会成员不渲染 |
| REQ-FUNC-371 | “公开决议”卡同时展示业委会决议与业主代表决议，并用来源标签区分两类 | 用户“公开决议包含业委会决议和业主代表决议” | Must Have | 变更（单一列表 → 双来源 + 标签） | 点击进入对应决议详情 |
| REQ-FUNC-372 | 财务公开对所有登录用户可见（含游客与同住人）；业委会成员额外看到账户合计与报表入口 | 用户确认“游客可以看财务” | Must Have | 变更（账户余额卡按角色分层） | 游客只显示账户合计 + 报表入口，不展示逐账户明细（Q-RH-03 决策） |
| REQ-FUNC-373 | 业委会成员的首页提供一张“管理快捷”卡，包含收入表、报销/备用金、历史支出导入；其他角色不显示 | 现有快捷入口 + 用户“整合，排序” | Must Have | 变更（快捷入口宫格 → 单卡） | 不重复“待办/投票/报表”等已有卡片入口 |
| REQ-FUNC-374 | 首页不得重复展示同一指标：删除 4 张统计卡与 Hero 中的重复计数徽章；数量只出现在对应模块标题；移除 Hero 手机号 | 用户“卡面的信息有较多的冗余…可以整合” | Must Have | 变更（4 统计卡 + Hero 徽章 → 模块标题） | 模块隐藏时不保留空占位 |
| REQ-FUNC-375 | Web 三套主题（霓虹玻璃/极光 Bento/赛博终端）使用相同的模块顺序与栅格占位；微信小程序使用相同模块顺序的单列卡片流，底部 Tab 保持“首页/决议/投票/我的” | 用户“让不同角色从 web 或者小程序进来”“包含微信小程序的” | Should Have | 变更（主题各自布局 → 统一骨架） | 仅视觉样式可不同 |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-079 | 首页不新增后端接口或前端依赖；首屏请求只包含当前角色实际渲染的模块；在现有测试基线上零新增失败；三套主题下 768px 及以上无横向溢出，小程序常见机型下单列不截断 | 用户“不用改动代码”阶段已确认方案；项目画像 P8 禁用项 | Must Have | 新增 | 性能与兼容以构建、现有测试与人工多主题检查验证 |

## 约束

| ID | 约束 | 来源 |
|---|---|---|
| C-390 | 本次只改 Web 用户端与微信小程序前端；不改后端接口、权限模型、数据库结构与报表口径 | 用户“先梳理分析，画样式图，不用改动代码”后的实现范围确认 |
| C-391 | 身份判断复用现有 `/me` 的 `units[].role` 与 `committee.position`，不新增身份字段 | `frontend/src/stores/auth.js:9-17` |
| C-392 | 不改变现有路由与小程序 Tab 结构；模块跳转沿用既有页面 | 现网导航 |
| C-393 | 三套主题共用同一布局骨架，主题差异只体现在颜色、圆角、动效等视觉层 | `themes/*.web.css` |
| C-394 | 不引入新的前端依赖 | 画像 P8 |
| C-395 | 后台管理端首页不在本次范围 | 用户描述限定“主页面 / 小程序” |
| C-396 | 前端隐藏模块仅用于体验，不能替代后端权限校验；越权请求仍应返回既有 401/403 | 画像 P6 权限模型 |
| C-397 | 投票与公开决议类模块在无数据时保留空态文案、不隐藏模块；任务类模块（待我处理 / 待我表决 / 待办审批）数量为 0 时不显示（Q-RH-02 决策） | 用户 2026-11-25 决策“不隐藏” |

## 超出范围

- 新后端接口、新数据模型、新报表口径。
- 后台管理端首页改版。
- 消息推送、未读红点、站内通知中心。
- 用户自定义布局或拖拽排序。
- 小程序底部 Tab 结构调整。

## 待确认推断项

无（INFERRED 0 条）。

## 开放问题

| 编号 | 问题 | 默认口径（已定稿） | 阻断 |
|---|---|---|---|
| Q-RH-01 | “待我表决”是否需要展示参与率（如 68%）？现有投票接口是否返回参与人数/应参与人数尚未确认 | **结论（2026-11-25）：** 不展示参与率，只展示标题、截止时间与参与状态，不新增后端字段 | 否 |
| Q-RH-02 | 投票与公开决议在没有数据时是隐藏还是保留空态？ | **结论（2026-11-25）：** 不隐藏，保留空态文案；任务类模块仍按 0 隐藏（见 C-397） | 否 |
| Q-RH-03 | 游客是否能看到账户明细列表？ | **结论（2026-11-25）：** 只显示“账户合计 + 查看报表”，不展示逐账户明细 | 否 |

## 决策记录

| 编号 | 决策值 | 日期 | 来源 | 受影响位置 |
|---|---|---|---|---|
| D-RH-01 | 不展示投票参与率 | 2026-11-25 | 用户回复“q-rh-01 好” | REQ-FUNC-369 备注；US-357 AC-357-01 |
| D-RH-02 | 投票与公开决议无数据时保留空态、不隐藏 | 2026-11-25 | 用户回复“q-rh-02 不隐藏” | C-397；US-354 AC-354-01 |
| D-RH-03 | 游客只显示账户合计 + 报表入口 | 2026-11-25 | 用户回复“q-rh-03 好” | REQ-FUNC-372 备注；US-354 AC-354-02 |
