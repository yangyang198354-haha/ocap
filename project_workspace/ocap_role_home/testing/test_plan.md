<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-25T13:01:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/requirements/user_stories.md</file>
    <file>project_workspace/ocap_role_home/development/implementation_plan.md</file>
    <file>project_workspace/ocap_role_home/development/code_review_report.md</file>
    <file>project_workspace/ocap_role_home/architecture/module_design.md</file>
    <file>frontend/tests/home_role.spec.js</file>
    <file>miniprogram/tests/home_role.spec.js</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — ocap_role_home（GROUP_D）

## 测试策略

- 被测改动：Web 与微信小程序首页按角色（游客 / 同住人 / 产权业主 / 业主代表 / 业委会委员 / 多重身份）编排模块；删除 4 张统计卡、Hero 重复计数徽章与快捷宫格；两端模块顺序统一。仅前端改动，后端接口、权限、表结构、依赖均未变（C-390、C-394）。
- 范围：in scope = MOD-215/216/217（Web 能力 getter、首页编排、Bento 占位）与 MOD-218/219（小程序能力 getter、首页编排）；out of scope = 后端接口实现、主题源文件（`themes/*.theme.json`）、部署（GROUP_E）、小程序新增页面（C-392 已禁止）。
- 环境：
  - Web：Node + vitest 3 + Vue Test Utils + Element Plus，HTTP 层替身（`frontend/tests/http.mock.js`），jsdom。
  - 小程序：vitest + 自建 uni-app 桩（`miniprogram/tests/stubs/`），HTTP 层 `uni.request` 替身。
  - 后端：本次只跑既有契约用例；本机环境未安装 Django（`ModuleNotFoundError: No module named 'django'`），后端契约用例 BLOCKED，由前端静态契约用例替代（见集成报告）。
