<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T14:34:03+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/test_plan.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap_registry_import/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：信息公开与多平台内容中心（ocap_content_publish）

## 现状与影响

现有 CI：`.github/workflows/ci.yml`（GitHub Actions，`push`/`pull_request` → `main` 与 `workflow_dispatch`，`concurrency` 取消同组旧运行，`permissions: contents read`）。三个 job，只测试与构建，不部署（画像 P7）。本次不重建流水线，只评估影响。

| job | 现有内容 | 本次改动的影响 | 是否需改 ci.yml |
|---|---|---|---|
| `backend`（Python 3.13） | `pip install -r requirements.txt` → `manage.py check --settings=config.test_settings` → `manage.py test ... -v 2` | 新增依赖 `cryptography>=42.0,<51.0`（`backend/requirements.txt`，x86 wheel 在 CI 可用）；新 app `apps.content`（INSTALLED_APPS）；后端用例增至 519（本机 Python 3.12 PM 复跑）；`MIGRATION_MODULES` 置空，CI 不执行 content 0001/0002 | 否 |
| `frontend`（Node 20） | `npm ci` → 主题检查 → `vitest --passWithNoTests` → `npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 新增 7 个 `@tiptap/*` 依赖（3.33.1），`package-lock.json` 已同步，`npm ci` 即按锁安装；前端用例 16 个文件 / 154 个用例，`--passWithNoTests` 不再掩盖无用例（M-DE-004 的缺口已关闭） | 否 |
| `miniprogram`（Node 20） | `npm install --legacy-peer-deps` → `vitest --passWithNoTests` | 新增 `RichBlocks.vue`、`pages/info/*`；用例 75 个；无新依赖。小程序不在本次发布范围 | 否 |

结论：**无需修改 `ci.yml`**，理由——无新服务、无新环境变量（测试设置里 `DJANGO_ALLOW_EPHEMERAL_SECRET=1` 使缺密钥时生成进程内随机钥）、无新测试层、依赖由既有 install 步骤覆盖。module_design 与 PM 均未要求改动 CI 文件，因此 devops-engineer 不直接修改。

**登记的已知缺口（不阻塞本次部署，由部署计划预检补位）**：

| 编号 | 缺口 | 影响 | 补位 |
|---|---|---|---|
| CI-GAP-1 | CI 的 Python 为 3.13，目标机 Python 版本未知（Django 5.2 要求 ≥3.10，故目标机必为 3.10 及以上）；GR-C-002-F01 就是版本差异（3.14 vs 3.12/3.13）漏检的先例 | 目标机 3.10/3.11 上可能出现 CI 未覆盖的语法或注解求值问题 | deployment_plan PRE-104 记录版本；DEPLOY-003 解包后用目标机 `venv/bin/python` 执行 `compileall` 与 `manage.py check`，失败即在迁移前停止并回滚 |
| CI-GAP-2 | CI 不跑 `makemigrations --check --dry-run`（画像 P4 列出，P8/CR-023 要求）、不跑 `compileall` | 迁移漂移或手写迁移与模型不一致不会在 CI 暴露 | deployment_plan PRE-006 在开发机执行；**建议**后续在 `backend` job 增加两步（命令见 PIPE-02/03），本批不改 |
| CI-GAP-3 | CI 不覆盖 aarch64 wheel（`cryptography`） | 树莓派上 `pip install` 可能需要编译 | deployment_plan PRE-105 在目标机用 `pip install --dry-run --only-binary=:all:` 只读验证 |
| CI-GAP-4 | CI 不执行迁移到 MySQL | content 0001/0002 在 MySQL 的 DDL 行为（`LONGBLOB`、utf8mb4 唯一索引长度）仅靠设计推演 | DEPLOY-002 先 mysqldump；DEPLOY-006 迁移前后检查表数量；失败按 ROLLBACK-006 处理 |

CI 门控（E2 前置，写入 deployment_plan PRE-003）：待部署提交 `955c63a` 的 CI run 必须为 `success`。E1 编写时观察到 run `42972838320`（标题"交付后评审返工…"）为 `completed / success`；E2 开始前须由执行者再次用 `gh run list --branch main` 核对同一提交，且 PM 复核。**不得在 CI 非绿或未结束时执行 E2。**

## 流水线概览

```
[Source] → [Static Check] → [Backend check+test] → [Migration drift] → [Frontend install+test+build] → [Miniprogram test]
    ── CI（ci.yml）覆盖到此 ──
  → [Package: git archive + 前端 dist] → [Deploy 测试环境] → [Smoke（只读）] → [E2E / 人工验证 M-01~M-07]
    ── 由 deployment_plan（E2）在开发机与目标机执行，CI 不 ssh 目标机 ──
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR → `main`；手动 | `actions/checkout@v4` | 检出成功 | abort-and-notify（GitHub 通知） |
| PIPE-02 | Static Check | 同上 | 仓库根：`python -m compileall -q backend`（画像 P4；**现有 CI 未含**，见 CI-GAP-2） | 退出码 0 | abort-and-notify；部署前由 E2 预检补跑 |
| PIPE-03 | Backend check | 同上 | `backend/`：`python manage.py check --settings=config.test_settings`（CI 现有）；`python manage.py makemigrations --check --dry-run --settings=config.test_settings`（**CI 未含**，E2 PRE-006 补跑，产物不得提交） | 退出码 0，`no issues` / `No changes detected` | abort-and-notify |
| PIPE-04 | Backend Unit+Integration+E2E+Smoke | 同上 | `backend/`：`python manage.py test --settings=config.test_settings -v 2`（SQLite 内存库，外部服务只经 `apps/integrations/fakes.py`；分层命令：`manage.py test tests.unit` / `tests.integration` / `tests.e2e` / `tests.smoke`） | 退出码 0；相对基线零新增失败（GR-D-004 复跑：unit 138 / integration 342 / e2e 33 / smoke 6，合计 519） | abort-and-notify；禁止"跳过失败继续部署" |
| PIPE-05 | Frontend 安装 | 同上 | `frontend/`：`npm ci`（按 `package-lock.json`） | 退出码 0 | abort-and-notify |
| PIPE-06 | Frontend 检查与单元 | 同上 | 仓库根 `node scripts/themes/build.mjs --strict --check`；`frontend/`：`npx vitest run --passWithNoTests` | 退出码 0；154 passed | abort-and-notify |
| PIPE-07 | Frontend Build | 同上 | `frontend/`：`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0；`dist/index.html` 资源前缀 `/ocap/assets/` | abort-and-notify |
| PIPE-08 | Miniprogram 单元 | 同上 | `miniprogram/`：`npm install --no-audit --no-fund --legacy-peer-deps`；`npx vitest run --passWithNoTests` | 退出码 0；75 passed（构建与发布不在本次范围） | abort-and-notify |
| PIPE-09 | Package（手动，部署时） | E2 授权之后 | 后端：`git archive --format=tar.gz -o /tmp/ocap_backend_<TS>.tar.gz 955c63a:backend`；前端：PIPE-07 命令在开发机重新构建后 `tar -czf /tmp/frontend_dist_<TS>.tar.gz -C frontend/dist .`；systemd 单元：`git archive ... 955c63a:deploy/systemd ocap-content-worker.service` | 两端 SHA256 一致；后端包不含 `.env`/`venv/`/`var/` | 有限次重试上传（最多 3 次，间隔 ≥20 秒）后仍失败 → abort（目标机尚无变更时报 DEPLOYMENT_FAILED） |
| PIPE-10 | Deploy 测试环境 | E2：PM 在 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名「测试」，且 PIPE-01~08 的 CI 结果为 success | deployment_plan DEPLOY-001~010 | 每步退出码与预期输出符合；失败按 ROLLBACK 逆序 | abort + 回滚（见计划），不重试已开始的非幂等步骤 |
| PIPE-11 | Smoke（只读） | 部署成功后 | deployment_plan "部署后验证" V-01~V-20 | 全部通过 | 部分失败 → DEPLOYED_WITH_ISSUES，由用户决定是否回滚 |
| PIPE-12 | E2E / 人工验证 | 部署后，用户执行 | e2e_test_report 人工清单 M-01~M-07（含公众号真实联调，P4 禁止自动化） | 用户确认 | 缺陷回流 GROUP_C |

## 环境矩阵

只列画像 P7 中存在的环境（无 staging、无生产，故无晋升流程）。

| 配置项 | 测试（树莓派） |
|---|---|
| 访问入口 | 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/` |
| SSH | 外网 `ssh -p 57279 yangyang@47.109.197.217`（ED25519 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，密钥认证）；内网 `yangyang@192.168.31.51:22` |
| 实例数 | `ocap-backend`（gunicorn 127.0.0.1:9000，4 workers，`--timeout 90`，R2 实测）× 1 单元；**新增** `ocap-content-worker` × 1（单线程，ADR-063）；`ocap-run-due-jobs.timer` 不变 |
| 资源 | 树莓派 4 GB 内存，与 Freeark 同机；worker `MemoryMax=400M`、`Nice=10`（deploy/systemd 模板）；R2 时可用内存约 1.7 GB、`/` 可用 16 GB（部署时须重测） |
| 外部依赖 | MySQL 库 `ocap`（主机见 `.env` 的 DB_HOST）；微信公众号、DeepSeek、火山方舟、即梦：**测试期只经 Fakes，真实联调仅人工（P4）**；公众号出口 IP 白名单由用户配置 |
| 配置来源 | `/home/yangyang/ocap/backend/.env`（不入库、不进快照、不回显）。现有键见画像 P7；**新增 4 键**：`CONTENT_CRED_ENC_KEY`（目标机生成）、`CONTENT_CRED_ENC_KEY_PREV`（空）、`CONTENT_MEDIA_PATH_PREFIX=/ocap/api/v1`、`CONTENT_PUBLIC_BASE_URL=https://ai-freeark.xin/ocap`（签名绝对地址 = BASE + `/api/v1/content/media/…`，核对 `media.py:279-285`） |
| 本地状态（必须保留） | `backend/.env`、`backend/venv/`、`backend/var/`（媒体与附件）、MySQL 业务数据 |
| nginx | ocap 站点 8090（`/etc/nginx/sites-available/ocap`）；Freeark nginx 仅允许改 `location ^~ /ocap/` 段，nginx 只 `reload` |
| 部署需用户确认 | 是（画像 P7）。授权见 phase_status 2026-11-11T14:19:20 DEPLOY_AUTH；E2 仍需 PM 在 invocation 中写入 |

## 制品管理

- **无制品库**（画像 P7：tar → scp → 解包，不用容器、不用 pscp 逐文件）。制品为开发机临时文件，部署后保留在 `/tmp`，不入库。
- 存储位置：开发机 `/tmp/`；目标机 `/tmp/`（上传暂存）与 `/home/yangyang/ocap/snapshots/`（回滚快照，保留 ≥ 7 天，清理需用户确认）。
- 命名：`ocap_backend_<TS>_<提交短哈希>.tar.gz`、`frontend_dist_<TS>_<提交短哈希>.tar.gz`、`ocap_systemd_<TS>.tar.gz`；快照 `backend-<TS>.tar.gz`、`web-<TS>.tar.gz`、`db-ocap-<TS>.sql.gz`、`env-<TS>`。`<TS>` 为 DEPLOY-001 在目标机取得的 14 位时间戳，全程复用。
- 后端制品来源为 `git archive <提交>:backend`（只含已跟踪文件，保证不含未跟踪文件、`.env`、`venv`、`var`）；前端制品在开发机按锁文件构建（`npm ci`）。
- 晋升条件：CI success + 计划门控通过 + 用户授权；单环境，无晋升。
- 风险：无制品库意味着无法按制品版本一键回退，回滚依赖目标机上的 tar 快照；前端构建发生在开发机工作树，因此要求 `frontend/` 无未提交改动（PRE-004）；依赖（`pip install`）在目标机联网安装，PyPI 不可达或无 aarch64 wheel 会在 DEPLOY-004 前被 PRE-105 拦截。
