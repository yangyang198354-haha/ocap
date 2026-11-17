<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-17T22:30:38+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线（INCREMENTAL，ocap_identity_property）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`（GitHub Actions，`main` 的 push/PR 与手动触发；只测试与构建，不部署，画像 P7）。三个 job：

| job | 阶段 |
|---|---|
| backend | Python 3.13；装 MySQL 客户端构建依赖；`pip install -r requirements.txt`；`manage.py check --settings=config.test_settings`；`manage.py test --settings=config.test_settings -v 2`（全量） |
| frontend | Node 20；`npm ci`；`node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` |
| miniprogram | Node 20；`npm install --legacy-peer-deps`；`npx vitest run --passWithNoTests` |

本批改动对 CI 的影响（逐项核对 module_design「受影响的运行单元」与 implementation_plan）：

| 影响项 | 结论 |
|---|---|
| 新增依赖 | 无。`git diff HEAD -- backend/requirements.txt` 为空；`package.json`/`package-lock.json` 零改动 |
| 新测试层 | 无。新增用例落在既有位置：`backend/tests/{unit,integration,e2e}/test_phone_match_*.py`、`frontend/tests/identity_property_*.spec.js`、`miniprogram/tests/identity_property_*.spec.js`，被现有 `manage.py test` / `vitest run` 自动收集 |
| 新服务 / 环境变量 | 无；无新增 systemd 单元、定时任务、`.env` 键 |
| 迁移 | 新增 `residency/0004_phone_match_prompt.py`。CI 的 `test_settings` 置空 `MIGRATION_MODULES`，**CI 不执行任何迁移**（画像 P4）；迁移正确性由 E2 在测试机 MySQL 上验证（MV-04，见 deployment_plan DEPLOY-006） |
| 后端契约测试读前端源码 | `test_frontend_contract.py`、`test_owner_auth_v2_contract.py` 读取前端/小程序源码；后端 job 全量运行已覆盖（画像 P4、M-PM-006） |
| 小程序构建 | CI 只跑 vitest，不构建小程序（`build:mp-weixin` 在本机基线即失败，ocap_brand_layout GR-C-001-F04）；小程序发布为人工（deployment_plan `[MANUAL]`） |

**结论：无需修改 `ci.yml`**（module_design 与 PM 均未要求修改；不凭空重建流水线）。

基线（PM/测试报告实测，工作树 HEAD c5ed0ab + 本批未提交改动）：后端 1025 通过、前端 41 文件 482/482、小程序 18 文件 135/135，相对基线新增失败 0。

**缺口与建议（不改文件，供用户决定）：**

1. 本批改动**尚未提交**，CI 尚未在本批代码上运行过（HEAD 的 CI run 44032717170 对应上一批）。画像 P9：commit 由用户确认后主会话执行，push 另需用户明确同意。建议部署前后任一时点提交并 push 以拿到 CI 结果；未 push 时部署以本地工作树为准（skill §0），版本标识用 `git status` 摘要 + tar SHA256（M-DE-006）。
2. CI 不跑迁移（`MIGRATION_MODULES` 置空），迁移的前进与回退只在开发机临时 SQLite（implementation_plan）与 E2 的测试机 MySQL 验证。可选改进：在 backend job 追加一个独立步骤，用不置空迁移的临时 SQLite 配置执行 `migrate` 与 `migrate residency 0003`，并保留 `makemigrations --check --dry-run`。需要新建专用 settings，超出本批范围，仅建议。
3. `makemigrations --check --dry-run` 不在 CI 中（画像 P4 只列为本地检查，且既有 content 等 app 有 8 条 `Alter field id` 漂移输出，非本批）。本批以 deployment_plan 预检 PRE-A05 做"residency/accounts 无漂移"的 scoped 检查。
4. 前端 `--passWithNoTests` 对无用例的包不报错（M-DE-004）。前端当前 41 个 spec，不构成缺口，仅保持登记。

## 流水线概览

[Source: push/PR → main] → [Lint: compileall、theme check] → [Build: 前端 vite build] → [Unit+Integration+E2E: 后端全量 / 前端 vitest / 小程序 vitest] → [Package: 部署时在开发机 tar，非 CI] → [Deploy 测试：人工授权的 E2] → [Smoke: 部署后验证] → [E2E: P4-1 只读 HTTP 探测，E2 可选]

CI 止于构建与测试；Package/Deploy/Smoke 不在 CI 中（画像 P7），由 GROUP_E2 按 deployment_plan 执行。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 `main`、手动触发 | `actions/checkout@v4` | 检出成功 | abort-and-notify（Actions 失败通知） |
| PIPE-02 | Django 系统检查 | PIPE-01 之后（backend job） | `python manage.py check --settings=config.test_settings`（cwd `backend/`） | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端全量测试（含 unit/integration/e2e/smoke、契约测试） | PIPE-02 之后 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0；本批基线 1025 通过 | abort-and-notify；不重试（测试失败不是瞬态） |
| PIPE-04 | 风格生成物检查 | frontend job，`npm ci` 之后 | `node scripts/themes/build.mjs --strict --check`（cwd 仓库根） | 退出码 0 | abort-and-notify |
| PIPE-05 | 前端测试 | PIPE-04 之后 | `npx vitest run --passWithNoTests`（cwd `frontend/`） | 退出码 0；本批基线 41 文件 482 条 | abort-and-notify |
| PIPE-06 | 前端构建 | PIPE-05 之后 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`（cwd `frontend/`） | 退出码 0 | abort-and-notify |
| PIPE-07 | 小程序测试 | miniprogram job，`npm install --legacy-peer-deps` 之后 | `npx vitest run --passWithNoTests`（cwd `miniprogram/`） | 退出码 0；本批基线 18 文件 135 条 | abort-and-notify；`npm install` 的网络瞬态错误可重试 1 次（有限次 retry），测试失败不重试 |
| PIPE-08 | 打包（非 CI，部署时） | E2 授权后 | 开发机 `tar` 后端目录（排除 `__pycache__ venv .env var db.sqlite3`）与 `frontend/dist`；整包 `scp`，不用 pscp 逐文件（P8） | 本地与目标机 SHA256 一致 | `DEPLOYMENT_FAILED`（目标机未变更时无需回滚） |
| PIPE-09 | 部署测试环境（非 CI） | 用户当轮授权，`PRODUCTION_DEPLOY_CONFIRM=true` 与环境名「测试」 | 见 deployment_plan DEPLOY-001~009 | 全部 DEPLOY 退出码 0 | 立即停止，从失败步骤起按逆序 ROLLBACK；禁止"跳过失败继续部署" |
| PIPE-10 | 部署后冒烟（非 CI） | PIPE-09 完成后 | deployment_plan「部署后验证」V-01~V-20 | 全部通过 | `DEPLOYED_WITH_ISSUES`，交 PM/用户决定是否回滚 |
| PIPE-11 | 远程 E2E 探测（非 CI，可选） | 用户确认夹具将占用的真实专有部分后 | deployment_plan DEPLOY-010~012（只读 GET，仅 `e2e_` 账号，P4-1） | 断言全部通过且夹具已清理 | 夹具在同一次 `trap cleanup EXIT` 调用内清理；失败仍必须清理 |

