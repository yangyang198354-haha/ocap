<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-24T23:28:54+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_multi_account_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_multi_account_ux/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/integration_test_report.md</file>
    <file>project_workspace/ocap_multi_account_ux/testing/e2e_test_report.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — 多账户落账与财务报表 UI（ocap_multi_account_ux）

> **本轮不执行部署**。GROUP_E1 只产出计划；E2 必须在用户当轮明确授权后另行调用，且 invocation 的 `special_instructions` 必须含 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名（画像 P7“部署需用户确认=是”）。子代理不执行 commit / push / ssh / 部署（画像 P9）。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/apps/ledger/{models,services,views,urls,historical,apps}.py`；`backend/apps/income/views.py`；`backend/apps/claims/views.py`；`backend/apps/approval/services.py` | `backend/apps/ledger/migrations/0008_historical_expense_approval.py`（新增 3 个可空字段 + 2 处仅 choices/default 的 AlterField，无回填） | 无（Python 源码直接覆盖） | `ocap-backend` 停止 → 迁移 → 启动 |
| Web 前端 | 新建 `frontend/src/shared/AccountSelect.vue`；修改 `portal/{Reports,AccountCard,ReportDetailDialog,Income,Claims,HistoricalExpenses}.vue`、`admin/AdminAccounts.vue`、`shared/api.js`、`shared/confirm.js` | 无 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 替换静态目录 `/home/yangyang/ocap/web/ocap` |
| 微信小程序 | `miniprogram/pages/claims/index.vue`、`miniprogram/utils/api.js` | 无 | `UNI_INPUT_DIR=<repo>\miniprogram` + `npm run build:mp-weixin`（产物到临时目录） | 仅构建；上传体验版由人工完成，不在本计划内 |
| MySQL `ocap` 库 | — | `ledger 0008` | — | 迁移前备份 2 张历史支出表 |

迁移细节（MOD-207）：`HistoricalExpenseBatch` 增加 `account`（FK `LedgerAccount`，`null=True, blank=True, on_delete=PROTECT`）、`approval_instance_id`（BigInteger，可空）、`decided_at`（DateTime，可空）；批次 `status` 与行 `status` 的 `choices/default` 变化不产生数据库 DDL。现有批次（`IMPORTED`/`VOIDED`、`account=NULL`）不需要回填，旧语义保持可读（`IMPORTED`、`VOIDED` 仍在 choices 中）。迁移可逆（反向 `RemoveField` + 还原 choices），回滚会**丢失**新批次写入的账户/审批关联。

## 目标环境与策略

- 环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`，画像 P7）。生产环境不存在。
- 策略：**recreate**（单实例、无法双版本并存；停机窗口内完成停服 → 覆盖代码 → 迁移 → 启动）。预计停机 1–3 分钟（0008 仅 3 个可空列，无回填）；验证窗口紧接启动后执行。
- 不使用 Docker/容器、不做 rolling/blue-green/canary（画像 P7 无多实例与流量切换能力）。
- 不改 nginx 配置、不重启 nginx、不触碰 Freeark 的服务与目录；`var/` 与上传文件不被触碰。

## 变量与执行约定

| 变量 | 取值方式 | 用途 |
|---|---|---|
| `$SHA` | E2 时 `git rev-parse --short HEAD`（用户提交推送后的提交） | 制品命名、报告 |
| `$TS` | DEPLOY-001 目标机 `date +%Y%m%d%H%M%S` 输出 | 快照与制品命名、回滚锚点 |
| `$SCRATCH` | 开发机 `$env:TEMP\ocap_pkg_<SHA>` | 本地制品暂存 |
| `$OCAP_DEST` | `yangyang@192.168.31.51`（画像 P7） | ssh / scp 目标 |
| `$A` | `/home/yangyang/ocap` | 目标机应用根 |
| `$AUX` | PRE-05 检测到的 `ocap-run-due-jobs.timer` 等辅助单元；不存在则为空 | 停服/恢复 |

