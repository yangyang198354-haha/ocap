<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-26T23:45:32+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_typography_unify/phase_status.md</file></input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格 — Web 端字体与标题统一

## 执行摘要

用户原文：「检查导航栏一级、二级菜单字体，各个页面，卡片字体大家是否合适。 有些页面又中英文标题，有些页面缺少标题。 全部梳理一下，统一一下字体，标题」。

经用户确认的范围：**Web 两端全部**（管理端侧边一级/二级导航、用户端导航、所有页面与卡片，含 bento/neon/terminal 三套主题），不含微信小程序；标题以**中文主标题为主**，英文仅作品牌/装饰小字或去掉；**允许补写缺失标题并直接改名**。

功能需求 9 条 / 非功能需求 5 条 / 约束 4 条。`[INFERRED]` 2 条（2 ÷ (9+5) = **14.3%** ≤ 20%）。
优先级默认规则：用户明确提到的"导航字体""页面与卡片字体""中英混用标题""缺失标题"记为 Must Have；由统一规范推导出的层级与术语一致性记为 Should Have。

## 现有系统基线（INCREMENTAL）

统一入口：全局字号与标题类集中在 `frontend/src/shared/style.css`；字体变量由 `frontend/src/theme/generated/themes.css:29-30,142-143,546-547,1184-1185` 按主题生成；主题差异在 `themes/*.web.css` 覆盖。

### 全局字体与标题类（基线）

| 位置 | 现状 | 证据 |
|---|---|---|
| 正文字体 | `--font`：MiSans / HarmonyOS Sans SC / PingFang SC / system-ui / Microsoft YaHei | `frontend/src/theme/generated/themes.css:29` |
| 等宽字体 | `--mono`：SF Mono / JetBrains Mono / ui-monospace / Menlo / Consolas | `frontend/src/theme/generated/themes.css:30` |
| 页面标题 | `.page-head h1` 24px/32px/700；移动端 22px/30px | `frontend/src/shared/style.css:34,176` |
| 页面眉标 | `.page-eyebrow` 11px/600，大写、字距 .12em、强调色 | `frontend/src/shared/style.css:33` |
| 卡片标题 | `.title` 18px/650；终端主题 mono+大写 | `frontend/src/shared/style.css:29`；`themes/terminal.web.css:30-34` |
| 分区标题 | `.section-title` 14px/650、次要色 | `frontend/src/shared/style.css:150` |
| 首页问候 | `.home-greeting` 24px/700，桌面 30px | `frontend/src/shared/style.css:245,277` |
| 首页卡片标题 | bento 主题单独放大到 20px | `themes/bento.web.css:480` |

### 导航字体（基线）

| 元素 | 现状 | 证据 |
|---|---|---|
| 一级菜单 | `.side-item` 使用 `font: inherit`，继承 body 16px；bento 覆盖 17px、neon 16px、terminal 16px | `frontend/src/shared/style.css:98-103`；`themes/bento.web.css:422`；`themes/neon.web.css:198`；`themes/terminal.web.css:216` |
| 二级菜单 | `.side-sub-item` 14px，三套主题均未覆盖字号 | `frontend/src/shared/style.css:111-115` |
| 窄屏切换条 | `.sub-nav-item` 未设字号，继承 16px，与二级 14px 不一致 | `frontend/src/shared/style.css:140-143` |
| 终端主题 | `.title`/`.side-item`/`.side-sub-item`/`.sub-nav-item` 统一强制 mono + `text-transform: uppercase` + 字距 .06em | `themes/terminal.web.css:30-34` |
| 激活态 | 一级/二级均为 `font-weight: 650` | `frontend/src/shared/style.css:105-107` |

### 页面标题盘点表（用户端）

