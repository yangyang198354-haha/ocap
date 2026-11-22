<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T12:58:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_navigation_ia/development/implementation_plan.md</file>
    <file>project_workspace/ocap_navigation_ia/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — 导航信息架构整合

## 现状与影响

- 现有 CI：`.github/workflows/ci.yml`，三个 job（backend / frontend / miniprogram），触发 `push main`、`pull_request main`、`workflow_dispatch`；只测试与构建，不部署。
- 本次改动对 CI 的影响：
  - 后端 job：仅测试文件变化（契约测试改为“宿主+拆分目录”并集），命令与依赖不变，**无需修改**。
  - 前端 job：新增 `frontend/tests/navigation_ia.spec.js`，`npx vitest run --passWithNoTests` 会自动纳入；`npm run build -- --base=/ocap/` 已存在，**无需修改**。
  - 小程序 job：新增 `miniprogram/tests/navigation_ia.spec.js`，`npx vitest run` 自动纳入；**测试无需修改**。
- 建议（未直接修改 CI，`[INFERRED]`）：小程序 job 目前只跑测试、不构建。建议后续追加可选步骤（需项目负责人确认后再改 CI）：
  `UNI_INPUT_DIR=${{ github.workspace }}/miniprogram npm run build:mp-weixin`，成功标准为 `DONE Build complete.`。
- 结论：本批次不修改 CI 配置。

## 流水线概览

[Source] → [Lint/静态检查] → [Build] → [Unit] → [Integration] → [Package] → [Deploy 测试环境] → [Smoke] → [E2E]

本次实际执行形态（沿用现有 CI + 本地部署）：

- `backend` job：`manage.py check` → 全量 Django 测试。
- `frontend` job：`npm ci` → 主题定义 check → vitest → Vite build。
- `miniprogram` job：`npm install` → vitest。
- 部署：开发机构建 → tar → scp → 目标机解包 → 目录交换（无后端重启、无迁移）。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 main | checkout | 工作区干净 | abort-and-notify |
| PIPE-02 | 静态检查 | 同 PIPE-01 | `cd backend && python manage.py check --settings=config.test_settings`；`node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端测试 | 同 PIPE-01 | `cd backend && python manage.py test --settings=config.test_settings -v 2` | 全部 OK（基线 1167） | abort-and-notify |
| PIPE-04 | 前端测试 | 同 PIPE-01 | `cd frontend && npx vitest run --passWithNoTests` | 全部通过（基线 575） | abort-and-notify |
| PIPE-05 | 前端构建 | PIPE-04 通过 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，`dist/index.html` 存在 | abort-and-notify |
| PIPE-06 | 小程序测试 | 同 PIPE-01 | `cd miniprogram && npx vitest run --passWithNoTests` | 全部通过（基线 147） | abort-and-notify |
| PIPE-07 | 小程序构建（本地/可选） | 本地发布前 | `$env:UNI_INPUT_DIR='<repo>\\miniprogram'; npm run build:mp-weixin` | `DONE Build complete.` | abort-and-notify |
| PIPE-08 | 制品归档（可选） | PIPE-05 后 | `tar -czf frontend_dist_<TS>.tar.gz -C frontend/dist .` + `sha256sum` | SHA256 已记录 | abort-and-notify |
| PIPE-09 | 部署测试环境 | 用户单独授权（E2） | 见 `deployment_plan.md` | 全部 DEPLOY 成功 | 按计划回滚 |
| PIPE-10 | 部署后冒烟 | DEPLOY 完成 | 见 `deployment_plan.md` 验证清单 | 全部通过 | 按计划回滚或按人工决定 |
| PIPE-11 | E2E | 冒烟通过 | 人工验证清单 MV-01~MV-04（或后续接入浏览器 E2E） | 与 e2e_test_report 一致 | 记录问题，不阻断已发布静态资源 |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 `192.168.31.51`（用户 `yangyang`，免密 SSH） | 同一主机，经 Freeark frp |
| 服务 | gunicorn `127.0.0.1:9000`（`ocap-backend`）+ nginx `8090` | 复用 Freeark nginx `^~ /ocap/` → `8090` |
| 数据库 | MySQL `192.168.31.98:3306` / 库 `ocap`（本次不迁移） | 同上 |
| 访问入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 外部依赖 | Freeark 服务（不得重启/改配置） | 同左 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（不读取其值） | 同左 |
| 部署需用户确认 | 是 | 是 |

生产环境：画像 P7 中不存在，本流水线不设计生产晋升。

## 制品管理

- 存储位置：开发机构建 + 目标机 `/home/yangyang/ocap/web/ocap`（不设独立制品库）。
- 命名：`frontend_dist_<TS>.tar.gz`，`<TS>=yyyyMMddHHmmss`；同时记录 `SHA256`。
- 晋升条件：CI 三 job 全绿 + 用户部署授权（E2）+ 远端提交哈希与本地一致。
- 风险：无制品库，回滚依赖目标机快照与保留的 `ocap.old.<TS>` 目录；需保留 ≥ 7 天。