- 远端命令在 PowerShell 中用**单引号**整体传给 `ssh`，使 `$TS`、`$DB_PASSWORD` 等在目标机展开；涉及本地变量时用双引号并先 `echo` 完整命令核对（M-DE-050：单引号内 `$VAR` 远端展开）。
- 凭据只从目标机 `/home/yangyang/ocap/backend/.env` 读取（`DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT`），不写入本文件、不回显；`mysqldump` 用 `MYSQL_PWD` 环境变量传递口令，避免出现在进程参数中。
- 每条 `DEPLOY` 失败即停止后续步骤，按“回滚步骤”从对应 `ROLLBACK` 逆序执行。

## 预检清单

| 编号 | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| PRE-01 | 待部署提交已推送、工作区干净 | 开发机：`git status --short`；`git log -1 --format='%h %s'`；`git rev-parse --short HEAD` | 工作区干净（DEPLOY-002 会再次强制校验）；`HEAD` 已推送到 `github.com/yangyang198354-haha/ocap` 的 `main`；记录 `$SHA`。当前 HEAD 为 `6bd59e1`，本批改动与任务前既有改动（如 `backend/apps/core/audit.py`）均未提交 → **E2 前必须由用户确认提交范围并推送**，否则 BLOCKED |
| PRE-02 | CI 全绿 | GitHub Actions `CI`（3 个 job） | 全绿（`backend` 在 Django 5.2 下 1256 条零失败） |
| PRE-03 | 测试门控 | 读 `phase_status.md` | GROUP_A~D 均 APPROVED、GR-D-001=PASS_WITH_CONDITIONS |
| PRE-04 | 远端可达与磁盘 | `ssh $OCAP_DEST 'df -h /home | tail -1'` | 可用空间 > 1GB（代码/Web 快照 + 转储） |
| PRE-05 | 服务与辅助单元状态 | `ssh $OCAP_DEST 'systemctl is-active ocap-backend; systemctl list-unit-files | grep -E "ocap-run-due-jobs\.(timer|service)" || true'` | `ocap-backend` 为 `active`；记录辅助单元清单到 `$AUX` |
| PRE-06 | 运行目录与本地状态 | `ssh $OCAP_DEST 'test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && test -f /home/yangyang/ocap/web/ocap/index.html && echo DIRS_OK'` | 输出 `DIRS_OK` |
| PRE-07 | 迁移基线与旧数据状态 | 见下方“PRE-07 只读脚本” + `manage.py showmigrations ledger` / `migrate --plan` | `ledger.0008` 未应用；`migrate --plan` **恰为 1 行** `ledger.0008_historical_expense_approval`；`BATCH_TOTAL`/`BATCH_NULL_ACCOUNT`/`BATCH_STATUSES`/`ROW_STATUSES` 记录为基线，状态取值 ⊆ `{IMPORTED, VOIDED}`、批次 `account` 全为 NULL。多于 1 行或其他 app 有未应用迁移 → 停止并上报 |
| PRE-08 | 备份能力 | `ssh $OCAP_DEST 'command -v mysqldump && mkdir -p /home/yangyang/ocap/snapshots && df -h /home | tail -1'` | `mysqldump` 存在；快照目录可写 |
| PRE-09 | Web 与配置锚点 | `ssh $OCAP_DEST 'sha256sum /home/yangyang/ocap/web/ocap/index.html; sha256sum /home/yangyang/ocap/backend/.env'` | 两个 SHA256 非空并记入部署报告（`.env` 仅记录哈希，不记录内容） |
| PRE-10 | 账户数据可用性 | 见下方“PRE-07 只读脚本”中的 `ACCOUNTS_ENABLED` / `DEFAULT_ACCOUNTS` | 启用账户 ≥ 1；默认账户 = 1（为 0 时记录并转人工确认：AC-416 的默认选中会退化为第一个账户，不阻断启动） |
| PRE-11 | 制品排除本地状态 | 核对 DEPLOY-002 制品清单 | 后端 tar 中 `^\./(venv|var|\.env)` 计数为 0；Web tar 不含目标机上传目录（本批不触碰 `var/`） |
| PRE-12 | 小程序构建前置 | 开发机 `Test-Path miniprogram/manifest.json` | `True`（配合 `UNI_INPUT_DIR` 使用） |
| PRE-13 | E2 授权 | 读取本次 E2 invocation 的 `special_instructions` | 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与“测试”环境名；计划版本 = `phase_status` 中 APPROVED 版本；否则 BLOCKED，不执行任何命令 |