| 路由 | 文件 | 标题标记 | 当前文案 | 语言 | 样式 | 结论 |
|---|---|---|---|---|---|---|
| `/` | `frontend/src/portal/Home.vue:9` | `h2.home-greeting` | 你好，{昵称} | 中文 | 24/700，桌面 30 | 无页面级标题 |
| `/info` | `frontend/src/portal/InfoList.vue:5-6` | `page-eyebrow` + `h1` | INFORMATION / 信息公开 | 中英 | 24/700 | 有英文眉标 |
| `/polls` | `frontend/src/portal/Polls.vue:5-6` | `page-eyebrow` + `h1` | POLLS / 投票 / 调查 | 中英 | 24/700 | 有英文眉标；斜杠两侧带空格 |
| `/reports` | `frontend/src/portal/Reports.vue:5-6` | `page-eyebrow` + `h1` | FINANCE / 财务报表 | 中英 | 24/700 | 有英文眉标 |
| `/resolutions` | `frontend/src/portal/Resolutions.vue:5-6` | `page-eyebrow` + `h1` | RESOLUTIONS / 业委会决议 | 中英 | 24/700 | 有英文眉标 |
| `/me`（窄屏） | `frontend/src/portal/Me.vue:6-12` | `page-eyebrow` + `h1` + `h3.title` | ACCOUNT / 我的 / 我的 | 中英 | 24/700 + 18/650 | 同页重复两个"我的" |
| `/resolutions/:id` | `frontend/src/portal/ResolutionDetail.vue:4` | `h3.title` | 决议标题 | 中文 | 18/650 | 详情页用卡片标题充当页面标题 |
| `/polls/:id` | `frontend/src/portal/PollDetail.vue:4` | `h3.title` | 投票标题 | 中文 | 18/650 | 同上 |
| `/info/:id` | `frontend/src/portal/InfoDetail.vue:8` | `h2`（无类） | 文章标题 | 中文 | 浏览器默认 | 字号失控 |
| `/tasks` | `frontend/src/portal/Tasks.vue:4` | `h3.title` | 审批待办 | 中文 | 18/650 | 无页面标题 |
| `/claims`、`/claims/todo` | `frontend/src/portal/Claims.vue:5` | `h3.title` | 报销 / 备用金 | 中文 | 18/650 | 与导航"报销/备用金"空格不一致 |
| `/income` | `frontend/src/portal/Income.vue:4` | `h3.title` | 收入表 | 中文 | 18/650 | 无页面标题 |
| `/historical-expenses` | `frontend/src/portal/HistoricalExpenses.vue:6` | `h3.title` | 历史支出导入 | 中文 | 18/650 | 无页面标题 |
| `/units`（我的身份与房屋） | `frontend/src/portal/units/UnitsIdentity.vue:6,46` | 仅 `el-tab-pane label` | 我的身份与房屋 | 中文 | Element 默认 | 无页面标题，依赖 Tab 名 |
| `/units/appeal` | `frontend/src/portal/units/AppealCenter.vue:5,8` | 仅 `el-tab-pane label` | 认证申诉 / 我的申诉 | 中文 | Element 默认 | 无页面标题 |
| `/units/applications` | `frontend/src/portal/units/UnitsApplications.vue:4` | `h3.title` | 我的同住人申请 | 中文 | 18/650 | 无页面标题 |
| `/units/review` | `frontend/src/portal/units/UnitsReview.vue:4` | `h3.title` | 待我审批的同住人申请 | 中文 | 18/650 | 无页面标题 |
| `/units/pick` | `frontend/src/portal/units/UnitsPick.vue:6` | `h3.title` | 认证产权 | 中文 | 18/650 | 无页面标题 |
| `/me/*` | `frontend/src/portal/me/MeProfile.vue:9`、`MeStyle.vue:6`、`MePassword.vue:5`、`MeEmail.vue:5`、`MeCancel.vue:5`、`MePhone.vue:5,16` | `h3.title` | 个人资料 / 系统设置 / 设置密码 / 邮箱验证 / 账号注销 / 绑定手机×2 | 中文 | 18/650 | 无页面标题；MePhone 重复标题 |
| `/users/:id/profile` | `frontend/src/portal/UserProfile.vue:10` | `h3.profile-name` | 昵称 | 中文 | 18/650 | 无页面标题（昵称充当标题） |

### 页面标题盘点表（管理端）

