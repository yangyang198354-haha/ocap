<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-18T11:54:19+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线（INCREMENTAL，ocap_batch_1118）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`（GitHub Actions，`main` 的 push/PR 与手动触发；只测试与构建，不部署，画像 P7）。三个 job：

| job | 阶段 |
|---|---|
| backend | Python 3.13；装 MySQL 客户端构建依赖；`pip install -r requirements.txt`；`manage.py check --settings=config.test_settings`；`manage.py test --settings=config.test_settings -v 2`（全量） |
| frontend | Node 20；`npm ci`；`node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` |
| miniprogram | Node 20；`npm install --legacy-peer-deps`；`npx vitest run --passWithNoTests` |

本批改动对 CI 的影响（逐项核对 module_design「受影响的运行单元」与 implementation_plan，并用本地 `git status` 复核）：

| 影响项 | 结论 |
|---|---|
| 新增依赖 | 无。`git status --short -- backend/requirements.txt frontend/package.json frontend/package-lock.json miniprogram` 输出 0 行 |
| 新测试层 | 无。新增用例落在既有位置（`backend/tests/{unit,integration,e2e}/test_batch1118_*.py`、`frontend/tests/batch1118_*.spec.js` 等，本地未跟踪 13 个、修改 11 个测试文件），被现有 `manage.py test` / `vitest run` 自动收集 |
| 新服务 / 环境变量 | 无新增 systemd 服务、`.env` 键、端口 |
| 迁移 | 新增 `committee/0002_seat_registry_holder.py`、`residency/0005_membership_registry_owner.py`。CI 的 `test_settings` 置空 `MIGRATION_MODULES`，**CI 不执行任何迁移**（画像 P4）；迁移正确性由 E2 在测试机 MySQL 上验证（M-7，见 deployment_plan DEPLOY-005/006、V-03/V-04） |
| 后端契约测试读前端源码 | `test_frontend_contract.py`、`test_owner_auth_v2_contract.py` 读取前端源码；后端 job 全量运行已覆盖（画像 P4、M-PM-006） |
| 小程序 | 本批不改源码；CI 仍跑 vitest（基线 18 文件 135 条）；不构建、不发布 |
| nginx | `client_max_body_size` 不在仓库、不在 CI，由 E2 在测试机上改（deployment_plan DEPLOY-009/010），对 CI 无影响 |
| 浅克隆 | CI 默认浅克隆，依赖 `git show` 基线提交的用例（如 `test_requirements_numbering.py`）在 CI 中 skipUnless 跳过（M-DE-019，CI 环境 skipped=1 为既知）；不给 CI 加 `paths-ignore` 排除被扫描的文档目录 |

**结论：无需修改 `ci.yml`**（module_design 与 PM 均未要求修改；不凭空重建流水线）。本批未改任何 CI 文件。

基线（GROUP_D 报告、PM 复跑 2026-11-18 11:43）：后端 Ran 1119 OK（unit 236 / integration 806 / e2e 71 / smoke 6）；前端 45 文件 531/531；小程序 18 文件 135/135；相对基线新增失败 0。

**缺口与建议（不改文件，供用户决定）：**

1. 本批改动**尚未提交**（HEAD `c3a10ce`，工作树 52 个 M、21 个 `??`），CI 尚未在本批代码上运行。画像 P9：commit 由用户确认后主会话执行，push 另需用户明确同意。未提交时部署以本地工作树为准（skill §0），版本标识用 `git status` 摘要 + tar SHA256（M-DE-006）；若 PM 在 E2 前已提交，改记新 HEAD，计划不变。
2. CI 不跑迁移；`Seat.user` 改可空这类 DDL 只在 E2 的测试机 MySQL 上第一次真实执行。可选改进（需新建专用 settings，超出本批范围，仅建议）：backend job 增一步用不置空迁移的临时 SQLite 配置执行 `migrate` 与 `migrate committee 0001`、`migrate residency 0004`。
3. `makemigrations --check --dry-run` 不在 CI 中（画像 P4 只列为本地检查）。本批以 deployment_plan 预检 PRE-A04 做 committee/residency 的 scoped 检查，必须用不置空迁移的临时 settings（M-DE-037，直接用 `config.test_settings` 会误报）。
4. 本批新增用例的"时区跨午夜"类（TC-INT-1140~1142）依赖 patch 时间，CI 在 UTC 运行，已由用例冻结时间保证稳定；不需要 CI 改动。
5. 前端 `--passWithNoTests` 对无用例的包不报错（M-DE-004）。前端当前 45 个 spec，不构成缺口，仅保持登记。

## 流水线概览

[Source: push/PR → main] → [Lint: compileall、theme check、Django check] → [Build: 前端 vite build] → [Unit+Integration+E2E: 后端全量 / 前端 vitest / 小程序 vitest] → [Package: 部署时在开发机 tar，非 CI] → [Deploy 测试：人工授权的 E2] → [Smoke: 部署后验证] → [E2E: P4-1 只读 HTTP 探测，E2 可选，需单独授权]

CI 止于构建与测试；Package / Deploy / Smoke 不在 CI 中（画像 P7），由 GROUP_E2 按 deployment_plan 执行。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 `main`、手动触发 | `actions/checkout@v4` | 检出成功 | abort-and-notify（Actions 失败通知） |
| PIPE-02 | Django 系统检查 | PIPE-01 之后（backend job） | `python manage.py check --settings=config.test_settings`（cwd `backend/`） | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端全量测试（unit/integration/e2e/smoke、契约） | PIPE-02 之后 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0；本批基线 1119 通过（CI 环境 skipped=1 为既知） | abort-and-notify；不重试（测试失败不是瞬态） |
| PIPE-04 | 风格生成物检查 | frontend job，`npm ci` 之后 | `node scripts/themes/build.mjs --strict --check`（cwd 仓库根） | 退出码 0 | abort-and-notify |
| PIPE-05 | 前端测试 | PIPE-04 之后 | `npx vitest run --passWithNoTests`（cwd `frontend/`） | 退出码 0；本批基线 45 文件 531 条 | abort-and-notify |
| PIPE-06 | 前端构建 | PIPE-05 之后 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`（cwd `frontend/`） | 退出码 0 | abort-and-notify |
| PIPE-07 | 小程序测试 | miniprogram job，`npm install --legacy-peer-deps` 之后 | `npx vitest run --passWithNoTests`（cwd `miniprogram/`） | 退出码 0；本批基线 18 文件 135 条 | abort-and-notify；`npm install` 网络瞬态错误可重试 1 次（有限次 retry），测试失败不重试 |
| PIPE-08 | 打包（非 CI，部署时） | E2 授权后 | 开发机 `tar` 后端目录（排除 `__pycache__ venv .env .env.* var db.sqlite3`）；`VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` 后 `grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js` ≥ 1 才打包 `frontend/dist`；整包 `scp`，不用 pscp 逐文件（P8） | 本地与目标机 SHA256 一致；前缀门槛通过 | `DEPLOYMENT_FAILED`（目标机未变更时无需回滚） |
| PIPE-09 | 部署测试环境（非 CI） | 用户当轮授权，`PRODUCTION_DEPLOY_CONFIRM=true` 与环境名「测试」 | 见 deployment_plan DEPLOY-001~011 | 全部 DEPLOY 退出码 0 | 立即停止，从失败步骤起按逆序 ROLLBACK；禁止"跳过失败继续部署" |
| PIPE-10 | 部署后冒烟（非 CI） | PIPE-09 完成后 | deployment_plan「部署后验证」V-01~V-23 | 全部通过 | `DEPLOYED_WITH_ISSUES`，交 PM/用户决定是否回滚 |
| PIPE-11 | 远程 E2E 探测（非 CI，**可选，需单独授权**） | 用户确认夹具将占用的真实专有部分后 | deployment_plan DEPLOY-012~014（只读 GET，仅 `e2e_` 账号，P4-1） | 断言全部通过且夹具已清理 | 夹具在同一次 `trap cleanup EXIT` 调用内清理；失败仍必须清理 |