**PRE-07 / PRE-10 只读脚本**（写 `%TEMP%\ocap_ledger_baseline.py` 后经 stdin 传入 `manage.py shell`；全部用原始 SQL，避免旧模型无 `account` 字段导致 `FieldError`）：

```python
from django.db import connection

cur = connection.cursor()
def one(sql):
    cur.execute(sql)
    return cur.fetchone()[0]
def column(sql):
    cur.execute(sql)
    return [r[0] for r in cur.fetchall()]

tables = set(connection.introspection.table_names())
print("TABLES_PRESENT", {"ledger_historicalexpensebatch", "ledger_historicalexpenserow"} <= tables)
print("BATCH_TOTAL", one("SELECT COUNT(*) FROM ledger_historicalexpensebatch"))
print("BATCH_STATUSES", sorted(set(column("SELECT DISTINCT status FROM ledger_historicalexpensebatch"))))
print("ROW_STATUSES", sorted(set(column("SELECT DISTINCT status FROM ledger_historicalexpenserow"))))
has_account = "account_id" in {c.name for c in connection.introspection.get_table_description(cur, "ledger_historicalexpensebatch")}
print("HAS_ACCOUNT_COL", has_account)
print("BATCH_ACCOUNT_NULL", one("SELECT COUNT(*) FROM ledger_historicalexpensebatch WHERE account_id IS NULL") if has_account else "N/A_BEFORE_MIGRATION")
print("ACCOUNTS_ENABLED", one("SELECT COUNT(*) FROM ledger_ledgeraccount WHERE status='ENABLED'"))
print("DEFAULT_ACCOUNTS", one("SELECT COUNT(*) FROM ledger_ledgeraccount WHERE status='ENABLED' AND is_default=1"))
```

- 迁移前 `HAS_ACCOUNT_COL False`、`BATCH_ACCOUNT_NULL N/A_BEFORE_MIGRATION` 属预期；`BATCH_TOTAL` 与 `BATCH_STATUSES` 即为兼容性基线。

## 部署步骤

### DEPLOY-001: 生成回滚锚点（目标机，只读 + 快照）
- 组件：后端源码、Web 静态产物、历史支出 2 张表、迁移计划
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
  ledger_historicalexpensebatch ledger_historicalexpenserow > $A/snapshots/ledger-history-$TS.sql
