<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-27T00:18:27+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_typography_unify/requirements/user_stories.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/module_design.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/tech_stack.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — Web 端字体与标题统一（GROUP_C）

## 实现概览

- 模块数：8（MOD-220 ~ MOD-227）；改动 48 个前端源码文件（1 新建 + 47 修改）、3 个主题源文件、1 个生成态文件、13 个现有测试文件。
- 实现顺序（拓扑）：MOD-221 排版令牌 → MOD-220 PageHead → MOD-223 导航术语 → MOD-222 主题清理 → MOD-227 生成态重建 → MOD-224 管理端页面 → MOD-225 用户端页面 → MOD-226 卡片/重复标题收敛。
- 依据：module_design.md 的令牌表、IFC-453 与 MOD-224/225 文件清单；未新增任何第三方依赖或字体文件。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-221 | `frontend/src/shared/style.css` | 修改 | — | M | `:root` 新增 7 组字号/行高与 4 个字重令牌；`.title`/`.section-title`/`.side-item`/`.side-sub-item`/`.sub-nav-item`/`.page-head h1` 只用令牌；删除 `.page-eyebrow`；新增 `.sr-only`；窄屏标题用 `--text-page-title-sm` | DONE |
| 2 | MOD-220 | `frontend/src/shared/PageHead.vue` | 新建 | MOD-221 | S | 固定渲染 `header.page-head > h1.page-title`，支持 `description`、`srOnly` 与右侧默认插槽 | DONE |
| 3 | MOD-223 | `frontend/src/layout/menus.js` | 修改 | — | S | 「我的认证与申述」→「我的认证与申诉」；斜杠保持无空格 | DONE |
| 4 | MOD-222 | `themes/bento.web.css`、`themes/neon.web.css`、`themes/terminal.web.css` | 修改 | MOD-221 | M | 删除 bento 一级 17px / 首页卡片 20px、neon 16px、terminal 16px 覆盖；terminal 移除全局 `uppercase` 与 `.06em` 字距；移除 terminal `.page-eyebrow` 与 `h1::before "> "` | DONE |
| 5 | MOD-227 | `frontend/src/theme/generated/themes.css` | 重新生成 | MOD-222 | S | 运行 `node scripts/themes/build.mjs` 生成，未手改 | DONE |
| 6 | MOD-224 | `frontend/src/admin/*.vue`（16 个） | 修改 | MOD-220/221 | M | 无类 `h2`、`h3.title` 页面标题替换为 `PageHead`；多区块页只保留一个 h1，操作按钮进入标题区插槽 | DONE |
| 7 | MOD-225 | `frontend/src/portal/**/*.vue`（24 个） | 修改 | MOD-220/221 | H | 列表页接入 `PageHead`；删除英文眉标；详情页实体标题升为 h1；无标题页补标题；首页加 `sr-only` h1 | DONE |
| 8 | MOD-226 | `Home.vue`、`Me.vue`、`me/MePhone.vue`、`AdminFinance.vue`、`AdminUsers.vue`、`AdminAudit.vue` | 修改 | MOD-221 | M | 首页卡片标题统一 `.title`（bento 20px 已删）；`Me` 去重复「我的」；`MePhone` 合并为单一页面标题；多区块页标题动态化 | DONE |

> 说明：MOD-224 文档写“15 个文件”，实际清单列名 16 个，按实际目录全部实现（GR-B-001 条件：以完整清单为准，不按正文旧算术）。

## 需求追溯

