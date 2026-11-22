<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T19:57:32+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap_approval_flow/architecture/module_design.md</file>
    <file>project_workspace/ocap_approval_flow/development/implementation_plan.md</file>
    <file>project_workspace/ocap_approval_flow/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_approval_flow/testing/integration_test_report.md</file>
    <file>project_workspace/ocap_approval_flow/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — 审批流程多步化与或/与签（ocap_approval_flow）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，push/PR 到 `main` 触发，含 3 个 job：

| Job | 步骤 | 命令 |
|---|---|---|
| `backend` | Django system check + 全量测试 | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` |
| `frontend` | 主题检查、vitest、生产构建 | `node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） |
| `miniprogram` | 安装依赖、vitest | `npx vitest run --passWithNoTests` |

本次改动对 CI 的影响：

- 后端新增 `backend/tests/integration/test_approval_flow_steps.py`（19 条）与 1 个迁移，`backend` job 的全量测试自动收集，**无需改配置**（M-DE-044）。
- Web 新增 `frontend/tests/approval_steps_ui.spec.js`（5 条）与组件，`frontend` job 的 vitest glob 自动收集，**无需改配置**。
- 小程序新增 `miniprogram/tests/approval_flow_contract.spec.js`（3 条）与 2 个页面，`miniprogram` job 自动收集，**无需改配置**。
- 无新增依赖、无新增环境变量、无新增服务；不使用 Docker（画像 P8）。
- **CO-001 结论**：`miniprogram` job 只跑测试，不跑小程序构建；仓库的小程序根目录就是 `miniprogram/`（`manifest.json` 在根，无 `src/`）。`npm run build:mp-weixin` 必须显式设置 `UNI_INPUT_DIR=<repo>\miniprogram`，否则 uni-app 默认查找 `src/manifest.json` 而失败。本批次已在开发机按该方式验证：`DONE Build complete.`、`EXIT=0`、产物 `app.json` 存在（输出指向 `%TEMP%\ocap_mp_build_check`，未写入仓库）。CI 不需要为此改动；小程序上传仍由人工在微信开发者工具完成。

## 流水线概览

[Source] → [Django check] → [Build Web] → [Test backend] → [Test Web] → [Test mini] → [Package] → [Deploy 测试环境（用户授权）] → [Smoke] → [E2E-替代]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| PIPE-02 | Django 检查 | PIPE-01 通过 | `python manage.py check --settings=config.test_settings`（`backend/`） | 退出码 0，无 `core.W` 未注册引用告警 | abort |
| PIPE-03 | Web 构建 | PIPE-01 通过 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`（`frontend/`） | 退出码 0，生成 `dist/` | abort |
| PIPE-04 | 后端测试 | PIPE-02 通过 | `python manage.py test --settings=config.test_settings -v 2` | 零新增失败（基线：`test_tc_int_964` 预存在失败） | abort |
| PIPE-05 | Web 测试 | PIPE-03 通过 | `npx vitest run --passWithNoTests`（`frontend/`） | 零新增失败；本批 581 条通过 | abort |
| PIPE-06 | 小程序测试 | PIPE-01 通过 | `npx vitest run --passWithNoTests`（`miniprogram/`） | 零新增失败；本批 151 条通过 | abort |
| PIPE-07 | Package | PIPE-04/05/06 全绿 + 用户确认提交推送 | 见 `deployment_plan.md` DEPLOY-002 | 制品 SHA256 已记录；制品含提交号与 `TS` | abort（不上传） |
| PIPE-08 | Deploy 测试环境 | E2 invocation 含用户本轮授权 | 见 `deployment_plan.md` | 每个 DEPLOY 命中预期 | 按计划回滚 |
| PIPE-09 | Smoke | PIPE-08 完成 | 只读 curl、文件存在性、`manage.py shell` schema 检查 | 全部通过 | 触发回滚 |
| PIPE-10 | E2E（替代） | PIPE-09 通过 | 多步审批 API 端到端用例（已在 PIPE-04 执行） | 端到端旅程通过 | abort-and-notify |

失败处理只允许 abort-and-notify（CI）或按部署计划回滚（PIPE-08）；禁止跳过失败继续部署。

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 `192.168.31.51`（用户 `yangyang`，免密 SSH） | 同左，经 frp |
| 入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 后端 | systemd `ocap-backend`（gunicorn `127.0.0.1:9000`） | 同左 |
| 数据库 | MySQL `192.168.31.98:3306`，独立库 `ocap`（自签证书） | 同左 |
| Web 静态目录 | `/home/yangyang/ocap/web/ocap` | 同左 |
| 计划任务 | 如存在 `ocap-run-due-jobs.timer`，停服窗口内一并停止并在启动后恢复（PRE-05 记录） | 同左 |
| 实例数 / 资源 | 单实例；资源以目标机实际为准（画像 P7 未登记数值，不自行假设） | 同左 |
| 部署方式 | tar → scp → 解包 → 迁移 → systemd 重启（画像 P7） | 同左 |
| 部署需用户确认 | 是 | 是 |

生产环境不存在（画像 P7）；不使用 Docker/容器；不改动 Freeark 的端口、服务名、目录与数据库库名。

## 制品管理

- 存储位置：无制品库。后端与 Web 在开发机打包为 tar，上传到目标机 `/tmp` 后暂存解包；Web 替换 `/home/yangyang/ocap/web/ocap`。
- 命名：`backend_<short-sha>_<TS>.tar.gz`、`frontend_dist_<short-sha>_<TS>.tar.gz`；`<short-sha>` = 待部署提交的短哈希，`<TS>` = 目标机锚点时间戳（`yyyyMMddHHmmss`）。
- 排除项：后端包排除 `venv`、`var`、`.env`、`.env.*`、`__pycache__`、`db.sqlite3`，保证不覆盖目标机本地状态。
- 小程序：仅本地构建产物（`UNI_OUTPUT_DIR` 指向临时目录或本地 `dist`），不进入目标机；上传微信体验版由人工在微信开发者工具确认后执行，不在自动部署内。
- 晋升条件：CI 全绿（PIPE-04~06）→ GROUP_D 门控 PASS → 用户确认提交并推送 → E2 收到用户本轮明确授权。
- 风险：目标机无版本目录并存，依赖锚点快照回滚；小程序上传不可撤回，故只构建不自动上传。
