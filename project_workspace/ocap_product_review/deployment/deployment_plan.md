<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-14T09:58:00+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/integration_test_report.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>phase_status.md</file>
    <file>deployment/cicd_pipeline.md</file>
    <file>../ocap_admin_polish/deployment/deployment_plan.md</file>
    <file>../ocap_admin_polish/deployment/deployment_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 产品评审修正 部署计划（测试环境）

> GROUP_E1 产出，**尚未执行**。本计划不连接任何目标环境。执行（GROUP_E2）须用户当轮明确授权测试环境部署，且 PM 在 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名"测试"（画像 P7：测试环境"部署需用户确认=是"）。
> 测试门控：phase_status 中 GROUP_D = APPROVED（GR-D-003 PASS_WITH_CONDITIONS：后端 712、前端 244、小程序 94 全过；远程 HTTP E2E 22 条 BLOCKED 待本计划的 DEPLOY-010 执行）。
> 本计划步骤编号沿用 ocap-deploy skill 的写法，但按本批需要重新编号；`[INFERRED]` 标记的取值汇总在文末。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端（房屋聚合/身份汇总） | `backend/apps/residency/housing.py`（新）、`residency/{views,urls,services,models}.py`、`identity/services.py`、`committee/services.py` | 无 | 无 | `ocap-backend` 重启 |
| 后端（权限/配置/限制） | `backend/apps/claims/views.py`、`income/views.py`、`core/{limits(新),config,views,urls,audit}.py`、`accounts/views.py`、`polls/views.py`、`content/styles.py`、`ledger/views.py` | 无 | 无 | 同上；`ocap-content-worker`（若已安装）随后端一并重启（module_design 建议，非必须） |
| 后端迁移 | `backend/apps/residency/migrations/0002_closed_status.py`（手写，AlterField×2，仅 choices） | **有**，仅此 1 个；无 SQL、不触碰数据（module_design「数据迁移」） | 无 | 迁移后重启 |
| E2E 夹具命令 | `backend/apps/jobs/e2e_fixture.py`、`jobs/management/commands/e2e_fixture.py`（新） | 无 | 无 | 不常驻；仅 E2 在测试机、设置 `OCAP_E2E_FIXTURE=1` 后执行 |
| Web 前端 | `frontend/src/{portal,admin,shared,stores,router}/**`（含新 `AdminStyleTemplates.vue`、`shared/{labels,confirm,usePaging,adminText}.js` 等） | 无 | `npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 替换静态产物 `web/ocap/` |
| 远程 E2E 套件 | `backend/tests/remote/*`（在执行端运行，不部署到目标机的运行路径；随后端包进入目标机但不执行） | 无 | 无 | 无 |
| 小程序 | `miniprogram/**`（新页面、组件、api.js、pages.json） | 无 | `uni build` 未验证（GR-C-001-F02） | **不在本次服务器部署范围**：构建、体验版提交、审核属人工步骤（见 UC-08） |
| 定时任务 timer / nginx / Freeark | 无 | 无 | 无 | 无需操作：timer 下次触发自动用新代码；本批不改 nginx、不 reload（画像 P7、P8） |
| `backend/requirements.txt`、前端/小程序 `package*.json`、`deploy/systemd/` | 无改动（`git status` 核实） | — | — | 无新依赖，不需要目标机 `pip install` |

## 目标环境与策略

- 环境：**仅"测试"**（画像 P7；生产不存在）。树莓派 `raspberrypi`；外网入口 `https://ai-freeark.xin/ocap/`；SSH 经外网通道 `yangyang@47.109.197.217:57279`（阿里云 VPS + frp，密钥认证；首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止）。`ai-freeark.xin:9999` 不可用，不使用。
- 方式：物理机部署（tar → scp → 解包 → migrate → systemd 重启）；不用容器、不做 pscp 逐文件上传（画像 P8）；不改动 Freeark 的服务/端口/目录/库。
- 策略：**recreate**。理由：单实例、无冗余，也无蓝绿/金丝雀所需的双环境或分流；包先上传到 `/tmp`，停机窗口内只做"停服务 → 解包 → 迁移 → 启服务"。前端静态用同目录改名切换，无单独停机。
- 预计停机：约 1~2 分钟（停 `ocap-content-worker` 最长可达其 `TimeoutStopSec=150`，若 worker 正在处理任务）`[INFERRED]`；迁移无 SQL，预计 < 5 秒 `[INFERRED]`，以实测为准。
- 数据库：MySQL `192.168.31.98` 库 `ocap`，本次仅 1 个元数据迁移。
- 数据变更风险：不改写存量数据；**清册（RegistryUnit/RegistryOwner/RegistryPhone，RegistryUnit 预期 5742）部署前后计数必须相同**。

## 执行约定（变量与引号）

执行端（开发机/E2 会话）先设置变量。远程命令一律用**双引号**，使 `$TS` 等本地值在本地展开；远端要展开的变量写 `\$`；每条含变量的远程命令先 `echo` 出完整命令核对。`$OCAP_SSH` 不加引号使用。

```bash
OCAP_HOST=47.109.197.217; OCAP_PORT=57279; OCAP_USER=yangyang
CM=$(mktemp -d /tmp/ocs.XXXX)          # ControlPath 必须在短目录（socket 路径 ≤108 字节，M-DE-010）
OCAP_SSH="ssh -p $OCAP_PORT -o ControlMaster=auto -o ControlPath=$CM/%C -o ControlPersist=10m $OCAP_USER@$OCAP_HOST"
OCAP_SCP="scp -P $OCAP_PORT -o ControlPath=$CM/%C"
OCAP_DEST="$OCAP_USER@$OCAP_HOST"
A=/home/yangyang/ocap                  # 部署根；backend/ web/ snapshots/（画像 P7）
```

- 外网 SSH 通道对连续新建连接间歇 `Connection closed`（M-DE-009）：用 ControlMaster 复用；**只对"建连"重试**（有限 3 次），已开始的非幂等命令（解包、迁移）断开后先只读核对状态再决定，不盲目重发。
- 需要 `.env` 的远端命令用 `cd $A/backend && set -a && . ./.env && set +a && …`，**不 `cat .env`**，不把任何 `DB_*`/`DJANGO_SECRET_KEY` 值写入输出或文档。
- 本地日志放会话 scratchpad，不入库；日志与报告中不含口令。

## 预检清单

任一项不通过 → 停止，不进入 DEPLOY（目标机尚无变更 → `DEPLOYMENT_FAILED`）。

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-001 待部署版本（需用户确认，UC-01） | 开发机仓库根：`git rev-parse HEAD`；`git status --short \| wc -l`；`git status --short -- backend frontend miniprogram \| grep -v '^ M' \| head` | 当前 HEAD `afa1fe8`，工作区有大量**未提交**改动与未跟踪新文件（含迁移 0002、夹具、`tests/remote/`）。**必须先由用户确认其一**：A）用户确认提交（可不 push，push 须用户另行明确同意，画像 P9），以该 `COMMIT`（完整 40 位哈希）为部署版本，要求 `git status --short -- backend frontend miniprogram deploy` 为空；B）用户明确同意从工作区打包，记录 `HEAD`、状态摘要与包 SHA256。**推荐 A**。未确认则 BLOCKED |
| PRE-002 本地测试与构建复跑（引用 GR-D-003，**部署前必须复跑**） | 用 PM 会话 venv `$PY`（Python 3.12 + Django 5.2.19，画像 P4）：<br>`(cd backend && $PY manage.py check --settings=config.test_settings)`<br>`python -m compileall -q backend`<br>`(cd backend && $PY manage.py makemigrations --check --dry-run --settings=config.test_settings)`<br>`(cd backend && $PY manage.py test --settings=config.test_settings)`<br>`(cd frontend && npx vitest run --passWithNoTests)`<br>`(cd miniprogram && npx vitest run --passWithNoTests)`<br>`node scripts/themes/build.mjs --strict --check` | `check` 无问题；compileall 退出 0；`No changes detected`；后端 `Ran 712 … OK`；前端 `244 passed (244)`；小程序 `94 passed (94)`；主题检查退出 0。**任一失败 → 停止部署并上报**（不得用"跳过"继续）。基线来源：GR-D-003、integration/e2e 报告 |
| PRE-003 迁移文件符合画像 P6 | `head -1 backend/apps/residency/migrations/0002_closed_status.py`；`grep -c "Generated by Django" backend/apps/residency/migrations/0002_closed_status.py`；`git diff --name-status HEAD -- backend/apps \| grep migrations`（方案 A 则对比 `$COMMIT`） | 首行含"手写迁移（画像 P6）"；`Generated by Django` 计数 0；本批新增迁移仅 `residency/0002_closed_status.py`（无其它 `A`/`M` 迁移文件）。不得在目标机生成迁移 |
| PRE-004 无依赖变更 | `git diff --quiet HEAD -- backend/requirements.txt frontend/package.json frontend/package-lock.json miniprogram/package.json && echo UNCHANGED` | `UNCHANGED`（否则按 ocap-deploy skill 增加 pip 安装步骤并重新评审本计划） |
| PRE-005 SSH 可达与指纹 | `ssh-keyscan -p 57279 -t ed25519 47.109.197.217 2>/dev/null \| ssh-keygen -lf -`；`$OCAP_SSH 'hostname'` | 指纹等于 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`；主机名 `raspberrypi` |
| PRE-006 资源 | `$OCAP_SSH 'df -h /home; free -m'` | `/home` 可用 ≥ 2 GB；内存 available ≥ 500 MB |
| PRE-007 服务与端口基线 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl is-active ocap-run-due-jobs.timer; systemctl list-unit-files "ocap-content-worker*" --no-legend; systemctl is-active ocap-content-worker; ss -ltn \| grep -E ":(80\|8000\|8080\|8090\|9000)\\b"; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'` | `ocap-backend`、timer 均 `active`；记录 worker 单元是否存在及 `is-active` 值（后续 DEPLOY-003/006 据此决定是否停/启，记为本地变量 `WORKER_WAS_ACTIVE`）；8000/8080/80 非 ocap 占用，9000/8090 属 ocap；Freeark 8080 返回 `200` |
| PRE-008 目标机本地状态保护 | `$OCAP_SSH "test -f $A/backend/.env && echo ENV_OK; test -d $A/backend/venv && echo VENV_OK; test -d $A/backend/var && echo VAR_OK; grep -Eq '^DJANGO_SECRET_KEY=.+' $A/backend/.env && echo SECRET_KEY_SET; stat -c '%U %n' $A/web/ocap; ls $A"` | 四个 OK/SET 标记齐全（不打印 .env 内容）；记录 `web/ocap` 属主（历史上曾为 root，M-DE-013）；`$A` 下仅 `backend web snapshots`（可有 `.env` 外的既有项，如实记录）。本批**不覆盖** `.env`、`venv/`、`var/` |
| PRE-009 迁移现状 | `$OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan > /tmp/mig_before.txt; grep -c '^\[ \]' /tmp/mig_before.txt; grep '^\[ \]' /tmp/mig_before.txt"` | 命令成功；**未应用条数 0**（旧代码不含 0002，故计划中看不到它）；记录 `residency` 当前仅 `0001_initial [X]` |
| PRE-010 数据库备份可行 | `$OCAP_SSH 'command -v mysqldump gzip sha256sum'` | 三个命令都存在（`mysqldump` 沿用上批已批准做法，画像未登记，见 notes `[TOOL_UNREGISTERED]` 提示）；缺失 → BLOCKED，不自行安装 |
| PRE-011 Freeark 与 nginx 基线 | `$OCAP_SSH 'sudo nginx -t'`；`curl -s -o /dev/null -w "%{http_code}\n" https://ai-freeark.xin/` | `syntax is ok` / `test is successful`；外网首页 `200`（本批不改 nginx，仅作基线） |
| PRE-012 执行端具备 E2E 依赖 | `python3 -c "import requests; print(requests.__version__)"` | 可导入（`requests` 在 `backend/requirements.txt`）；缺失标 BLOCKED，不自行安装（画像 P4） |
| PRE-013 用户确认事项已取得 | 对照"需用户在授权时确认的事项"UC-01 ~ UC-10 | PM 在 invocation `special_instructions` 中写明每项确认结论；UC-02 ~ UC-05 未确认则不得执行 DEPLOY-009 |

## 部署步骤

依赖顺序：基础设施（快照/备份）→ 制品 → 数据层（迁移）→ 服务层（重启）→ 前端（静态）→ 验证 → E2E。本批无新基础设施组件（对应 architecture_design 部署视图：后端、定时任务、内容 worker、前端静态、小程序包（人工）、E2E 夹具、数据库）。

### DEPLOY-001: 生成回滚锚点、数据库备份与清册基线

- 组件：目标机本地状态与数据库（architecture_design 部署视图「数据库」）
- 位置：开发机经 SSH 到目标机
- 命令：
  ```bash
  # 1) 本地取一次锚点并全程复用（M-DE-003）
  TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
  echo "$TS" | grep -Eq '^[0-9]{14}$' || echo "TS 非法，停止"
  # 2) 目标机现状指纹（代码回滚锚点，M-DE-006）：本地版本 + 目标机文件哈希
  git rev-parse HEAD; git status --short | wc -l
  $OCAP_SSH "cd $A/backend && sha256sum apps/residency/models.py apps/core/config.py apps/accounts/views.py apps/claims/views.py"
  $OCAP_SSH "ls -l $A/web/ocap/index.html; grep -o 'assets/index-[^\"]*' $A/web/ocap/index.html"
  # 3) 快照（排除 venv/var/.env，防膨胀也防回滚误删，M-DE-011）
  $OCAP_SSH "mkdir -p $A/snapshots \
   && tar czf $A/snapshots/backend-$TS.tar.gz -C $A --exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__ backend \
   && sudo tar czf $A/snapshots/web-$TS.tar.gz -C $A web"
  # 4) 数据库备份（目标测试库自签证书，需 --skip-ssl，M-DE-008；口令经 MYSQL_PWD 环境变量，不进命令行）
  $OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && MYSQL_PWD=\"\$DB_PASSWORD\" mysqldump --skip-ssl -h \"\$DB_HOST\" -P \"\$DB_PORT\" -u \"\$DB_USER\" \"\$DB_NAME\" | gzip > $A/snapshots/ocap-$TS.sql.gz; echo DUMP_EXIT=\${PIPESTATUS[0]}"
  # 5) 清册基线计数（部署前后必须相同）
  $OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c \"from apps.registry.models import RegistryUnit as U, RegistryOwner as O, RegistryPhone as P; print('REGISTRY_BASE', U.objects.count(), O.objects.count(), P.objects.count())\" | tee $A/snapshots/registry-counts-$TS.txt"
  # 6) 校验
  $OCAP_SSH "tar tzf $A/snapshots/backend-$TS.tar.gz | head -3; sudo tar tzf $A/snapshots/web-$TS.tar.gz | head -3; ls -l $A/snapshots/*-$TS.*; sha256sum $A/snapshots/*-$TS.*"
  ```
- 预期：`DUMP_EXIT=0`；4 个文件（backend tar、web tar、sql.gz、registry-counts）存在且大小非零；`REGISTRY_BASE` 第一个数为 5742（若不是，如实记录并向用户说明，以实测为准）；SHA256 记入报告。注：快照含 `web` 目录时用 `sudo`（属主可能为 root）。nginx 本批不改，故不备份 nginx 配置。
- 回滚: ROLLBACK-001

### DEPLOY-002: 构建并上传制品（开发机 → 目标机 `/tmp`）

- 组件：后端包、Web 前端静态包（architecture_design：Django 后端、Web 前端静态资源）
- 位置：开发机（构建）→ 目标机（仅上传，不解包）
- 命令：
  ```bash
  # 后端包。方案 A（推荐，PRE-001 已确认提交；只含已提交的跟踪文件，M-DE-012）：
  git cat-file -t "$COMMIT"                                  # 必须输出 commit
  git archive "$COMMIT:backend" --format=tar.gz -o /tmp/ocap-backend-$TS.tar.gz
  # 方案 B（仅用户明确同意从工作区打包时）：
  # tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
  #     -czf /tmp/ocap-backend-$TS.tar.gz -C backend .
  tar tzf /tmp/ocap-backend-$TS.tar.gz | grep -Ec '(^|/)(venv|var)/|(^|/)\.env$|__pycache__'   # 期望 0
  tar tzf /tmp/ocap-backend-$TS.tar.gz | grep -E 'residency/migrations/0002_closed_status.py|e2e_fixture.py|core/limits.py|residency/housing.py'   # 期望 5 行
  # 前端包（工作树构建；方案 A 下 frontend/ 须无未跟踪/未提交文件）
  (cd frontend && npm ci && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/)
  grep -o 'assets/index-[^"]*' frontend/dist/index.html            # 记录 bundle 名
  grep -c '/ocap/assets/' frontend/dist/index.html                  # 期望 ≥ 1
  tar czf /tmp/ocap-frontend-$TS.tar.gz -C frontend/dist .
  # 上传并校验
  $OCAP_SCP /tmp/ocap-backend-$TS.tar.gz /tmp/ocap-frontend-$TS.tar.gz "$OCAP_DEST:/tmp/"
  sha256sum /tmp/ocap-backend-$TS.tar.gz /tmp/ocap-frontend-$TS.tar.gz
  $OCAP_SSH "sha256sum /tmp/ocap-backend-$TS.tar.gz /tmp/ocap-frontend-$TS.tar.gz"
  ```
- 预期：包内无 `venv/var/.env/__pycache__`（计数 0）；5 个新文件齐全；前端构建退出 0（chunk 体积警告为既有）；两端 SHA256 逐个一致。此时目标机服务与目录**未变化**；失败 → `DEPLOYMENT_FAILED`（无需回滚）。
- 回滚: ROLLBACK-002

### DEPLOY-003: 停止服务（进入停机窗口）

- 组件：`ocap-backend`（gunicorn 127.0.0.1:9000）、`ocap-content-worker`（若存在且 active）
- 位置：目标机
- 命令：
  ```bash
  # WORKER_WAS_ACTIVE 取 PRE-007 记录值（active / inactive / 单元不存在）
  $OCAP_SSH 'sudo systemctl stop ocap-content-worker 2>/dev/null; true'     # worker 先停（其 After=ocap-backend）；最长等 TimeoutStopSec=150
  $OCAP_SSH 'sudo systemctl stop ocap-backend; systemctl is-active ocap-backend'
  ```
- 预期：`ocap-backend` 输出 `inactive`；worker 若存在为 `inactive`；`ocap-run-due-jobs.timer` 保持不动（停机期间触发的一次性进程若连库失败属预期，恢复后下一分钟自动补跑）。
- 回滚: ROLLBACK-003

### DEPLOY-004: 解包后端代码

- 组件：Django 后端（MOD-074 ~ MOD-081）
- 位置：目标机（来自 DEPLOY-002 的 `/tmp` 包）
- 命令：
  ```bash
  $OCAP_SSH "tar xzf /tmp/ocap-backend-$TS.tar.gz -C $A/backend"
  $OCAP_SSH "cd $A/backend && ls apps/residency/migrations/0002_closed_status.py apps/jobs/management/commands/e2e_fixture.py apps/jobs/e2e_fixture.py apps/core/limits.py apps/residency/housing.py && test -f .env && test -d venv && test -d var && echo LOCAL_STATE_INTACT"
  $OCAP_SSH "cd $A/backend && venv/bin/pip install --dry-run -r requirements.txt | tail -3"
  $OCAP_SSH "cd $A/backend && sha256sum apps/residency/models.py apps/core/config.py"   # 与本地文件哈希比对
  ```
- 预期：5 个新文件存在；`LOCAL_STATE_INTACT`（`.env`/`venv`/`var` 未被覆盖）；`pip --dry-run` 退出 0 且无需安装新包（PRE-004）；两个文件哈希与本地对应文件一致。注意：解包只覆盖与新增，不删除已移除的旧文件（本批无仓库内删除的后端文件，以 `git diff --name-status` 的 `D` 为准，若有则记入报告）。
- 回滚: ROLLBACK-004

### DEPLOY-005: 数据库迁移（仅 residency.0002_closed_status）

- 组件：数据库（architecture_design：residency 0002，AlterField ×2，仅 choices，不触碰数据）
- 位置：目标机
- 命令：
  ```bash
  E="cd $A/backend && set -a && . ./.env && set +a"
  $OCAP_SSH "$E && venv/bin/python manage.py check"
  # 门控 1：待应用迁移恰为 1 条且为 residency.0002_closed_status
  $OCAP_SSH "$E && venv/bin/python manage.py showmigrations --plan | grep '^\[ \]'"
  # 门控 2：确认无 DDL（输出只应有 BEGIN/注释/COMMIT，不含 ALTER/CREATE/DROP/UPDATE/INSERT/DELETE）
  $OCAP_SSH "$E && venv/bin/python manage.py sqlmigrate residency 0002 | tee /tmp/sqlmigrate_0002.txt; grep -Eic 'ALTER TABLE|CREATE |DROP |UPDATE |INSERT |DELETE ' /tmp/sqlmigrate_0002.txt"
  # 执行
  $OCAP_SSH "$E && venv/bin/python manage.py migrate --noinput"
  $OCAP_SSH "$E && venv/bin/python manage.py showmigrations residency"
  ```
- 预期：`check` 无问题；门控 1 恰一行 `residency.0002_closed_status`（多于一条或为别的迁移 → **停止，不执行 migrate**，视为步骤失败并按 ROLLBACK-004 恢复）；门控 2 的计数为 `0`（有 DDL → 停止，同上）；`migrate` 退出 0，输出 `Applying residency.0002_closed_status... OK`；`showmigrations residency` 显示 `[X] 0001_initial`、`[X] 0002_closed_status`。不在目标机运行 `makemigrations`（画像 P6、P8）。
- 回滚: ROLLBACK-005

### DEPLOY-006: 启动服务

- 组件：`ocap-backend`；`ocap-content-worker`（仅当 `WORKER_WAS_ACTIVE=active`）
- 位置：目标机
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend'
  $OCAP_SSH 'sudo journalctl -u ocap-backend -n 40 --no-pager'
  # 仅当 PRE-007 记录 worker 原为 active：
  $OCAP_SSH 'sudo systemctl start ocap-content-worker && sleep 3 && systemctl is-active ocap-content-worker; sudo journalctl -u ocap-content-worker -n 20 --no-pager'
  ```
- 预期：`active`；日志无 `Traceback`/`ERROR`；worker（若有）`active` 且无新增崩溃。
- 回滚: ROLLBACK-006

### DEPLOY-007: 发布前端静态资源

- 组件：Web 前端静态资源（`--base=/ocap/`；经 nginx 8090 与 Freeark `/ocap/` 反代对外，nginx 不变）
- 位置：目标机（来自 DEPLOY-002 的 `/tmp` 包）
- 命令：
  ```bash
  # 先只读确认属主（M-DE-013）。下列命令统一使用 sudo，避免属主为 root 时半删除
  $OCAP_SSH "stat -c '%U' $A/web/ocap"
  $OCAP_SSH "sudo rm -rf $A/web/ocap.new && sudo mkdir -p $A/web/ocap.new \
   && sudo tar xzf /tmp/ocap-frontend-$TS.tar.gz -C $A/web/ocap.new \
   && test -f $A/web/ocap.new/index.html \
   && sudo mv $A/web/ocap $A/web/ocap.old-$TS && sudo mv $A/web/ocap.new $A/web/ocap \
   && sudo chown -R yangyang:yangyang $A/web/ocap"
  $OCAP_SSH "ls -l $A/web/ocap/index.html; grep -o 'assets/index-[^\"]*' $A/web/ocap/index.html"
  ```
- 预期：`index.html` 存在且引用的 `assets/index-*.js/css` 与 DEPLOY-002 记录的 bundle 名一致、与旧版不同；`web/ocap.old-$TS` 保留（回滚用，≥ 7 天后人工清理）。
- 回滚: ROLLBACK-007

### DEPLOY-008: 部署后只读验证（门控，E2E 前必须通过）

- 组件：全部
- 位置：执行端 + 目标机（只读，除登录失败探测外不写数据）
- 命令/URL：见"部署后验证"V-01 ~ V-16。
- 预期：关键项全部通过；关键项失败（服务非 active、日志 Traceback、迁移状态不符、清册计数变化）→ 视为步骤失败，从 ROLLBACK-008 起逆序回滚；非关键项失败 → 继续但最终状态至多 `DEPLOYED_WITH_ISSUES`。
- 回滚: ROLLBACK-008

### DEPLOY-009: 夹具 setup（测试机内创建 `e2e_` 数据；需 UC-02 ~ UC-05 已确认）

- 组件：E2E 夹具命令 `manage.py e2e_fixture setup`（module_design IFC-278；画像 P4-1：由 E2 在测试机用 manage.py 创建）
- 位置：目标机（经 SSH）；密码由执行端生成，经 **stdin** 传入，不进命令行、不落盘
- 命令：
  ```bash
  # 执行端生成并保管密码（满足密码规则：长度在配置范围内、含字母与数字、非弱口令）；不 echo、不写文件
  OCAP_E2E_PASSWORD=$(python3 -c 'import secrets;print("E2e"+secrets.token_hex(10)+"x9")')
  # 先 dry 核对：只读列出将被占用的 3 套住宅，给用户确认（UC-02）
  $OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c \"from apps.jobs.e2e_fixture import _free_units; print([(u.id, u.specific_part) for u in _free_units(3, set())])\""
  # 执行 setup（参数取自 e2e_test_report 的 E2E 执行清单）
  printf '%s' "$OCAP_E2E_PASSWORD" | $OCAP_SSH 'IFS= read -r OCAP_E2E_PASSWORD; export OCAP_E2E_PASSWORD; cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25' | tee e2e_setup_$TS.json
  $OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status"
  ```
- 预期：`setup` 退出 0，输出 JSON（`accounts`、`units`、`flows`、`registry_counts`），手机号已脱敏、不含密码；`registry_counts` 与 `REGISTRY_BASE` 完全相同；`status` 显示 e2e 数据已创建、`claim_amount_max` 为 `1000000.00`。`setup` 在单个事务内，"可选房屋不足"或号段被非 e2e 用户占用时报错退出且**不留任何数据**（`CommandError`，退出码非 0）。注：本步命令的远端部分是单引号且不含本地变量（密码走 stdin），这是有意的。
- 回滚: ROLLBACK-009

### DEPLOY-010: 运行远程 HTTP E2E（执行端 → 公开入口）

- 组件：`backend/tests/remote/run_remote.py`（TC-E2E-320 ~ 341，22 条；只经 `https://ai-freeark.xin/ocap/`，不直连数据库、不经 SSH，画像 P4-1）
- 位置：执行端（只需 Python + `requests`）
- 命令：
  ```bash
  # 环境变量名：OCAP_E2E_BASE_URL、OCAP_E2E_PASSWORD（与夹具同值）、可选 OCAP_E2E_SLOW；不要设置 OCAP_E2E_ALLOW_LOCAL
  OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD="$OCAP_E2E_PASSWORD" \
    python3 backend/tests/remote/run_remote.py -v 2>&1 | tee e2e_remote_$TS.log ; echo "RUN_EXIT=${PIPESTATUS[0]}"
  # 可选慢用例（TC-E2E-332，约 31 分钟，对应人工清单 H-7，UC-07 确认后才加）：
  #   在上面命令前加 OCAP_E2E_SLOW=1
  ```
- 预期：`Ran 22 tests`；`OK (skipped=2)`：TC-E2E-328 因测试环境无已生成报表 SKIP（若已有报表则通过，skipped=1），TC-E2E-332 默认 SKIP；`RUN_EXIT=0`（1=有失败，2=缺环境变量或被护栏拒绝，此时未发出任何请求）。护栏：目标主机非 `ai-freeark.xin`、未登记的写请求、写有效的 `claim.amount_max`、`registry/import` 非 `dry_run=1` 均在发出前报错；用例不得把 e2e 报销/备用金/收入表推进到审批通过（避免账本分录，module_design MOD-081）。
- 失败处理：**不回滚代码**；记录失败用例名、HTTP 状态与路径（不含令牌/口令）进 deployment_report，缺陷回流 GROUP_C；**无论成败立即进入 DEPLOY-011**；中途中断（网络/SSH 断开）也先 `status` 查看残留再清理。
- 回滚: ROLLBACK-010

### DEPLOY-011: 夹具 cleanup 与验收

- 组件：`manage.py e2e_fixture cleanup`
- 位置：目标机
- 命令：
  ```bash
  F="cd $A/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture"
  $OCAP_SSH "$F cleanup"                 # 默认 dry-run：核对 would_delete 仅为 e2e_ 数据；记录退出码
  $OCAP_SSH "$F cleanup --execute"       # 实际删除（分批；双条件护栏）
  $OCAP_SSH "$F status"
  $OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c \"from apps.registry.models import RegistryUnit as U, RegistryOwner as O, RegistryPhone as P; print('REGISTRY_NOW', U.objects.count(), O.objects.count(), P.objects.count())\""
  ```
- 预期：dry-run 的 `would_delete` 只含 `e2e_` 前缀数据；`--execute` 退出 0；`status`：所有 e2e 计数为 0、`registry_counts` 与 `REGISTRY_BASE` 相同、`claim_amount_max` 仍为 `1000000.00`；`REGISTRY_NOW` 与 `REGISTRY_BASE` 逐项相同（RegistryUnit 5742 不变）。清理后若计数与基线不一致或出现非 `e2e_` 数据变化 → 立即停止并上报，**不得自行修复清册**。
- 例外：`cleanup` 发现 e2e 数据产生了账本分录（`LedgerEntry`）时**退出码 2、不删除任何数据**并列出明细 → 见 ROLLBACK-011 的 `[MANUAL_ROLLBACK_REQUIRED]`。
- 回滚: ROLLBACK-011

小程序包：不在本次服务器部署范围。构建（`uni build`，GR-C-001-F02 未验证）、体验版提交与审核由用户在微信开发者工具/小程序后台人工完成；对应人工验证清单见 e2e_test_report H-1。

## 回滚步骤（逆序）

最后部署的最先回滚。触发规则：DEPLOY-001 ~ 008 任一步骤失败且目标机已有变更 → 立即停止后续步骤，从失败步骤的 ROLLBACK 起逆序执行；DEPLOY-009 ~ 011 失败 → 只做 e2e 数据清理（ROLLBACK-009），**不回滚代码**（除非用户决定）。

**执行回滚前的变量核验（必须做）**：

```bash
TS=<DEPLOY-001 记录的 ANCHOR_TS>                       # 取自 DEPLOY-001 的输出/报告，不得重新 date
echo "$TS" | grep -Eq '^[0-9]{14}$' || echo "TS 非法，停止"
$OCAP_SSH "ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/ocap-$TS.sql.gz $A/snapshots/registry-counts-$TS.txt"   # 四个文件都在才继续
$OCAP_SSH "tar tzf $A/snapshots/backend-$TS.tar.gz | grep -c 'residency/migrations/0002_closed_status.py\|e2e_fixture.py\|core/limits.py\|residency/housing.py'"   # 期望 0：确认这 5 个文件是本批新增，快照中没有
# 执行任何含 $TS 的远程命令前先 echo 完整命令核对（双引号在本地展开）
```

### ROLLBACK-011: 回滚 DEPLOY-011（cleanup）

- 类型：无可逆操作
- 命令：无。删除 `e2e_` 数据是预期终态，快照/备份不含 e2e 数据，不尝试恢复。
- [MANUAL_ROLLBACK_REQUIRED: `cleanup` 退出码 2（e2e 数据已产生账本分录 `LedgerEntry`，会影响真实季度/年度报表）。夹具拒绝自动删除。处理：暂停，列出分录明细，由用户决定如何处理账本数据；数据风险：误删账本会改变真实报表。`cleanup --execute` 在其它错误下中止时，状态可能是"部分已删除"，先 `status` 查看，再重新执行 `cleanup`（幂等）。]

### ROLLBACK-010: 回滚 DEPLOY-010（远程 E2E）

- 类型：正式回滚（经 ROLLBACK-009）
- 命令：远程用例对 `e2e_` 账号产生的写入（申请、申诉、模板、内容草稿、附件、未通过审批的报销）由夹具清理删除，等同 ROLLBACK-009。
- 预期：无其它残留。审计日志 `AuditLog` 中的 e2e 记录**不删除**（夹具设计：审计保留），见"不可逆步骤汇总"。

### ROLLBACK-009: 回滚 DEPLOY-009（夹具 setup）

- 类型：正式回滚（= DEPLOY-011 的命令）
- 命令：`$OCAP_SSH "$F cleanup"` → `$OCAP_SSH "$F cleanup --execute"` → `$OCAP_SSH "$F status"`（`F` 定义见 DEPLOY-011）
- 变量取值与核验：`F` 为本地拼接的完整远端命令，执行前 `echo "$F"` 核对其含 `OCAP_E2E_FIXTURE=1`；cleanup 不需要密码。
- 预期：e2e 计数全 0；`registry_counts` 与 `REGISTRY_BASE` 相同；3 套被占用住宅的户主槽位释放（夹具的 `Membership` 随清理删除）。

### ROLLBACK-008: 回滚 DEPLOY-008（验证）

- 类型：无变更（记录现场）
- 命令：`$OCAP_SSH 'sudo journalctl -u ocap-backend -n 100 --no-pager' > e2e_scene_$TS.log`；保存 `showmigrations residency` 与失败检查项输出到 scratchpad（不含口令）。
- 预期：现场可追溯；随后按 ROLLBACK-007 起逆序执行。

### ROLLBACK-007: 回滚 DEPLOY-007（前端静态）

- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH "test -d $A/web/ocap.old-$TS && sudo rm -rf $A/web/ocap.failed && sudo mv $A/web/ocap $A/web/ocap.failed && sudo mv $A/web/ocap.old-$TS $A/web/ocap && sudo chown -R yangyang:yangyang $A/web/ocap"
  # 若 ocap.old-$TS 已不存在，改用快照（先移走现目录，再解包，只动 web/）：
  # $OCAP_SSH "sudo mv $A/web/ocap $A/web/ocap.failed && sudo tar xzf $A/snapshots/web-$TS.tar.gz -C $A"
  ```
- 变量取值与核验：`TS` 见上；执行后 `ls -l $A/web/ocap/index.html`，`grep -o 'assets/index-[^"]*'` 的 bundle 名等于 DEPLOY-001 记录的旧 bundle 名。
- 预期：外网 `/ocap/` 返回 200 且 bundle 回到旧值。

### ROLLBACK-006: 回滚 DEPLOY-006（停止服务，为迁移回退与代码恢复做准备）

- 类型：正式回滚
- 命令：`$OCAP_SSH 'sudo systemctl stop ocap-content-worker 2>/dev/null; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend'`
- 预期：`inactive`。

### ROLLBACK-005: 回滚 DEPLOY-005（迁移回退）

- 类型：正式回滚（可逆：`residency.0002` 仅 choices，无 SQL、无数据转换）
- 命令（**必须在 ROLLBACK-004 恢复旧代码之前执行**——旧代码里没有 0002 迁移文件，无法反向迁移）：
  ```bash
  E="cd $A/backend && set -a && . ./.env && set +a"
  $OCAP_SSH "$E && venv/bin/python manage.py showmigrations residency"                       # 执行前确认 0002 为 [X]
  $OCAP_SSH "$E && venv/bin/python manage.py shell -c \"from apps.residency.models import Appeal as A_, ResidentApplication as R; print('CLOSED_ROWS', A_.objects.filter(status='CLOSED').count(), R.objects.filter(status='CLOSED').count())\""
  $OCAP_SSH "$E && venv/bin/python manage.py migrate residency 0001 --noinput"
  $OCAP_SSH "$E && venv/bin/python manage.py showmigrations residency"                       # 期望 0001 [X]、0002 [ ]
  ```
- 变量取值与核验：迁移名固定（`residency` / `0001`）；先看 `CLOSED_ROWS`：若 > 0（迁移后有用户注销产生了已关闭记录），反向迁移仍可执行，但这些行保留为 `CLOSED`，旧代码只会按原值显示，不影响约束（`pending_slot` 已为 NULL，module_design「数据迁移·是否可逆」）；把数量写入报告。
- 预期：`0002_closed_status` 显示 `[ ]`。无数据丢失，因此**不**标 `[MANUAL_ROLLBACK_REQUIRED]`；整库恢复兜底见下方 ROLLBACK-001。

### ROLLBACK-004: 回滚 DEPLOY-004（恢复后端代码；叠加解包，不 rm 目录，M-DE-011）

- 类型：正式回滚（禁止 `git reset/clean/stash`；目标机无 git）
- 命令：
  ```bash
  $OCAP_SSH "tar xzf $A/snapshots/backend-$TS.tar.gz -C $A"          # 叠加解包：覆盖被改动的旧文件；快照已排除 venv/var/.env，不会动它们
  # 清理本批新增、旧代码不引用的 5 个文件（核验已在"变量核验"中完成：快照里不存在这些文件）
  $OCAP_SSH "cd $A/backend && rm -f apps/residency/migrations/0002_closed_status.py apps/jobs/e2e_fixture.py apps/jobs/management/commands/e2e_fixture.py apps/core/limits.py apps/residency/housing.py"
  $OCAP_SSH "cd $A/backend && sha256sum apps/residency/models.py apps/core/config.py apps/accounts/views.py apps/claims/views.py && test -f .env && test -d venv && echo LOCAL_STATE_INTACT"
  ```
- 变量取值与核验：`TS` 为 DEPLOY-001 记录的值（执行前核验见上）；执行后四个文件的 SHA256 须等于 DEPLOY-001 记录的旧值；`.env`/`venv` 仍在。不能叠加覆盖到的"本批新增的其它文件"（本批新增的测试文件等，位于 `tests/` 下，不被旧代码引用）保留无害。
- 预期：代码回到部署前状态。

### ROLLBACK-003: 回滚 DEPLOY-003（重启回旧代码）

- 类型：正式回滚（须在 ROLLBACK-005、004 之后）
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend; sudo journalctl -u ocap-backend -n 30 --no-pager'
  # 仅当 PRE-007 记录 worker 原为 active：
  $OCAP_SSH 'sudo systemctl start ocap-content-worker && sleep 3 && systemctl is-active ocap-content-worker'
  ```
- 预期：`active`，日志无 `Traceback`；外网 `https://ai-freeark.xin/ocap/` 返回 200。

### ROLLBACK-002: 回滚 DEPLOY-002（清理上传包）

- 类型：正式回滚
- 命令：`$OCAP_SSH "rm -f /tmp/ocap-backend-$TS.tar.gz /tmp/ocap-frontend-$TS.tar.gz"`
- 预期：目标机 `/tmp` 无本批包（开发机本地副本保留）。

### ROLLBACK-001: 数据层兜底（人工）

- 类型：紧急止血（仅当前述步骤无法恢复时；默认不需要，因为本批迁移无数据变更）
- 命令：经用户确认后：`gunzip -c $A/snapshots/ocap-$TS.sql.gz | mysql --skip-ssl -h "$DB_HOST" … "$DB_NAME"`（连接参数从目标机 `.env` 读取，口令经 `MYSQL_PWD`，不写入文档）。先在临时库导入并核对 `registry_registryunit` 条数（应为 `REGISTRY_BASE` 第一项）与抽样，再对目标库执行。
- 变量取值与核验：`TS` 取自 DEPLOY-001；`registry-counts-$TS.txt` 作为核对基线。
- [MANUAL_ROLLBACK_REQUIRED: 整库覆盖会丢失快照之后的所有写入（含真实用户在部署窗口内的注册、认证、申请等）；仅在代码回滚与迁移回退均不可用时，由用户确认后使用。]

## 不可逆步骤汇总

| 步骤 | 风险 | 处置 |
|---|---|---|
| `residency.0002` 正向/反向 | 仅 choices，无 SQL、无数据转换；反向后迁移期间产生的 `CLOSED` 行保留，仅显示值不被旧代码识别 | 可逆，不标人工；ROLLBACK-005 写明核验；已做 mysqldump 兜底 |
| DEPLOY-011 `cleanup --execute`（删除 `e2e_` 数据） | 删除不可恢复；设计即一次性数据 | 预期终态；dry-run 先核对 would_delete 仅为 `e2e_` 数据 |
| 夹具/E2E 写入的 `AuditLog` | 夹具不删除审计（设计如此），测试环境审计表将永久含 `e2e_` 相关记录 | 接受并在 deployment_report 说明；用户如需清理须另行授权 |
| `cleanup` 退出码 2（账本分录） | 误删账本会改变真实季度/年度报表 | `[MANUAL_ROLLBACK_REQUIRED]`（ROLLBACK-011），暂停等待用户决定 |
| ROLLBACK-001 整库恢复 | 丢失快照后所有写入 | `[MANUAL_ROLLBACK_REQUIRED]`，用户确认后执行 |
| 部署窗口内注销账号产生的 `CLOSED` 申请/申诉 | 回滚代码后不会重新打开 | 记录数量，随报告交用户 |

## 部署后验证

关键 = 失败则视为 DEPLOY-008 失败并回滚；非关键 = 失败记 `DEPLOYED_WITH_ISSUES`。`TS` 复用 DEPLOY-001 的值；写库的探测数据一律唯一化并带 `e2e_` 前缀。

| 检查项 | 命令 / URL | 成功标准 | 级别 |
|---|---|---|---|
| V-01 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` | 关键 |
| V-02 worker 与 timer | `$OCAP_SSH 'systemctl is-active ocap-content-worker ocap-run-due-jobs.timer'`（worker 仅当部署前存在） | 与部署前状态一致（均 `active`） | 非关键 |
| V-03 日志无新错误 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-10 min' --no-pager \| grep -Ec 'Traceback\|ERROR'"` | 输出 `0` | 关键 |
| V-04 迁移状态 | `$OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan \| grep -c '^\[ \]'; venv/bin/python manage.py showmigrations residency"` | 未应用数 `0`；`0001`、`0002` 均 `[X]` | 关键 |
| V-05 清册计数不变 | DEPLOY-001 的 `REGISTRY_BASE` 与同命令再次计数（`REGISTRY_NOW`）比对 | RegistryUnit/Owner/Phone 三个数逐项相同（RegistryUnit 5742） | 关键 |
| V-06 新路由存在（未登录 401 而非 404） | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/api/v1/me/housing`；同法 `…/system/limits`、`…/me` | `401` | 关键 |
| V-07 登录接口可用（错误凭据，不用真实口令） | `curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d "{\"identifier\":\"e2e_nobody_$TS\",\"password\":\"wrong1\",\"client\":\"miniapp\"}" https://ai-freeark.xin/ocap/api/v1/auth/login/password` | `400`（`LOGIN_FAILED`）；非法 `client` 值另验 `400 INVALID_VALUE`（`"client":"x"`） | 关键 |
| V-08 管理端登录接口 | 同法 `POST …/admin/auth/login`，用户名 `e2e_nobody_$TS`、错误口令 | `400` 或 `401`（非 5xx、非连接失败） | 非关键 |
| V-09 外网前端首页 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200` | 关键 |
| V-10 前端静态与 bundle | 取 `index.html` 中的 `assets/index-*.js`，`curl` 该资源（外网与内网 `http://192.168.31.51:8090/ocap/`） | 均 `200` 且非空；bundle 名等于 DEPLOY-002 记录值（404 → 检查 Freeark `^~ /ocap/`，本批不改） | 关键 |
| V-11 SPA 回退与新页 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/admin/login`；`…/ocap/admin/content/styles` | 均 `200` 且为 index.html | 非关键 |
| V-12 Freeark 未受影响 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/`；`$OCAP_SSH 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/'` | 均 `200` | 关键 |
| V-13 失败单元与端口归属 | `$OCAP_SSH 'systemctl --state=failed --no-pager; ss -ltnp \| grep -E ":(8000\|8080\|8090\|9000)\\b"'` | 无 `freeark-*`、`ocap-*` 失败单元；8000/8080 属 Freeark，8090/9000 属 ocap | 关键 |
| V-14 夹具命令可用且当前无 e2e 数据 | `$OCAP_SSH "cd $A/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status"` | 退出 0；e2e 计数全 0；`registry_counts` 与 `REGISTRY_BASE` 相同；`claim_amount_max` = `1000000.00` | 关键（E2E 前置） |
| V-15 夹具选房前置 | DEPLOY-009 的只读选房命令 | 返回 ≥ 3 套（住宅、无有效房屋关系、无待审申诉/申请）；列出 `(id, specific_part)` 供用户确认（UC-02）。不足 → 不执行 DEPLOY-009，E2E 标 BLOCKED（`[DATA_REQUIRED]`） | 关键（E2E 前置） |
| V-16 窗口内无进行中的半数决议（UC-03 前置） | 只读查询 `Resolution` 状态分布（`manage.py shell -c`，字段与状态名以代码为准），或管理端目视 | 无处于表决中的真实决议；有则请用户决定是否推迟 E2E | 非关键 |
| V-20 远程 E2E 结果（DEPLOY-010 后） | `e2e_remote_$TS.log` | `Ran 22`；0 失败；`RUN_EXIT=0`；skip 数符合预期 | 非关键（失败 → `DEPLOYED_WITH_ISSUES`） |
| V-21 清理验收（DEPLOY-011 后） | `status` 输出与 `REGISTRY_NOW` | e2e 计数全 0；`registry_counts` = `REGISTRY_BASE`；`claim_amount_max` = `1000000.00` | 关键 |
| V-22 E2E 期间无服务端异常 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '<DEPLOY-009 开始时间>' --no-pager \| grep -Ec 'Traceback'"` | 输出 `0`（`<…>` 由 E2 记录的本地值代入，先 echo 核对） | 非关键 |
| V-23 人工验证（不由 E2 执行） | e2e_test_report H-1 ~ H-9（小程序真机、确认弹窗、三套风格视觉、测试环境注销流程、全局配置写入、慢用例等） | 由用户在部署后完成；列入 deployment_report 遗留问题 | 非关键 |

## 需用户在授权时确认的事项

E2 执行前，PM 须逐项向用户说明并取得结论，写入 `special_instructions`（GR-B-001-F03、GR-D-003 条件）。UC-02 ~ UC-05 的任何一项未确认，不得执行 DEPLOY-009 ~ 011（DEPLOY-001 ~ 008 的服务器部署不依赖它们）。

| 编号 | 事项 | 说明与影响 | 选项（推荐项加粗） |
|---|---|---|---|
| UC-01 | 部署版本 | 当前 HEAD `afa1fe8`，约 134 项改动未提交（含迁移 0002、夹具、`tests/remote/`、`project_workspace/ocap_product_review/`）。部署依据哪个版本？push 另需用户明确同意（画像 P9） | **A. 用户确认提交（可不 push），按该 commit 用 `git archive` 打包**；B. 明确同意从工作区打包（记录 HEAD、状态摘要与 SHA256；包内容可能与任何提交不一致） |
| UC-02 | 夹具占用 3 套住宅的户主槽位 | `setup --units 3` 从清册中按 id 升序选 3 套"住宅类、无有效房屋关系、无待审申诉/申请"的专有部分，为 `e2e_` 用户建立 `Membership`（只写关系行，不改清册）。窗口期间，真实业主在这 3 套房屋认证时只能成为"产权业主"（户主槽位已被占）；cleanup 后恢复。DEPLOY-009 会先列出这 3 套的 id 与专有部分供你确认 | **同意**；不同意（则远程 E2E 不执行，标 BLOCKED） |
| UC-03 | 临时新增 2 名 `e2e_` 委员（+1 名业主代表） | `e2e_member`、`e2e_member2` 为委员席位、`e2e_rep` 为业主代表席位，窗口期间"在任人数"（半数决议分母）增加 2（业主代表不计入分母，module_design MOD-081）。若窗口内有真实的半数同意决议在表决/统计，分母会偏大 | **同意，且窗口内无进行中的半数决议（V-16）**；改期 |
| UC-04 | 手机号号段 `1990000xxxx` | 夹具账号占用 `1990000 0001 ~ 0010`（及批量用户 `…1001+`）；`setup` 先检查冲突，被非 `e2e_` 用户占用则报错退出；短信为 console 替身，不会外发 | **同意** |
| UC-05 | 窗口期间对真实用户的可见影响与时长 | ① 管理端"注册用户"列表出现 `e2e_*` 用户（含 25 个 `e2e_bulk_NN`）；② **公开决议列表出现 25 条标题 `e2e_决议NN` 的已通过决议，真实成员翻页会看到（可能占满第一页）**；③ 管理端审批流程/版式模板/内容出现 `e2e_` 项；④ 审计日志永久含 e2e 记录。预计窗口 ≈ setup 1~2 分钟 + E2E 约 5~10 分钟（本地自检 8~9 秒，远程经 frp/反代放大）+ cleanup 1~2 分钟，合计约 10~15 分钟 `[INFERRED]`；加慢用例 +31 分钟 | **在低峰时段执行，接受上述可见影响**；改期；缩小 `--bulk-resolutions`（会使 AC-161-01 翻页用例无法验证） |
| UC-06 | 远程不修改全局配置 `claim.amount_max`（Q-B-02） | 远程只验证默认上限 1,000,000.00 的边界、非管理员 403、非法值 400；"改为 500,000.00 再恢复"仅在本地测过。`status` 会校验 `claim_amount_max` 仍为默认 | **同意（保守）**；若要远程验证需用户明确授权放宽画像 P4-1，并由 `finally` 恢复 |
| UC-07 | 慢用例 TC-E2E-332 | 等待约 31 分钟验证小程序会话 31 分钟后仍有效（H-7） | **不跑（默认 SKIP，列人工清单）**；跑 |
| UC-08 | 小程序包 | 不在服务器部署范围；`uni build` 未验证，体验版提交/审核由用户人工完成 | **知悉** |
| UC-09 | 缺少测试数据的用例 | TC-E2E-328 需测试环境至少 1 份已生成报表，否则 SKIP；AC-150-02 远程不测（`--units 4` 才可测，H-6） | **知悉，接受 SKIP** |
| UC-10 | 授权形式 | 画像 P7：测试环境"部署需用户确认=是"。授权须由 PM 依据用户本轮消息写入 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true` 与环境名"测试"，且环境名与本计划一致 | 用户当轮明确授权 |

## 取值汇总：`[INFERRED]`

| 项 | 取值 | 依据/说明 |
|---|---|---|
| 停机时长 1~2 分钟、迁移 < 5 秒 | 估算 | 无 SQL 的元数据迁移；上批 31 秒停机，以实测为准 |
| E2E 窗口 10~15 分钟 | 估算 | 本地自检 22 条 8~9 秒，远程放大系数无实测 |
| ControlPersist 10m、建连重试 3 次 | 运维经验值 | M-DE-009 |
| 快照/备份保留 ≥ 7 天 | 沿用 ocap-deploy skill | — |
| `mysqldump --skip-ssl` 参数 | 沿用上批已验证做法（M-DE-008） | 画像未登记 `mysqldump` |
