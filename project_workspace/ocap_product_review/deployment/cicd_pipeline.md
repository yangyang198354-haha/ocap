<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-14T09:55:00+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/integration_test_report.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>phase_status.md</file>
    <file>../ocap_admin_polish/deployment/deployment_plan.md</file>
    <file>../ocap_admin_polish/deployment/deployment_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 说明：产品评审修正（INCREMENTAL）

> 本批已有 CI（`.github/workflows/ci.yml`，GitHub Actions，画像 P7）。本文只描述本次改动对 CI 的影响，不重建流水线，**不修改任何 CI 文件**。CI 只跑测试与构建，不部署；部署由开发机/E2 按 `.claude/skills/ocap-deploy/SKILL.md` 手动执行（画像 P7、P9）。

## 现状与影响

现有 CI 三个 job（均在 push/PR 到 `main` 与 `workflow_dispatch` 触发；`concurrency` 取消同分支旧运行）：

| job | 现有步骤 | 本次改动的影响 |
|---|---|---|
| backend | Python 3.13 → 装 MySQL 客户端头文件 → `pip install -r requirements.txt` → `manage.py check --settings=config.test_settings` → `manage.py test --settings=config.test_settings -v 2` | 新增测试文件（`tests/unit/test_product_review_rules.py`、`tests/integration/test_product_review_{api,ac,gap_stories,rework1,rework2}.py`、`test_e2e_fixture_command.py`、`test_migration_residency_0002.py`、`test_requirements_numbering.py`、`tests/e2e/test_product_review_{journeys,content}.py`）均匹配默认 `test*.py`，**会被现有命令自动收集**，无需改命令。本地基线：全量 712（unit 162 + integration 497 + e2e 47 + smoke 6）。 |
| frontend | Node 20 → `npm ci` → 主题检查 `node scripts/themes/build.mjs --strict --check` → `npx vitest run --passWithNoTests` → `npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 新增 `frontend/tests/product_review_*.spec.js` 自动收集；本地基线 vitest 244/244。`package.json`、`package-lock.json` 未改动（`git status` 核实），无新依赖。 |
| miniprogram | Node 20 → `npm install --legacy-peer-deps` → `npx vitest run --passWithNoTests` | 新增 `miniprogram/tests/product_review_*.spec.js` 自动收集；本地基线 94/94。CI 无小程序构建步骤（`uni build` 在开发机工具链上未验证，GR-C-001-F02），属既有缺口。 |

逐项影响核对：

| 项 | 结论 |
|---|---|
| 新增依赖 | 无。`requests` 已在 `backend/requirements.txt:3`（远程套件使用）；`backend/requirements.txt`、前端/小程序 `package*.json` 无改动。 |
| 新测试层 | 有：远程 HTTP E2E（`backend/tests/remote/{remote_client,remote_cases,run_remote}.py`）。文件名不匹配 `test*.py`，`manage.py test` 默认不收集（E2E 报告：全量 712 不含 22 条远程用例）。**远程套件不应在 CI 运行**：它只允许访问 `https://ai-freeark.xin/…`，依赖已在测试机创建的 `e2e_` 夹具与 `OCAP_E2E_PASSWORD`，CI 中不设这些环境变量时 `run_remote.py` 退出码 2 且不发请求；且画像 P4-1 限定"仅部署后、由 E2 执行"。 |
| 新服务 / 新环境变量 | 无（CI 不涉及测试机）。运行期新增的 `OCAP_E2E_FIXTURE`、`OCAP_E2E_PASSWORD`、`OCAP_E2E_BASE_URL`、`OCAP_E2E_SLOW` 只在 E2 手工执行时使用，**不写入 CI、不作为仓库 secret**；`OCAP_E2E_ALLOW_LOCAL` 仅本地自检用。 |
| 迁移 | `residency/0002_closed_status`（手写，仅 choices）。CI 以 `MIGRATION_MODULES` 置空运行，不执行迁移；迁移正反向由 `test_migration_residency_0002.py` 用 `tests/migration_settings.py`（临时 SQLite 文件库，子进程）验证，随 backend job 一起跑，无需额外服务。 |
| 文档扫描类用例 | `test_requirements_numbering.py` 读取仓库内 `project_workspace/*/requirements`；其中 TC-INT-485 用 `git show afa1fe8:…` 对比基线原文，`actions/checkout@v4` 默认浅克隆（深度 1）时该用例按 `skipUnless` **跳过**（不会失败）。因此 CI 的 skip 数可能比本地多 1。要在 CI 真正执行需 `fetch-depth: 0`（见可选项 O-2）。**不要给 CI 加 `paths-ignore: project_workspace/**`**，否则需求文档改动不再触发这类扫描。 |
| Python 版本差异 | 本批全部测试结果来自 Python 3.12.3 / Django 5.2.19（画像 P4：本机无 3.13）；CI 使用 Python 3.13。本批首次 push 将是这套测试在 3.13 上的首次运行，`[INFERRED]` 风险低（无新依赖），以 CI 首次运行结果为准；失败时按 abort-and-notify 处理，不跳过。 |
| 既有 CI 缺口（不新增，仅登记） | ① `--passWithNoTests` 对无用例包会掩盖缺失（M-DE-004；本批前端/小程序均有用例，不受影响）；② CI 无 `python -m compileall -q backend` 与 `makemigrations --check --dry-run` 步骤（画像 P4 已登记命令但 CI 未使用）；③ 无小程序构建。 |

