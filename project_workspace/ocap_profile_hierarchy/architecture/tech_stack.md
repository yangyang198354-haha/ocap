<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-21T11:44:58+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>frontend/package.json</file>
    <file>miniprogram/package.json</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈：个人主页信息层级与实名认证徽章

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| Web 框架 | Vue 3 + `<script setup>` | `^3.5.13`（`frontend/package.json:23`） | 沿用 | 现有 UserProfile.vue 已使用组合式 API | REQ-FUNC-267 | 低 |
| Web 组件库 | Element Plus | `^2.8.7`（`frontend/package.json:21`） | 沿用 | 复用 `el-tag`，无需新组件 | REQ-FUNC-265/266 | 低 |
| Web 构建 | Vite | `^6.0.1`（`frontend/package.json:30`） | 沿用 | 现有构建链 | REQ-FUNC-267 | 低 |
| Web 测试 | Vitest + @vue/test-utils + jsdom | `^2.1.9` / `^2.4.6` / `^25.0.1`（`frontend/package.json:28-31`） | 沿用 | 新增顺序与样式断言 | US-273/274/275 | 低 |
| 小程序框架 | uni-app（Vue 3） | `^3.0.0-4060620250520001`（`miniprogram/package.json:13-15`） | 沿用 | 现有“我的”页技术栈 | REQ-FUNC-268 | 低 |
| 小程序样式 | WXSS + 主题 CSS 变量 | 现有 `theme/generated/themes.scss:7-18`、`App.vue:21-24` | 沿用 | 使用 `--text`/`--muted`/`--success` 自动适配主题 | REQ-FUNC-265/266 | 中：自定义属性作用域 |
| 小程序测试 | Vitest + @vue/test-utils | `^2.1.9` / `^2.4.6`（`miniprogram/package.json:22-25`） | 沿用 | 页面级渲染与失败降级断言 | US-276 | 低 |
| 数据访问 | 既有 Django API `GET /me/profile`、`GET /users/{id}/profile` | 现有代码（`backend/apps/accounts/views.py:280-291`、`backend/apps/identity/services.py:84-115`） | 沿用 | 不新增端点、不新增字段 | REQ-FUNC-267/268 | 低 |
| 新增依赖 | 无 | — | — | 徽章用现有标签与字符图标 | — | — |

## 技术风险

| 级别 | 风险 | 缓解措施 |
|---|---|---|
| Medium | WXSS 自定义属性在组件作用域内的可见性差异可能导致颜色取不到 | 使用页面已有全局类（`.tag`、`.tag.is-success`）与 ThemeRoot 变量；构建后在微信开发者工具按 4 个主题各检查一次 |
| Low | `el-tag` 默认样式覆盖自定义 class，导致颜色/字体差异断言失败 | 断言以实际计算样式或 class 为准，必要时提高选择器优先级；测试同时检查 class 存在 |
| Low | “我的”页新增 `api.profile()` 增加一次请求，弱网时首屏变慢 | 与 `auth.fetchMe()`、`housing()` 并行发起；失败静默降级（ADR-159） |