chmod 600 $A/snapshots/ledger-history-$TS.sql
echo "ANCHOR_TS=$TS"
ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/migplan-$TS.txt $A/snapshots/ledger-history-$TS.sql
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/ledger-history-$TS.sql
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -cE '^backend/(\.env|venv/|var/)' || true
grep -c 'ledger.0008' $A/snapshots/migplan-$TS.txt || true
grep -c 'CREATE TABLE' $A/snapshots/ledger-history-$TS.sql
```
- 预期：输出 `ANCHOR_TS=<14 位>`；4 个文件非零；3 个 SHA256 非空；排除项计数 `0`；基线 `ledger.0008` 计数 `0`；转储含 `CREATE TABLE` 计数 `2`。`TS` 与 SHA256 记入部署报告；快照保留 ≥ 7 天。
- 失败且目标机无变更 → `DEPLOYMENT_FAILED`，无需回滚。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建与打包（不触碰目标机）
- 组件：后端源码包、Web 构建产物
- 位置：开发机
- 命令：
```powershell
if (git status --porcelain) { throw 'WORKTREE_DIRTY' }
$SHA = git rev-parse --short HEAD
$SCRATCH = "$env:TEMP\ocap_pkg_$SHA"
New-Item -ItemType Directory -Force $SCRATCH | Out-Null
$env:VITE_API_BASE = '/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
if ($LASTEXITCODE -ne 0) { throw 'WEB_BUILD_FAILED' }
(Select-String -Path frontend\dist\assets\* -Pattern '暂无可用账户' -List | Measure-Object).Count     # 须 >= 1（AccountSelect）
(Select-String -Path frontend\dist\assets\* -Pattern '审批通过后才写入台账' -List | Measure-Object).Count   # 须 >= 1（历史支出新文案）
(Select-String -Path frontend\dist\assets\* -Pattern 'reports-account-grid' -List | Measure-Object).Count    # 须 >= 1（报表卡片网格）
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='.env.*' --exclude='var' --exclude='db.sqlite3' `
    -czf "$SCRATCH\backend_${SHA}_<TS>.tar.gz" -C backend .
$listing = tar tzf "$SCRATCH\backend_${SHA}_<TS>.tar.gz"
($listing | Select-String -Pattern '^\./apps/ledger/migrations/0008_historical_expense_approval\.py$|^\./apps/ledger/(historical|services|views)\.py$|^\./apps/(income|claims)/views\.py$').Count   # 须 6
($listing | Select-String -Pattern '(^|/)\.env(\.|$)|^\./venv/|^\./var/').Count   # 须 0
tar -czf "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" -C frontend/dist .
(Get-ChildItem -Recurse -File frontend\dist).Count
Get-FileHash "$SCRATCH\backend_${SHA}_<TS>.tar.gz", "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz", frontend\dist\index.html -Algorithm SHA256 | Format-Table Hash, Path
```
- 预期：工作区干净校验通过；`✓ built` 且退出码 0；三个标记计数均 ≥ 1；后端关键路径计数 `6`；排除项计数 `0`；`dist` 文件数、3 个 SHA256 记入报告。门槛不过 → 停止，不上传（目标机无变更）。
- 说明：`<TS>` 需在 DEPLOY-001 取得后代入；可在取锚点前先构建、取得 `TS` 后再按含 `TS` 的文件名打包/重命名，以缩短停机窗口。
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并暂存（开发机 → 目标机 `/tmp`）
- 位置：开发机 → 目标机
- 命令：
```powershell
scp "$SCRATCH\backend_${SHA}_<TS>.tar.gz" "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" "$OCAP_DEST:/tmp/"
ssh $OCAP_DEST "sha256sum /tmp/backend_${SHA}_<TS>.tar.gz /tmp/frontend_dist_${SHA}_<TS>.tar.gz"   # 须与 DEPLOY-002 一致
ssh $OCAP_DEST "rm -rf /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && mkdir /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && tar xzf /tmp/backend_${SHA}_<TS>.tar.gz -C /tmp/ocap_backend_stage_<TS> && tar xzf /tmp/frontend_dist_${SHA}_<TS>.tar.gz -C /tmp/ocap_web_stage_<TS> && test -f /tmp/ocap_backend_stage_<TS>/manage.py && test -f /tmp/ocap_backend_stage_<TS>/apps/ledger/migrations/0008_historical_expense_approval.py; ls -a /tmp/ocap_backend_stage_<TS> | grep -c '^\.env' || true"
```
- 预期：两端 SHA256 一致；暂存后端含 `manage.py` 与 `0008_historical_expense_approval.py`；`.env*` 计数 `0`；暂存前端文件数 = DEPLOY-002 的 `dist` 文件数。不符 → 停止，按 ROLLBACK-003 清理暂存，`DEPLOYMENT_FAILED`。
- 回滚: ROLLBACK-003

