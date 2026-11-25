<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-25T13:05:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_role_home/architecture/module_design.md</file>
    <file>project_workspace/ocap_role_home/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_role_home/development/implementation_plan.md</file>
    <file>project_workspace/ocap_role_home/testing/e2e_test_report.md</file>
    <file>.github/workflows/ci.yml</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — ocap_role_home

## 现状与影响

- 现有 CI：`.github/workflows/ci.yml`，触发 `push`/`pull_request` 到 `main` 及 `workflow_dispatch`，含 3 个 job：
  - `backend`：Python 3.13 + MySQL client → `manage.py check` → 全量 Django 测试。
  - `frontend`：Node 20 → `npm ci` → 主题校验 `node scripts/themes/build.mjs --strict --check`（仓库根）→ `npx vitest run --passWithNoTests` → `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`。
  - `miniprogram`：Node 20 → `npm install --legacy-peer-deps` → `npx vitest run --passWithNoTests`。
- 本次改动（纯前端展示层）：`frontend/src/portal/Home.vue`、`frontend/src/stores/auth.js`、`frontend/src/shared/style.css`、`miniprogram/pages/index/index.vue`、`miniprogram/store/auth.js`；测试在既有两个 `tests/` 目录内。
- 对 CI 的影响：**无需修改 CI 配置**。无新增依赖、无后端变更、无 `themes/*.theme.json` 变更；新增测试由既有 vitest 命令自动收集；主题生成物无需重跑。
- 需要用户/PM 执行的前置动作：当前工作在 `home-links` 分支，CI 只在 `main` 触发；合并/PR 到 `main` 由用户执行（子代理不提交、不推送，画像 P9）。待部署提交以合并后的 commit SHA 为准。
- 既有缺口（本计划不擅自改 CI）：CI 未构建微信小程序；本次 `npm run build:mp-weixin` 的构建验证放在本地/部署前预检执行。若后续要把小程序构建纳入 CI，需 PM/用户另行批准后新增步骤（`UNI_INPUT_DIR=. npx uni build -p mp-weixin --outDir <tmp>`）。
- 禁止项核对（画像 P8）：不使用容器、不引入新服务/新环境变量；流水线与部署均为物理机 + nginx + systemd 既有方式。

## 流水线概览

[Source] → [Theme check] → [Backend checks + tests] → [Web tests] → [Web build] → [Package Web 制品] → [Mini program tests] → [Mini program build（本地/预检）] → [Deploy 测试环境] → [Smoke] → [E2E/人工清单]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 `main` 或手动 | 平台 checkout（`actions/checkout@v4`） | 检出目标 commit | abort-and-notify |
| PIPE-02 | 主题一致性 | 每次 CI | `node scripts/themes/build.mjs --strict --check`（仓库根） | 退出码 0，生成物无漂移 | abort-and-notify（阻断后续） |
| PIPE-03 | 后端校验与测试 | 每次 CI | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` | 退出码 0 | abort-and-notify |
| PIPE-04 | Web 测试 | 每次 CI | `cd frontend`：`npm ci`；`npx vitest run --passWithNoTests` | 退出码 0；本次基线 58 files / 613 tests | abort-and-notify |
| PIPE-05 | Web 构建 | PIPE-04 通过 | `cd frontend`：`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0；`dist/index.html` 与 `dist/assets/*` 生成 | abort-and-notify |
| PIPE-06 | Web 制品打包 | PIPE-05 通过 | `tar -czf ocap-web-${DEPLOY_SHA:0:8}-$(date +%Y%m%d%H%M%S).tar.gz -C frontend/dist .`；`sha256sum` | 生成 tar + SHA256 记录；产物内 `index.html` 引用的 assets 全部存在 | abort-and-notify |
| PIPE-07 | 小程序测试 | 每次 CI | `cd miniprogram`：`npm install --no-audit --no-fund --legacy-peer-deps`；`npx vitest run --passWithNoTests` | 退出码 0；本次基线 23 files / 157 tests | abort-and-notify |
| PIPE-08 | 小程序构建（本地/预检） | 部署前 | `cd miniprogram`：`UNI_INPUT_DIR=. npx uni build -p mp-weixin --outDir <临时目录>` | 输出 `DONE Build complete.`，`app.json` 可解析 | abort-and-notify；发布动作（微信上传）不在本次范围 |
| PIPE-09 | 部署测试环境 | GROUP_E1 APPROVED；用户当轮明确授权（E2） | 见 `deployment_plan.md` 的 DEPLOY-001~006 | 全部 DEPLOY 成功且部署后验证通过 | 按 `deployment_plan.md` 回滚；禁止跳过失败继续部署 |
| PIPE-10 | 冒烟 / E2E 替代 | PIPE-09 成功 | 部署后验证清单（HTTP 200、制品文案、日志无新错误、外部可达） | 全部通过 | 失败即回滚并通知 |

## 环境矩阵

| 配置项 | 测试环境（树莓派，内网 nginx:8090） | 测试环境（外网 frp:443） | 生产环境 |
|---|---|---|---|
| 是否存在（画像 P7） | 存在 | 存在（同一目标的对外入口） | 不存在 |
| 运行单元 | nginx 静态站 + systemd `ocap-backend`（gunicorn） | 与内网同一站点，经 frp 转发 | — |
| Web 静态目录 | `/home/yangyang/ocap/web/ocap`（画像/记忆 M-DE-046） | 同左 | — |
| 本次变更 | Web 静态产物替换 | 随内网同步生效 | — |
| 后端 | 不变，不重启、不迁移 | 同左 | — |
| 数据库 | MySQL（外部依赖），本次无迁移 | 同左 | — |
| 配置来源 | 目标机 `.env`（不读取、不写入内容） | 同左 | — |
| 必须保留的本地状态 | `.env`、`venv/`、`var/`、目标机本地数据与日志 | 同左 | — |
| 部署需用户确认 | 是（画像 P7） | 是 | — |
| 实例数 / 资源 | 单实例；磁盘需 ≥ 200 MB 临时空间 [INFERRED] | 同左 | — |

## 制品管理

- 存储位置：无制品库；在开发机/CI 构建，tar 上传至目标机 `/home/yangyang/ocap/tmp/`，保留最近 2 个版本供回滚。
- 命名：`ocap-web-<commit 前 8 位>-<YYYYmmddHHMMSS>.tar.gz`；同名 `.sha256` 记录校验和。
- 内容：仅 `frontend/dist` 内容（`index.html`、`assets/`、静态资源），不含源码、`.env`、`node_modules`。
- 晋升条件：PIPE-02~07 全绿 + GROUP_D 测试门控 APPROVED + 用户当轮 E2 明确授权 + 目标环境名与 `deployment_plan.md` 一致。
- 小程序：本地构建产物仅用于验证 `DONE Build complete.` 与 `app.json` 可解析；上传发布由用户通过微信开发者工具执行（RU-4，不在 E1/E2 范围）。
- 风险：本地构建与 CI 构建存在 Node/依赖差异 → 以 `package-lock.json` 为准，记录 `node -v`/`npm -v` 与制品 SHA256；目标机不做构建（避免本地状态被触碰）。
