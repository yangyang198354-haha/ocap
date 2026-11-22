<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T19:57:32+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_approval_flow/architecture/module_design.md</file>
    <file>project_workspace/ocap_approval_flow/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_approval_flow/development/implementation_plan.md</file>
    <file>project_workspace/ocap_approval_flow/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — 审批流程多步化与或/与签（ocap_approval_flow）

> **本轮不执行部署**。GROUP_E1 只产出计划；E2 必须在用户当轮明确授权后另行调用，且 invocation 的 `special_instructions` 必须含 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名（画像 P7“部署需用户确认=是”）。子代理不执行 commit / push（画像 P9）。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/apps/approval/{models,services,views,urls,apps}.py`；`backend/apps/{claims,income,resolutions}/views.py` | `backend/apps/approval/migrations/0003_approval_steps.py`（新建 3 表 + 2 表加字段 + 回填） | 无（Python 源码直接覆盖） | `ocap-backend` 停止 → 迁移 → 启动 |
| Web 前端 | `frontend/src/admin/AdminFlows.vue`、`admin/parts/StepsEditor.vue`、`portal/Tasks.vue`、`portal/ApprovalTimeline.vue`、`portal/ResolutionDetail.vue`、`shared/api.js`、`shared/labels.js` | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` | 替换静态目录 `/home/yangyang/ocap/web/ocap` |
| 微信小程序 | `miniprogram/pages/approvals/index.vue`、`detail.vue`、`pages.json`、`pages/me/index.vue`、`utils/api.js`、`utils/labels.js` | 无 | `UNI_INPUT_DIR=<repo>\miniprogram` + `UNI_OUTPUT_DIR=<临时目录>` 后 `npm run build:mp-weixin` | 仅构建；上传微信体验版由人工完成，不在本计划内 |
| MySQL `ocap` 库 | — | `approval 0003` | — | 迁移前备份 4 张审批表 |

## 目标环境与策略

