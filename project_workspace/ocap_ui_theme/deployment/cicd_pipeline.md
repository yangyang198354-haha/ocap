<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-09T22:33:30+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.claude/agents/project_profile.md</file>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap_ui_theme/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_ui_theme/architecture/module_design.md</file>
    <file>project_workspace/ocap_ui_theme/development/implementation_plan.md</file>
    <file>project_workspace/ocap_ui_theme/testing/e2e_test_report.md</file>
    <file>project_workspace/ocap/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI 流水线（PHASE_10）：ocap 多风格界面增量

## 现状与影响

- 已有 CI：`.github/workflows/ci.yml`（GitHub Actions，触发 push/PR 到 main 与手动），三个 job：`backend`（Python 3.13，check + 全量测试）、`frontend`（Node 20，`npm ci` → vitest → build）、`miniprogram`（Node 20，vitest）。CI 不含任何部署、ssh、scp 步骤（`grep deploy|ssh|scp ci.yml` 无结果）；推送 main 只触发 CI，不部署（画像 P7）。
- 本次改动对 CI 的影响：
  1. **新增校验**：`scripts/themes/build.mjs --strict --check`（GR-D-001/002 条件）。校验 `themes/*.theme.json` 合规，并核对生成物（`frontend/src/theme/generated/{themes.css,registry.js}`、`miniprogram/theme/generated/{registry.js,themes.scss}`）与源文件一致（防漂移）。仅使用 `node:fs/path/url`，无新依赖；已核对未使用 Node 21+ 才有的 API（grep `globSync|groupBy|import.meta.dirname|parseArgs|styleText` 无结果），CI Node 20 可运行；本地 Node 22.23.3 实跑 rc=0。
  2. **新测试层无需改配置**：后端新增用例由 `manage.py test` 全量自动发现（本地 244 OK）；frontend 12 文件 / 122 用例、miniprogram 10 文件 / 69 用例由 vitest 自动发现；`frontend/tests/theme_build.spec.js` 通过相对路径 `../../scripts/themes/build.mjs` 与 `themes/` 读取仓库根文件，CI 检出完整仓库即可。
  3. **新增迁移** `accounts/0002_user_theme_key.py`：后端测试 `MIGRATION_MODULES` 置空不跑迁移，CI 不覆盖迁移本身；迁移漂移由部署预检的 `makemigrations --check --dry-run` 把关（见下"建议"）。
  4. 无新增依赖（`backend/requirements.txt`、`frontend/package.json`、`frontend/package-lock.json` 相对 `c0d1f0a` 与 HEAD 均无差异）、无新服务、无新环境变量。
  5. 前端构建（PIPE-07）保留，仍为 `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`。
- **对 ci.yml 的实际修改（PM 明确授权，最小改动）**：在 `frontend` job 的 "Install dependencies" 之后、vitest 之前插入 1 个步骤：
  ```yaml
  - name: Theme definitions check (validate + generated files not drifted)
    working-directory: .
    run: node scripts/themes/build.mjs --strict --check
  ```
  `working-directory: .` 覆盖 job 默认的 `frontend`，使脚本在仓库根运行。放在 frontend job（已装 Node 20）是为避免新增 job 与重复 checkout；失败即 abort 该 job，后续 vitest/构建不再执行。已用 PyYAML 解析确认 YAML 合法、步骤顺序正确。
- **提交前提（风险）**：`themes/`、`scripts/themes/`、`frontend/src/theme/`、`miniprogram/components/`、`miniprogram/store/theme.js`、`miniprogram/theme/`（若未跟踪）及全部新测试当前为**未跟踪**文件（`git status`）。提交时必须一并纳入，否则 CI 的 themes 步骤与 `theme_build.spec.js` 会因文件缺失失败。commit/push 由用户确认后由主会话执行（画像 P9），本阶段不执行。
- 已知缺口（沿用上期，不在本次修改范围）：CI 无迁移漂移检查；`--passWithNoTests` 保留（两端现有真实用例，掩盖风险已降低）；小程序构建（`build:mp-weixin`）基线即失败（CR-007），CI 只跑小程序 vitest，不做构建。

