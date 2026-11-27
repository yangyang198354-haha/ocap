<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-27T10:18:09.8607259+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>testing/integration_test_report.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>.github/workflows/ci.yml</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — 审批与同住人申请历史记录

## 现状与影响

- 现有 `.github/workflows/ci.yml` 在 `main` 的 push、PR 与手动触发时运行三个并行 job：`backend`、`frontend`、`miniprogram`；CI 不部署。
- 后端 job 已执行 `manage.py check --settings=config.test_settings` 与全量 Django 测试，因此自动收集 `backend/tests/integration/test_approval_history.py`。
- 前端 job 已执行主题一致性检查、全量 `npx vitest run --passWithNoTests` 和生产构建，因此自动收集本批 3 个新测试文件及扩展后的契约测试。
- 本批无新增依赖、服务、环境变量、主题定义、小程序改动或数据库迁移；**无需修改 CI 配置**。
- 最终本地证据：后端 1266 条（1264 pass、2 skip、0 fail），前端 64 文件/639 条全部通过，Web 1887 modules transformed 并构建成功。critical path 4/4 覆盖、2/2 通过。
- commit/push/合并到 `main` 由用户确认后按画像 P9 执行；子代理与本计划均不执行这些操作。
- 禁止项核对：不使用容器、不使用 pscp、不生成全量迁移、不让测试连接生产数据库；画像中无生产环境。

## 流水线概览

[Source] → [Backend / Web / Mini program 现有 CI 并行] → [本地分层与 critical path 已批准] → [人工制品打包] → [用户当轮授权] → [DEPLOY 测试（内网）] → [Smoke / 人工复核]

说明：制品打包与部署不加入 GitHub Actions，保持画像“CI 只跑测试与构建，不部署”的既有边界。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push/PR 到 `main` 或手动 | `actions/checkout@v4` | 检出待验 commit | abort-and-notify |
| PIPE-02 | Backend | 每次 CI | `backend/`：`python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` | 两命令退出码 0；新增 7 条后端历史用例被收集并通过 | abort-and-notify |
| PIPE-03 | Web 测试 | 每次 CI | 仓库根主题检查 `node scripts/themes/build.mjs --strict --check`；`frontend/`：`npm ci`；`npx vitest run --passWithNoTests` | 退出码 0；新增 UNIT 2、页面 INT 4、E2E 2 及契约用例均通过 | abort-and-notify |
| PIPE-04 | Web 构建 | PIPE-03 通过 | `frontend/`：`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0；生成 `dist/index.html` 与 `dist/assets/` | abort-and-notify |
| PIPE-05 | Mini program 回归 | 每次 CI，虽本批无小程序改动 | `miniprogram/`：既有依赖安装与 `npx vitest run --passWithNoTests` | 退出码 0；不构建、不发布小程序 | abort-and-notify |
| PIPE-06 | 制品打包（部署计划，非 CI） | GROUP_D APPROVED；隔离的 `REF` 源码检查通过 | 见 `deployment_plan.md` DEPLOY-002～004；后端 `git archive`，前端本地构建后 tar + SHA256 | 两端制品与校验和齐全；来源均为同一 `REF`，不混入无关工作树改动 | abort-and-notify |
| PIPE-07 | 部署测试（内网） | GROUP_E1 APPROVED 且用户当轮明确授权该环境 | 见 `deployment_plan.md` DEPLOY-001～005 | 全部 DEPLOY 与验证成功 | 立即停止后续步骤并按 ROLLBACK 逆序恢复；禁止跳过失败继续 |
| PIPE-08 | Smoke / E2E 人工复核 | PIPE-07 完成 | 部署后验证 V-01～V-12 | 服务、路由、页面、权限与关键旅程符合标准 | 服务/数据/权限失败即回滚；视觉问题保留现场并回流 |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机与入口 | 树莓派 `192.168.31.51`，nginx `8090`，`http://192.168.31.51:8090/ocap/` | 同一树莓派，经既有 frp/nginx，`https://ai-freeark.xin/ocap/` |
| 后端 | systemd `ocap-backend`，gunicorn `127.0.0.1:9000`；本批需重启 | 与内网共用服务 |
| Web | `/home/yangyang/ocap/web/ocap`；本批替换静态产物 | 同一目录，经既有 `^~ /ocap/` 反代 |
| 数据库 | 独立 MySQL `ocap`；本批无迁移、无写入结构变更 | 同左 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`；只核验存在与哈希，不读取或输出内容 | 同左 |
| 本地状态 | 保留 `.env`、`venv/`、`var/`、日志与业务数据；后端代码快照排除这些运行状态 | 同左 |
| 同机约束 | 不占用或重启 Freeark 的 80/8000/8080、`freeark-*` 服务与代码；不改 nginx | 同左 |
| 部署需用户确认 | 是；本计划默认目标仅为“测试（内网）” | 是；只有授权也明确包含“测试（外网）”时才执行外网复验 |

## 制品管理

- 无独立制品库；在隔离且干净的 `REF` 工作树构建，开发机临时目录保存 tar 与 SHA256，上传目标机 `/tmp/`，目标快照位于 `/home/yangyang/ocap/snapshots/`。
- 命名：`ocap-approval-history-<完整REF>-<TS>-backend.tar.gz`、`...-web.tar.gz`；另记录 `REF`、制品 SHA256、目标快照 SHA256。
- 后端包由 `git archive ${REF}:backend` 生成，不含 `.env`、`venv/`、`var/` 或无关未提交内容；Web 包只含该 `REF` 的 `frontend/dist` 内容。
- 晋升条件：GROUP_D/GROUP_E1 APPROVED、相关 CI 成功、预检全部通过、用户当轮授权与计划目标环境完全一致。
- 风险：本地与 CI 运行时可能不同；以 lockfile 和同一 `REF` 为准，记录 Node/Python 版本、测试结果与 SHA256。快照和旧静态目录保留，不在本计划自动清理。
