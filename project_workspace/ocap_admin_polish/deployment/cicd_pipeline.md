<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T23:37:44.2269690+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：管理端打磨（INCREMENTAL）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，触发 `push main`、`pull_request main`、`workflow_dispatch`；三个 job：

| Job | 覆盖内容 | 本次是否需改 |
|---|---|---|
| `backend` | Python 3.13、安装 `backend/requirements.txt`、`manage.py check --settings=config.test_settings`、`manage.py test --settings=config.test_settings -v 2` | 否（新增测试自动被发现） |
| `frontend` | Node 20、`npm ci`、`node scripts/themes/build.mjs --strict --check`、`npx vitest run --passWithNoTests`、`npm run build -- --base=/ocap/` | 否（主题源与生成物同步、测试与构建均覆盖） |
| `miniprogram` | Node 20、`npm install --legacy-peer-deps`、`npx vitest run --passWithNoTests` | 否（本次小程序零改动） |

本次改动的影响：新增后端测试 31 个（自动发现）、前端测试 24 个（vitest 自动发现）、两个手写迁移（由测试直接调用或在目标机执行，CI 不跑迁移）、主题源文件与生成物同时变更（`build.mjs --check` 会校验生成物未漂移）。**结论：CI 无需修改。**

## 流水线概览

[Source] → [Backend check + Unit/Integration/E2E] → [Frontend theme check + tests + build] → [Miniprogram tests] → [制品：git archive + dist tar] → [Deploy（人工授权，E2）] → [Smoke] → [人工视觉走查]

CI 只测不部署（画像 P7）；部署由 E2 在用户授权后按 `deployment_plan.md` 执行。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 后端系统检查 | push/PR | `cd backend && python manage.py check --settings=config.test_settings` | 退出码 0、无 issue | abort-and-notify |
| PIPE-02 | 后端全量测试 | PIPE-01 通过 | `cd backend && python manage.py test --settings=config.test_settings -v 2` | `OK`，零失败（允许既有 skip=9） | abort-and-notify |
| PIPE-03 | 主题定义与生成物校验 | push/PR | `node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort-and-notify |
| PIPE-04 | 前端测试 | PIPE-03 通过 | `cd frontend && npx vitest run --passWithNoTests` | 181 passed / 0 failed | abort-and-notify |
| PIPE-05 | 前端生产构建 | PIPE-04 通过 | `cd frontend && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，`dist/index.html` 生成 | abort-and-notify |
| PIPE-06 | 小程序测试 | push/PR | `cd miniprogram && npx vitest run --passWithNoTests` | 75 passed / 0 failed | abort-and-notify |
| PIPE-07 | 制品打包（部署时） | 用户授权 E2 | `git archive <COMMIT>:backend` + 前端 `dist` tar；记录 SHA256 | 两个 tar 的 SHA256 有输出且两端一致 | abort-and-notify |
| PIPE-08 | 部署 | E2 授权 | 见 `deployment_plan.md` DEPLOY-001~008 | 每步预期满足 | 按计划回滚 |
| PIPE-09 | 部署后冒烟 | PIPE-08 成功 | 见 `deployment_plan.md` V-01~V-08 | 全部通过或列出失败项 | 由用户决定回滚 |
| PIPE-10 | 人工视觉走查 | PIPE-09 后 | `testing/test_plan.md` M-01~M-05 | 15 页 × 3 风格与 OQ-11 确认 | 记录问题，必要时回流 |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 192.168.31.51（用户 yangyang） | 同上，经 frp |
| 后端 | systemd `ocap-backend` + gunicorn 127.0.0.1:9000 | 同左 |
| Web | nginx 8090，路径 `/ocap/` | VPS 443 + nginx `^~ /ocap/` 反代 |
| 数据库 | MySQL 192.168.31.98:3306 / 库 `ocap` | 同左 |
| 前端构建 | 开发机/CI：`npm run build -- --base=/ocap/` | 同左 |
| 部署需用户确认 | 是 | 是 |
| 生产环境 | 画像 P7 中不存在 | — |

## 制品管理

- 后端：`git archive "$COMMIT":backend` 生成 `ocap-backend-$TS.tar.gz`；只从已推送 commit 生成，不打包工作区。
- 前端：开发机 `npm run build -- --base=/ocap/` 后打 `ocap-frontend-$TS.tar.gz`（`dist/` 内容）。
- 存储：开发机 `/tmp` → 目标机 `/tmp`；回滚快照 `/home/yangyang/ocap_snapshots/$TS/`。
- 命名：`<组件>-$TS.tar.gz`，`TS` 为部署开始时间；记录 SHA256，上传前后各算一次。
- 晋升条件：CI 全绿 + 用户明确授权 E2 + 预检通过；无中央制品库，目标机本地保留上一版快照作为回滚锚点（画像 P7 既有约定）。

## 本次不需要的 CI 变更

- 不新增依赖、不新增 job、不改 Node/Python 版本。
- 迁移不进入 CI 执行路径（测试库 `MIGRATION_MODULES` 置空，迁移函数由测试直接调用），与既有约定一致。
- 若日后希望 CI 校验迁移文件语法，可加 `python -m compileall`（已在本地自验证中执行），本次不改 CI。