**结论：本次无需修改 `ci.yml`。** 可选改进（不在本次实施，需 module_design 或 PM 明确要求后才改动画像 P7 的 CI 文件）：

| 编号 | 可选项 | 理由 | 风险 |
|---|---|---|---|
| O-1 | backend job 增加步骤 `python manage.py makemigrations --check --dry-run --settings=config.test_settings`（Django 5.2.x，P4 命令） | 防迁移漂移与 makemigrations 产物混入（P6） | 注意 `test_settings` 置空迁移，可检测范围有限（已知 OBS-3：启用迁移时 content 应用存在漂移，见集成报告），启用前先确认退出码为 0 |
| O-2 | backend job 的 checkout 增加 `fetch-depth: 0` | 使 TC-INT-485 在 CI 真正执行而非跳过 | 克隆变慢（仓库体量小，影响有限） |
| O-3 | backend job 增加 `python -m compileall -q backend` | 画像 P4"静态检查"，目前 CI 没有任何 lint | 无 |

## 流水线概览

```
CI（GitHub Actions，自动）
[Source: push/PR main]
   ├─► [Backend] check → 全量测试(unit+integration+e2e+smoke)
   ├─► [Frontend] 主题检查 → vitest → build(--base=/ocap/)
   └─► [Miniprogram] vitest

开发机/E2（手动，不在 CI）
[本地预检复跑] → [Package: tar + SHA256] → [Deploy: ocap-deploy, 测试环境]
   → [部署后冒烟(只读)] → [远程 HTTP E2E: 夹具 setup → run_remote → 夹具 cleanup]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source（CI） | push/PR 到 `main`、手动 `workflow_dispatch` | `actions/checkout@v4` | 检出成功 | abort-and-notify（作业失败） |
| PIPE-02 | Backend 系统检查（CI） | PIPE-01 | `cd backend && python manage.py check --settings=config.test_settings` | 退出码 0、`no issues` | abort-and-notify，不进入测试 |
| PIPE-03 | Backend Unit+Integration+E2E+Smoke（CI） | PIPE-02 | `cd backend && python manage.py test --settings=config.test_settings -v 2` | 退出码 0；本地基线 712 条全过（CI 可能有 ≥1 条 skip，见上） | abort-and-notify；不自动重试（测试失败不属于瞬时故障） |
| PIPE-04 | Frontend 主题检查（CI） | PIPE-01 | `node scripts/themes/build.mjs --strict --check`（仓库根） | 退出码 0（定义校验通过、生成物无漂移） | abort-and-notify |
| PIPE-05 | Frontend 单测（CI） | PIPE-04 | `cd frontend && npx vitest run --passWithNoTests` | 退出码 0；本地基线 244/244 | abort-and-notify |
| PIPE-06 | Frontend 构建（CI） | PIPE-05 | `cd frontend && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0（chunk>500kB 体积警告为既有，不算失败） | abort-and-notify |
| PIPE-07 | Miniprogram 单测（CI） | PIPE-01 | `cd miniprogram && npx vitest run --passWithNoTests`（依赖 `npm install --legacy-peer-deps`） | 退出码 0；本地基线 94/94 | abort-and-notify；依赖安装失败可有限重试 1 次（网络类），其余不重试 |
| PIPE-08 | 本地预检复跑（开发机/E2，手动） | 用户授权部署前 | 见 deployment_plan PRE-002：`check`、`compileall`、`makemigrations --check --dry-run`、后端全量、前端 vitest + 构建、小程序 vitest | 与 GR-D-003 基线一致（712 / 244 / 94，零失败，迁移无漂移） | **停止部署**，上报 PM；不得"跳过失败继续部署" |
| PIPE-09 | Package（开发机，手动） | PIPE-08 通过 | 后端：`git archive "$COMMIT:backend"`（或经用户确认的工作区 tar）；前端：`npm ci` + `npm run build -- --base=/ocap/` 后 tar `dist/`；`sha256sum` | 包可列出，不含 `venv/`、`.env`、`var/`；SHA256 已记录 | 停止并上报 |
| PIPE-10 | Deploy 测试环境（E2，手动） | E1 已批准 + 用户当轮授权（画像 P7"部署需用户确认=是"） | deployment_plan 的 DEPLOY-001 ~ 007 | 各步预期满足 | 失败且目标机已有变更 → 逆序执行 ROLLBACK；目标机无变更 → `DEPLOYMENT_FAILED` |
| PIPE-11 | 部署后冒烟（E2，只读） | PIPE-10 | deployment_plan DEPLOY-008（V-01 ~ V-16） | 关键项全部通过 | 关键项失败 → 视为 DEPLOY-008 失败并回滚；非关键项 → `DEPLOYED_WITH_ISSUES` 交用户决定 |
| PIPE-12 | 远程 HTTP E2E（E2，手动，画像 P4-1） | PIPE-11 通过 + 夹具确认事项已获用户确认 | 夹具 `setup` → `backend/tests/remote/run_remote.py` → 夹具 `cleanup --execute` | 22 条中 20 通过、0 失败、skipped=2（TC-E2E-328/332 的 SKIP 条件见 e2e_test_report）；清理后 e2e 计数 0、清册计数不变 | 失败不回滚代码；**无论成败都执行清理**；失败用例记入 deployment_report，缺陷回流 GROUP_C |