- 环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`，画像 P7）。生产环境不存在。
- 策略：**recreate**（单实例、无法双版本并存；停机窗口内完成停服 → 覆盖代码 → 迁移 → 启动）。预计停机 1–3 分钟（取决于迁移回填耗时）；验证窗口紧接启动后执行。
- 不使用 Docker/容器、不做 rolling/blue-green/canary（画像 P7 无多实例与流量切换能力）。
- 不改 nginx 配置、不重启 nginx、不触碰 Freeark 的服务与目录。

## 变量与执行约定

| 变量 | 取值方式 | 用途 |
|---|---|---|
| `$SHA` | E2 时 `git rev-parse --short HEAD`（用户提交推送后的提交） | 制品命名、报告 |
| `$TS` | DEPLOY-001 目标机 `date +%Y%m%d%H%M%S` 输出 | 快照与制品命名、回滚锚点 |
| `$SCRATCH` | 开发机 `$env:TEMP\ocap_pkg_<SHA>` | 本地制品暂存 |
| `$OCAP_DEST` | `yangyang@192.168.31.51`（画像 P7） | ssh / scp 目标 |
| `$A` | `/home/yangyang/ocap` | 目标机应用根 |
| `AUX_ACTIVE` | PRE-05 检测到的 `ocap-run-due-jobs.timer` 等辅助单元；不存在则为空 | 停服/恢复 |

- 远端命令在 PowerShell 中用**单引号**整体传给 `ssh`，使 `$TS`、`$DB_PASSWORD` 等在目标机展开；涉及本地变量时用双引号并先 `echo` 完整命令核对（M-DE-通用：单引号内 `$VAR` 远端展开）。
- 凭据只从目标机 `/home/yangyang/ocap/backend/.env` 读取（`DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT`），不写入本文件、不回显；`mysqldump` 用 `MYSQL_PWD` 环境变量传递口令，避免出现在进程参数中。
- 每条 `DEPLOY` 失败即停止后续步骤，按“回滚步骤”从对应 `ROLLBACK` 逆序执行。

## 预检清单

| 编号 | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| PRE-01 | 待部署提交已推送 | 开发机：`git status --short`；`git log -1 --format='%h %s'`；`git rev-parse --short HEAD` | 工作区干净；`HEAD` 已推送到 `github.com/yangyang198354-haha/ocap` 的 `main`；记录 `$SHA`。当前 HEAD 为 `f7316cb`，本批改动尚未提交 → **E2 前必须由用户确认后提交并推送**，否则 BLOCKED |
| PRE-02 | CI 全绿 | GitHub Actions `CI`（3 个 job） | 全绿；后端仅允许 `test_tc_int_964` 预存在失败 |
| PRE-03 | 测试门控 | 读 `phase_status.md` | GROUP_A~D 均 APPROVED、GR-D-001=PASS |
| PRE-04 | 远端可达与磁盘 | `ssh $OCAP_DEST 'df -h /home | tail -1'` | 可用空间 > 1GB（快照 + 迁移回填） |
| PRE-05 | 服务与辅助单元状态 | `ssh $OCAP_DEST 'systemctl is-active ocap-backend; systemctl list-unit-files | grep -E "ocap-run-due-jobs\.(timer|service)" || true'` | `ocap-backend` 为 `active`；记录辅助单元清单到 `AUX_ACTIVE` |
| PRE-06 | 运行目录与本地状态 | `ssh $OCAP_DEST 'test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && test -f /home/yangyang/ocap/web/ocap/index.html && echo DIRS_OK'` | 输出 `DIRS_OK` |
| PRE-07 | 迁移基线 | `ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations approval; venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'` | `approval.0003` 未应用；`migrate --plan` **恰为 1 行** `approval.0003_approval_steps`。多于 1 行或其他 app 有未应用迁移 → 停止并上报（目标库状态与预期不符） |
| PRE-08 | 备份能力 | `ssh $OCAP_DEST 'command -v mysqldump && mkdir -p /home/yangyang/ocap/snapshots && df -h /home | tail -1'` | `mysqldump` 存在；快照目录可写 |
| PRE-09 | Web 锚点 | `ssh $OCAP_DEST 'sha256sum /home/yangyang/ocap/web/ocap/index.html; sha256sum /home/yangyang/ocap/backend/.env'` | 两个 SHA256 非空并记入部署报告（`.env` 仅记录哈希，不记录内容） |
| PRE-10 | nginx 配置 | `ssh $OCAP_DEST 'sudo -n nginx -t'` | `syntax is ok`；记录备份文件数 `ls /etc/nginx/sites-available/ocap.bak_* | wc -l` |
| PRE-11 | 目标机本地状态不被覆盖 | 核对 DEPLOY-002 制品清单 | 后端 tar 中 `^\./(venv|var|\.env)` 计数为 0；Web tar 不含目标机上传目录（本批不触碰 `var/`） |
| PRE-12 | E2 授权 | 读取本次 E2 invocation 的 `special_instructions` | 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与“测试”环境名；计划版本 = `phase_status` 中 APPROVED 版本；否则 BLOCKED，不执行任何命令 |

## 部署步骤

