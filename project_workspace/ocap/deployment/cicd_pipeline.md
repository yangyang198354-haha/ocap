<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-08T23:50:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>.claude/agents/project_profile.md</file>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap/architecture/architecture_design.md</file>
    <file>project_workspace/ocap/architecture/module_design.md</file>
    <file>project_workspace/ocap/development/implementation_plan.md</file>
    <file>project_workspace/ocap/testing/test_plan.md</file>
    <file>backend/requirements.txt</file>
    <file>frontend/package.json</file>
    <file>miniprogram/package.json</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI 流水线（PHASE_10 CICD_SETUP）

## 现状与影响

> 1.2.0 增量（2026-11-08 返工后）：Web 与小程序已有真实 vitest 用例（`frontend/tests/*.spec.js` 共 33 个 it/test，`miniprogram/tests/*.spec.js` 共 30 个，含前后端契约测试），PIPE-06/PIPE-09 由“0 用例通过”变为真实执行；后端测试 278（PIPE-04 阈值随之上调，见下）。`ci.yml` 无需为此修改：`--passWithNoTests` 保留不影响正确性（有用例时照常执行，用例失败照常退出非 0）。CI 仍不部署，新增的 systemd timer（`deploy/systemd/ocap-run-due-jobs.*`）不进入 CI，由部署计划 DEPLOY-009 处理。对 `ci.yml` 的**可选**加固建议（不在本次直接修改）：见文末“对 ci.yml 的修改建议”。

- 仓库此前**没有 CI**：`.github/workflows/` 不存在，测试只在开发机与测试机上手工执行。
- 本次新增 `.github/workflows/ci.yml`，只做校验与构建，**不做任何部署**，不连接数据库与外部服务（画像 P7）。
- 对现有运行单元无影响：不生成制品、不改 systemd unit、不改 nginx。
- 依赖变化：CI 需要在 Ubuntu 上编译 `mysqlclient`，因此安装 `default-libmysqlclient-dev` 与 `pkg-config`（运行依赖，非新增 Python 包）。

## 流水线概览

```
[Source: push/PR → main]
  ├─ [Backend] 安装依赖 → Django check → 全量测试（SQLite 内存库）
  ├─ [Web] 安装依赖 → vitest → vite build（base=/ocap/）
  └─ [Miniprogram] 安装依赖 → vitest
（无 Package / Deploy / Smoke / E2E 阶段）
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 检出 | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| PIPE-02 | 后端依赖 | 同上 | `apt-get install default-libmysqlclient-dev pkg-config`；`pip install -r backend/requirements.txt` | 退出码 0 | abort-and-notify |
| PIPE-03 | 后端静态检查 | 同上 | `python manage.py check --settings=config.test_settings` | 输出 `System check identified no issues` | abort-and-notify |
| PIPE-04 | 后端测试 | 同上 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0，`Ran N tests` 且 `OK`；N ≥ 278（2026-11-08 返工后基线；画像 P4 仍写 120，待 PM 更新） | abort-and-notify（不重试） |
| PIPE-05 | 前端依赖 | 同上 | `npm ci`（`frontend/package-lock.json`） | 退出码 0 | abort-and-notify |
| PIPE-06 | 前端测试 | 同上 | `npx vitest run --passWithNoTests`（保留；建议去掉，见文末） | 退出码 0，且输出 `Test Files` ≥ 4 passed（api / auth.store / pages / login），无失败 | abort-and-notify |
| PIPE-07 | 前端构建 | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，生成 `frontend/dist/index.html` 且资源路径以 `/ocap/assets/` 开头 | abort-and-notify |
| PIPE-08 | 小程序依赖 | 同上 | `npm install --no-audit --no-fund --legacy-peer-deps`（无 lock 文件；uni-app 依赖存在 peer 冲突，需 `--legacy-peer-deps`） | 退出码 0 | abort-and-notify |
| PIPE-09 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests`（保留；建议去掉） | 退出码 0，且 `Test Files` ≥ 3 passed（api / pages / store），无失败 | abort-and-notify |

## 环境矩阵

| 配置项 | CI（GitHub Actions） | 测试环境（树莓派 192.168.31.51） |
|---|---|---|
| 实例数 | 托管 runner，每 job 1 台 | 1 台（与 Freeark 共存） |
| 资源 | ubuntu-latest 默认 | 4 GB 内存；ocap 常驻约 250 MB |
| Python | 3.13 | 3.13.5（独立 venv） |
| Node | 20 | 不参与运行（前端为静态产物） |
| 数据库 | SQLite `:memory:`（`config.test_settings`） | MySQL 192.168.31.98:3306 / 库 `ocap` |
| 外部依赖 | 全部内存替身（短信 memory、邮件 locmem） | 短信 `console` 替身；微信未配置 |
| 配置来源 | 仓库内 `config/test_settings.py` | `/home/yangyang/ocap/backend/.env`（不入仓库） |
| 部署需确认 | 不适用（CI 不部署） | 是 |

## 制品管理

- **CI 不产出制品**：无构建产物上传、无镜像、无制品库（画像 P8 禁止容器化）。
- 前端 `dist` 与后端代码在部署时由**部署机本地构建/打包**，见 `deployment_plan.md`。
- 风险：制品与提交的对应关系依赖提交号人工记录（回滚锚点），无制品库校验；测试环境可接受。

## 已知缺口

| 缺口 | 影响 | 处置 |
|---|---|---|
| ~~`frontend/` 与 `miniprogram/tests/` 无用例~~ | 已解决：两端均有真实用例（含契约测试） | 无 |
| 后端测试使用 SQLite 内存库 | 不覆盖 MySQL 方言/索引差异 | 测试环境部署后人工冒烟覆盖（`deployment_plan.md` 部署后验证） |
| 定时任务 RU-2 未纳入 CI | systemd 单元本身无自动化校验 | `run_due_jobs` 逻辑由后端用例覆盖；单元文件由 DEPLOY-009 的 `systemd-analyze verify` 校验。可选：CI 增加 `systemd-analyze verify deploy/systemd/*` 步骤 |
| CI 未执行迁移漂移检查 | CR-023 类问题（用错误 Django 版本生成迁移）只在部署预检发现 | 建议见下 |

## 对 ci.yml 的修改建议（仅建议，未修改文件，需 PM/用户批准后另行改动）

1. 前端、小程序测试步骤去掉 `--passWithNoTests`，改为 `npx vitest run`：现在已有用例，若误删测试文件应当失败而非静默通过。
2. 后端 job 增加一步：`python manage.py makemigrations --check --dry-run --settings=config.test_settings`（CI 使用 `backend/requirements.txt` 中受限的 Django 5.2.x，可早发现 CR-023 类漂移）。
3. 可选：增加 `systemd-analyze verify deploy/systemd/ocap-run-due-jobs.service deploy/systemd/ocap-run-due-jobs.timer` 步骤（ubuntu runner 自带 systemd-analyze）。
