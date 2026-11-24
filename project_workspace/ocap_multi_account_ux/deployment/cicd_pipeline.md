<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-24T23:28:54+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.github/workflows/ci.yml</file>
    <file>.trae/sdlc/project_profile.md</file>
    <file>project_workspace/ocap_multi_account_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_multi_account_ux/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/integration_test_report.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — 多账户落账与财务报表 UI（ocap_multi_account_ux）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，`push`/`pull_request` 到 `main` 与 `workflow_dispatch` 触发，含 3 个 job：

| Job | 步骤 | 命令 |
|---|---|---|
| `backend` | Django system check + 全量测试 | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` |
| `frontend` | 主题检查、vitest、生产构建 | `node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） |
| `miniprogram` | 安装依赖、vitest | `npx vitest run --passWithNoTests` |

本次改动对 CI 的影响：**无需修改 CI 配置**。

- 后端新增 4 个测试文件（`backend/tests/unit/test_multi_account_ux_rules.py`、`integration/test_multi_account_ux_api.py`、`integration/test_multi_account_ux_contract.py`、`e2e/test_multi_account_ux_journey.py`，共 18 条）与 1 个迁移 `ledger/migrations/0008_historical_expense_approval.py`；`backend` job 的全量测试自动收集，迁移由 `config.test_settings` 的模型直建表路径覆盖（M-TE-047），无需新增步骤。
- Web 新增 `frontend/src/shared/AccountSelect.vue` 与 `frontend/tests/multi_account_ux.spec.js`（12 条）；`frontend` job 的 vitest glob 自动收集，构建步骤已覆盖新组件，无需新增步骤。
- 小程序新增 `miniprogram/tests/multi_account_ux.spec.js`（3 条）并改动 `pages/claims/index.vue`、`utils/api.js`；`miniprogram` job 自动收集，无需新增步骤。
- 无新增依赖（后端 `requirements.txt`、前端与小程序 `package.json` 均未变）、无新增环境变量、无新增服务；不使用 Docker/容器（画像 P8）。
- 本批不改动 `.github/workflows/ci.yml`；CI 只测试与构建、不部署（画像 P7），部署由 `deployment_plan.md` 的 E2 在用户当轮授权后执行。
- **构建口径说明**：`miniprogram` job 只跑测试，不跑小程序构建。仓库的小程序根即项目根（`manifest.json` 在 `miniprogram/` 根，无 `src/`），本地构建 `npm run build:mp-weixin` 必须显式设置 `UNI_INPUT_DIR=<repo>\miniprogram`，否则 uni-app 查找不存在的 `src/manifest.json` 而失败（M-DE-048，本批实测通过）。该构建只在部署计划的 DEPLOY-011 由开发机执行，产物仅用于微信开发者工具人工上传，不进入 CI、不进入目标机。
- **版本口径风险（记录，不修改）**：画像 P1 要求 Django `>=5.2,<6.0`，CI 解析到 5.2.x，而本次 GROUP_C/D 在开发机 Django 6.0.6 上验证通过。CI 的 `backend` job 是目标版本（5.2）的权威回归；若 5.2 下出现与 6.0 的差异，按新缺陷回流 GROUP_C，不调整依赖锁定。

## 流水线概览