### DEPLOY-001: 生成回滚锚点（目标机，只读 + 快照）
- 组件：后端源码、Web 静态产物、数据库 4 张审批表、迁移计划、nginx 备份
- 位置：目标机
- 命令（以 `bash -s` 通过 ssh 执行，避免引号展开问题；`Get-Content -Raw anchor.sh | ssh $OCAP_DEST "bash -s"`）：
```bash
set -e
TS=$(date +%Y%m%d%H%M%S); A=/home/yangyang/ocap; mkdir -p $A/snapshots
tar czf $A/snapshots/backend-$TS.tar.gz --exclude='backend/venv' --exclude='backend/var' --exclude='backend/.env' --exclude='backend/.env.*' --exclude='__pycache__' -C $A backend
tar czf $A/snapshots/web-$TS.tar.gz -C $A web
cd $A/backend && set -a && . ./.env && set +a
venv/bin/python manage.py showmigrations --plan > $A/snapshots/migplan-$TS.txt
MYSQL_PWD="$DB_PASSWORD" mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl "$DB_NAME" \
  approval_approvalflow approval_flowapprover approval_approvalinstance approval_approvalaction > $A/snapshots/approval-$TS.sql
chmod 600 $A/snapshots/approval-$TS.sql
sudo cp -p /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS
echo "ANCHOR_TS=$TS"
ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/migplan-$TS.txt $A/snapshots/approval-$TS.sql
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/approval-$TS.sql
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -cE '^backend/(\.env|venv/|var/)' || true
grep -c 'approval.0003' $A/snapshots/migplan-$TS.txt || true
grep -c 'CREATE TABLE' $A/snapshots/approval-$TS.sql
```
- 预期：输出 `ANCHOR_TS=<14 位>`；4 个文件非零；3 个 SHA256 非空；排除项计数 `0`；基线 `approval.0003` 计数 `0`；转储含 `CREATE TABLE` 计数 `4`。`TS` 与 SHA256 记入部署报告；快照保留 ≥ 7 天。
- 失败且目标机无变更 → `DEPLOYMENT_FAILED`，无需回滚。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建与打包（不触碰目标机）
- 组件：后端源码包、Web 构建产物
- 位置：开发机
- 命令：
```powershell
$SHA = git rev-parse --short HEAD
$SCRATCH = "$env:TEMP\ocap_pkg_$SHA"
New-Item -ItemType Directory -Force $SCRATCH | Out-Null
$env:VITE_API_BASE = '/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
if ($LASTEXITCODE -ne 0) { throw 'WEB_BUILD_FAILED' }
(Select-String -Path frontend\dist\assets\*.js -Pattern '或签（任一通过）' -List | Measure-Object).Count   # 须 >= 1
(Select-String -Path frontend\dist\assets\*.js -Pattern '审批过程' -List | Measure-Object).Count         # 须 >= 1
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='.env.*' --exclude='var' --exclude='db.sqlite3' `
    -czf "$SCRATCH\backend_${SHA}_<TS>.tar.gz" -C backend .