PIPE-01 ~ PIPE-07 为现有 CI；PIPE-08 ~ PIPE-12 不在 CI 中（画像 P7：CI 不部署）。

## 环境矩阵

只列画像 P7 中存在的环境。

| 配置项 | CI（GitHub runner，仅测试） | 测试（树莓派，唯一部署目标） | 生产 |
|---|---|---|---|
| 存在性 | ubuntu-latest，Python 3.13、Node 20 | 画像 P7 | **无**（不设计任何生产环节） |
| 实例数 | 每次运行独立 | 后端 1 个 systemd 服务 `ocap-backend`（gunicorn 127.0.0.1:9000，进程数以现有单元为准）；`ocap-content-worker` 1 个（若已安装，MemoryMax 400M）；`ocap-run-due-jobs.timer` 每分钟一次性进程；无冗余 | — |
| 资源 | 通用 runner | 树莓派，与 Freeark（uvicorn:8000、nginx:80/8080、frpc）同机共存；部署前要求磁盘可用 ≥ 2 GB、可用内存 ≥ 500 MB（ocap-deploy skill） | — |
| 外部依赖 | 无（SQLite 内存库、`apps/integrations/fakes.py` 替身） | MySQL `192.168.31.98:3306` 库 `ocap`；短信 `console` 替身；微信/邮件不真实调用 | — |
| 配置来源 | `config.test_settings` | `/home/yangyang/ocap/backend/.env`（键名见画像 P7，值不入文档，部署不覆盖该文件） | — |
| 入口 | — | 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/` | — |
| 部署需用户确认 | 不适用 | **是**（须用户当轮授权，授权中写明环境名"测试"） | — |
| nginx / Freeark | — | 本批不改动（不 reload、不触碰 Freeark 服务/端口/目录/库，画像 P7、P8） | — |

## 制品管理

- 存储位置：**无制品库**。制品为开发机本地生成的 tar 包，经 scp 上传到目标机 `/tmp/` 后解包，部署后可保留本地副本；**目标机本地不构建前端**（前端在开发机构建，后端无编译步骤，仅在 requirements 变更时目标机 `pip install`，本批无变更）。
- 命名：
  - 后端包 `ocap-backend-<TS>.tar.gz`、前端包 `ocap-frontend-<TS>.tar.gz`（`TS` = DEPLOY-001 在目标机取得的 14 位时间戳）；
  - 版本标识 = 提交号（`COMMIT`，来自 `git rev-parse`）+ 两个包的 SHA256（上传前后两端各算一次比对）；若经用户确认从工作区打包，则记录 `git rev-parse HEAD`、`git status --short` 摘要与包 SHA256（ocap-deploy skill §0）；
  - 回滚快照（目标机 `/home/yangyang/ocap/snapshots/`，画像 P7）：`backend-<TS>.tar.gz`、`web-<TS>.tar.gz`，另加 `ocap-<TS>.sql.gz`（mysqldump）、`registry-counts-<TS>.txt`。保留 ≥ 7 天。
- 晋升条件：无多环境晋升（仅测试环境）。进入 Deploy 的条件 = PIPE-08 预检全部通过 + E1 已批准 + 用户授权。
- 无制品库的风险：① 包只存在于开发机与目标机 `/tmp`，丢失后只能由提交号重新生成；② 目标机无 git，回滚锚点为"快照 + SHA256 + 提交号/工作区摘要"，无法在目标机上反查提交；③ 工作区打包时包内容可能与任何提交都不一致，因此计划优先采用"已确认提交"（见 deployment_plan 待确认事项 UC-01）。
