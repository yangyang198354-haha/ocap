<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T23:31:48+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/architecture/module_design.md</file>
    <file>backend/requirements.txt</file>
    <file>frontend/package.json</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型 — ocap_profile_ux

本次为 INCREMENTAL，**不新增任何第三方依赖**，全部沿用现有栈（画像 P1/P8）。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言 | Python | 3.12（画像 P1；本机实测 3.14，差异已在开发报告说明） | 沿用 | 既有运行时 | 全部 | 低 |
| Web 框架 | Django | `>=5.2,<6.0`（`backend/requirements.txt:1`） | 沿用 | 既有 | 全部 | 低 |
| API 框架 | Django REST Framework | `>=3.15,<4.0`（`backend/requirements.txt:2`） | 沿用 | 既有权限/分页 | 全部 | 低 |
| 数据库 | MySQL（测试环境 192.168.31.98:3306 库 `ocap`）；测试用 SQLite 内存库 | 画像 P1/P7；`config/test_settings` | 沿用 | 既有 | MOD-153 迁移 | 低（小表 ALTER） |
| Web 前端 | Vue 3 + Vite | `vue ^3.5.13`、`vite ^6.0.1`（`frontend/package.json:25,30`） | 沿用 | 既有 | 255–263 | 低 |
| UI 组件库 | Element Plus | `^2.8.7`（`frontend/package.json:22`） | 沿用 | 既有；本次只用 `el-table`/`el-collapse`/`el-switch`/`el-input`/`el-date-picker` | 255/258/262/263 | 低 |
| 前端测试 | vitest + @vue/test-utils | `vitest ^2.1.9`、`@vue/test-utils ^2.4.6`（`frontend/package.json:29-30`） | 沿用 | 画像 P4 | 全部 | 低 |
| 后端测试 | Django test runner | Django 内置 | 沿用 | 画像 P4 | 全部 | 低 |
| 默认头像资源 | 内置 SVG（新建 `frontend/src/assets/avatar-default.svg`） | 自绘，< 2 KB | 新增资源（非依赖） | 零外网、≤100 KB、深浅背景可见 | 256、NFUNC-054 | 低 |
| 进程管理/部署 | systemd + gunicorn + nginx（tar 快照部署），非容器 | 画像 P7/P8 | 沿用 | 既有 | 全部 | 低 |
| 迁移工具 | Django migrations（手写、单 app） | 画像 P6 | 沿用 | 既有约定，禁用 makemigrations 全量产物 | MOD-153 | 低 |

## 技术风险

| 等级 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 席位/房屋关系多条件过滤涉及跨表查询（清册业主房产 vs 绑定用户认证房产），可能出现重复行或 N+1 | 使用 `Exists` 子查询替代 join+`distinct`（M-SA-010）；增加"每页查询数不随行数增长"的测试；5000 条数据量的响应时间用例覆盖 REQ-NFUNC-053 |
| Medium | 头像上限从 2 MB 放宽到 5 MB，前端绕过时依赖后端拒绝 | 后端 `SPECS` 为唯一权威；补 4.9 MB 通过、5.1 MB → 413 `FILE_TOO_LARGE` 的边界测试 |
| Medium | 公开 profile 端点可能误带敏感字段 | 白名单序列化 + 契约测试逐字段断言（不得出现 phone/email/birthday/account_no） |
| Low | 实名取值依赖 `Membership.registry_owner`，历史上的认证记录可能为空 | 为空时不展示实名并禁用开关；测试覆盖无清册业主的用户 |
| Low | Element Plus 日期控件默认高度与输入框不一致，布局回归窄屏可能换行错位 | 统一 `size` 与固定宽度，测试覆盖 ≥768px 与 <768px 两种视口 |