$listing = tar tzf "$SCRATCH\backend_${SHA}_<TS>.tar.gz"
($listing | Select-String -Pattern '^\./apps/approval/(services|models)\.py$|^\./apps/approval/migrations/0003_approval_steps\.py$').Count   # 须 3
($listing | Select-String -Pattern '(^|/)\.env(\.|$)|^\./venv/|^\./var/').Count   # 须 0
tar -czf "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" -C frontend/dist .
(Get-ChildItem -Recurse -File frontend\dist).Count
Get-FileHash "$SCRATCH\backend_${SHA}_<TS>.tar.gz", "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz", frontend\dist\index.html -Algorithm SHA256 | Format-Table Hash, Path
```
- 预期：`✓ built` 且退出码 0；两个文案计数均 ≥ 1（本批次实测各 `4`）；后端关键路径计数 `3`；排除项计数 `0`；`dist` 文件数、3 个 SHA256 记入报告。门槛不过 → 停止，不上传（目标机无变更）。
- 说明：`ts` 需在 DEPLOY-001 取得后代入；可在取锚点前先构建、取得 `TS` 后再按含 `TS` 的文件名打包/重命名，以缩短停机窗口。
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并暂存（开发机 → 目标机 `/tmp`）
- 位置：开发机 → 目标机
- 命令：
```powershell
scp "$SCRATCH\backend_${SHA}_<TS>.tar.gz" "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" "$OCAP_DEST:/tmp/"
ssh $OCAP_DEST "sha256sum /tmp/backend_${SHA}_<TS>.tar.gz /tmp/frontend_dist_${SHA}_<TS>.tar.gz"   # 须与 DEPLOY-002 一致
ssh $OCAP_DEST "rm -rf /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && mkdir /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && tar xzf /tmp/backend_${SHA}_<TS>.tar.gz -C /tmp/ocap_backend_stage_<TS> && tar xzf /tmp/frontend_dist_${SHA}_<TS>.tar.gz -C /tmp/ocap_web_stage_<TS> && test -f /tmp/ocap_backend_stage_<TS>/manage.py && test -f /tmp/ocap_backend_stage_<TS>/apps/approval/migrations/0003_approval_steps.py; ls -a /tmp/ocap_backend_stage_<TS> | grep -c '^\.env' || true"
```
- 预期：两端 SHA256 一致；暂存后端含 `manage.py` 与 `0003_approval_steps.py`；`.env*` 计数 `0`；暂存前端文件数 = DEPLOY-002 的 `dist` 文件数。不符 → 停止，按 ROLLBACK-003 清理暂存，`DEPLOYMENT_FAILED`。
- 回滚: ROLLBACK-003

### DEPLOY-004: 停止后端与辅助单元（目标机首个状态变更点）
- 组件：systemd `ocap-backend`（及 PRE-05 检测到的 `AUX_ACTIVE`）
- 位置：目标机
- 命令：
```powershell
$AUX = '<PRE-05 记录的辅助单元，空格分隔>'
ssh $OCAP_DEST "for u in $AUX; do sudo systemctl stop \$u; done; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend || true; for u in $AUX; do systemctl is-active \$u || true; done"
```
- 预期：`ocap-backend` 与 `AUX` 均 `inactive`。`stop` 已执行而后续 `cp` 失败 → 目标机已有变更，**立即**从 ROLLBACK-004 起回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 覆盖后端代码（保留 `.env` / `venv` / `var`）
- 组件：`/home/yangyang/ocap/backend`
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST "cp -a /tmp/ocap_backend_stage_<TS>/. /home/yangyang/ocap/backend/ && test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && ls -l /home/yangyang/ocap/backend/apps/approval/migrations/0003_approval_steps.py && sha256sum /home/yangyang/ocap/backend/.env"
```
- 预期：命令成功；迁移文件存在；`.env` SHA256 = PRE-09 记录值（制品不含 `.env`，`cp -a` 不会覆盖）。本批后端无删除文件（`git status` 无 `D`），叠加覆盖不需要清理旧文件。
- 回滚: ROLLBACK-005

### DEPLOY-006: 数据库迁移 `approval 0003`（目标机 MySQL）
`[MANUAL_ROLLBACK_REQUIRED（条件触发）: 回滚时若已存在多步流程/会签步骤/步骤状态 step_order>1，或已产生 schema_version=2 的在办实例，反向迁移会丢失步骤数据并使旧代码无法处理这些实例；此时不得自动反向，见 ROLLBACK-006。MySQL DDL 非事务，迁移中途失败可能留下半应用结构，须按 DEPLOY-001 的转储人工核对。]`
- 组件：数据层（module_design「数据迁移」）；3 张新表 + 2 张表加字段 + 回填
- 位置：目标机
- 命令（先门控，后执行）：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'
```
  **门控**：输出必须**恰为 1 行** `approval.0003_approval_steps`，否则停止，不执行 `migrate`，按 ROLLBACK-005 起回滚代码。通过后：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -10; venv/bin/python manage.py showmigrations approval'
```
  **schema 校验**（写 `%TEMP%\approval_schema_check.py` 后经 stdin 传入）：
