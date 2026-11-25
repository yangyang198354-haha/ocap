<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-25T12:18:30+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_role_home/requirements/requirements_spec.md</file><file>project_workspace/ocap_role_home/architecture/architecture_design.md</file><file>project_workspace/ocap_role_home/architecture/module_design.md</file><file>frontend/package.json</file><file>miniprogram/package.json</file><file>backend/requirements.txt</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 技术选型（增量）

> 本次为 INCREMENTAL 纯前端改造，**不新增任何第三方依赖**（C-394、REQ-NFUNC-079）。下表全部为“沿用”，版本出处均为仓库依赖清单，未使用联网查询。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| Web 语言/框架 | Vue 3（Composition API） | `^3.5.13`（`frontend/package.json:23`） | 沿用 | 现有首页即 Vue SFC，改动只在其内 | 366~375 | 低 |
| Web 构建 | Vite | `^6.0.1`（`frontend/package.json:30`） | 沿用 | 现有构建链 | 375 | 低 |
| Web 组件库 | Element Plus | `^2.8.7`（`frontend/package.json:21`） | 沿用 | 复用 `el-empty`、按钮等现有组件 | 366~374 | 低 |
| Web 状态 | Pinia | `^2.1.7`（`frontend/package.json:22`） | 沿用 | 能力 getter 放在现有 auth store | 366、368、369、370 | 低 |
| Web 样式 | 现有 `style.css` + 主题变量 | 仓库现有（`frontend/src/shared/style.css:178-219`） | 沿用 | 满足 C-393 共用骨架 | 374、375 | 中：三主题占位需回归 |
| 主题生成 | `scripts/themes/build.mjs` | 仓库现有（`scripts/themes/build.mjs:1-10,188-191`） | 沿用 | 主题源 `themes/*.theme.json` → 生成 CSS/SCSS，禁止手改生成物 | 375 | 中：忘记重跑会产物漂移 |
| 小程序框架 | uni-app (Vue 3) | `@dcloudio/uni-app ^3.0.0-4060620250520001`（`miniprogram/package.json:13`） | 沿用 | 现有小程序工程 | 366~375 | 低 |
| 小程序构建 | uni build（mp-weixin） | `miniprogram/package.json:6-9` | 沿用 | 现有发布链 | 375 | 低 |
| 测试（两端） | vitest | `^2.1.9`（`frontend/package.json:31`、`miniprogram/package.json:25`） | 沿用 | 现有单测框架，用于断言模块顺序/可见性 | 366~375 | 低 |
| 后端框架 | Django + DRF | `Django>=5.2,<6.0`、`djangorestframework>=3.15,<4.0`（`backend/requirements.txt:1-2`） | 沿用（不改动） | 本次不触碰后端 | — | 低 |
| 数据存储 | MySQL（测试 SQLite） | 画像 P1/P7 | 沿用（不改动） | 无表结构与迁移变更 | — | 低 |
| 部署方式 | tar + scp + systemd（非容器） | 画像 P7 | 沿用（不改动） | 本次仅前端静态产物重建 | — | 低 |
| 新增依赖 | 无 | — | — | C-394 | — | 无 |

## 技术风险

| 等级 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 两端模块顺序常量各自维护，可能漂移（ADR-200） | GROUP_D 增加“两端模块 key 顺序一致”的断言用例；实现时用同名常量注释互指 |
| Medium | 三主题共用 4 栏骨架后，个别模块在新占位下溢出或留白 | `frontend/tests/theme_build.spec.js` + ≥768px 无横向溢出的人工/自动检查（AC-360-01）；仅在 `style.css` 与主题变量层调整 |
| Medium | “待我表决”对前 3 条并发详情请求失败会显示“未确认” | `Promise.allSettled` 单条降级，不阻塞卡片其他内容；请求数固定上限 3（ADR-198） |
| Low | 主题生成物与源 JSON 不同步 | 修改 `themes/*.theme.json` 后必须运行 `node scripts/themes/build.mjs`，并在构建前跑 `--check` 类校验 |
| Low | 前端隐藏被误当权限边界 | 后端权限保持不变（C-396）；测试覆盖越权仍返回 401/403 的既有行为 |
| Low | 无数据模块空态导致首屏变长 | 已由 C-397 与用户决策接受；内容类空态使用紧凑 `el-empty` / 单行文案 |
