<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-14T17:53:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
    <file>project_workspace/ocap_identity_display/development/implementation_plan.md</file>
    <file>project_workspace/ocap_identity_display/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_identity_display/testing/integration_test_report.md</file>
    <file>project_workspace/ocap_identity_display/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：用户端身份显示与认证房屋信息

## 现状与影响

现有 CI：`.github/workflows/ci.yml`
- `backend`：Python 3.13，`manage.py check` + 全量 Django 测试（`config.test_settings`）。
- `frontend`：Node 20，`npm ci`，主题定义校验，vitest，生产构建（`--base=/ocap/`）。
- `miniprogram`：Node 20，`npm install --legacy-peer-deps`，vitest（不构建小程序）。

本次改动影响：
- 新增后端测试 `tests/integration/test_identity_display.py`、`tests/e2e/test_identity_display_journey.py`，由后端 job 自动纳入。
- 新增前端测试 `frontend/tests/identity_display.spec.js`、小程序测试 `miniprogram/tests/identity_display.spec.js`，由各自 job 自动纳入。
- 无新增依赖、无新增环境变量、无新增服务、无数据库迁移。

**无需修改 CI 配置。**

## 流水线概览

[Source] → [Backend check + tests] → [Frontend theme check + tests + build] → [Miniprogram tests] → [Package] → [Deploy（手动，E2 授权后）] → [Smoke]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| P-01 | Source | push / PR 到 `main` | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| P-02 | 后端检查与测试 | 同上 | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` | 退出码 0；572 项测试 OK（skipped=9） | abort-and-notify，不部署 |
| P-03 | 前端校验、测试与构建 | 同上 | `node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`npm run build -- --base=/ocap/` | 主题 check 通过；185 项通过；构建成功 | abort-and-notify，不部署 |
| P-04 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests` | 78 项通过 | abort-and-notify，不部署 |
| P-05 | 制品打包 | 手动触发部署时在开发机执行 | 后端 tar（排除 `__pycache__/venv/.env/var/db.sqlite3`）；前端 `dist` tar | 包生成、SHA256 记录 | abort-and-notify |
| P-06 | 部署 | 用户当轮明确授权（E2） | 见 `deployment_plan.md` | 全部 DEPLOY 完成 | 逆序 ROLLBACK |
| P-07 | 部署后冒烟 | P-06 成功后 | 见 `deployment_plan.md` 验证表 | 全部检查通过 | 失败即报告，按用户决定回滚 |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 `192.168.31.51`，用户 `yangyang` | 同左，经 frp + VPS 443 |
| 后端 | gunicorn `127.0.0.1:9000`，systemd `ocap-backend` | 同左 |
| 前端 | nginx `8090`，`/home/yangyang/ocap/web/ocap` | `https://ai-freeark.xin/ocap/` |
| 数据库 | MySQL `192.168.31.98:3306/ocap` | 同左 |
| 配置来源 | `/home/yangyang/ocap/backend/.env` | 同左 |
| 部署需确认 | 是 | 是 |

生产环境：画像 P7 中不存在，不设计。

## 制品管理

- 存储位置：开发机临时目录 + 目标机 `/home/yangyang/ocap/snapshots`（回滚锚点）。
- 命名：后端 `backend-<TS>.tar.gz`、前端 `web-<TS>.tar.gz`、nginx `*.bak_<TS>`，`TS=YYYYMMDDHHMMSS`。
- 晋升条件：P-02~P-04 全部通过 + 用户当轮部署授权。
- 小程序：不在本流水线构建/发布（画像 RU-4），由用户侧微信开发者工具发布。
- 无制品库；风险：制品不可追溯，靠锚点时间戳与 tar SHA256 定位（已知缺口，见 ocap-deploy §8）。