### DEPLOY-004: 停止后端与辅助单元（目标机首个状态变更点）
- 组件：systemd `ocap-backend`（及 PRE-05 检测到的 `$AUX`）
- 位置：目标机
- 命令：
```powershell
$AUX = '<PRE-05 记录的辅助单元，空格分隔>'
ssh $OCAP_DEST "for u in $AUX; do sudo systemctl stop \$u; done; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend || true; for u in $AUX; do systemctl is-active \$u || true; done"
```
- 预期：`ocap-backend` 与 `$AUX` 均 `inactive`。`stop` 已执行而后续 `cp` 失败 → 目标机已有变更，**立即**从 ROLLBACK-004 起回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 覆盖后端代码（保留 `.env` / `venv` / `var`）
- 组件：`/home/yangyang/ocap/backend`
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST "cp -a /tmp/ocap_backend_stage_<TS>/. /home/yangyang/ocap/backend/ && test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && ls -l /home/yangyang/ocap/backend/apps/ledger/migrations/0008_historical_expense_approval.py && sha256sum /home/yangyang/ocap/backend/.env"
```
- 预期：命令成功；迁移文件存在；`.env` SHA256 = PRE-09 记录值（制品不含 `.env`，`cp -a` 不会覆盖）。本批后端无删除文件（`git status` 无 `D`），叠加覆盖不需要清理旧文件。
- 回滚: ROLLBACK-005

### DEPLOY-006: 数据库迁移 `ledger 0008`（目标机 MySQL）
`[MANUAL_ROLLBACK_REQUIRED（条件触发）: 回滚时若已存在部署后新建的 PENDING/REJECTED/WITHDRAWN 批次或 PENDING 行，反向迁移会丢失账户/审批关联，且旧代码无法解释这些状态；此时不得自动反向，见 ROLLBACK-006。MySQL DDL 非事务，迁移中途失败可能留下半应用结构，须按 DEPLOY-001 转储人工核对。]`
- 组件：数据层（module_design「数据迁移」）；3 个可空列（含 1 个 FK）
- 位置：目标机
- 命令（先门控，后执行）：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'
```
  **门控**：输出必须**恰为 1 行** `ledger.0008_historical_expense_approval`，否则停止，不执行 `migrate`，按 ROLLBACK-005 起回滚代码。通过后：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -10; venv/bin/python manage.py showmigrations ledger'
```
  **schema 与数据校验**（写 `%TEMP%\ledger_schema_check.py` 后经 stdin 传入）：
```python
from django.db import connection
from apps.ledger.models import HistoricalExpenseBatch

names = set(connection.introspection.table_names())
cur = connection.cursor()
cols = lambda t: {c.name for c in connection.introspection.get_table_description(cur, t)}
print("TABLES_OK", {"ledger_historicalexpensebatch", "ledger_historicalexpenserow"} <= names)
print("BATCH_COLS", {"account_id", "approval_instance_id", "decided_at"} <= cols("ledger_historicalexpensebatch"))
print("BATCH_TOTAL", HistoricalExpenseBatch.objects.count())
print("BATCH_NULL_ACCOUNT", HistoricalExpenseBatch.objects.filter(account__isnull=True).count())
print("BATCH_STATUSES", sorted(set(HistoricalExpenseBatch.objects.values_list("status", flat=True))))
```
```powershell
Get-Content -Raw "$env:TEMP\ledger_schema_check.py" | ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell'
```
- 预期：`Applying ledger.0008_historical_expense_approval... OK`；`showmigrations` 中 `[X]`；`TABLES_OK True`、`BATCH_COLS True`；`BATCH_TOTAL`/`BATCH_NULL_ACCOUNT` 与 PRE-07 基线一致；`BATCH_STATUSES` ⊆ `{IMPORTED, VOIDED}`（迁移不回填、不改旧数据）。迁移失败或 schema 不符 → 目标机已有变更，从 ROLLBACK-006 起逆序回滚（先只读查询状态，不盲目重试）。
- 回滚: ROLLBACK-006

### DEPLOY-007: 启动后端并检查日志
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST "sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend && systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID; for u in $AUX; do sudo systemctl start \$u; done; systemctl is-active ocap-backend"
ssh $OCAP_DEST "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -30"
```
- 预期：`active`；`ActiveEnterTimestamp` 与 PRE-05 时不同；`$AUX`（如存在）恢复 `active`；日志无 `Traceback`、无 `ERROR`、无 `no such column` / `Unknown column` / `doesn't exist`。失败 → 从 ROLLBACK-007 起逆序回滚。
- 回滚: ROLLBACK-007

