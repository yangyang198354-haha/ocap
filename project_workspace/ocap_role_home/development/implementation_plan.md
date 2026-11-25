<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-25T12:38:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_role_home/requirements/requirements_spec.md</file><file>project_workspace/ocap_role_home/requirements/user_stories.md</file><file>project_workspace/ocap_role_home/architecture/architecture_design.md</file><file>project_workspace/ocap_role_home/architecture/module_design.md</file><file>project_workspace/ocap_role_home/architecture/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 实现计划

## 实现概览

5 个模块、7 个源码文件（3 个 Web 源码、2 个小程序源码、2 个测试相关样式/代码不计）、10 个既有测试文件按新行为做最小调整。实现顺序按依赖拓扑：MOD-215/MOD-218（能力）→ MOD-217（骨架样式）→ MOD-216/MOD-219（页面编排）。无后端、无迁移、无新增依赖。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-215 | `frontend/src/stores/auth.js` | 修改 | — | L | 新增 `isRepresentative`、`ownerUnits`、`hasOwnerUnit`、`residentUnits`、`hasResidentUnit`、`isGuest`（IFC-436） | DONE |
| 2 | MOD-218 | `miniprogram/store/auth.js` | 修改 | — | L | 同口径 getter（IFC-442） | DONE |
| 3 | MOD-217 | `frontend/src/shared/style.css` | 修改 | — | L | 新增 `.home-half`/`.home-full` 占位与 ≥768px 规则（IFC-441）；保留原 `.home-grid` 2 栏基础与主题 4 栏覆盖 | DONE |
| 4 | MOD-216 | `frontend/src/portal/Home.vue` | 修改 | 1、3 | H | 角色档案顺序表、任务模块插入、公开决议双来源、待我表决有界详情、财务分层、移除统计卡/Hero 徽章/快捷宫格/手机号、信息公开模块 | DONE |
| 5 | MOD-219 | `miniprogram/pages/index/index.vue` | 修改 | 2 | H | 与 Web 相同的模块 key/顺序，单列卡片流；任务 0 隐藏、内容空态保留 | DONE |
| 6 | — | `frontend/tests/*.spec.js`（7 个） | 修改 | 4 | M | 旧首页断言按新行为最小调整 | DONE |
| 7 | — | `miniprogram/tests/*.spec.js`（5 个） | 修改 | 5 | M | 同上 | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-354 | AC-354-01 | Home.vue `profile`/`bodyModules`、欢迎卡 `auth.isGuest` 去认证；index.vue 同名逻辑 | DONE | 游客档案无 housing/pending*/management，不请求 `/approval/tasks`、`/me/housing` |
| US-354 | AC-354-02 | Home.vue finance 卡 `!auth.isGuest` 才渲染逐账户行；`publicFeed` 带来源标签 | DONE | 游客只展示合计 + 报表入口 |
| US-354 | AC-354-03 | miniprogram index.vue `CONTENT_ORDER.guest`，单列；pages.json 未改 Tab | DONE | 底部 Tab 保持原样 |
| US-355 | AC-355-01 | Home.vue `CONTENT_ORDER.resident`；housing 卡只读无管理操作 | DONE | 顺序：欢迎→房屋→投票→决议→信息→财务 |
| US-355 | AC-355-02 | `hasOwnerUnit` 才请求 `meApi.housing()`；`taskModules` 仅 owner | DONE | 同住人不请求 `/me/housing` |
| US-355 | AC-355-03 | 投票/决议/财务模块对 resident 可见；`publicFeed` 双来源 | DONE | 与产权业主一致 |
| US-356 | AC-356-01 | Home.vue housing 卡“我的房屋 · N”+ 房屋明细链接 | DONE | 点击卡片进入 `/units` |
| US-356 | AC-356-02 | `pendingReview`（`hasOwnerUnit && pendingReview > 0`），标题“待我处理 · N”，链接 `/units` | DONE | 0 时整卡不进入清单 |
| US-356 | AC-356-03 | `bodyModules` 中 management 仅 `isCommittee`；`loadRepVotes`/tasks 按能力 | DONE | 非委员不请求 `/approval/tasks` |
| US-357 | AC-357-01 | `loadRepVotes`（前 3 条 OPEN+REP_VOTE）+ `participationText` | DONE | 只显示标题、截止、参与状态；无参与率 |
| US-357 | AC-357-02 | `loadRepVotes` 过滤 `kind === 'REP_VOTE'` | DONE | 普通调查只进 polls 模块 |
| US-357 | AC-357-03 | `publicFeed` 合并 `resolutions` + `CLOSED REP_VOTE`，带来源标签 | DONE | 不显示 pendingTasks/management |
| US-358 | AC-358-01 | `pendingTasks` 任务卡，最多 3 条 + “全部” | DONE | 0 条不渲染（C-397） |
| US-358 | AC-358-02 | finance 合计 + 报表入口；management 收入表/报销/历史支出导入（Web） | DONE | 小程序管理项见 DEV-2 |
| US-358 | AC-358-03 | 删除 `.home-stat` 4 卡、`.home-metrics` 徽章；数量仅在模块标题 | DONE | 测试断言 `.home-stat`/`.home-q` 为 0 |
| US-359 | AC-359-01 | committee 档案 + 任务排序 `pendingTasks → pendingReview` | DONE | 顺序：待办审批→待我处理→财务→管理快捷→投票→决议 |
| US-359 | AC-359-02 | representative 档案 + 任务排序 `pendingVotes → pendingReview` | DONE | 顺序：待我表决→待我处理→投票→决议→财务→信息 |
| US-359 | AC-359-03 | 任务模块数量为 0 时不入清单 | DONE | 无占位卡 |
| US-360 | AC-360-01 | style.css `.home-half/.home-full`；主题 4 栏由生成物提供 | DONE | 见 DEV-1（Hero 占位） |
| US-360 | AC-360-02 | miniprogram `CONTENT_ORDER` 与 Web 同名同序；单列 | DONE | 无统计宫格 |