| 路由 | 文件 | 标题标记 | 文案 | 样式 | 结论 |
|---|---|---|---|---|---|
| `/admin/registry` | `frontend/src/admin/AdminRegistry.vue:5` | `h3.title` | 业主清册 | 18/650 | 无页面标题 |
| `/admin/appeals` | `frontend/src/admin/AdminAppeals.vue:4` | `h3.title` | 产权申诉审核 | 18/650 | 无页面标题 |
| `/admin/memberships` | `frontend/src/admin/AdminMemberships.vue:5` | `h3.title` | 用户房屋关系 | 18/650 | 无页面标题 |
| `/admin/seats` | `frontend/src/admin/AdminSeats.vue:7` | `h3.title` | 业委会席位 / 业主代表 | 18/650 | 无页面标题 |
| `/admin/flows` | `frontend/src/admin/AdminFlows.vue:5` | `h3.title` | 审批流程 | 18/650 | 无页面标题 |
| `/admin/finance*` | `frontend/src/admin/AdminFinance.vue:4,20` | `h3.title` | 财务（报销 / 备用金）、金额上限 | 18/650 | 同页两个标题；括号+空格混排 |
| `/admin/finance/accounts` | `frontend/src/admin/AdminAccounts.vue:5` | `h3.title` | 账户管理 | 18/650 | 无页面标题 |
| `/admin/users*` | `frontend/src/admin/AdminUsers.vue:5,23` | `h3.title` | 管理员账号、注册用户 | 18/650 | 同页两个标题 |
| `/admin/audit*` | `frontend/src/admin/AdminAudit.vue:4,12` | `h3.title` | 系统配置、审计日志 | 18/650 | 同页两个标题 |
| `/admin/content/posts` | `frontend/src/admin/AdminContentPosts.vue:4` | `h2`（无类） | 信息公开 | 浏览器默认 | 标题标记与其余页面不同 |
| `/admin/content/posts/:id` | `frontend/src/admin/AdminContentEditor.vue:4` | `h2`（无类） | 编辑内容 | 浏览器默认 | 标题标记不同 |
| `/admin/content/styles` | `frontend/src/admin/AdminStyleTemplates.vue:6` | `h3.title` | 我的版式模板 | 18/650 | 无页面标题 |
| `/admin/content/media` | `frontend/src/admin/AdminMedia.vue:4` | `h2`（无类） | 素材库 | 浏览器默认 | 标题标记不同 |
| `/admin/content/services*` | `frontend/src/admin/AdminAiServices.vue:3` | `h2`（无类） | AI 服务配置 · {模型与生成服务｜提示词模板} | 浏览器默认 | 中英混排 + 动态副题 |
| `/admin/content/platforms` | `frontend/src/admin/AdminPlatforms.vue:3` | `h2`（无类） | 平台账户 | 浏览器默认 | 标题标记不同 |
| `/admin/content/settings` | `frontend/src/admin/AdminContentSettings.vue:3` | `h2`（无类） | 内容中心参数 | 浏览器默认 | 标题标记不同 |

### 导航文案与页面标题的不一致（基线）

