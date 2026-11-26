<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-26T23:48:20+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_typography_unify/requirements/requirements_spec.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — Web 端字体与标题统一

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 | 依赖 |
|---|---|---|---|---|---|
| MOD-220 | 页面标题组件 | `frontend/src/shared/PageHead.vue`（新建） | 渲染唯一 `header.page-head > h1`，可选说明行与右侧插槽；支持 `srOnly` | REQ-FUNC-376/383/384 | MOD-221 |
| MOD-221 | 排版令牌与全局规则 | `frontend/src/shared/style.css`（修改） | 定义字号/行高/字重令牌；`.page-head h1`、`.title`、`.side-item`、`.side-sub-item`、`.sub-nav-item` 只引用令牌；新增 `.sr-only` | REQ-FUNC-380/381/382、REQ-NFUNC-083 | 无 |
| MOD-222 | 主题覆盖清理 | `themes/bento.web.css`、`themes/neon.web.css`、`themes/terminal.web.css`（修改） | 删除字号覆盖（bento 一级 17、neon 16、terminal 16、bento 首页 20）；terminal 移除 `uppercase` 与字距 | REQ-FUNC-381/382、REQ-NFUNC-080 | MOD-221 |
| MOD-223 | 导航术语修正 | `frontend/src/layout/menus.js`（修改） | 「我的认证与申述」→「我的认证与申诉」；「投票/调查」「报销/备用金」统一斜杠无空格（与页面标题一致） | REQ-FUNC-379 | 无 |
| MOD-224 | 管理端页面迁移 | `frontend/src/admin/*.vue`（修改 15 个） | 无类 `h2` 与 `h3.title` 替换为 `PageHead`；多标题页面保留一个页面标题，其余降为分区标题 | REQ-FUNC-378/382/383 | MOD-220、MOD-221 |
| MOD-225 | 用户端页面迁移 | `frontend/src/portal/**/*.vue`（修改 21 个） | 列表页改用 `PageHead`；移除英文眉标；详情页实体标题升为 `h1`；无标题页补标题；首页加 `sr-only h1` | REQ-FUNC-376/377/378/384 | MOD-220、MOD-221 |
| MOD-226 | 卡片标题与重复标题收敛 | `frontend/src/portal/Home.vue`、`Me.vue`、`me/MePhone.vue`、`AdminFinance.vue`、`AdminUsers.vue`、`AdminAudit.vue`（修改） | 首页卡片标题统一 18px；窄屏 `Me` 去掉重复"我的"；`MePhone` 两处重复 h3 合并；多区块页只保留一个页面标题 | REQ-FUNC-382/383、US-363 | MOD-221 |
| MOD-227 | 主题生成态重建 | `frontend/src/theme/generated/themes.css`（构建产物） | 由现有主题构建脚本重新生成，确保与 MOD-222 一致；不手工编辑 | REQ-NFUNC-080 | MOD-222 |

## 模块详情

### MOD-220 页面标题组件

- 文件：`frontend/src/shared/PageHead.vue`（新建）
- IFC-453：

```ts
interface PageHeadProps {
  title: string          // 中文主标题，必填
  description?: string   // 可选说明行（如管理端副题）
  srOnly?: boolean       // true 时 h1 视觉隐藏，仅屏幕阅读器可见（首页）
}
// 默认插槽：标题右侧操作区（按钮/筛选），渲染在 header 内
// 渲染结构：<header class="page-head"><h1 class="page-title">{title}</h1>
//           <p v-if="description" class="page-desc">{description}</p><slot/></header>
```

- 输入校验：`title` 为空时开发态 `console.warn` 并不渲染 `h1`（避免空标题通过测试）；生产态仍渲染空 `h1` 以便测试发现。
- 鉴权：无（纯展示组件）。
- 依赖：MOD-221 的 `.page-head/.page-title/.sr-only` 规则。

### MOD-221 排版令牌与全局规则

新增令牌（`style.css :root`，供全站与测试断言）：