### DEPLOY-008: 后端只读验证
- 位置：目标机
- 命令：
```powershell
ssh $OCAP_DEST 'curl -s -o /dev/null -w "API_REPORTS=%{http_code}\n" "http://127.0.0.1:9000/api/v1/ledger/reports?account_id=1"; curl -s -o /dev/null -w "API_HIST=%{http_code}\n" http://127.0.0.1:9000/api/v1/admin/ledger/historical-expenses/batches; curl -s -o /dev/null -w "API_WITHDRAW=%{http_code}\n" -X POST http://127.0.0.1:9000/api/v1/admin/ledger/historical-expenses/batches/1/withdraw; curl -s -o /dev/null -w "API_SUMMARY=%{http_code}\n" http://127.0.0.1:9000/api/v1/ledger/accounts/summary'
```
- 预期：未带令牌时四者均为 `401`（证明新路由已加载且鉴权生效）；若任一返回 `404` 说明代码未正确覆盖或服务未重启，停止并回滚。全部通过才继续 DEPLOY-009。
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
- 命令见“部署后验证”表 V-07~V-11。
- 预期：全部 PASS；失败 → ROLLBACK-009。
- 回滚: ROLLBACK-010

### DEPLOY-011: 构建小程序产物（开发机，不部署、不上传）
- 组件：微信小程序（MOD-214）
- 位置：开发机
- 命令：
```powershell
$env:UNI_INPUT_DIR = 'C:\Users\胖子熊\MyProject\ocap\miniprogram'
$env:UNI_OUTPUT_DIR = "$env:TEMP\ocap_mp_build_<TS>"
npm --prefix miniprogram run build:mp-weixin
if ($LASTEXITCODE -ne 0) { throw 'MP_BUILD_FAILED' }
if (-not (Test-Path "$env:UNI_OUTPUT_DIR\app.json")) { throw 'MP_APP_JSON_MISSING' }
(Get-ChildItem -Recurse -Filter *.js $env:UNI_OUTPUT_DIR | Select-String -Pattern '请选择入账账户' -List | Measure-Object).Count   # 须 >= 1
```
- 预期：`DONE Build complete.`、退出码 0、`app.json` 存在、文案计数 ≥ 1。仅供微信开发者工具导入与人工上传，**不写入仓库、不进入目标机**。
- 说明：必须显式设置 `UNI_INPUT_DIR`，否则 uni-app 会查找不存在的 `src/manifest.json`（M-DE-048，本批实测通过）。
- 回滚: ROLLBACK-011

### DEPLOY-012: 部署后冒烟与人工验证（只读）
- 位置：目标机 / 浏览器 / 微信开发者工具
- 执行“部署后验证”表 V-01~V-13 与人工清单 M-01~M-04；**人工项未通过不得判定部署成功**（COND-D-01）。
- 回滚: ROLLBACK-012

## 回滚步骤（逆序）