- 判定模式：INCREMENTAL baseline（零新增失败）。基线（GROUP_C 门控）：Web `Test Files 57 passed / Tests 607 passed`；小程序 `Test Files 22 passed / Tests 154 passed`。
- 分层：unit = 纯函数 / store 单模块、外部依赖 mock；integration（前端）= 组件 + 仓库 + 路由 + HTTP 替身（跨模块协作、请求是否发起与请求参数）；契约 = 客户端 API 调用路径 → 后端路由静态解析（`frontend/tests/layout_contract.spec.js`，MP 侧 `approval_flow_contract.spec.js`）；E2E = 项目无浏览器 E2E 框架，按组件/集成级多步旅程替代。
- critical path 口径：替代（前端组件级多步用例 TC-WEB-601~606、TC-INT-601~603）。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-354-01 | TC-WEB-601、TC-INT-601、TC-WEB-502、TC-MP-502、TC-MP-906 | 前端集成 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/home_role.spec.js`；`identity_display.spec.js`；`identity_property_pages.spec.js` | 游客 `/me`（`is_guest=true`） | 挂载首页 | 依次为欢迎卡（去认证）→公开决议→投票→信息公开→财务；无房屋/任务/管理；不请求 `/me/housing`、`/approval/tasks` | `ME{guest:true}` |
| AC-354-02 | TC-WEB-601、TC-INT-601 | 前端集成 | auto | 新写 | 同上 | 游客 + 单账户摘要 | 挂载首页 | 只显示 `¥100.00` 与报表入口，不显示账户名“公共账户”；决议带来源标签 | `accounts:[{公共账户,100.00}]` |
| AC-354-03 | TC-INT-601、TC-UNIT-882 | 前端集成 / 单元 | auto | 新写 + 现有 | `miniprogram/tests/home_role.spec.js`；`miniprogram/tests/brand_login.spec.js` | 游客 | 挂载首页 / 读 `pages.json` | 公开决议在投票之前；tabBar 仍为“首页/决议/投票/我的”4 项；单列结构由页面根布局保证（视觉见 M-02） | — |
| AC-355-01 | TC-WEB-604 | 前端集成 | auto | 新写 | `frontend/tests/home_role.spec.js` | 仅 RESIDENT 身份 | 挂载首页 | 我的房屋→投票→公开决议→信息公开→财务公开；无邀请/变更户主操作 | `RESIDENT_UNIT` |
| AC-355-02 | TC-WEB-604 | 前端集成 | auto | 新写 | 同上 | 仅 RESIDENT 身份 | 挂载首页 | 不显示“待我处理”，不请求 `/me/housing` | 同上 |
| AC-355-03 | TC-WEB-604 | 前端集成 | auto | 新写 | 同上 | 同住人 + 公开决议 + 已截止 REP_VOTE | 挂载首页 | 公开决议含“业主代表决议”来源；财务保留逐账户明细（与业主一致） | `CLOSED REP_VOTE id=32` |
| AC-356-01 | TC-WEB-501、TC-MP-501、TC-MP-906、TC-INT-885 | 前端集成 | auto | 现有 | `frontend/tests/identity_display.spec.js`；`miniprogram/tests/identity_display.spec.js`；`miniprogram/tests/identity_property_pages.spec.js`；`frontend/tests/layout_pages.spec.js` | HEAD/OWNER 房屋 N 套 | 挂载首页 | 显示“我的房屋 · N”，可进入 `/units` 明细；不再逐套展示名称/类型/面积 | 2 套（3 套同构） |
| AC-356-02 | TC-WEB-916、TC-WEB-605、TC-INT-603、TC-UNIT-555 | 前端集成 | auto | 现有 + 新写 | `frontend/tests/identity_property_identity_page.spec.js`；`home_role.spec.js`；`miniprogram/tests/product_review_ui.spec.js` | 待审 2 / 待审 0 / 委员兼户主 | 挂载首页 | 待审 2 显示“待我处理 · 2”并指向 `/units`；0 时整卡隐藏且无 0 占位；只有一张卡 | `pending_review_count=2/0` |
| AC-356-03 | TC-WEB-605、TC-UNIT-556 | 前端集成 / 单元 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/product_review_ui.spec.js` | 非委员产权业主 | 挂载首页 | 无“待办审批”“管理快捷”，不请求 `/approval/tasks`（路由表未登记该路径，请求即抛错） | `OWNER_UNIT`，无 position |
| AC-357-01 | TC-WEB-602、TC-INT-602 | 前端集成 | auto | 新写 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/home_role.spec.js` | 代表 + 2 条 OPEN REP_VOTE + 已投票/未投票 | 挂载首页 | “待我表决 · 2”，逐条标题/截止/已投票/未投票；无“参与率”；仅请求 2 条详情 | `/polls/21,22` |
| AC-357-02 | TC-WEB-602、TC-INT-602 | 前端集成 | auto | 新写 | 同上 | 混入普通调查（SURVEY） | 挂载首页 | 普通调查不出现在“待我表决”，仅出现在“投票与调查” | `kind=SURVEY id=23` |
| AC-357-03 | TC-WEB-602、TC-WEB-606 | 前端集成 | auto | 新写 | `frontend/tests/home_role.spec.js` | 代表 + 公开决议（含 CLOSED REP_VOTE） | 挂载首页 | 公开决议同时含业委会/业主代表来源标签；无“待办审批”“管理快捷”，不请求 `/approval/tasks` | `CLOSED REP_VOTE id=24` |
| AC-358-01 | TC-WEB-603、TC-INT-603、TC-MP-015b | 前端集成 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/home_role.spec.js`；`miniprogram/tests/pages.spec.js` | 委员 + 4 项审批 | 挂载首页 | “待办审批 · 4”，最多列出 3 条并提供“全部”；接口 403 时任务卡隐藏 | 4 条任务 |
| AC-358-02 | TC-WEB-603、TC-WEB-017 | 前端集成 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`frontend/tests/pages.spec.js` | 委员 | 挂载首页 | 财务显示合计与“报表”入口；管理快捷含收入表、报销/备用金、历史支出导入 | 空账户 |
| AC-358-03 | TC-WEB-603、TC-WEB-605、TC-UNIT-940（三风格首页用例） | 前端集成 / 单元 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`frontend/tests/ui_blocks.spec.js` | 委员 / 业主 / 三主题 | 挂载首页 / 逐主题挂载 | 无 `.home-stat`、`.home-q` 统计卡与宫格；待办/投票/决议数量只在模块标题出现一次；“待我处理”只有一张卡 | 3 个主题 |
| AC-359-01 | TC-WEB-603、TC-INT-603 | 前端集成 | auto | 新写 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/home_role.spec.js` | 委员兼户主 + 2 条待审 | 挂载首页 | 待办审批→待我处理·2→财务公开→管理快捷；仅一张待我处理卡 | `MEMBER + OWNER_UNIT` |
| AC-359-02 | TC-WEB-606 | 前端集成 | auto | 新写 | `frontend/tests/home_role.spec.js` | 代表兼户主 + 1 条待审 | 挂载首页 | 待我表决→待我处理·1→投票→公开决议→财务公开→信息公开；待我处理不重复 | `REPRESENTATIVE + OWNER_UNIT` |
| AC-359-03 | TC-WEB-605、TC-UNIT-555 | 前端集成 | auto | 新写 + 现有 | `frontend/tests/home_role.spec.js`；`miniprogram/tests/product_review_ui.spec.js` | 户主 + 待审总数 0 | 挂载首页 | 不显示“待我处理”，无 0 占位卡 | `pending_review_count=0` |
| AC-360-01 | TC-UNIT-940（三风格首页用例）、知识库布局用例（三份 `web.css` 均按 `html[data-theme]` 定义 `.home-*`） | 单元 | auto | 现有 | `frontend/tests/ui_blocks.spec.js` | 三主题 key | 逐主题挂载 / 读生成 CSS | 同角色模块与占位一致，仅颜色/圆角/动效不同；无统计卡宫格 | neon / bento / cyber |
| AC-360-02 | TC-INT-601、TC-INT-602、TC-INT-603、TC-UNIT-882 | 前端集成 / 单元 | auto | 新写 + 现有 | `miniprogram/tests/home_role.spec.js`；`miniprogram/tests/brand_login.spec.js` | 游客/代表/委员 | 挂载首页 | 模块顺序与 Web 一致；无统计卡宫格；tabBar 4 项不变（单列视觉见 M-02） | 三种角色 fixture |

## 测试数据需求

- 全部为用例内 fixture（`/me` 身份对象、`/polls`、`/resolutions`、`/ledger/accounts/summary`、`/info/posts`、`/me/housing`、`/approval/tasks`），不连接真实后端、不写持久存储，运行后可重复。
- 身份字段沿用画像事实：`identities.units[].role ∈ {HEAD, OWNER, RESIDENT}`、`identities.committee.position ∈ {CHAIR, VICE_CHAIR, MEMBER, REPRESENTATIVE}`、`is_guest`。
- 无 `[DATA_REQUIRED]`。
- 后端契约 `backend/tests/integration/test_frontend_contract.py` 需要 Django 环境；本机未安装 Django，标环境 BLOCKED（非数据缺失），替代与补跑见集成报告与人工清单 M-04。

## 不可测项

| AC | 原因 | 处理 |
|---|---|---|
| AC-360-01（宽度 ≥768px 无横向溢出；三主题仅颜色/圆角/动效不同） | jsdom 无布局引擎与像素渲染，无法断言实际占位尺寸与横向溢出 | 模块顺序/占位结构已由 TC-UNIT-940 与生成 CSS 用例覆盖；视觉与溢出进人工清单 M-01 |
| AC-360-02（小程序单列卡片流视觉与底部 Tab 外观） | 无微信开发者工具/真机环境 | 顺序与 tabBar 文案已自动化（TC-INT-601~603、TC-UNIT-882）；单列视觉进人工清单 M-02 |
| AC-358-02（小程序管理快捷三项） | DEV-2（已批准）：小程序无收入表/历史支出页，C-392 不加路由，只保留报销/备用金与待我审批；Web 三项已由 TC-WEB-603 覆盖 | 按已接受偏差处理，不算缺陷；人工清单 M-03 确认微信端入口文案 |
| AC-356-01（恰好 3 套房文案） | 用例以 2 套变体验证“我的房屋 · N”与跳转，3 套为同构数据（N 为动态值） | 不单列不可测；以 2 套用例覆盖公式 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-354 游客公开内容 | TC-WEB-601、TC-INT-601、TC-WEB-502、TC-MP-502、TC-INT-602（间接） | 前端集成 |
| US-355 同住人同版式 | TC-WEB-604、TC-MP-501（房屋数量） | 前端集成 |
| US-356 产权业主房屋与待我处理 | TC-WEB-501、TC-WEB-916、TC-WEB-605、TC-MP-906、TC-INT-603 | 前端集成 |
| US-357 业主代表待我表决 | TC-WEB-602、TC-WEB-606、TC-INT-602 | 前端集成 |
| US-358 委员工作台 | TC-WEB-603、TC-INT-603、TC-WEB-017 | 前端集成 |
| US-359 多重身份组合 | TC-WEB-603、TC-WEB-606、TC-WEB-605、TC-INT-603 | 前端集成 |
| US-360 三主题与小程序一致（Should Have） | TC-INT-601~603、TC-UNIT-882、TC-UNIT-940 | 前端集成 / 单元 |

覆盖结论：Must Have 6/6 故事均有真实执行用例；无空行。