```python
from django.db import connection
from apps.approval.models import ApprovalFlow, ApprovalInstance, ApprovalStep, ApprovalStepState

names = set(connection.introspection.table_names())
cur = connection.cursor()
cols = lambda t: {c.name for c in connection.introspection.get_table_description(cur, t)}
print("TABLES_OK", {"approval_approvalstep", "approval_stepapprover", "approval_approvalstepstate"} <= names)
print("INSTANCE_COL", "current_step_order" in cols("approval_approvalinstance"))
print("ACTION_COLS", {"step_state_id", "step_order"} <= cols("approval_approvalaction"))
print("STEP_COUNT", ApprovalStep.objects.count())
print("DESIGNATED_FLOWS", ApprovalFlow.objects.filter(mode="DESIGNATED").count())
print("PENDING_DESIGNATED_NO_STATE", ApprovalInstance.objects.filter(
    status="PENDING", flow__mode="DESIGNATED", step_states__isnull=True).distinct().count())
print("MULTI_STEP_FLOWS", ApprovalFlow.objects.filter(steps__order__gt=1).distinct().count())
print("STEP_STATE_GT1", ApprovalStepState.objects.filter(step_order__gt=1).count())
```
```powershell
Get-Content -Raw "$env:TEMP\approval_schema_check.py" | ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell'
```
- 预期：`Applying approval.0003_approval_steps... OK`；`showmigrations` 中 `[X]`；`TABLES_OK True`、`INSTANCE_COL True`、`ACTION_COLS True`、`STEP_COUNT` = `DESIGNATED_FLOWS`、`PENDING_DESIGNATED_NO_STATE 0`、`MULTI_STEP_FLOWS 0`、`STEP_STATE_GT1 0`（后两项是回滚安全条件，记入报告）。迁移失败或 schema 不符 → 目标机已有变更，从 ROLLBACK-006 起逆序回滚（先只读查询状态，不盲目重试）。
- 回滚: ROLLBACK-006

### DEPLOY-007: 启动后端并检查日志
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST "sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend && systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID; for u in $AUX; do sudo systemctl start \$u; done; systemctl is-active ocap-backend"
ssh $OCAP_DEST "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -30"
```
- 预期：`active`；`ActiveEnterTimestamp` 与 PRE-05 时不同；`AUX`（如存在）恢复 `active`；日志无 `Traceback`、无 `ERROR`、无 `no such column` / `Unknown column` / `doesn't exist`。失败 → 从 ROLLBACK-007 起逆序回滚。
- 回滚: ROLLBACK-007

### DEPLOY-008: 后端只读验证
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST 'curl -s -o /dev/null -w "API_ME=%{http_code}\n" http://127.0.0.1:9000/api/v1/me; curl -s -o /dev/null -w "API_TASKS=%{http_code}\n" http://127.0.0.1:9000/api/v1/approval/tasks; curl -s -o /dev/null -w "API_INSTANCE=%{http_code}\n" http://127.0.0.1:9000/api/v1/approval/instances/1'
```
- 预期：未带令牌时三者均为 `401`（证明新路由已加载且鉴权生效）；若返回 `404` 说明代码未正确覆盖或服务未重启，停止并回滚。全部通过才继续 DEPLOY-009。
- 回滚: ROLLBACK-008

### DEPLOY-009: 替换 Web 静态目录
- 组件：`/home/yangyang/ocap/web/ocap`（nginx `ocap` 站点，不改配置）
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap/web && rm -rf ocap.new && mkdir ocap.new && tar xzf /tmp/frontend_dist_${SHA}_<TS>.tar.gz -C ocap.new && rm -rf ocap.old && mv ocap ocap.old && mv ocap.new ocap && echo WEB_SWAPPED && ls -l ocap/index.html && find ocap -type f | wc -l && sha256sum ocap/index.html"
```
- 预期：`WEB_SWAPPED`；文件数 = 本地 `dist`；`index.html` SHA256 = 本地。`mv ocap ocap.old` 已执行而后续失败 → 立即从 ROLLBACK-009 起回滚（优先 `mv ocap.old ocap`）。
- 回滚: ROLLBACK-009

