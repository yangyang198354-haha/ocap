<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T11:04:22+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap_appeal_center/architecture/module_design.md</file>
    <file>project_workspace/ocap_appeal_center/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：申诉与同住人申请记录中心

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，3 个 job：

- `backend`：`python manage.py check --settings=config.test_settings` + `python manage.py test --settings=config.test_settings -v 2`。
- `frontend`：主题定义检查 → `npx vitest run --passWithNoTests` → `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`。
- `miniprogram`：安装依赖 → `npx vitest run --passWithNoTests`。

本次改动对 CI 的影响：

- 后端新增测试（`backend/tests/integration/test_appeal_center_flow.py`、`backend/tests/e2e/test_appeal_center_e2e.py`）会被既有 `manage.py test` 自动收集。
- 前端新增 `frontend/tests/appeal_center_flow.spec.js` 会被既有 vitest glob 自动收集。
- 小程序仅 `miniprogram/utils/labels.js` 增加 `WITHDRAWN` 标签，既有 vitest 覆盖。
- 无新增依赖、无新测试层、无新环境变量。

**结论：无需修改 CI 配置。**

已知限制（本批不修改 CI，仅记录）：`config.test_settings` 使用 `MIGRATION_MODULES` 禁用迁移，CI 的 `backend` job 不会执行 `0006_appeal_center` 的真实 DDL；因此部署计划在目标机上增加 `sqlmigrate` 只读门控（DEPLOY-005），并要求 `makemigrations --check` 无差异。

## 流水线概览

[Source] → [Lint/主题检查] → [Build] → [Unit/Integration] → [Package] → [Deploy（人工授权）] → [Smoke] → [E2E-替代]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| P1 | Source | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| P2 | 主题检查 | 同 P1 | `node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort |
| P3 | 后端检查与测试 | 同 P1 | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings` | 1167 tests / OK (skipped=2)，零新增失败 | abort |
| P4 | 前端测试 | 同 P1 | `npx vitest run --passWithNoTests` | 50 文件 / 568 tests passed，零新增失败 | abort |
| P5 | 前端构建 | P4 通过 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，生成 `frontend/dist/` | abort |
| P6 | 小程序测试 | 同 P1 | `npm install --legacy-peer-deps`；`npx vitest run --passWithNoTests` | 既有用例全部通过 | abort |
| P7 | Package | P1~P6 通过 + 用户授权 | 本地打后端/前端 tar（含锚点 TS 与 SHA256） | SHA256 已记录且两端一致 | abort |
| P8 | Deploy（测试环境） | 用户本轮明确授权 | 见 `deployment_plan.md` | 每个 DEPLOY 命中预期 | 按计划逆序回滚 |
| P9 | Smoke | P8 完成 | 只读 curl / systemctl / 文件存在性检查 | 部署后验证清单全部通过 | 触发回滚 |
| P10 | E2E-替代 | P9 通过 | 后端多步 API 旅程用例（已在 P3 执行，TC-E2E-1615/1616） | 2/2 通过 | abort |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 192.168.31.51（用户 `yangyang`，免密 SSH） | 同左，经 frp |
| 入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 后端 | gunicorn `127.0.0.1:9000`，systemd `ocap-backend` | 同左 |
| 静态目录 | `/home/yangyang/ocap/web/ocap` | 同左 |
| 数据库 | MySQL `192.168.31.98:3306`，库 `ocap` | 同左 |
| 部署方式 | tar 打包 → scp → 解包 → migrate → systemd 重启 | 同左 |
| 部署需确认 | 是 | 是 |

生产环境不存在（画像 P7）；不使用 Docker/容器（画像 P8）；不改动 Freeark 的服务、端口、目录、库。

## 制品管理

- 存储位置：无制品库；制品先放目标机 `/tmp`，快照放 `/home/yangyang/ocap/snapshots/`。
- 命名：`ocap-backend-<TS>.tar.gz`、`ocap-frontend-<TS>.tar.gz`、`backend-<TS>.tar.gz`、`web-<TS>.tar.gz`、`ocap-<TS>.sql.gz`（`<TS>` 为 14 位时间戳）。
- 晋升条件：CI 全绿 + 测试三层门控通过（GROUP_D APPROVED）+ 用户本轮部署授权。
- 风险：目标机无制品库、无版本目录并存；回滚依赖锚点快照与数据库备份。
