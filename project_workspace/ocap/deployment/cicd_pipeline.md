<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-08T11:20:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.trae/sdlc/project_profile.md</file>
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
| PIPE-04 | 后端测试 | 同上 | `python manage.py test --settings=config.test_settings -v 2` | 退出码 0，`Ran N tests` 且 `OK`；N ≥ 120 | abort-and-notify（不重试） |
| PIPE-05 | 前端依赖 | 同上 | `npm ci`（`frontend/package-lock.json`） | 退出码 0 | abort-and-notify |
| PIPE-06 | 前端测试 | 同上 | `npx vitest run --passWithNoTests` | 退出码 0；当前无用例时明确输出跳过 | abort-and-notify |
| PIPE-07 | 前端构建 | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，生成 `frontend/dist/index.html` 且资源路径以 `/ocap/assets/` 开头 | abort-and-notify |
| PIPE-08 | 小程序依赖 | 同上 | `npm install --no-audit --no-fund`（无 lock 文件） | 退出码 0 | abort-and-notify |
| PIPE-09 | 小程序测试 | 同上 | `npx vitest run --passWithNoTests` | 退出码 0 | abort-and-notify |

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
| `frontend/` 与 `miniprogram/tests/` 无任何用例文件（后者仅有 `setup.js`） | PIPE-06 / PIPE-09 实际为“0 用例通过” | 保留 job 与 `--passWithNoTests`，补充用例后自动生效；不新造用例（超出本次范围） |
| 后端测试使用 SQLite 内存库 | 不覆盖 MySQL 方言/索引差异 | 测试环境部署后由人工冒烟覆盖（`deployment_plan.md` 部署后验证） |
| 定时任务 RU-2 未纳入 CI | 无自动化覆盖 | 由 `tests/` 内 `run_due_jobs` 用例间接覆盖 |
