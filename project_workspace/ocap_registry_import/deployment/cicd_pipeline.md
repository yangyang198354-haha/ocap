<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-10T23:16:12+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>architecture/architecture_design.md</file><file>architecture/module_design.md</file><file>architecture/tech_stack.md</file><file>development/implementation_plan.md</file><file>testing/unit_test_report.md</file><file>testing/integration_test_report.md</file><file>testing/e2e_test_report.md</file><file>project_workspace/ocap_registry_import/phase_status.md</file><file>.trae/skills/ocap-deploy/SKILL.md</file><file>.github/workflows/ci.yml</file></input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：业主清册导入增强（US-092 ~ US-104）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`（GitHub Actions，触发 `push`/`pull_request` → `main` 与 `workflow_dispatch`），三个 job：

| job | 内容 | 本次改动影响 |
|---|---|---|
| `backend`（ubuntu-latest，Python 3.13） | `pip install -r requirements.txt`；`manage.py check`；`manage.py test --settings=config.test_settings -v 2` | 无需修改。新增后端用例 80 个随全量测试执行；`openpyxl>=3.1,<4.0` 已在 `backend/requirements.txt:5`，CI 安装后 xlsx 分支可被真实执行。 |
| `frontend`（Node 20） | `npm ci`；`node scripts/themes/build.mjs --strict --check`；`npx vitest run --passWithNoTests`；`npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 无需修改。新增 `frontend/tests/registry_import.spec.js`（4 个用例）随 vitest 执行。 |
| `miniprogram`（Node 20） | `npm install --no-audit --no-fund --legacy-peer-deps`；`npx vitest run --passWithNoTests` | 无需修改。小程序页面改动由既有 69 个用例回归。 |

CI 只跑测试与构建，不部署（画像 P7）。本次改动不新增服务、不新增环境变量、不新增运行时依赖，因此**不需要修改 ci.yml**；唯一与 CI 相关的变化是后端测试规模从 247 增至 327。

## 流水线概览

```
[Source] → [Static Check] → [Backend Tests] → [Frontend Check+Tests+Build] → [Miniprogram Tests]
        → [Package]  (手动/部署时) → [Deploy 测试环境] → [Smoke] → [E2E-API]
```

- CI 覆盖到 `[Miniprogram Tests]`；`[Package]` 之后由部署计划（`deployment/deployment_plan.md`）在开发机与目标机执行，CI 不 push 制品、不 ssh 目标机。
- 部署后冒烟与 E2E-API 在目标环境执行（见部署计划"部署后验证"）。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR → `main`；手动触发 | `actions/checkout@v4` | 检出成功 | abort-and-notify |
| PIPE-02 | Static Check | 同上 | `python -m compileall -q backend`；`python manage.py check --settings=config.test_settings` | 退出码 0，`System check identified no issues` | abort-and-notify |
| PIPE-03 | Backend Tests | 同上 | `cd backend && python manage.py test --settings=config.test_settings -v 2` | 退出码 0；`Ran 327 tests / OK`（数量随用例增长，只要求 0 失败） | abort-and-notify（禁止跳过失败继续） |
| PIPE-04 | Frontend Theme Check | 同上 | `node scripts/themes/build.mjs --strict --check` | 退出码 0，无漂移 | abort-and-notify |
| PIPE-05 | Frontend Tests | 同上 | `cd frontend && npx vitest run --passWithNoTests` | 退出码 0；本地基线 124 passed / 2 既有环境失败（Linux CI 无 Windows 路径/行尾问题，期望 0 失败） | abort-and-notify |
| PIPE-06 | Frontend Build | 同上 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0，产出 `frontend/dist` | abort-and-notify |
| PIPE-07 | Miniprogram Tests | 同上 | `cd miniprogram && npm install --no-audit --no-fund --legacy-peer-deps && npx vitest run --passWithNoTests` | 退出码 0；69 passed | abort-and-notify |
| PIPE-08 | Package | 部署前，开发机手动 | `tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' -czf /tmp/ocap_backend_<TS>.tar.gz -C backend .`；前端 `npm run build` 后 `tar -czf frontend_dist_<TS>.tar.gz -C frontend/dist .`；记录两者 SHA256 | 两个 tar 生成、SHA256 写入部署记录 | abort-and-notify |
| PIPE-09 | Deploy 测试环境 | 用户授权 E2 后 | 见 `deployment_plan.md` DEPLOY-001~007 | 每步预期匹配 | 停止并逆序回滚 |
| PIPE-10 | Smoke | 部署成功后 | `curl` 内网/外网入口、`systemctl is-active ocap-backend`、`journalctl` | 见部署计划"部署后验证" | 失败 → 评估回滚 |
| PIPE-11 | E2E-API | 冒烟通过后 | 目标环境低风险只读接口：`GET /ocap/api/v1/admin/registry/import/spec` 未认证返回 401/403；xlsx 模板由 Django shell 生成并校验 ZIP 结构 | 路由存在、xlsx 产物有效 | 记录为 DEPLOYED_WITH_ISSUES，交 PM 决定 |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） | 生产 |
|---|---|---|---|
| 主机 | 树莓派 `192.168.31.51`（`yangyang`，免密 SSH） | 同左，经 Freeark frp 通道 | 无（画像 P7） |
| 服务 | gunicorn `127.0.0.1:9000`（`ocap-backend.service`）+ nginx `8090` | Pi nginx `8080` + VPS 443（复用 Freeark `^~ /ocap/`） | — |
| 数据库 | MySQL `192.168.31.98:3306` 库 `ocap` | 同左 | — |
| 实例数 | 单实例 | 单实例 | — |
| 资源 | 磁盘 ≥ 2 GB 可用、内存 ≥ 500 MB 可用（部署预检） | 同左 | — |
| 外部依赖 | 短信 `console` 替身；微信未配置（画像 P7） | 同左 | — |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（不入库、不改写） | 同左 | — |
| 部署需用户确认 | 是 | 是 | — |
| 部署方式 | tar 快照 → scp → 解包 → 迁移 → systemd 重启（非容器） | 同左 | — |

本次无 nginx 配置变更（前端仍为 `/ocap/` + `/ocap/api/v1`），不触碰 Freeark 配置。

## 制品管理

- 无制品库：制品在开发机生成 tar，`/tmp` 暂存后 scp 到目标机 `/tmp`，随后解包。
- 命名：`ocap_backend_<YYYYmmddHHMMSS>.tar.gz`、`frontend_dist_<YYYYmmddHHMMSS>.tar.gz`；同一 `TS` 即本次部署的回滚锚点。
- 完整性：部署记录写入两个 tar 的 SHA256；目标机上解包前用 `sha256sum` 核对（scp 后核对）。
- 留存：目标机 `/home/yangyang/ocap/snapshots/backend-<TS>.tar.gz`、`web-<TS>.tar.gz` 与 nginx 配置备份保留 ≥ 7 天。
- 晋升条件：CI 全绿（PIPE-02~07）→ E1 计划批准 → 用户 E2 授权 → 预检全通过；任一不满足不得部署。
- 风险：目标机无 git，无法用提交号做锚点；以时间戳 + SHA256 + 本地 HEAD 哈希共同标识（见部署计划预检）。