### 建议（未修改，需 PM/用户批准后另行改动）

1. backend job 增加 `python manage.py makemigrations --check --dry-run --settings=config.test_settings`（Django 5.2.x 受 requirements 约束，可在 CI 早发现 CR-023 类漂移）。
2. frontend/miniprogram 去掉 `--passWithNoTests`。

## 流水线概览

```
[Source: push/PR → main, 手动]
  ├─ [Backend]     依赖 → Django check → 全量测试（SQLite 内存库）
  ├─ [Web]         npm ci → ★themes-check → vitest → vite build（base=/ocap/）
  └─ [Miniprogram] 依赖 → vitest
（无 Package / Deploy / Smoke / E2E 阶段；部署由 deployment_plan 在 E2 手工执行）
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 检出 | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| PIPE-02 | 后端依赖 | 同上 | `apt-get install default-libmysqlclient-dev pkg-config`；`pip install -r requirements.txt` | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端系统检查 | 同上 | `python manage.py check --settings=config.test_settings` | `System check identified no issues` | abort-and-notify |
| PIPE-04 | 后端全量测试 | 同上 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0；`Ran N tests` 且 `OK`；N ≥ 244（本次基线，2026-11-09 实跑） | abort-and-notify（不重试） |
| PIPE-05 | 前端依赖 | 同上 | `npm ci` | 退出码 0 | abort-and-notify |
| **PIPE-10** | **风格定义校验与防漂移（新增）** | 同上（frontend job 内，PIPE-05 之后） | `node scripts/themes/build.mjs --strict --check`（工作目录仓库根，Node 20） | 退出码 0（定义合规；生成物与源一致） | abort-and-notify（不重试，失败说明风格定义不合规或需重新运行构建并提交生成物） |
| PIPE-06 | 前端测试 | 同上 | `npx vitest run --passWithNoTests` | 退出码 0；Test Files 12 passed / Tests 122 passed（本次基线），无失败 | abort-and-notify |
| PIPE-07 | 前端构建 | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0；`frontend/dist/index.html` 存在，资源路径以 `/ocap/assets/` 开头 | abort-and-notify |
| PIPE-08 | 小程序依赖 | 同上 | `npm install --no-audit --no-fund --legacy-peer-deps` | 退出码 0 | abort-and-notify |
| PIPE-09 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests` | 退出码 0；Test Files 10 passed / Tests 69 passed（本次基线） | abort-and-notify |

编号说明：PIPE-10 为新增，沿用旧编号 PIPE-01~09 以免改变既有引用；执行顺序以"流水线概览"为准。

## 环境矩阵

画像 P7 仅有"测试"环境（无生产、无 staging，不设计晋升）。

| 配置项 | CI（GitHub Actions） | 测试（树莓派） |
|---|---|---|
| 实例数 | 托管 runner，每 job 1 台 | 1 台，与 Freeark 共存 |
| 资源 | ubuntu-latest 默认 | 见上期部署报告：可用内存约 1.8 GB，磁盘可用约 16 GB |
| Python / Node | Python 3.13 / Node 20 | Python 3.13.5（独立 venv）/ 不参与运行（前端为静态产物） |
| 数据库 | SQLite `:memory:`（`config.test_settings`） | MySQL 库 `ocap`（主机见 `.env` DB_HOST） |
| 外部依赖 | 全部内存替身 | 短信 `console` 替身；微信未配置 |
| 配置来源 | 仓库内 `config/test_settings.py` | `/home/yangyang/ocap/backend/.env`（不入仓库，不覆盖） |
| 部署需确认 | 不适用（CI 不部署） | 是 |

## 制品管理

- CI 不产出制品，无制品库（画像 P8 禁止容器化）。后端 tar 与前端 `dist` 在部署时由部署机（开发机）本地打包/构建，见 deployment_plan。
- 风险：制品与提交的对应关系靠人工记录（回滚锚点 `TS` + `git rev-parse HEAD` + 工作树摘要）；目标机无 git；本次工作树含大量未提交改动，须在 deployment_report 中完整记录。可接受（测试环境）。
- 小程序无制品：构建与发布不在本次范围。