| 令牌 | 值 | 用途 | 当前对应选择器 |
|---|---|---|---|
| `--text-page-title` | `24px/32px` | 页面主标题 | `.page-head h1`（现 24/32） |
| `--text-page-title-sm` | `22px/30px` | 窄屏页面标题 | `.page-head h1` @<768（现 22/30） |
| `--text-card-title` | `18px/26px` | 卡片标题 | `.title`（现 18/650） |
| `--text-section-title` | `14px/20px` | 分区标题 | `.section-title`（现 14/650） |
| `--text-nav-primary` | `15px/22px` | 一级导航 | `.side-item`（现 16/17） |
| `--text-nav-secondary` | `13px/20px` | 二级导航/窄屏切换条 | `.side-sub-item` 14、`.sub-nav-item` 16 |
| `--text-meta` | `12px/18px` | 元信息/说明行 | 各页零散 11–13px |
| `--weight-title` | `700` | 页面标题字重 | — |
| `--weight-card-title` | `650` | 卡片标题字重 | `.title` 650 |
| `--weight-nav-primary` | `600` | 一级导航字重 | 650/600 混用 |
| `--weight-nav-secondary` | `500` | 二级导航字重 | 650（激活态） |

规则要求：

- `.page-head h1`、`.title`、`.section-title`、`.side-item`、`.side-sub-item`、`.sub-nav-item` 的 `font-size/line-height/font-weight` 只允许来自上表令牌。
- 新增 `.sr-only`（视觉隐藏、仍可被读屏访问）。
- `.page-eyebrow` 规则删除（REQ-FUNC-377）。

### MOD-222 主题覆盖清理

| 文件 | 删除/修改 | 证据 |
|---|---|---|
| `themes/bento.web.css` | 删除 `.side-item` 17px 覆盖（:422）、`.home-grid .title` 20px 覆盖（:480） | 现有基线 |
| `themes/neon.web.css` | 删除 `.side-item` 16px 覆盖（:198） | 现有基线 |
| `themes/terminal.web.css` | 删除 `.title/.side-item/.side-sub-item/.sub-nav-item` 的 `text-transform: uppercase` 与 `letter-spacing: .06em`（:30-34），保留 `font-family: var(--mono)` 与 16px 覆盖删除 | 现有基线 |

主题仍可覆盖：`--font`、`--mono`、颜色、圆角、阴影、动效（C-399）。

### MOD-223 导航术语修正

- `frontend/src/layout/menus.js`：修正错别字与斜杠空格；不得改动菜单层级、路径与权限过滤。
- 与页面标题对照表（requirements_spec.md《标题文案表》）保持一致。

### MOD-224 / MOD-225 页面迁移清单

管理端 15 个页面：`AdminRegistry`、`AdminAppeals`、`AdminMemberships`、`AdminSeats`、`AdminFlows`、`AdminFinance`、`AdminAccounts`、`AdminUsers`、`AdminAudit`、`AdminContentPosts`、`AdminContentEditor`、`AdminStyleTemplates`、`AdminMedia`、`AdminAiServices`、`AdminPlatforms`、`AdminContentSettings`（其中 Finance/Users/Audit 为同文件多标题，只保留一个页面标题）。

用户端 21 个页面：`Home`、`InfoList`、`Polls`、`Reports`、`Resolutions`、`Me`、`InfoDetail`、`ResolutionDetail`、`PollDetail`、`Tasks`、`Claims`、`Income`、`HistoricalExpenses`、`units/UnitsIdentity`、`units/AppealCenter`、`units/UnitsApplications`、`units/UnitsReview`、`units/UnitsPick`、`me/MeProfile`、`me/MeStyle`、`me/MePassword`、`me/MeEmail`、`me/MeCancel`、`me/MePhone`、`UserProfile`。

迁移规则：

1. 页面主标题统一 `<PageHead :title="…">`；详情页 `title` 绑定实体标题。
2. 页面内原有 `h2/h3` 若承担区块语义，保留但改用 `.section-title`（文本不变）。
3. 不允许在同一页面渲染两个 `h1`。
4. 首页：`<PageHead title="主页" sr-only />`，问候语保持 `h2`。

### MOD-226 卡片标题与重复标题

