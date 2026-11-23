<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T18:10:00+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>.github/workflows/ci.yml</file><file>.trae/sdlc/project_profile.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file><file>project_workspace/ocap_history_expense_import/development/implementation_plan.md</file><file>project_workspace/ocap_history_expense_import/testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — CI/CD 流水线

## 现状与影响

- 现有 CI：`.github/workflows/ci.yml`，三个 job：`backend`（Python 3.13 + MySQL client 依赖 → `manage.py check` → 全量测试）、`frontend`（Node 20 → `npm ci` → 主题定义严格检查 → vitest → 生产构建）、`miniprogram`（Node 20 → vitest）。
- 本次改动影响：
  - 后端新增 MOD-192~197 与 0004 迁移、27 条后端测试：被现有 `manage.py test` 自动纳入，无需改 workflow。
  - 前端新增 `HistoricalExpenses.vue`、路由/API/报表入口与 1 个 spec：被现有 vitest 与 build 步骤自动纳入，无需改 workflow。
  - 无新增 Python/Node 依赖（`openpyxl` 已在 `backend/requirements.txt`）。
  - 无新服务、无新环境变量、无新定时任务。
- 结论：**无需修改 CI 配置**；本次仅按现有流水线执行。

## 流水线概览

[Source] → [Lint/静态检查] → [Build] → [Unit] → [Integration] → [Package] → [Deploy 测试环境] → [Smoke] → [E2E]

- 其中 Unit/Integration/E2E 由后端测试目录与前端 vitest 分层承载；部署仅到测试环境，且需用户当轮授权。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 `main`、手动 | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | 静态检查（后端） | 同上 | `python manage.py check --settings=config.test_settings` | 退出码 0 | abort-and-notify |
| PIPE-03 | 测试（后端全量） | 同上 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0；当前 1218 通过 | abort-and-notify |
| PIPE-04 | 静态检查（前端主题） | 同上 | `node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort-and-notify |
| PIPE-05 | 测试（前端） | 同上 | `npx vitest run --passWithNoTests` | 退出码 0；当前 55 文件/590 通过 | abort-and-notify |
| PIPE-06 | 构建（前端） | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，`dist/index.html` 存在 | abort-and-notify |
| PIPE-07 | 测试（小程序） | 同上 | `npx vitest run --passWithNoTests` | 退出码 0 | abort-and-notify |
| PIPE-08 | 部署（测试环境） | **用户当轮授权**后由 PM 触发 | 见 `deployment_plan.md` | 全部 DEPLOY 成功且验证通过 | 按计划逆序回滚 |
| PIPE-09 | 部署后冒烟 | 随 PIPE-08 | 见 `deployment_plan.md`“部署后验证” | 全部通过 | 回滚或由用户决定 |

> CI 不含部署（画像 P7：CI 只跑测试与构建）。失败处理仅 abort-and-notify，不允许跳过失败继续部署。

## 环境矩阵

| 配置项 | 测试环境 |
|---|---|
| 主机 | 树莓派：外网 `yangyang@47.109.197.217:57279`（ED25519 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`）；内网 `yangyang@192.168.31.51:22` |
| 实例数 | 单实例（gunicorn `127.0.0.1:9000`，systemd `ocap-backend`） |
| 资源 | 磁盘 ≥ 2 GB、内存 ≥ 500 MB 可用（部署预检） |
| 外部依赖 | MySQL `192.168.31.98:3306` 库 `ocap`；短信 console 替身；微信未配置 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（只读引用，不打印内容） |
| 部署需确认 | 是（用户当轮明确授权） |
| 前端入口 | 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/` |

生产环境：画像 P7 中不存在，不设计晋升。

## 制品管理

- 存储位置：无制品库，**目标机本地构建/解包**（后端 tar 解包，前端在开发机构建后上传 dist）。
- 命名：`/tmp/ocap_backend.tar.gz`、`/tmp/frontend_dist.tar.gz`；回滚锚点 `backend-<TS>.tar.gz`、`web-<TS>.tar.gz`（`TS=YYYYMMDDHHMMSS`）。
- 版本标识：`git rev-parse HEAD` + `git status --short` 摘要（目标机无 git；未授权 push 时以本地工作树为准）。
- 晋升条件：测试环境无晋升概念；部署前必须满足 CI 全绿 + 用户当轮授权。
- 风险：无制品签名/校验和；tar 解包只覆盖不删除旧文件（历史已移除文件可能残留）。
