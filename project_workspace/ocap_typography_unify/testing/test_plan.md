<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T00:58:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/requirements/user_stories.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/module_design.md</file>
    <file>project_workspace/ocap_typography_unify/development/implementation_plan.md</file>
    <file>project_workspace/ocap_typography_unify/development/code_review_report.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — Web 端字体与标题统一（GROUP_D）

## 测试策略

- **被测改动**：Web 前端排版令牌（MOD-221）、PageHead 组件（MOD-220）、管理端 16 页 + 用户端 24 页接入（MOD-224/225）、卡片/重复标题收敛（MOD-226）、三套主题清理（MOD-222）、生成态重建（MOD-227）、导航术语「申述→申诉」（MOD-223）。纯前端 CSS/结构/文案改动，无后端、无迁移、无小程序。
- **范围 in**：Web 前端 `frontend/src/**`、`themes/*.web.css`、`frontend/src/theme/generated/themes.css`。
- **范围 out**：后端、数据库、小程序（`*.mp.css`）、真实浏览器视觉度量（jsdom 不计算布局/对比度/横向滚动 → 列入人工验证清单）。
- **环境**：Windows PowerShell 5；Node 22.12；前端 `vitest run`（jsdom，`VITE_API_BASE=/ocap/api/v1`）；不连真实服务，HTTP 由测试 mock。
- **判定模式**：INCREMENTAL → **baseline 零新增失败模式**。基线来源：干净基线（`git stash -u` 暂存本次全部改动后）全量实跑结果 `Tests 1 failed (622) | 621 passed`，唯一失败 `product_review_ui.spec.js` TC-UNIT-577（预存，与本次无关，已在 code_review 定性）。本批次新增用例必须全部通过，且相对该基线无新增失败。
- **分层**（无 tag，按文件语义分层，与既有套件口径一致）：
  - UNIT：单文件/单组件、读 CSS 源或单组件挂载（外部依赖 mock）：`tests/typography_tokens.spec.js`（新）、`layout_css.spec.js`、`layout_menus.spec.js`、`theme_build.spec.js`、`theme.spec.js`、`brand.spec.js`、`admin_theme.spec.js`、`ui_blocks.spec.js`。
  - INT：跨组件/路由挂载页面、真实 Vue 路由：`layout_pages.spec.js`、`layout_nav.spec.js`、`pages.spec.js`、`qa_int_theme.spec.js`、`identity_property_match_panel.spec.js`。
  - E2E：多步页面旅程（路由 + 状态流转），jsdom 可执行的最高端到端级：`layout_e2e.spec.js`、`identity_property_e2e.spec.js`、`qa_e2e_theme.spec.js`、`profile_hierarchy_e2e.spec.js`。
- **critical path 口径**：本项目无真实浏览器 E2E 框架，按规则 10 用**替代（jsdom 路由多步旅程，即上述 E2E 层文件）**。critical path = Must Have 故事（US-361~368）的 E2E 用例。

## AC 映射