### ROLLBACK-012: 反向回滚 DEPLOY-012
- 类型：正式回滚（无操作）
- 说明：只读验证，无状态变更；若冒烟或人工项失败，按失败项定位到 ROLLBACK-009（前端）或 ROLLBACK-006 起（后端/数据），并按 COND-D-02 回流 GROUP_C。

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
Get-Content -Raw "$env:TEMP\ledger_rollback_check.py" | ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell'
```
  脚本内容：
```python
from apps.ledger.models import HistoricalExpenseBatch, HistoricalExpenseRow
print("NEW_STATUS_BATCHES", HistoricalExpenseBatch.objects.filter(status__in=["PENDING", "REJECTED", "WITHDRAWN"]).count())
print("PENDING_ROWS", HistoricalExpenseRow.objects.filter(status="PENDING").count())
print("ACCOUNT_LINKED_BATCHES", HistoricalExpenseBatch.objects.filter(account__isnull=False).count())
```
  - `NEW_STATUS_BATCHES 0` 且 `PENDING_ROWS 0` → 可执行反向：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate ledger 0007 --noinput 2>&1 | tail -5; venv/bin/python manage.py showmigrations ledger'
```
    预期：`Unapplying ledger.0008_historical_expense_approval... OK`；`ledger.0008` 变回 `[ ]`。反向删除 3 个列，`ACCOUNT_LINKED_BATCHES` 指向的账户/审批关联数据丢失；旧批次（`account=NULL`）不受影响。
  - **任一不为 0** → 停止自动回滚，标 `[MANUAL_ROLLBACK_REQUIRED]`：部署后已产生新状态批次或待入账行，反向会丢字段且旧代码无法解释 `PENDING/REJECTED/WITHDRAWN`。人工选项：保留新后端并前滚修复，或先在旧 UI 中处理这些批次（入账/作废）后再反向。**不得直接反向迁移。**
  - 若迁移执行中途失败（DDL 非事务）：用 DEPLOY-001 的 `ledger-history-<TS>.sql` 与 `SHOW COLUMNS` 人工核对，不盲目重试。

