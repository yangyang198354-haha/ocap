<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-26T23:48:20+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_typography_unify/architecture/module_design.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈 — Web 端字体与标题统一

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 前端框架 | Vue 3 + `<script setup>` | `^3.5.13`（frontend/package.json） | 沿用 | 现有 SPA 技术栈 | 全部 | Low |
| 构建 | Vite | `^6.0.1`（frontend/package.json） | 沿用 | 现有构建与主题生成流程 | REQ-NFUNC-084 | Low |
| UI 组件 | Element Plus | `^2.8.7`（frontend/package.json） | 沿用 | 现有页面已使用 | REQ-FUNC-378 | Low |
| 路由 | vue-router | `^4.4.5`（frontend/package.json） | 沿用 | 不新增路由 | C-401 | Low |
| 状态 | Pinia | `^2.1.7`（frontend/package.json） | 沿用 | 无新增状态 | — | Low |
| 样式 | 原生 CSS + 主题 CSS 生成 | 仓库现有 `style.css` + `themes/*.web.css` | 沿用 | 统一令牌用原生自定义属性，无新依赖 | REQ-FUNC-380/381 | Low |
| 字体 | 系统字体栈 `--font` / `--mono` | `frontend/src/theme/generated/themes.css:29-30` | 沿用 | 满足 C-400（不引入新字体文件/CDN） | REQ-NFUNC-081 | Medium：不同操作系统字体回退差异 |
| 测试 | Vitest + @vue/test-utils | `^2.1.9`（frontend/package.json） | 沿用 | 现有前端测试体系 | REQ-NFUNC-084 | Low |
| 部署 | nginx 静态站点（`/ocap/`）+ systemd 后端 | 画像 P7 | 沿用 | 仅前端产物变化 | — | Low |

未新增任何第三方依赖。

## 技术风险

| 级别 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 现有 90+ 处测试断言旧 `h3.title`/旧导航文案，改变标记会集中失败 | 先在设计层固定"旧标记→新标记"映射（module_design 迁移规则），D 阶段按文件清单逐项更新，全量复跑基线 |
| Medium | 删除三套主题的字号覆盖可能影响未盘点到的页面（如弹窗、空态） | C 阶段用 `git grep` 搜索 `font-size` 覆盖清单，逐条确认；主题构建测试断言"无字号覆盖" |
| Medium | 系统字体在不同设备（Windows/macOS/树莓派浏览器）回退不同，导致标题宽度差异 | 只统一字号/字重/行高，不追求像素级字宽；375px 视口断言"无横向滚动"而非固定宽度 |
| Low | terminal 主题去掉 uppercase 后辨识度下降 | 保留 mono 字族与配色，code review 时人工确认 |