### DEPLOY-010: Web 与入口验证
- 位置：目标机
- 命令见“部署后验证”表 V-05~V-09。
- 预期：全部 PASS；失败 → ROLLBACK-009。
- 回滚: ROLLBACK-010

### DEPLOY-011: 构建小程序产物（开发机，不部署、不上传）
- 组件：微信小程序（MOD-190）
- 位置：开发机
- 命令：
```powershell
$env:UNI_INPUT_DIR = 'C:\Users\胖子熊\MyProject\ocap\miniprogram'
$env:UNI_OUTPUT_DIR = "$env:TEMP\ocap_mp_build_<TS>"
npm --prefix miniprogram run build:mp-weixin
if ($LASTEXITCODE -ne 0) { throw 'MP_BUILD_FAILED' }
if (-not (Test-Path "$env:UNI_OUTPUT_DIR\app.json")) { throw 'MP_APP_JSON_MISSING' }
(Get-ChildItem -Recurse -Filter *.js $env:UNI_OUTPUT_DIR | Select-String -Pattern '或签（任一通过）' -List | Measure-Object).Count   # 须 >= 1
```
- 预期：`DONE Build complete.`、退出码 0、`app.json` 存在、文案计数 ≥ 1。仅供微信开发者工具导入与人工上传，**不写入仓库、不进入目标机**。
- 说明（CO-001）：不要直接在该目录运行 `npm run build:mp-weixin` 而不设 `UNI_INPUT_DIR`，否则 uni-app 会查找不存在的 `src/manifest.json`。本批次已按上述方式实测通过。
- 回滚: ROLLBACK-011

### DEPLOY-012: 部署后冒烟与人工验证（只读）
- 位置：目标机 / 浏览器 / 微信开发者工具
- 执行“部署后验证”表 V-01~V-10；人工验证清单见文末。
- 回滚: ROLLBACK-012

## 回滚步骤（逆序）

### ROLLBACK-012: 反向回滚 DEPLOY-012
- 类型：正式回滚（无操作）
- 说明：只读验证，无状态变更；若冒烟失败，按失败项定位到 ROLLBACK-009（前端）或 ROLLBACK-006 起（后端/数据）。

### ROLLBACK-011: 清理小程序临时产物
- 类型：正式回滚
- 命令：`Remove-Item -Recurse -Force "$env:TEMP\ocap_mp_build_<TS>"`
- 预期：临时目录不存在；仓库与目标机均无变更。

### ROLLBACK-010: 反向回滚 DEPLOY-010
- 类型：正式回滚（无操作）
- 说明：只读验证；失败时执行 ROLLBACK-009。

