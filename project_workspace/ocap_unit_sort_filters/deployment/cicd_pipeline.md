<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-16T12:49:26+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/test_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：选房排序统一、地下车位归属修正与后台清册过滤器

## 现状与影响

现有 CI：`.github/workflows/ci.yml`（GitHub Actions，push/PR 到 main）。
- `backend`：Python 3.13，`manage.py check` + 全量 Django 测试（`config.test_settings`，SQLite 内存库）。
- `frontend`：Node 20，`npm ci`，主题定义校验，vitest，生产构建（`--base=/ocap/`）。
- `miniprogram`：Node 20，`npm install --legacy-peer-deps`，vitest。

本次改动对 CI 的影响（依据 module_design「受影响的运行单元」、implementation_plan）：
- 新增后端测试 6 个文件（unit 3、integration 6 含契约、e2e 1，合计 99 条）与前端 `frontend/tests/registry_filters.spec.js`（11 条），由现有 job 自动收集；基线 723 -> 822（后端）、248 -> 259（前端）、小程序 97 不变（e2e_test_report 全量回归表）。
- 无新增依赖、无新增环境变量、无新增服务、无数据库迁移（`makemigrations --check` 无漂移）。
- 两条新管理命令随后端代码入库，CI 只经 SQLite 测试库覆盖，不在 CI 中执行真实数据操作。
- 新增 `.gitignore` 规则（导出文件不入库）；CI 无需感知。
- `backend/tests/remote/` 不被默认测试命令收集（画像 P4-1），CI 不运行。

**无需修改 CI 配置。** 已知缺口：CI 仍使用 `--passWithNoTests`（画像 P4 写法），本批前端/小程序均已有用例，缺口不再适用于本批；画像 P4 登记的既有失败 `test_tc_int_311`（模板回灌）在 GR-C-001 PM 复跑 723/723 OK 时已不出现，以实跑为准。

## 流水线概览

[Source] -> [后端 check + 全量测试] -> [前端 主题校验 + vitest + build] -> [小程序 vitest] -> [Package（开发机，授权后）] -> [Deploy 测试环境（阶段 A，须授权）] -> [Smoke] -> [数据操作阶段 B~D（各自独立授权，非流水线自动阶段）] -> [远程 E2E（阶段 E，须授权）]

数据操作阶段（relocate dry-run、apply、export）**不是 CI/CD 自动阶段**，永远不进入任何自动化触发（ADR-101：不做成迁移，避免被 `migrate --noinput` 自动执行）。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 main | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | 后端检查与测试 | 同上 | `cd backend && python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2` | 退出码 0；822 项 OK，无 skip | abort-and-notify，不部署 |
| PIPE-03 | 前端校验、测试与构建 | 同上 | `node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 主题 check 通过；259 项通过；构建退出码 0 | abort-and-notify |
| PIPE-04 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests` | 97 项通过 | abort-and-notify |
| PIPE-05 | 迁移漂移检查（开发机，部署前，M-DE-002） | 部署授权前 | `cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings` | 退出码 0（No changes detected）；注意使用 Django 5.2.x 的 venv | 非 0 即停止，交回开发（不得在目标机生成迁移，P8） |
| PIPE-06 | 制品打包 | 用户当轮授权阶段 A 后，开发机 | 后端：`git archive --format=tar.gz 15ea79e:backend`（只含已提交跟踪文件，M-DE-012）；前端：在工作树构建 `frontend/dist`（要求 `git diff --quiet 15ea79e -- frontend` 且无未跟踪文件）；记录两包 SHA256 | 包生成、SHA256 已记录 | abort-and-notify |
| PIPE-07 | 部署（测试环境） | 用户当轮授权阶段 A | 见 deployment_plan DEPLOY-001~004 | 全部 DEPLOY 完成、验证通过 | 逆序 ROLLBACK（不得跳过失败继续部署） |
| PIPE-08 | 部署后冒烟 | PIPE-07 成功后 | 见 deployment_plan「部署后验证」 | 全部检查通过 | 失败即报告，按用户决定回滚；至多对「建连」重试 3 次（M-DE-009） |
| PIPE-09 | 数据操作（阶段 B/C/D） | 各阶段用户当轮独立授权，且上一阶段结果已汇报并获用户确认 | 见 deployment_plan | 各阶段成功标准 | abort-and-notify；不自动重试写操作 |
| PIPE-10 | 远程 HTTP E2E（阶段 E） | 用户当轮授权阶段 E | 画像 P4-1：e2e_ 夹具 setup -> `backend/tests/remote/run_remote.py` -> 夹具 cleanup | 本批相关用例通过；清理后清册计数与基线相同 | abort-and-notify；失败仍须执行 cleanup |

触发说明：PIPE-01~05 为自动/开发机阶段；PIPE-06 起全部为手动，且每个授权点见 deployment_plan「授权点总表」。CI 只跑测试与构建，不部署（画像 P7）。

## 环境矩阵

| 配置项 | 测试 |
|---|---|
| 主机 | 树莓派，用户 `yangyang`；外网 SSH `-p 57279 yangyang@47.109.197.217`（Claude 主会话/E2 用）；内网 `192.168.31.51:22` |
| 后端 | gunicorn `127.0.0.1:9000`，systemd `ocap-backend`（1 个服务；实例数不涉及，沿用现状） |
| 前端 | nginx `8090`，`/home/yangyang/ocap/web/ocap`；外网 `https://ai-freeark.xin/ocap/` |
| 数据库 | MySQL 库 `ocap`（主机见 `.env` 的 DB_HOST）；Freeark 库不触碰 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（不 cat、不输出；仅 `set -a; . ./.env` 加载） |
| 外部依赖 | 短信 console 替身；微信未配置；本批不调用任何外部服务 |
| 部署需用户确认 | 是（每个阶段当轮独立授权） |

生产环境：画像 P7 中不存在，不设计。晋升（staging -> prod）：不适用。

## 制品管理

- 存储位置：开发机会话临时目录（后端包、前端包）+ 目标机 `/home/yangyang/ocap/snapshots`（回滚快照、数据备份）。
- 命名：后端 `backend-<TS>.tar.gz`、前端 `web-<TS>.tar.gz`、nginx `*.bak_<TS>`；数据备份 `underground-<TS2>.jsonl`、`ocapdb-registry-<TS2>.sql`；`TS=YYYYMMDDHHMMSS`。
- 版本标识：部署版本 = 本地 main 提交 `15ea79ea51c87d56cd1cd8113cba81007649575a`（尚未推送）；包 SHA256 在两端比对并记入报告（M-DE-006：目标机无 git，仅时间戳不足以定位版本）。
- 晋升条件：PIPE-02~05 通过 + 用户当轮授权。
- 无制品库；风险：制品不可追溯，靠锚点 TS、提交号与 tar SHA256 定位（已知缺口，沿用 ocap-deploy §9）。推送到 GitHub 需用户另行同意（P9）；未推送时 CI 不会跑本批提交，部署前的测试证据以 GR-D-001 PM 复跑为准 [INFERRED: 建议用户在授权推送后确认 GitHub CI 通过]。
- 小程序：不在本流水线构建/发布（本批无源码改动，顺序由服务端接口生效）。
- 含个人信息的导出文件（阶段 D）：不是制品，不入库、不上传到任何位置，仅存本地仓库根（`.gitignore` 已忽略）。