## 迁移

无。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| DEV-1：Hero 仍为 `span 2`（主题中 `grid-row: span 2`），未改成 `span 4` | IFC-441 `.home-hero { grid-column: span 4; }` | 三套主题的生成 CSS 已对 `.home-hero` 设定 `span 2 / row span 2`，改 `span 4` 需同时改 3 个主题源并改变既有视觉构图；4 栏 Bento 骨架本身不变 | 仅占位宽度差异，不影响模块顺序与 AC |
| DEV-2：小程序“管理快捷”仅含“报销 / 备用金”“待我审批” | REQ-FUNC-373 / AC-358-02 列三项 | 小程序无收入表、历史支出导入页面；C-392 禁止新增路由 | Web 三项齐全；小程序沿用既有页面，不产生死链 |
| DEV-3：小程序构建命令需 `UNI_INPUT_DIR=.` | 画像 P4 `npm run build:mp-weixin` | 仓库小程序为 HBuilderX 根目录布局，而 uni CLI 默认读取 `src/`；属既有工程配置问题 | 未改仓库配置；构建已用环境变量成功验证 |

## 开放问题

- [ASSUMPTION] “业主代表决议”按架构 A-01，以 `status=CLOSED` 的 `REP_VOTE` 投票充当。
- [ASSUMPTION] 游客“去认证”Web 指向 `/units/pick`，小程序指向 `/pages/units/index`（两端既有认证入口不同）。
- [ASSUMPTION] 业主代表“待我表决”计数以有界的前 3 条详情为准；超过 3 条时计数最多显示 3，卡片本身最多 3 条。
- [ASSUMPTION] 非游客（同住人/产权业主）保留逐账户明细；游客按 D-RH-03 只看合计。