### ROLLBACK-009: 恢复旧 Web 静态产物
- 类型：正式回滚
- 命令（优先目录交换，其次快照解包）：
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap/web && if [ -d ocap.old ]; then rm -rf ocap && mv ocap.old ocap && echo WEB_RESTORED_BY_SWAP; else rm -rf ocap && tar xzf /home/yangyang/ocap/snapshots/web-<TS>.tar.gz -C /home/yangyang/ocap/web && echo WEB_RESTORED_BY_SNAPSHOT; fi; sha256sum ocap/index.html"
```
- 变量取值与核验：`<TS>` 取自 DEPLOY-001 报告；执行前 `tar tzf /home/yangyang/ocap/snapshots/web-<TS>.tar.gz | grep -c '^web/ocap/index.html$'` 须为 `1`。
- 预期：`WEB_RESTORED_*`；`index.html` SHA256 = PRE-09 记录值。

### ROLLBACK-008: 反向回滚 DEPLOY-008
- 类型：正式回滚（无操作）
- 说明：只读验证；失败时执行 ROLLBACK-007 与 ROLLBACK-005。

### ROLLBACK-007: 停止后端（为回滚代码/迁移做准备）
- 类型：正式回滚
- 命令：`ssh $OCAP_DEST "sudo systemctl stop ocap-backend; systemctl is-active ocap-backend || true"`
- 预期：`inactive`。

### ROLLBACK-006: 迁移回滚（条件执行；默认人工）
- 类型：正式回滚 / `[MANUAL_ROLLBACK_REQUIRED]`
- 前置判定（只读）：
```powershell
Get-Content -Raw "$env:TEMP\approval_schema_check.py" | ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell'
```
  - `MULTI_STEP_FLOWS 0` 且 `STEP_STATE_GT1 0` 且不存在 `strategy="ALL"` 的步骤，且部署后未产生 `flow_snapshot.schema_version=2` 的在办实例 → 可执行反向：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate approval 0002 --noinput 2>&1 | tail -5; venv/bin/python manage.py showmigrations approval'
```
    预期：`Unapplying approval.0003_approval_steps... OK`；`approval.0003` 变回 `[ ]`。反向会删除 3 张新表与 2 个字段，并丢失步骤名/策略；`FlowApprover` 由迁移写回（数据源为备份转储，若写回不完整按转储补齐）。
  - **任一不满足** → 停止自动回滚，标 `[MANUAL_ROLLBACK_REQUIRED]`：多步配置或 v2 在办实例已存在，反向会丢数据且旧代码无法处理 v2 快照。人工选项：保留新后端代码并前滚修复、或导出并清理这些实例后反向。**不得直接反向迁移。**

### ROLLBACK-005: 恢复后端代码快照
- 类型：正式回滚
- 命令：
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap && tar xzf snapshots/backend-<TS>.tar.gz -C /home/yangyang/ocap && test -f backend/manage.py && test -x backend/venv/bin/python && sha256sum backend/.env && ls backend/apps/approval/migrations/ | tail -5"
```
- 变量取值与核验：`<TS>` 来自 DEPLOY-001；快照不含 `.env`/`venv`/`var`，解包为叠加覆盖，**不删除**目标机本地文件。
- 预期：`.env` SHA256 = PRE-09；`0003_approval_steps.py` 仍存在（快照后新增文件不被旧代码引用，保留无害；如需彻底清理需人工确认）。
- 注意：不能单独恢复代码而不处理迁移——旧代码读取 v2 快照会失败，必须与 ROLLBACK-006 的判定结果一起决定顺序。

### ROLLBACK-004: 恢复停机前状态
- 类型：正式回滚
- 命令：
```powershell
ssh $OCAP_DEST "sudo systemctl start ocap-backend; for u in $AUX; do sudo systemctl start \$u; done; systemctl is-active ocap-backend"
```
- 说明：仅在“只执行了 DEPLOY-004、未覆盖代码/未迁移”时执行；若已部署代码或迁移，必须先完成 ROLLBACK-006/005，再启动。

### ROLLBACK-003: 清理远端暂存
- 类型：正式回滚
- 命令：`ssh $OCAP_DEST "rm -rf /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> /tmp/backend_<SHA>_<TS>.tar.gz /tmp/frontend_dist_<SHA>_<TS>.tar.gz"`
- 预期：文件与目录不存在。

### ROLLBACK-002: 清理本地制品
- 类型：正式回滚
- 命令：`Remove-Item -Recurse -Force "$SCRATCH"`
- 预期：本地暂存目录不存在。

### ROLLBACK-001: 锚点处置
- 类型：正式回滚（无操作）
- 说明：快照、哈希清单、迁移计划、转储与 nginx 备份保留 ≥ 7 天用于追溯；不得在回滚完成前删除。

## 不可逆步骤汇总

| 步骤 | 不可逆点 | 处置 |
|---|---|---|
| DEPLOY-006 | 数据回填把旧流程折算为 1 步；反向迁移会删除步骤名/策略/步骤状态 | 迁移前备份 4 张表；反向仅在单步 ANY、无 v2 在办实例时执行；否则 `[MANUAL_ROLLBACK_REQUIRED]` |
| DEPLOY-006 | MySQL DDL 非事务，中途失败可能留下半应用结构 | 不盲目重试；用 `showmigrations` + `approval_schema_check.py` + 转储人工核对后决定 |
| DEPLOY-005 + DEPLOY-006 组合 | 部署后新建的 `schema_version=2` 在办实例无法被旧代码处理 | 回滚前统计；存在则人工决定前滚或清理实例 |
| DEPLOY-009 | 浏览器可能缓存旧 `index.html` | 发布后提示强刷（Ctrl+F5）；`ocap.old` 保留至验证通过 |
| 小程序上传（不在本计划） | 微信平台上传后不可撤回 | 仅在微信开发者工具人工确认后上传 |
| nginx 备份清理 | 删除 `ocap.bak_TS` 后无法回到旧配置 | 本次不改 nginx，不清理备份 |

## 部署后验证

| 编号 | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `ssh $OCAP_DEST 'systemctl is-active ocap-backend'` | `active` |
| V-02 | 日志无新错误 | `ssh $OCAP_DEST "sudo journalctl -u ocap-backend --since '-5 min' --no-pager | grep -cE 'Traceback|ERROR|Unknown column|no such column'"` | `0` |
| V-03 | 新表/字段 | `approval_schema_check.py` | `TABLES_OK True`、`INSTANCE_COL True`、`ACTION_COLS True` |
| V-04 | 回填完整 | 同上 | `STEP_COUNT` = `DESIGNATED_FLOWS`；`PENDING_DESIGNATED_NO_STATE 0` |
| V-05 | 新路由鉴权 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/approval/tasks` | `401` |
| V-06 | 时间线路由鉴权 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/approval/instances/1` | `401` |
| V-07 | Web 首页 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | `200` |
| V-08 | 新文案在产物中 | `ssh $OCAP_DEST 'grep -rl "或签（任一通过）" /home/yangyang/ocap/web/ocap/assets | head -1'` | 输出非空 |
| V-09 | 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200` |
| V-10 | 小程序产物（本地） | `Test-Path "$env:UNI_OUTPUT_DIR\app.json"` | `True` |
| V-11 | 前端主资源 | 从 `index.html` 取引用的 `assets/index-*.js`，`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/<路径>` | `200` |