| AC | 用例 ID | 层 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 数据 |
|---|---|---|---|---|---|---|---|---|
| 361-01 每页唯一 h1 | layout_e2e 现有 h1 断言（findAll('h1')=单元素）；TC-INT-890 | E2E | 现有 | layout_e2e.spec.js；layout_pages.spec.js | mock /me | 路由到各页 | 每 main 内恰 1 个 h1 | mock |
| 361-02 首页 sr-only h1「主页」 | TC-INT-890（首页渲染） | INT | 现有 | layout_pages.spec.js | mock /me | 路由 / | 存在 1 个 h1 文本「主页」且 .sr-only | mock |
| 361-03 登录/注册无 h2 作页标题 | auth_shell 现有渲染 | INT | 现有 | auth_shell.spec.js；layout_e2e | — | 渲染登录/注册 | 无 h2 冒充页面标题 | mock |
| 362-01 全站无 .page-eyebrow | **TC-UNIT-2107** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css + 3 主题 + generated | 无 .page-eyebrow 选择器 | 无 |
| 362-02 英文仅品牌位 | TC-UNIT-841~849 | UNIT | 现有 | brand.spec.js | — | 读源码 | 英文品牌只在 .brand/.side-brand | 无 |
| 362-03 /admin/content/services h1=AI 服务配置 | layout_pages 现有管理端标题断言 | INT | 现有 | layout_pages.spec.js | mock /me | 路由 /admin/content/services | h1=「AI 服务配置」 | mock |
| 363-01 缺标题页补 h1 | layout_e2e 现有 h1 断言 | E2E | 现有 | layout_e2e.spec.js | mock | 路由各页 | 每页有 h1 且中文 | mock |
| 363-02 中英混用改纯中文 | TC-UNIT-801/808、TC-INT-809 | UNIT | 现有 | layout_menus.spec.js；layout_e2e | — | 渲染菜单 | 标题纯中文 | mock |
| 363-03 两端「信息公开」h1 一致 | TC-INT-889、layout_e2e | INT | 现有 | layout_pages.spec.js；layout_e2e.spec.js | mock | 路由 /info 与 /admin/content/posts | 两端 h1 均「信息公开」 | mock |
| 364-01 一二级术语统一「申诉」 | TC-UNIT-801/804/809、TC-INT-804 | UNIT | 现有 | layout_menus.spec.js；layout_nav.spec.js | — | 读菜单/渲染 | 文案为「申诉」非「申述」 | mock |
| 364-02 全仓无「申述」 | layout_menus/nav/e2e 文案断言 | UNIT | 现有 | layout_menus.spec.js 等 | — | 读源码/渲染 | 无「申述」残留 | 无 |
| 364-03 两端 h1「信息公开」 | 同 363-03 | INT | 现有 | 同上 | mock | 同上 | 同上 | mock |
| 365-01 页标题 24/32/700 窄屏 22 | **TC-UNIT-2101** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css | 令牌值与规则引用令牌，窄屏切 22px | 无 |
| 365-02 卡片标题 18/26/650 bento 无 20px | **TC-UNIT-2102** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css + bento + generated | 令牌值；无 20px 覆盖 | 无 |
| 365-03 h2/h3 来自阶梯无浏览器默认 | **TC-UNIT-2103** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css | 三个层级字号均 var(--text-*) | 无 |
| 366-01 一级导航 15/600 三主题无覆盖 | **TC-UNIT-2104** + TC-UNIT-870 | UNIT | 新写+现有 | typography_tokens.spec.js；layout_css.spec.js | — | 读 style.css + 3 主题 | 令牌 15/600；主题无 font-size 覆盖 | 无 |
| 366-02 二级 13/500 小于一级 | **TC-UNIT-2105** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css + 3 主题 | 令牌 13/500；13<15 | 无 |
| 366-03 terminal 无 uppercase/.06em 中文宽度 | **TC-UNIT-2106** + 人工 M-01 | UNIT | 新写+人工 | typography_tokens.spec.js | — | 读 terminal 源 + 真实浏览器 | 源码无 uppercase 作用于标题/导航；浏览器实测宽度差 ≤2px | 无（人工需设备） |
| 367-01 卡片标题统一 .title | **TC-UNIT-2102** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css | .title=18/26/650 | 无 |
| 367-02 管理端无无类 h2 作卡标题 | TC-INT-890（管理端渲染） | INT | 现有 | layout_pages.spec.js | mock | 渲染管理页 | 卡片标题带 .title | mock |
| 367-03 terminal 卡标题不 uppercase 18px | **TC-UNIT-2106** | UNIT | 新写 | typography_tokens.spec.js | — | 读 terminal 源 | .title 无 uppercase | 无 |
| 368-01 两端页面标题单点样式一致 | **TC-UNIT-2101** | UNIT | 新写 | typography_tokens.spec.js | — | 读 style.css | .page-head h1/.page-title 单一规则 | 无 |
| 368-02 多区块页动态单 h1 | TC-INT-890（AdminFinance/Users/Audit） | INT | 现有 | layout_pages.spec.js | mock | 切换区块 | 始终 1 个 h1 | mock |
| 369-01 详情页实体标题为 h1 | identity_property_e2e mainTitles；layout_e2e 详情 | E2E | 现有 | identity_property_e2e.spec.js；layout_e2e.spec.js | mock | 路由详情页 | 实体名是 h1，元信息非标题 | mock |
| 369-02 375px 标题换行无横向滚动 | **TC-UNIT-2108** + 人工 M-02 | UNIT | 新写+人工 | typography_tokens.spec.js | — | 读 style.css + 真实浏览器 375px | 无 ellipsis/nowrap；浏览器无横向滚动、长标题换行 | 无（人工需设备） |

## 测试数据需求

- 所有前端测试均用 `vitest setup` 的 mock HTTP（`tests/setup.ts` 与各文件内 `mockApi`），无持久数据写入；不连真实后端。`[DATA_REQUIRED]` 无。

## 不可测项（自动化无法断言，进人工验证清单）

| AC | 原因 | 进人工清单 |
|---|---|---|
| 366-03 中文宽度差 ≤2px | jsdom 不计算真实字形宽度；需浏览器实测 bento/neon/terminal 同一标题渲染宽度对比 | M-01 |
| 369-02 375px 换行 / 无横向滚动 | jsdom 不布局；需真实浏览器 375px 视口验证长标题（如「财务报表与账户管理」）换行且无横向滚动条 | M-02 |

## 故事覆盖核对（Must Have，每个至少 1 个真实执行用例）

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-361 | layout_e2e h1 断言 + TC-INT-890 + TC-UNIT-2107 | E2E/INT/UNIT |
| US-362 | TC-UNIT-2107 + TC-UNIT-841~849 + layout_pages | UNIT/INT |
| US-363 | layout_e2e h1 断言 + TC-UNIT-801 + TC-INT-889 | E2E/UNIT/INT |
| US-364 | TC-UNIT-801/804/809 + TC-INT-804 + layout_menus | UNIT/INT |
| US-365 | TC-UNIT-2101/2102/2103 | UNIT |
| US-366 | TC-UNIT-2104/2105/2106 + TC-UNIT-870 + 人工 M-01 | UNIT |
| US-367 | TC-UNIT-2102/2106 + TC-INT-890 | UNIT/INT |
| US-368 | TC-UNIT-2101 + TC-INT-890（动态单 h1） | UNIT/INT |
| US-369（Should Have，不计入 critical path 分母） | identity_property_e2e mainTitles + TC-UNIT-2108 + 人工 M-02 | E2E/UNIT |

critical path 预期：US-361~368 共 8 个 Must Have，全部有 E2E/INT 真实执行用例 → 覆盖率 8/8 = 100%（最终值以 e2e_test_report 实跑为准）。