| US | AC | 实现位置（文件:组件/选择器） | 状态 | 说明 |
|---|---|---|---|---|
| US-361 | AC-361-01 | `shared/PageHead.vue:5`；全部 40 个页面接入 | DONE | 每页唯一 h1，位于 `.page-head` |
| US-361 | AC-361-02 | `portal/Home.vue:3`（`srOnly`） | DONE | 首页仅读屏 h1「主页」，问候语仍为 h2 |
| US-361 | AC-361-03 | `brand/AuthShell.vue`（未改） | DONE | 登录/注册页不在 MOD 清单；其 h1 为品牌字标，h2 为欢迎语装饰，未充当路由页主标题 |
| US-362 | AC-362-01 | 5 个列表页 `PageHead`；`style.css` 删除 `.page-eyebrow`；`terminal.web.css` 删除同名规则 | DONE | 全仓无 `page-eyebrow` |
| US-362 | AC-362-02 | 所有页面 `h1` 为中文；英文仅 `.brand/.side-brand`、`AuthShell` 品牌字标 | DONE | — |
| US-362 | AC-362-03 | `AdminAiServices.vue:3` | DONE | h1「AI 服务配置」，说明行由 `description` 承载 |
| US-363 | AC-363-01 | `UnitsIdentity/AppealCenter/Tasks/Income/HistoricalExpenses/MeProfile/MeStyle` 的 `PageHead` | DONE | 文案与《标题文案表》一致 |
| US-363 | AC-363-02 | 管理端 16 页 `PageHead` | DONE | 无残留无类 `h2`（全仓已核） |
| US-363 | AC-363-03 | `portal/Me.vue:4` | DONE | 删除正文重复 `h3.title`「我的」 |
| US-364 | AC-364-01 | `menus.js`；`Polls.vue:3`、`Claims.vue:3` | DONE | 「投票/调查」「报销/备用金」两侧无空格 |
| US-364 | AC-364-02 | `menus.js:31` | DONE | 全仓无「申述」 |
| US-364 | AC-364-03 | `AdminContentPosts.vue:3`、`InfoList.vue:3` | DONE | 两端 h1 均为「信息公开」 |
| US-365 | AC-365-01 | `style.css` 令牌 + `.page-head h1,.page-title` | DONE | 24/32/700；<768 22/30 |
| US-365 | AC-365-02 | `.title` 令牌；`bento.web.css` 删除 20px | DONE | 卡片标题 18/26/650 |
| US-365 | AC-365-03 | 全仓 h2/h3 均带 `.title`/`.section-title`/`.res-section-title`（后者改用令牌） | DONE | 无浏览器默认字号标题 |
| US-366 | AC-366-01 | `style.css` `.side-item`；三主题删除字号覆盖 | DONE | 三主题均 15/600 |
| US-366 | AC-366-02 | `.side-sub-item`、`.sub-nav-item` | DONE | 13/500 |
| US-366 | AC-366-03 | `terminal.web.css` 移除全局 uppercase 与字距 | DONE | 中文宽度与 bento/neon 一致 |
| US-367 | AC-367-01 | `.title` 令牌；首页 8 个卡片标题与详情卡片 | DONE | 统一类与字号 |
| US-367 | AC-367-02 | 管理端 16 页 | DONE | 无无类 h2 卡片标题 |
| US-367 | AC-367-03 | terminal 无 uppercase | DONE | 中文卡片标题不拉宽，18px |
| US-368 | AC-368-01 | `.page-head h1,.page-title` 单点样式 | DONE | 两端同字号/字重/上边距 |
| US-368 | AC-368-02 | `AdminFinance/AdminUsers/AdminAudit` 动态单 h1 | DONE | 条件区块不再各自输出标题 |
| US-369 | AC-369-01 | `ResolutionDetail.vue:4`、`PollDetail.vue:4`、`InfoDetail.vue:3` | DONE | 实体标题为 h1，元信息为辅助行 |
| US-369 | AC-369-02 | `.page-head h1` 无 nowrap/ellipsis，可换行 | DONE | 375px 验证由 GROUP_D 覆盖 |

### REQ-NFUNC-081 / 083 追溯（GR-B-001 条件）

| REQ | 实现位置 | 状态 | 说明 |
|---|---|---|---|
| REQ-NFUNC-081 字体回退一致 | `themes.css:29-30`（未改）；`style.css` 未新增 `font-family`；三主题仅保留 `--font/--mono` | DONE | 未新增字体文件/网络字体；正文 `--font`、等宽场景 `--mono` |
| REQ-NFUNC-083 响应式 | `style.css` 媒体查询 `.page-head h1,.page-title` 用 `--text-page-title-sm/--leading-page-title-sm`；导航二级 13px 为全尺寸统一 | DONE | 标题允许换行，无横向滚动样式 |

## 迁移

无。未新增/修改后端模型、表、索引，不执行数据库迁移。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `UnitsReview.vue` 不接入 `PageHead`，改为 `h2.title` | MOD-225 文件清单 | 该组件是 `/units` 页内的 Tab 区块，若再渲染 h1 会违反 AC-361-01「唯一 h1」与 MOD-225 规则 3 | 无功能影响；`/units` 的页面标题由 `UnitsIdentity` 的 `PageHead` 提供 |
| `.side-item.is-active` 保留 `font-weight: 650` 字面量（未改为令牌） | MOD-221 令牌表 | 既有 REQ-NFUNC-039 与 `layout_css.spec.js` 要求激活项有字重提示；模块令牌表也注明「650（激活态）」 | 仅激活态；常规项严格使用 `--weight-nav-primary` |
| terminal 删除 `page-head h1::before { content: "> " }` | ADR-204 仅要求移除 uppercase/字距 | 该伪元素使 h1 文本变成「> 标题」，违反 AC-362-01 纯中文 h1 断言 | 终端主题标题装饰略有变化，配色与其它装饰保留 |

## 开放问题

- `[ASSUMPTION]` 首页问候语 `.home-greeting` 保留主题级字号（28–36px），视为 Hero 装饰而非内容标题；若门控要求严格套用阶梯，可再收敛到 `--text-page-title` 系列。
- `--text-meta` / `--leading-meta` 已按设计令牌表定义，当前仅少量元信息使用字面量 12–13px，未全部替换为令牌；不影响力级一致性，建议 GROUP_D 补令牌断言时一并评估。
- 现有测试中部分注释与用例标题仍含旧措辞（如“h3.title”），仅调整断言选择器，未逐个改写注释，避免扩大 diff。
