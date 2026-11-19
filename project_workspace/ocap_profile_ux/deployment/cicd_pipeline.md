<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-19T00:38:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_profile_ux/testing/test_plan.md</file>
    <file>.github/workflows/ci.yml</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — ocap_profile_ux

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，三个 job：

| job | 内容 |
|---|---|
| backend | Python 3.13 + MySQL client 依赖；`manage.py check`；`manage.py test --settings=config.test_settings -v 2`（全量） |
| frontend | `npm ci`；`node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` |
| miniprogram | `npm install`；`npx vitest run --passWithNoTests` |

本次改动影响：

- 新增后端测试 `backend/tests/integration/test_profile_ux_api.py`、`backend/tests/e2e/test_profile_ux_journeys.py` 与前端的 `frontend/tests/profile_ux.spec.js`，位于既有测试目录，**CI 无需修改即自动纳入**。
- 新增迁移 `backend/apps/accounts/migrations/0004_user_profile_fields.py`，CI 测试库自动应用。
- 无新依赖（`backend/requirements.txt`、`frontend/package.json` 未改），无需调整安装步骤。
- 需注意：开发机 Windows 上有 6 个文件权限类既有失败；CI 为 Linux，预期不再失败，但首次运行需核对；如仍失败则按基线处理，不得跳过。

结论：**无需修改 CI 配置**。

## 流水线概览

[Source] → [Check] → [Backend tests] → [Frontend theme check] → [Frontend tests] → [Frontend build] →（测试环境部署由 E2 手动授权，不在 CI 内）

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 检出 | push/PR 到 main、手动触发 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| PIPE-02 | Django check | 同 PIPE-01 | `python manage.py check --settings=config.test_settings`（backend/） | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端全量测试 | 同 PIPE-01 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0；失败数 = 基线（Linux 预期 0） | abort-and-notify |
| PIPE-04 | 风格生成物一致性 | 同 PIPE-01 | `node scripts/themes/build.mjs --strict --check`（仓库根） | 退出码 0 | abort-and-notify |
| PIPE-05 | 前端测试 | 同 PIPE-01 | `npx vitest run --passWithNoTests`（frontend/） | 退出码 0 | abort-and-notify |
| PIPE-06 | 前端构建 | 同 PIPE-01 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | `✓ built`；产物含 `/ocap/api/v1` | abort-and-notify |
| PIPE-07 | 小程序测试 | 同 PIPE-01 | `npx vitest run --passWithNoTests`（miniprogram/） | 退出码 0 | abort-and-notify |

禁止"失败后继续部署"；部署由 E2 在用户当轮授权后手动执行（画像 P7：测试环境部署需用户确认）。

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 192.168.31.51 | 同一树莓派，经 Freeark frp（VPS `47.109.197.217:57279` → 内网 22） |
| 后端 | gunicorn `127.0.0.1:9000`（systemd `ocap-backend`） | 同左 |
| 数据库 | MySQL 192.168.31.98:3306 库 `ocap`（`DB_SSL_DISABLED=1`） | 同左 |
| Web | nginx `8090` 静态目录 `/home/yangyang/ocap/web/ocap` | 复用 Freeark nginx `^~ /ocap/`；`https://ai-freeark.xin/ocap/` |
| 配置来源 | 目标机 `backend/.env`（只引用位置，不写值） | 同左 |
| 部署需确认 | 是（画像 P7） | 是 |

生产环境：不存在，不设计晋升。

## 制品管理

- 无制品库。E2 在开发机打包：`backend-<TS>.tar.gz`、`web-<TS>.tar.gz`，`TS` 为 14 位时间戳，记录两端 SHA256。
- 命名含时间戳以定位回滚锚点（M-DE-006）；同时记录 `git status --short` 摘要、`frontend/dist/index.html` SHA256。
- 目标机不使用 git pull 部署；禁止 pscp 逐文件上传（画像 P8）。
