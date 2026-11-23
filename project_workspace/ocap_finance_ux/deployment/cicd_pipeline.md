<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T23:40:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_finance_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_finance_ux/testing/e2e_test_report.md</file>
    <file>.github/workflows/ci.yml</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — ocap_finance_ux

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，3 个 job：backend（`manage.py check` + 全量 `manage.py test --settings=config.test_settings`）、frontend（主题校验 + `vitest run` + `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`）、miniprogram（vitest）。CI 只跑测试与构建，不部署（画像 P7）。

本次改动影响：
- 后端新增 `backend/tests/unit/test_ledger_accounts_unit.py`、`tests/integration/test_finance_accounts_api.py`、`tests/e2e/test_finance_accounts_journey.py`，已被 `manage.py test` 自动发现，**无需改 CI**。
- 前端新增 `frontend/tests/finance_accounts_ui.spec.js`，已被 `vitest run` 自动发现，**无需改 CI**。
- 无新增第三方依赖、无新环境变量、无新服务（画像 P8 禁用项均未引入）。
- 小程序本次不改（C-374），miniprogram job 不受影响。

## 流水线概览

[Source] → [Lint/静态检查] → [Build] → [Unit] → [Integration] → [Package] → [Deploy（E2，人工授权后）] → [Smoke] → [E2E]

CI 内只覆盖到 Build/Unit/Integration；Deploy 及之后的冒烟由 E2 部署计划执行。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 后端静态检查 | push/PR 到 main | `python manage.py check --settings=config.test_settings` | 退出码 0 | abort-and-notify |
| PIPE-02 | 后端全量测试（含新增单测/集成/E2E 级） | 同上 | `python manage.py test --settings=config.test_settings -v 2` | `Ran 1206 tests / OK (skipped=2)`，零失败 | abort-and-notify |
| PIPE-03 | 前端主题与单测 | 同上 | `node scripts/themes/build.mjs --strict --check` + `npx vitest run --passWithNoTests` | 主题无漂移；`Test Files 53 passed` | abort-and-notify |
| PIPE-04 | 前端产物构建 | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | `✓ built`，退出码 0 | abort-and-notify |
| PIPE-05 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests`（miniprogram） | 通过或无用例 | abort-and-notify |

## 环境矩阵

| 配置项 | 测试（内网 192.168.31.51） | 测试（外网 frp） | 生产 |
|---|---|---|---|
| 存在性（画像 P7） | 存在 | 存在（同一主机） | 不存在 |
| 后端 | systemd `ocap-backend`，gunicorn `127.0.0.1:9000` | 同左 | — |
| 前端 | nginx `:8090` → `/home/yangyang/ocap/web/ocap` | 复用 Freeark nginx `^~ /ocap/`（`:8080` + VPS 443） | — |
| 数据库 | MySQL `192.168.31.98:3306` 库 `ocap` | 同左 | — |
| 配置来源 | 目标机 `backend/.env` | 同左 | — |
| 部署需用户确认 | 是 | 是 | — |

## 制品管理

- 制品：后端源码 tar（排除 `venv/var/.env/__pycache__`）、Web `frontend/dist` tar、数据库表转储。
- 命名：`backend_<SHA>_<TS>.tar.gz`、`frontend_dist_<SHA>_<TS>.tar.gz`、`ledger-<TS>.sql`；`TS` 为目标机 `date +%Y%m%d%H%M%S`。
- 存储：目标机 `/home/yangyang/ocap/snapshots/`（保留 ≥ 7 天），开发机临时目录在上传校验后清理。
- 晋升条件：CI 全绿 + E1 计划 APPROVED + E2 用户当轮授权（`PRODUCTION_DEPLOY_CONFIRM=true` 且环境名“测试”）。
- 无独立制品库：后端/前端均在开发机构建后 tar 传输（画像 P7 既有方式）；风险是构建环境差异，已用固定 Node 20/Python 3.13 CI 与本地命令对齐缓解。