## 环境矩阵

只列画像 P7 中存在的环境；无生产、无 staging，不设计晋升。

| 配置项 | 测试 |
|---|---|
| 主机 | 树莓派 `raspberrypi`；外网 SSH `-p 57279 yangyang@47.109.197.217`（首次连接核对 ED25519 指纹见画像 P7），内网 `192.168.31.51:22` |
| 实例数 | 单实例（gunicorn `127.0.0.1:9000`，systemd `ocap-backend`；nginx 8090，站点 `ocap`）；资源上限无登记 |
| 外部依赖 | MySQL 库 `ocap`（主机见 `.env` 的 `DB_HOST`）；短信 `SMS_GATEWAY_BACKEND=console` 替身；微信未真实调用 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（只引用键名，不读取、不打印值；本批无新键） |
| 部署需用户确认 | 是 |
| 同机共存 | Freeark（uvicorn:8000、nginx:80/8080、frpc）不得改动；**本批唯一的 nginx 写入**是 ocap 自身站点 `/etc/nginx/sites-available/ocap` 第 5 行 `client_max_body_size 20m→60m`（用户 2026-11-18 Q1=A）；`nginx` 只 `reload` 不 `restart`；Freeark 的 `sites-enabled/freeark` 只读核对 |

## 制品管理

- 无制品库。部署产物在**开发机**构建并打包：后端为工作树 tar（排除项见 PIPE-08），前端为 `frontend/dist` tar；临时放在开发机 `mktemp` 目录，目标机 `/tmp`，文件名含锚点 `TS`。
- 命名：`backend_<TS>.tar.gz`、`frontend_dist_<TS>.tar.gz`；目标机回滚快照 `snapshots/backend-<TS>.tar.gz`、`snapshots/web-<TS>.tar.gz`（画像 P7），另有逐文件哈希清单 `webhash-<TS>.sha256`、`backendhash-<TS>.sha256`、迁移计划 `migplan-<TS>.txt`、席位/成员关系表转储 `seat_membership-<TS>.sql`、nginx 站点备份 `sites-available/ocap.bak_<TS>`。
- 版本标识：本批未提交，HEAD 不能单独定位版本。记录 `git rev-parse HEAD`、`git status --short` 摘要、两个 tar 的 SHA256 与 `dist/index.html` SHA256。风险：同一 HEAD 的不同工作树会产出不同制品，须以 SHA256 为准。
- 晋升条件：只有测试环境，无晋升。部署前提是 GROUP_D 门控通过；人工验证项另行跟踪（M-1~M-8，见 deployment_plan）。
- 保留：快照、哈希清单、转储与 nginx 备份保留 ≥ 7 天；既往含个人信息的备份（`ocapdb-*.sql` 等）本批不得删除。快照排除 `.env`、`.env.*`、`venv`、`var`（上一批偏差 1：`backend/` 目录里既有 `.env.bak_*` 副本曾被打进快照，本批排除）。
