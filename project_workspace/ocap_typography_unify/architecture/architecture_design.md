<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-26T23:48:20+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_typography_unify/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — Web 端字体与标题统一

## 架构概览（INCREMENTAL）

本次改动全部落在现有 Vue 3 SPA 的展示层，不新增运行时服务、不改后端与路由。改动位置：

- 全局样式层：`frontend/src/shared/style.css`（新增排版令牌与页面标题规则）
- 主题层：`themes/{bento,neon,terminal}.web.css`（删除字号覆盖、收敛 terminal 的大小写作用域）
- 生成态：`frontend/src/theme/generated/themes.css`（由现有主题构建脚本重新生成）
- 组件层：新增共享 `PageHead.vue`，管理端 15 页 + 用户端 21 页接入
- 配置层：`frontend/src/layout/menus.js` 术语修正

关键质量属性：三主题字号一致（REQ-NFUNC-080）、语义唯一 h1（REQ-NFUNC-082）、零回归（REQ-NFUNC-084）。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Web 前端（管理端 + 用户端 SPA） | `frontend` Vite 构建 → nginx 静态站点（`/ocap/` 子路径） | 测试环境 192.168.31.51:8090（画像 P7） |
| 主题生成 | 构建前脚本生成 `frontend/src/theme/generated/themes.css` | 开发者本地构建 |
| 后端 | 无改动，不参与本次部署 | 不变 |

## ADR

### ADR-202: 页面标题的落地方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-376/378/383/384 要求每个页面有唯一 h1、管理端与用户端一致、详情页标题升级；现状是 5 页手写 `.page-head + h1`、6 页无类 `h2`、22 处 `h3.title`、4 页无任何标题。
- Options:
  - A 新增共享 `PageHead.vue`（props：`title`、`description?`、`srOnly?`；固定渲染 `header.page-head > h1`）：结构由组件保证，漏写 h1 不可能；缺点是要改 36 个页面文件。
  - B 只在 `style.css` 统一 `.page-head`、`.page-title` 类，各页面手写标记：改动小；缺点是 h1 唯一性与层级靠自觉，容易再次漂移（本次问题正是这样产生的）。
  - C 通过路由守卫自动注入标题：无法覆盖详情页实体标题、首页问候与管理端多区块页面，且会与页面级 loading 冲突。
- Decision: 选择 A。REQ-FUNC-376/383 的核心是"结构一致且可断言"，只有组件能保证；36 个页面文件属于机械替换，风险低于长期漂移。
- Consequences: 正向：h1 唯一、字号与间距单点维护、可直接用 DOM 断言测试。负向：一次性改动面大，需同步更新约 90 处依赖旧标记（`h3.title`/无类 `h2`）的现有测试。

### ADR-203: 排版令牌的存放位置
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-380/381、REQ-NFUNC-080/083 要求统一字号阶梯且三主题不得各自覆盖字号；现状字号散落在 `style.css` 与三套主题（一级导航 16/16/17）。
- Options:
  - A 在 `style.css :root` 定义排版令牌（`--text-page-title`、`--text-card-title`、`--text-section-title`、`--text-nav-primary`、`--text-nav-secondary`、对应 `--leading-*`），所有规则只引用令牌；主题只覆盖 `--font`/`--mono` 与颜色。
  - B 由主题生成器为每套主题生成字号令牌：沿用现有 `themes.css` 生成机制；缺点是字号成了主题差异项，违背 REQ-NFUNC-080。
  - C 在组件内写死字号：无法被主题生成与全局测试覆盖。
- Decision: 选择 A。字号是跨主题不变量，主题只应改变字族与配色（C-399）。
- Consequences: 正向：一处修改、全站生效，测试可直接断言令牌值。负向：删除三套主题中的字号覆盖属于破坏性样式清理，需要逐条确认没有其他依赖（尤其 bento 首页 20px 与 terminal 字距）。

### ADR-204: terminal 主题的大小写与字距作用域
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-381/382、US-366 AC-366-03；`themes/terminal.web.css:30-34` 对 `.title/.side-item/.side-sub-item/.sub-nav-item` 同时设置 `text-transform: uppercase` 与 `letter-spacing: .06em`，中文标题被拉宽、视觉与另外两套主题不一致。
- Options:
  - A 移除这四类元素的 `uppercase` 与字距，仅保留 `--mono` 字族：与 bento/neon 宽度一致；缺点是终端主题的"命令行感"减弱。
  - B 仅对英文内容生效（`:lang(en)` 或专用类 `.is-latin`）：保留风格；缺点是中文页面几乎无英文文本，实际效果接近 A，且增加选择器复杂度。
  - C 保持现状：违背 REQ-NFUNC-080。
- Decision: 选择 A。英文眉标按 REQ-FUNC-377 统一移除后，四类元素内容基本为中文，B 的收益接近零；品牌英文仍保留独立字距规则（`.brand`/`.side-brand`），终端风格不受影响。
- Consequences: 正向：三主题标题宽度一致，可测。负向：terminal 视觉辨识度略降，需要在 code review 中确认品牌与等宽数字仍突出。

### ADR-205: 术语一致性的保障方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-379、US-364；基线存在"投票/调查"与"投票 / 调查"、"申述"错别字等差异。
- Options:
  - A 引入运行时共享常量（`PAGE_TITLES`）供导航与页面共用：强一致；缺点是为 36 个页面引入一层间接引用，页面文案变成 key 查找，可读性下降。
  - B 以《标题文案表》为唯一事实来源，导航 `menus.js` 手工对齐，并新增契约测试比对"导航标签 ↔ 页面 h1 文本"：无运行时耦合；缺点是测试必须覆盖到每个页面。
  - C 只改文案不设测试：无法防止回归。
- Decision: 选择 B。与现有测试驱动风格一致（项目已有大量 DOM 文本断言），避免为文案引入运行时抽象。
- Consequences: 正向：零运行时成本、回归可测。负向：新增页面若忘记登记会被契约测试漏掉，需在测试中按路由表全量遍历。

## 开放问题 / ASSUMPTION

- [ASSUMPTION] 首页使用视觉隐藏 `h1`「主页」不影响现有首页视觉与测试（依赖 REQ-FUNC-376 的推断项；若用户否决，改为可见标题需重做首页布局）。
- [ASSUMPTION] 管理端 `AdminAiServices` 的副标题（模型与生成服务/提示词模板）下沉为页面说明行或 Tab，不改路由。