## 环境矩阵

只列画像 P7 中存在的环境；无生产、无 staging，不设计晋升。

| 配置项 | 测试 |
|---|---|
| 主机 | 树莓派 `raspberrypi`；外网 SSH `-p 57279 yangyang@47.109.197.217`（首次连接核对 ED25519 指纹见画像 P7），内网 `192.168.31.51:22` |
| 实例数 | 单实例（gunicorn `127.0.0.1:9000`，systemd `ocap-backend`；nginx 8090，站点 `ocap`）；资源上限无登记 |
| 外部依赖 | MySQL 库 `ocap`（主机见 `.env` 的 `DB_HOST`）；短信 `SMS_GATEWAY_BACKEND=console` 替身；微信未真实调用 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（只引用键名，不读取、不打印值；本批无新键） |
| 部署需用户确认 | 是 |
| 同机共存 | Freeark（uvicorn:8000、nginx:80/8080、frpc）不得触碰；nginx 本批不改 |

## 制品管理

- 无制品库。部署产物在**开发机**构建并打包：后端为工作树 tar（排除项见 PIPE-08），前端为 `frontend/dist` tar；临时放在开发机 `mktemp` 目录，目标机 `/tmp`，文件名含锚点 `TS`。
- 命名：`backend_<TS>.tar.gz`、`frontend_dist_<TS>.tar.gz`；目标机回滚快照 `snapshots/backend-<TS>.tar.gz`、`snapshots/web-<TS>.tar.gz`（画像 P7），另有逐文件哈希清单 `webhash-<TS>.sha256`。
- 版本标识：本批未提交，HEAD 不能单独定位版本。记录 `git rev-parse HEAD`、`git status --short` 摘要、两个 tar 的 SHA256 与 `dist/index.html` SHA256。风险：同一 HEAD 的不同工作树会产出不同制品，须以 SHA256 为准；若 PM 在 E2 前已提交，改记新 HEAD。
- 晋升条件：只有测试环境，无晋升。部署前提是 GROUP_D 门控通过且人工验证项另行跟踪（MV-01~04）。
- 保留：快照与哈希清单保留 ≥ 7 天；上批含个人信息的备份（`ocapdb-*.sql` 等）本批不得删除。