| 导航（`frontend/src/layout/menus.js`） | 页面标题 | 差异 |
|---|---|---|
| `menus.js` 「投票/调查」 | `Polls.vue` 「投票 / 调查」 | 斜杠空格不一致 |
| `menus.js` 「报销/备用金」 | `Claims.vue` 「报销 / 备用金」 | 斜杠空格不一致 |
| `menus.js` 「我的认证与申述」 | `UnitsAppeal`/`AppealCenter`「认证申诉」 | **错别字"申述"→"申诉"**，且名称不对应 |
| `menus.js` 「信息公开」 | `AdminContentPosts.vue`「信息公开」 | 管理端内容与用户端信息公开同名，含义不同 |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-376 | 除登录/注册/微信回调外，Web 两端每个路由页面都应有一个页面标题区：唯一的 `h1` 主标题 + 可选一行说明；首页无可见页面标题时提供仅屏幕阅读器可见的「主页」`h1` | 用户原文「有些页面缺少标题」；基线：`InfoList.vue:5-6` 等 5 页有 `page-head`，其余页面无 | Must Have | 变更 | 现状：5 页 page-head + h1，2 页 h2，其余 h3 或无标题 |
| REQ-FUNC-377 | 页面主标题只使用中文；英文仅允许出现在品牌标识与（可选的）页面眉标中，不得作为主标题，也不得出现"英文眉标只有部分页面有"的不一致 | 用户原文「有些页面又中英文标题」；用户确认「中文主标题为主」；基线：仅 `InfoList/Polls/Reports/Resolutions/Me` 5 页有英文眉标 | Must Have | 变更 | 建议统一移除英文眉标，仅保留品牌英文 |
| REQ-FUNC-378 | 当前没有页面标题的页面补齐中文页面标题：`我的身份与房屋`、`认证申诉`、`我的同住人申请`、`待我审批的同住人申请`、`认证产权`、`个人资料`、`系统设置`、`审批待办`、`收入表`、`历史支出导入`、`账户管理`、`报表详情`、管理端 13 个页面等 | 用户原文「允许补写」+ 基线盘点表 | Must Have | 新增 | 具体文案见下方"标题文案表" |
| REQ-FUNC-379 | 侧边导航一级/二级名称与对应页面主标题使用同一术语表：斜杠统一为「/」且两侧不加空格；「我的认证与申述」更正为「我的认证与申诉」；同一实体在导航与标题中名称一致 | 基线 `frontend/src/layout/menus.js` 与各页面标题对照表 | Must Have | 变更 | 含错别字修正 |
| REQ-FUNC-380 | 建立并应用统一字号阶梯：页面标题 24/700（窄屏 22）、卡片标题 18/650（首页卡片同用 18，取消 bento 单独 20）、正文 14/400、辅助与元信息 12–13/400–500、分区标题 14/650 次要色 | 用户原文「卡片字体是否合适」；基线 `style.css:29,34,150,176`；`bento.web.css:480` | Must Have | 变更 | 禁止用浏览器默认 h2 字号 |
| REQ-FUNC-381 | 导航字号统一：一级菜单 15px/600、二级菜单 13px/500、窄屏切换条 13px；三套主题只允许改变字族与颜色，不得各自覆盖字号；激活态字重与其余一致，不额外放大 | 用户原文「导航栏一级、二级菜单字体」；基线：一级 16/17px 三套主题不一致、二级 14、切换条 16 | Must Have | 变更 | bento 17 / neon 16 / terminal 16 → 15 |
| REQ-FUNC-382 | 所有卡片标题使用同一语义与样式类（卡片标题级），不得混用 `h2`/`h3`/无类标题；卡片内正文与辅助文字遵循字号阶梯 | 用户原文「卡片字体」；基线：`h2` 无类 6 处、`h3.title` 22 处 | Must Have | 变更 | 见盘点表管理端 |
| REQ-FUNC-383 | 管理端与用户端页面标题使用同一页面标题组件/类，标题区包含主标题（h1）；页面内次级区块使用分区标题级，不与页面标题同级 | 基线：管理端 6 页用无类 h2，其余用 h3；用户端 5 页 h1、其余 h3 | Must Have | 变更 | 统一后管理端与用户端视觉一致 |
| REQ-FUNC-384 | 详情页（决议、投票、信息公开、报表详情）把实体标题作为页面主标题（h1 级），实体元信息（状态、时间、发起人）作为辅助行；正文内小标题使用卡片/分区标题级 | 基线：`ResolutionDetail.vue:4`、`PollDetail.vue:4` 用 h3.title；`InfoDetail.vue:8` 用无类 h2 | Should Have | 变更 | 长标题需换行不截断 |

### 标题文案表（REQ-FUNC-378/379 的验收基线）