### 人工验证清单（自动化测试无法覆盖）

| 编号 | 对应 AC | 步骤 | 预期结果 | 所需环境 | critical path |
|---|---|---|---|---|---|
| MV-01 | AC-316-01~325-01 | 管理员登录 → 审批流程 → 新建 2 步流程（初审/终审），分别设 ANY、ALL 与审批人 → 保存 | 列表显示 `step_count=2`，步骤名与策略正确 | 浏览器 + 管理员账号 | 是 |
| MV-02 | AC-320-01~323-01 | 发起决议 → 第 1 步任一审批人通过 → 第 2 步全部通过 | 决议最终“通过”；每步状态与时间线正确 | 浏览器 + 3 个委员账号 | 是 |
| MV-03 | AC-321-03 | 会签步骤中一人拒绝 | 整单“拒绝”，后续步骤保持未开始 | 浏览器 + 委员账号 | 是 |
| MV-04 | AC-328-01~329-02 | 发起人、历史审批人、无关用户分别打开审批过程 | 前两者可见备注与时间；无关用户提示无权查看 | 浏览器 + 3 类账号 | 是 |
| MV-05 | REQ-NFUNC-064（M-01） | 两名审批人几乎同时提交会签步骤的“通过”（建议用两个浏览器窗口） | 仅推进一次，不重复推进；时间线各一条动作 | MySQL 真实行锁环境 | 是 |
| MV-06 | AC-331-01~331-02 | 小程序“待我审批”→ 审批 → 查看时间线 | 与 Web 同字段、同文案 | 微信开发者工具 | 是 |