### ROLLBACK-005: 恢复后端代码快照
- 类型：正式回滚
- 命令：
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap && tar xzf snapshots/backend-<TS>.tar.gz -C /home/yangyang/ocap && test -f backend/manage.py && test -x backend/venv/bin/python && sha256sum backend/.env && ls backend/apps/ledger/migrations/ | tail -5"
```
- 变量取值与核验：`<TS>` 来自 DEPLOY-001；快照不含 `.env`/`venv`/`var`，解包为叠加覆盖，**不删除**目标机本地文件。
- 预期：`.env` SHA256 = PRE-09；`0008_historical_expense_approval.py` 仍存在（快照后新增文件不被旧代码引用，保留无害；如需彻底清理需人工确认）。
- 注意：不能单独恢复代码而不处理迁移——旧代码不能处理新状态批次，必须与 ROLLBACK-006 的判定结果一起决定顺序。

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
- 说明：快照、哈希清单、迁移计划与转储保留 ≥ 7 天用于追溯；不得在回滚完成前删除。

## 不可逆步骤汇总

| 步骤 | 不可逆点 | 处置 |
|---|---|---|
| DEPLOY-006 | 反向迁移删除 `account/approval_instance_id/decided_at`，新批次的账户与审批关联丢失 | 迁移前转储 2 张表；反向仅在 `NEW_STATUS_BATCHES=0`、`PENDING_ROWS=0` 时执行；否则 `[MANUAL_ROLLBACK_REQUIRED]` |
| DEPLOY-006 | MySQL DDL 非事务，中途失败可能留下半应用结构 | 不盲目重试；用 `showmigrations` + schema 校验 + 转储人工核对后决定 |
| DEPLOY-005 + DEPLOY-006 组合 | 部署后新建的 `PENDING/REJECTED/WITHDRAWN` 批次与 `PENDING` 行无法被旧代码处理 | 回滚前统计；存在则人工决定前滚或先处理批次 |
| DEPLOY-009 | 浏览器可能缓存旧 `index.html` | 发布后提示强刷（Ctrl+F5）；`ocap.old` 保留至验证通过 |
| 小程序上传（不在本计划） | 微信平台上传后不可撤回 | 仅在微信开发者工具人工确认后上传 |
| 旧数据 `account=NULL` | 历史批次无账户归属，报表按账户读时依赖默认范围口径 | 本次不回填（C-389 不回溯）；记录基线，不做数据改写 |

## 部署后验证

| 编号 | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `ssh $OCAP_DEST 'systemctl is-active ocap-backend'` | `active` |
| V-02 | 日志无新错误 | `ssh $OCAP_DEST "sudo journalctl -u ocap-backend --since '-5 min' --no-pager | grep -cE 'Traceback|ERROR|Unknown column|no such column|FieldError'"` | `0` |
| V-03 | 新字段 | `ledger_schema_check.py` | `TABLES_OK True`、`BATCH_COLS True` |
| V-04 | 旧数据未被改写 | 同上 | `BATCH_TOTAL`、`BATCH_NULL_ACCOUNT` 与 PRE-07 基线一致；`BATCH_STATUSES` ⊆ `{IMPORTED, VOIDED}` |
| V-05 | 报表账户口径路由鉴权 | `curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:9000/api/v1/ledger/reports?account_id=1'` | `401` |
| V-06 | 历史支出批次路由鉴权 | `curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:9000/api/v1/admin/ledger/historical-expenses/batches/1/withdraw` | `401` |
| V-07 | Web 首页 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | `200` |
| V-08 | 前端主资源 | 从 `index.html` 取引用的 `assets/index-*.js`，`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/<路径>` | `200` |
| V-09 | 新文案在产物中 | `ssh $OCAP_DEST 'grep -rl "暂无可用账户" /home/yangyang/ocap/web/ocap/assets | head -1'` | 输出非空 |
| V-10 | 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200` |
| V-11 | 小程序产物（本地） | `Test-Path "$env:UNI_OUTPUT_DIR\app.json"` | `True` |
| V-12 | 账户数据可用于默认选中 | `manage.py shell` 只读查询 | `ACCOUNTS_ENABLED ≥ 1`；`DEFAULT_ACCOUNTS = 1`（为 0 时记录并转人工确认） |
| V-13 | 关键功能冒烟（唯一化写入） | 浏览器登录 → 收入逐条录入选账户 → 报销提交选账户 → 历史支出导入选账户（使用明显测试数据，如备注含 `SMOKE-<TS>`） | 台账仅写入所选账户；历史支出批次为“审批中”且未入账；测试数据可辨识 |

### 人工验证清单（自动化测试无法覆盖，COND-D-01 强制）

| 编号 | 对应 AC | 步骤 | 预期结果 | 所需环境 | 未通过处置 |
|---|---|---|---|---|---|
| M-01 | AC-410-01/02 | 管理后台财务-账户页查看“编辑”“设为默认”“停用/启用”按钮 | 按钮文字与背景对比清晰可辨（WCAG AA ≥ 4.5:1），默认账户“设为默认”置灰 | Chrome / Edge，`192.168.31.51:8090` | 部署不得判成功；按 COND-D-02 回流 GROUP_C 并重跑 GROUP_D |
| M-02 | AC-417-01/02 | 报表页在 1440px、1024px、768px 宽度下查看 3/8 个账户卡片 | 卡片从左到右等分屏宽；账户多于可视宽度时出现横向滚动条，不换行挤压 | 同上 | 同上 |
| M-03 | AC-417-03 | 8 个账户时横向滚动卡片区 | 合计余额标题与金额固定，不随卡片滚动 | 同上 | 同上 |
| M-04 | AC-421-01/02/03 | 打开任一账户报表详情，核对指标与明细 | 收入绿色系、支出红色系，与账户卡片流水颜色一致；仅支出/空明细显示正常 | 同上 | 同上 |

- 若目标环境启用账户不足 8 个，M-02/M-03 可用“临时停用部分账户”或“仅在本地开发环境构造 8 个账户”完成视觉复核，**不得在生产或他人的 Freeark 环境造数**；验证后恢复。