- 首页卡片标题统一走 `.title`（18px），删除 bento 的 20px 覆盖后无需页面改动；只核对所有卡片标题确实使用 `.title`。
- `Me.vue` 窄屏：删除正文中重复的 `h3.title`「我的」。
- `MePhone.vue`：两处 `h3` 合并为一个页面标题 + 分区标题。
- `AdminFinance/AdminUsers/AdminAudit`：首个标题为 `h1`，第二个改为 `.section-title`。

### MOD-227 主题生成态

- 运行现有主题构建（`npm run build` 前置脚本或 `scripts/` 下主题生成命令）；禁止手改 `frontend/src/theme/generated/themes.css`。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-376 | US-361 | MOD-220、MOD-225 |
| REQ-FUNC-377 | US-362 | MOD-221、MOD-225 |
| REQ-FUNC-378 | US-363 | MOD-224、MOD-225 |
| REQ-FUNC-379 | US-364 | MOD-223 |
| REQ-FUNC-380 | US-365 | MOD-221 |
| REQ-FUNC-381 | US-366 | MOD-221、MOD-222 |
| REQ-FUNC-382 | US-367 | MOD-221、MOD-222、MOD-226 |
| REQ-FUNC-383 | US-368 | MOD-220、MOD-224 |
| REQ-FUNC-384 | US-369 | MOD-220、MOD-225 |
| REQ-NFUNC-080 | US-366 | MOD-222、MOD-227 |
| REQ-NFUNC-082 | US-361 | MOD-220、MOD-225 |
| REQ-NFUNC-084 | — | 全部（回归） |

## 依赖关系

MOD-220 → MOD-221（使用 `.page-head/.page-title/.sr-only`）
MOD-224 → MOD-220、MOD-221
MOD-225 → MOD-220、MOD-221
MOD-226 → MOD-221
MOD-222 → MOD-221（令牌必须先存在，主题才能删除覆盖）
MOD-227 → MOD-222（生成态依赖主题源文件）

已检查：无循环依赖。

## 数据迁移

无。后端无字段/表/索引变更，不执行迁移。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| Web 前端构建 | 需要重新构建 | `npm run build -- --base=/ocap/`（含主题生成前置步骤） |
| 主题生成产物 | 需要重新生成 | `frontend/src/theme/generated/themes.css` 由脚本产出 |
| 后端 / 数据库 / systemd | 无影响 | 不重启、不迁移 |
| 微信小程序 | 无影响 | 不在范围（C-398） |

## 测试影响面（供 GROUP_D 制定计划）

现有测试大量断言旧标记与旧文案，必须同步更新，否则会出现"预期失败"：

| 测试文件 | 与本次相关断言 | 处理 |
|---|---|---|
| `frontend/tests/layout_pages.spec.js`（25 处） | 页面 `h3.title` 文本 | 改为 `h1`/`.page-title` 与新文案 |
| `frontend/tests/layout_nav.spec.js`（28 处）、`layout_menus.spec.js`（9 处） | 导航标签文本 | 更新「申述」→「申诉」等 |
| `frontend/tests/layout_e2e.spec.js`（27 处） | 页面标题与 `.title` | 改为页面标题断言 |
| `frontend/tests/admin_theme.spec.js`（7 处）、`qa_int_theme.spec.js`（5 处） | 主题字号/标题 | 改为断言令牌值 |
| `frontend/tests/batch1118_resolution_nav.spec.js`、`identity_property_e2e.spec.js` | 详情页标题 | 改为 `h1` |
| `frontend/tests/theme_build.spec.js`、`layout_css.spec.js` | 生成 CSS 内容 | 增加令牌与"无字号覆盖"断言 |

新增测试建议（不代替 D 的正式计划）：`typography_tokens.spec.js`（令牌值与三主题一致）、`page_titles.spec.js`（按路由遍历唯一 h1 与标题文案）、`nav_labels.spec.js`（menus.js 无"申述"、斜杠格式）。

## 领域与外部依赖出处

不适用（画像 P11 为"无"；本次不涉及硬件、算法或闭源 API）。