| 页面 | 现状 | 统一后主标题 |
|---|---|---|
| 我的身份与房屋 | 无标题（Tab 名） | 我的身份与房屋 |
| 认证申诉中心 | 无标题（Tab 名） | 我的认证与申诉 |
| 同住人申请列表 | 我的同住人申请 | 我的同住人申请 |
| 待审批申请 | 待我审批的同住人申请 | 待我审批的同住人申请 |
| 认证产权 | 认证产权 | 认证产权 |
| 审批待办 | 审批待办 | 审批待办 |
| 报销 / 备用金 | 报销 / 备用金 | 报销/备用金 |
| 投票 / 调查 | 投票 / 调查 | 投票/调查 |
| 个人资料/密码/邮箱/注销/手机 | 个人资料等 | 保持中文名称不变，改为页面标题级 |
| 我的（窄屏聚合页） | 我的 + h3 我的 | 我的（仅一个页面标题） |
| 管理端内容管理各页 | 编辑内容/素材库/平台账户/内容中心参数/AI 服务配置·… | 信息公开、素材库、平台账户、内容参数、AI 服务配置（副题用说明行） |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-080 | 三套主题（bento/neon/terminal）在同一页面的页面标题、卡片标题、一级/二级导航字号完全一致（像素级相同），仅允许字族、颜色、圆角、阴影差异 | 用户确认「含三套主题」；基线：`bento.web.css:422,480`、`neon.web.css:198`、`terminal.web.css:216` | Must Have | 变更 | 可被 CSS 断言测试 |
| REQ-NFUNC-081 | 字体回退一致：中文正文只使用 `--font` 栈，英文/数字等宽场景使用 `--mono` 栈；不得出现衬线字体回退或第三方网络字体请求 | 基线 `themes.css:29-30` | Must Have | 继承 | 不新增字体文件 |
| REQ-NFUNC-082 | 语义与可访问性：每个页面有且仅有一个 `h1`；标题层级不跳级（h1 → h2 → h3）；导航项文字对比度符合现有主题变量，命中区域不小于 `--hit-min` | 用户原文「标题」+ 基线 a11y 约定 | Must Have | 新增 | 可用 DOM 断言测试 |
| REQ-NFUNC-083 | 响应式：页面标题在窄屏（<768px）降为 22px/30px，导航二级项与切换条 13px；标题过长时换行，不出现横向滚动或截断省略 | 基线 `style.css:176` | Must Have | 继承 | 375px 宽度验证 |
| REQ-NFUNC-084 | 零回归：本次改动后前端现有测试全部通过（基线模式零新增失败），三套主题构建校验通过 | 画像 P5 基线模式 | Must Have | 新增 | PM 亲自复跑 |

## 约束

| ID | 约束 | 来源 |
|---|---|---|
| C-398 | 仅改 Web 前端（`frontend/src/`、`themes/*.web.css`、生成态 `frontend/src/theme/generated/themes.css`），不改微信小程序 `miniprogram/` 与后端接口 | 用户确认「Web 两端全部，不含小程序」 |
| C-399 | 保留三套主题的配色、圆角、阴影、动效差异，只统一字体层级与语言规范 | 用户确认「含三套主题」+ 现有主题体系 |
| C-400 | 不引入新的字体文件或第三方字体 CDN，沿用 `--font`/`--mono` 系统字体栈 | 现有实现与离线部署环境 |
| C-401 | 不调整路由、菜单信息架构与页面功能，只统一文案、字号、字重与标题层级 | 用户原文「统一字体、标题」 |

## 超出范围

- 微信小程序（uni-app）字体与标题（用户确认不含）。
- 登录/注册/微信回调/管理端登录页的视觉重设计（仅要求不出现英文主标题、不新增可见标题）。
- 主题配色、圆角、阴影、动效调整（保留现状）。
- 后端、接口、数据模型变更。
- 新增或调整导航菜单项（只改文案，不改结构）。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| REQ-FUNC-376 | 首页不新增可见页面标题，用仅屏幕阅读器可见的 `h1`「主页」满足语义 | 首页是仪表盘，加可见标题会破坏现有视觉；用户要求"补齐标题" | 用户（可在开发前否决） |
| REQ-FUNC-377 | 英文眉标（INFORMATION/POLLS/FINANCE/RESOLUTIONS/ACCOUNT）统一**移除**，而非全站补齐 | 用户「英文仅作品牌/装饰小字或去掉」；补齐英文本土化成本高且无业务含义 | 用户（可改为全站保留） |

## 开放问题

1. 终端（terminal）主题现有 `text-transform: uppercase` + 字距 .06em 作用于中文标题，是否保留？本规格建议：mono 字体保留，`uppercase` 与字距只作用于英文字符，避免中文标题被拉宽。
2. 管理端「内容管理」二级菜单中「AI 服务·模型与生成服务」过长，统一后建议改为「AI 服务」，页面内用 Tab 区分"模型"与"提示词"；该调整涉及菜单结构，须用户确认是否在本次范围（当前按 C-401 只改文案不改结构，暂不改名）。
