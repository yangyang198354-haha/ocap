<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T12:01:25+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型 — 导航信息架构整合（增量）

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（前端/小程序） | JavaScript（ESM） | 随现有工程（`frontend/package.json:5` `"type":"module"`） | 沿用 | 不引入 TypeScript 编译链 | 全部 | 低 |
| Web 框架 | Vue 3 | `^3.5.13`（`frontend/package.json:23`） | 沿用 | 现有页面与组件全部基于 Vue 3 | 全部 | 低 |
| Web 构建 | Vite | `^6.0.1`（`frontend/package.json:30`） | 沿用 | 现有构建命令 `vite build` | 全部 | 低 |
| UI 组件库 | Element Plus | `^2.8.7`（`frontend/package.json:21`） | 沿用 | `el-tabs`、`el-dropdown`、`el-badge` 已满足需求；不新增组件库 | REQ-FUNC-301/305、REQ-NFUNC-061 | 中：`show-timeout`/`hide-timeout` 与过渡类名需实现时验证（A-01） |
| 状态管理 | Pinia | `^2.1.7`（`frontend/package.json:22`） | 沿用 | 复用 `housing` store 的角标与待审批数量 | REQ-FUNC-315 | 低 |
| 路由 | vue-router | `^4.4.5`（`frontend/package.json:24`） | 沿用 | 旧地址重定向与 query 白名单 | REQ-FUNC-314 | 低 |
| 小程序框架 | uni-app（Vue 3） | `^3.0.0-4060620250520001`（`miniprogram/package.json:13`） | 沿用 | 现有小程序工程与构建命令 `uni build -p mp-weixin` | REQ-FUNC-312/313 | 低 |
| 小程序构建 | Vite | `^5.2.8`（`miniprogram/package.json:24`） | 沿用 | 现有构建链 | 全部 | 低 |
| Web 测试 | vitest + @vue/test-utils | `^2.1.9` / `^2.4.6`（`frontend/package.json:28,31`） | 沿用 | 覆盖菜单配置、Tab、下拉分组与动效常量 | 全部 | 低 |
| 小程序测试 | vitest + @vue/test-utils | `^2.1.9` / `^2.4.6`（`miniprogram/package.json:22,25`） | 沿用 | 覆盖 Tab 切换、分组文案与页面路由 | 全部 | 低 |
| 新增第三方依赖 | **无** | — | — | 动效用 CSS/Vue 内置能力，菜单用现有 Element Plus | — | 低 |
| 容器化 | **不使用** | — | — | 画像 P8 禁用 Docker/容器化 | — | — |
| 部署方式 | 物理机：前端静态产物替换 | 画像 P7 | 沿用 | 本次无后端变更、无迁移；仅替换 Web 构建产物并重新构建小程序 | — | 低 |

## 技术风险

### High

无。

### Medium

| 风险 | 缓解措施 |
|---|---|
| Element Plus `el-dropdown` 的 `show-timeout`/`hide-timeout` 在当前版本行为与假设不一致（A-01），导致悬停延迟不生效 | 实现后在浏览器实测；不生效则在 `PortalUserMenu.vue` 内加 180ms `mouseenter` 计时包装，保持组件与视觉不变 |
| popper 被 teleport 到 `body`，`scoped` 样式无法命中，导致 400ms 过渡未生效 | 把过渡规则写到 `frontend/src/shared/style.css` 的全局选择器 `.user-menu-popper...`；测试断言常量与类名存在 |
| 小程序页面拆分与新增两页引入构建或路由遗漏 | `pages.json` 同步登记新页面；构建 `npm --prefix miniprogram run build:mp-weixin` 后在开发者工具逐页打开验证 |

### Low

| 风险 | 缓解措施 |
|---|---|
| Web 与小程序文案漂移（REQ-NFUNC-062） | 两端各维护一份常量表，测试逐字比对 C-363 的名称 |
| 旧地址重定向遗漏导致 404（C-362） | 路由测试覆盖 `/units/appeal`、`/units/appeals`、`/units/review`、`/me/identity` 等地址 |
| 非产权业主深链到 `?tab=review` 出现空 Tab | `initialTab` 白名单 + `ownsAnyUnit` 回落默认 Tab，测试覆盖非产权业主场景 |