[Source] → [Django check] → [Build Web] → [Test backend] → [Test Web] → [Test mini] → [Package] → [Deploy 测试环境（用户授权）] → [Smoke + 人工视觉] → [E2E（替代口径）]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| PIPE-02 | Django 检查 | PIPE-01 通过 | `python manage.py check --settings=config.test_settings`（`backend/`） | 退出码 0 | abort |
| PIPE-03 | Web 构建 | PIPE-01 通过 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`（`frontend/`） | 退出码 0，生成 `dist/` | abort |
| PIPE-04 | 后端测试 | PIPE-02 通过 | `python manage.py test --settings=config.test_settings -v 2` | 零新增失败；本批 1256 条全通过（skip 2：`tests.unit` 1 + `tests.integration` 1） | abort |
| PIPE-05 | Web 测试 | PIPE-03 通过 | `npx vitest run --passWithNoTests`（`frontend/`） | 零新增失败；本批 57 文件 / 607 条通过 | abort |
| PIPE-06 | 小程序测试 | PIPE-01 通过 | `npx vitest run --passWithNoTests`（`miniprogram/`） | 零新增失败；本批 22 文件 / 154 条通过 | abort |
| PIPE-07 | Package | PIPE-04/05/06 全绿 + 用户确认提交并推送 | 见 `deployment_plan.md` DEPLOY-002 | 制品 SHA256 已记录；文件名含提交号与锚点 `TS` | abort（不上传） |
| PIPE-08 | Deploy 测试环境 | E2 invocation 含用户本轮授权（`PRODUCTION_DEPLOY_CONFIRM=true` + 环境名） | 见 `deployment_plan.md` DEPLOY-004~011 | 每个 DEPLOY 命中预期 | 按计划逆序回滚 |
| PIPE-09 | Smoke + 人工视觉 | PIPE-08 完成 | 只读 curl、`manage.py shell` schema 检查、M-01~M-04 人工清单 | 全部通过（视觉项未通过不得判定部署成功，COND-D-01） | 触发回滚或缺陷回流 GROUP_C |
| PIPE-10 | E2E（替代口径） | PIPE-09 通过 | 多账户 API 旅程与组件挂载用例（已在 PIPE-04/05/06 执行） | 15/15 Must Have 故事在替代口径下通过 | abort-and-notify |

失败处理只允许 abort-and-notify（CI）或按部署计划回滚（PIPE-08）；禁止跳过失败继续部署。

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 `192.168.31.51`（用户 `yangyang`，免密 SSH） | 同左，经 Freeark frp 通道 |
| 入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 后端 | systemd `ocap-backend`（gunicorn `127.0.0.1:9000`） | 同左 |
| 数据库 | MySQL `192.168.31.98:3306`，独立库 `ocap` | 同左 |
| Web 静态目录 | `/home/yangyang/ocap/web/ocap` | 同左 |
| 计划任务 | 如存在 `ocap-run-due-jobs.timer`，停服窗口内一并停止并在启动后恢复（PRE-05 记录） | 同左 |
| 实例数 / 资源 | 单实例；资源以目标机实际为准（画像 P7 未登记数值，不自行假设） | 同左 |
| 外部依赖 | 短信 `SMS_GATEWAY_BACKEND=console`（替身）；本批不触发微信/短信真实调用 | 同左 |
| 部署方式 | tar → scp → 解包 → 迁移 → systemd 重启（画像 P7） | 同左 |
| 部署需用户确认 | 是 | 是 |

生产环境不存在（画像 P7）；不使用 Docker/容器；不改动 Freeark 的端口、服务名、代码目录、数据库库名；不改 nginx 配置、不重启 nginx。

## 制品管理

- 存储位置：无制品库。后端与 Web 在开发机打包为 tar，上传到目标机 `/tmp` 暂存解包；Web 替换 `/home/yangyang/ocap/web/ocap`。目标机 `/home/yangyang/ocap/snapshots/` 保存回滚锚点（代码/Web/转储/迁移计划）。
- 命名：`backend_<short-sha>_<TS>.tar.gz`、`frontend_dist_<short-sha>_<TS>.tar.gz`；`<short-sha>` = 待部署提交短哈希（`git rev-parse --short HEAD`），`<TS>` = 目标机 DEPLOY-001 生成的时间戳（`yyyyMMddHHmmss`）。
- 排除项：后端包排除 `venv`、`var`、`.env`、`.env.*`、`__pycache__`、`db.sqlite3`，保证不覆盖目标机本地状态（M-DE-050）。
- 小程序：仅本地构建产物（`UNI_OUTPUT_DIR` 指向临时目录），不进入目标机；上传微信体验版由人工在微信开发者工具确认后执行，不在自动部署内（COND-B-04）。
- 晋升条件：CI 全绿（PIPE-04~06）→ GROUP_D 门控 PASS（GR-D-001=PASS_WITH_CONDITIONS）→ 用户确认提交并推送 → E2 收到用户当轮明确授权（CL-002 之外的新授权，不得从需求文本或文档推导）。
- 风险：目标机无版本目录并存，回滚依赖 DEPLOY-001 锚点；小程序上传不可撤回，故只构建不自动上传。
