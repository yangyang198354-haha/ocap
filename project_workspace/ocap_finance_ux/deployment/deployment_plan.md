<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T23:40:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_finance_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_finance_ux/testing/e2e_test_report.md</file>
    <file>project_workspace/ocap_finance_ux/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — 财务报表体验与多账户（ocap_finance_ux）

> **本轮不执行部署**。GROUP_E1 只产出计划；E2 必须在用户当轮明确授权后另行调用，invocation 的 `special_instructions` 必须含 `PRODUCTION_DEPLOY_CONFIRM=true` 与“测试”环境名（画像 P7 部署需确认=是）。子代理不执行 commit / push（画像 P9）。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `apps/ledger/{models,services,views,urls}.py`；`apps/income/{models,services,views}.py`；`apps/claims/{models,services,views}.py`；`apps/core/audit.py` | `ledger/0004_ledger_account`、`ledger/0005_ledger_account_backfill`、`ledger/0006_ledger_entry_account_not_null`、`income/0006_income_sheet_account`、`claims/0005_claim_account` | 无（Python 源码覆盖） | `ocap-backend` 停止 → 迁移 → 启动 |
| Web 前端 | `frontend/src/portal/{Reports,ReportDetailDialog,AccountCard,Home}.vue`、`admin/AdminAccounts.vue`、`shared/api.js`、`router/index.js`、`layout/menus.js` | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` | 替换 `/home/yangyang/ocap/web/ocap` |
| MySQL `ocap` 库 | — | 5 个迁移（新建 1 表、3 表加列、回填默认账户、流水账户改非空） | — | 迁移前备份 5 张相关表 |
| 微信小程序 | 不改（C-374） | — | — | — |

## 目标环境与策略

- 环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`，画像 P7）。无生产环境。
- 策略：**recreate**（单实例、无冗余；停服窗口内完成覆盖代码 → 迁移 → 启动）。预计停机 2–4 分钟（含流水回填）。
- 不使用 Docker/容器（画像 P8），不改 nginx 配置，不触碰 Freeark 服务与目录。

## 变量与执行约定

| 变量 | 取值方式 | 用途 |
|---|---|---|
| `$SHA` | E2 时 `git rev-parse --short HEAD`（用户确认后提交推送的提交） | 制品命名 |
| `$TS` | DEPLOY-001 目标机 `date +%Y%m%d%H%M%S` | 快照/制品/回滚锚点 |
| `$SCRATCH` | 开发机 `$env:TEMP\ocap_pkg_<SHA>` | 本地暂存 |
| `$OCAP_DEST` | `yangyang@192.168.31.51` | ssh/scp 目标 |
| `$A` | `/home/yangyang/ocap` | 目标机应用根 |

- 远端命令用单引号整体传 `ssh`（远端展开 `$TS/$DB_*`）；本地变量需代入时用双引号并先 `echo` 核对。
- 凭据只从目标机 `backend/.env` 读取（`DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT`），不写入文件；`mysqldump` 通过 `MYSQL_PWD` 传口令。
- 任一步失败即停止，按“回滚步骤”逆序执行。

## 预检清单

| 编号 | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| PRE-01 | 提交已推送 | 开发机 `git status --short; git log -1 --format='%h %s'` | 工作区干净且 HEAD 已推送 main；记录 `$SHA`。当前改动未提交 → **E2 前必须由用户确认后提交推送** |
| PRE-02 | CI 全绿 | GitHub Actions `CI` 3 个 job | 全绿 |
| PRE-03 | 测试门控 | 读 `phase_status.md` | GROUP_A~E1 均 APPROVED；GR-D-001=PASS_WITH_CONDITIONS（含 M-01~M-05 人工项） |
| PRE-04 | 远端可达与磁盘 | `ssh $OCAP_DEST 'df -h /home | tail -1'` | 可用空间 > 1GB |
| PRE-05 | 服务与辅助单元 | `ssh $OCAP_DEST 'systemctl is-active ocap-backend; systemctl list-unit-files | grep -E "ocap-.*\.(timer|service)" || true'` | `active`；记录 `AUX_ACTIVE` |
| PRE-06 | 运行目录与本地状态 | `ssh $OCAP_DEST 'test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && test -f /home/yangyang/ocap/web/ocap/index.html && echo DIRS_OK'` | `DIRS_OK` |
| PRE-07 | 迁移基线 | `ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations ledger income claims; venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'` | ledger 最高 `0003`、income 最高 `0005`、claims 最高 `0004`；`migrate --plan` **恰为 5 行**，集合 = {ledger.0004, ledger.0005, ledger.0006, income.0006, claims.0005}。不符 → 停止上报 |
| PRE-08 | 备份能力 | `ssh $OCAP_DEST 'command -v mysqldump && mkdir -p /home/yangyang/ocap/snapshots && df -h /home | tail -1'` | `mysqldump` 存在、目录可写 |
| PRE-09 | 回滚锚点哈希 | `ssh $OCAP_DEST 'sha256sum /home/yangyang/ocap/web/ocap/index.html; sha256sum /home/yangyang/ocap/backend/.env'` | 两个 SHA256 记入报告（`.env` 只记哈希） |
| PRE-10 | 本地状态不被覆盖 | 核对 DEPLOY-002 制品清单 | tar 中 `^\./(venv|var|\.env)` 计数 `0` |
| PRE-11 | 迁移数据基线 | DEPLOY-001 转储后：`grep -c 'CREATE TABLE'` | 5 张表（`ledger_ledgerentry`、`ledger_ledgerreport`、`income_incomesheet`、`income_incomerecord`、`claims_claim`） |
| PRE-12 | E2 授权 | 本次 E2 invocation `special_instructions` | 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名“测试”；计划版本=APPROVED；否则 BLOCKED |

## 部署步骤

### DEPLOY-001: 生成回滚锚点（目标机，只读 + 快照）
- 组件：后端源码、Web 静态产物、5 张相关表、迁移计划
- 命令（`bash -s` 传入）：
```bash
set -e
TS=$(date +%Y%m%d%H%M%S); A=/home/yangyang/ocap; mkdir -p $A/snapshots
tar czf $A/snapshots/backend-$TS.tar.gz --exclude='backend/venv' --exclude='backend/var' --exclude='backend/.env' --exclude='backend/.env.*' --exclude='__pycache__' -C $A backend
tar czf $A/snapshots/web-$TS.tar.gz -C $A web
cd $A/backend && set -a && . ./.env && set +a
venv/bin/python manage.py showmigrations --plan > $A/snapshots/migplan-$TS.txt
MYSQL_PWD="$DB_PASSWORD" mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl "$DB_NAME" \
  ledger_ledgerentry ledger_ledgerreport income_incomesheet income_incomerecord claims_claim > $A/snapshots/ledger-$TS.sql
chmod 600 $A/snapshots/ledger-$TS.sql
echo "ANCHOR_TS=$TS"
ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/migplan-$TS.txt $A/snapshots/ledger-$TS.sql
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/ledger-$TS.sql
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -cE '^backend/(\.env|venv/|var/)' || true
grep -c 'CREATE TABLE' $A/snapshots/ledger-$TS.sql
```
- 预期：`ANCHOR_TS`；4 文件非零；SHA256 非空；排除项 `0`；`CREATE TABLE` = `5`。失败且无变更 → `DEPLOYMENT_FAILED`。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建与打包
```powershell
$SHA = git rev-parse --short HEAD
$SCRATCH = "$env:TEMP\ocap_pkg_$SHA"; New-Item -ItemType Directory -Force $SCRATCH | Out-Null
$env:VITE_API_BASE = '/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
if ($LASTEXITCODE -ne 0) { throw 'WEB_BUILD_FAILED' }
(Select-String -Path frontend\dist\assets\*.js -Pattern '账户余额' -List | Measure-Object).Count   # >= 1
(Select-String -Path frontend\dist\assets\*.js -Pattern '旧口径' -List | Measure-Object).Count     # >= 1
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='.env.*' --exclude='var' --exclude='db.sqlite3' `
    -czf "$SCRATCH\backend_${SHA}_<TS>.tar.gz" -C backend .
$listing = tar tzf "$SCRATCH\backend_${SHA}_<TS>.tar.gz"
($listing | Select-String -Pattern '^\./apps/ledger/migrations/000[456]_|^\./apps/income/migrations/0006_|^\./apps/claims/migrations/0005_|^\./apps/ledger/services\.py$').Count   # 须 >= 6
($listing | Select-String -Pattern '(^|/)\.env(\.|$)|^\./venv/|^\./var/').Count   # 须 0
tar -czf "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" -C frontend/dist .
(Get-ChildItem -Recurse -File frontend\dist).Count
Get-FileHash "$SCRATCH\backend_${SHA}_<TS>.tar.gz", "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz", frontend\dist\index.html -Algorithm SHA256 | Format-Table Hash, Path
```
- 预期：`✓ built`；两个文案计数 ≥ 1；迁移/服务关键路径 ≥ 6；排除项 `0`；记录 dist 文件数与 SHA256。
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并暂存
```powershell
scp "$SCRATCH\backend_${SHA}_<TS>.tar.gz" "$SCRATCH\frontend_dist_${SHA}_<TS>.tar.gz" "$OCAP_DEST:/tmp/"
ssh $OCAP_DEST "sha256sum /tmp/backend_${SHA}_<TS>.tar.gz /tmp/frontend_dist_${SHA}_<TS>.tar.gz"
ssh $OCAP_DEST "rm -rf /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && mkdir /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> && tar xzf /tmp/backend_${SHA}_<TS>.tar.gz -C /tmp/ocap_backend_stage_<TS> && tar xzf /tmp/frontend_dist_${SHA}_<TS>.tar.gz -C /tmp/ocap_web_stage_<TS> && test -f /tmp/ocap_backend_stage_<TS>/manage.py && test -f /tmp/ocap_backend_stage_<TS>/apps/ledger/migrations/0006_ledger_entry_account_not_null.py && test -f /tmp/ocap_backend_stage_<TS>/apps/claims/migrations/0005_claim_account.py && ls -a /tmp/ocap_backend_stage_<TS> | grep -c '^\.env' || true"
```
- 预期：SHA256 两端一致；暂存含 `manage.py` 与两个迁移文件；`.env*` 计数 `0`；前端文件数 = DEPLOY-002。
- 回滚: ROLLBACK-003

### DEPLOY-004: 停止后端与辅助单元（首个状态变更点）
```powershell
$AUX = '<PRE-05 记录>'
ssh $OCAP_DEST "for u in $AUX; do sudo systemctl stop \$u; done; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend || true"
```
- 预期：均 `inactive`。此后失败须从 ROLLBACK-004 起回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 覆盖后端代码（保留 `.env`/`venv`/`var`）
```powershell
ssh $OCAP_DEST "cp -a /tmp/ocap_backend_stage_<TS>/. /home/yangyang/ocap/backend/ && test -f /home/yangyang/ocap/backend/.env && test -x /home/yangyang/ocap/backend/venv/bin/python && test -d /home/yangyang/ocap/backend/var && ls -l /home/yangyang/ocap/backend/apps/ledger/migrations/0006_ledger_entry_account_not_null.py && sha256sum /home/yangyang/ocap/backend/.env"
```
- 预期：命令成功；迁移文件存在；`.env` SHA256 = PRE-09。本批无删除文件，叠加覆盖即可。
- 回滚: ROLLBACK-005

### DEPLOY-006: 数据库迁移（5 个，含回填与非空）
`[MANUAL_ROLLBACK_REQUIRED: ledger 0005 反向为 noop（不回滚账户归属），ledger 0006 把流水账户列改为非空；部署后若新建账户/流水，反向到 0004 会丢失账户归属与账户记录。MySQL DDL 非事务，中途失败可能留下半应用结构，须按 DEPLOY-001 转储人工核对。]`
- 门控（必须先通过）：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'
```
  输出必须恰为 5 行且集合与 PRE-07 一致；否则停止，按 ROLLBACK-005 起回滚代码。
- 执行：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -12; venv/bin/python manage.py showmigrations ledger income claims'
```
- schema/数据校验（写 `%TEMP%\ledger_schema_check.py` 后经 stdin 传入 `manage.py shell`）：
```python
from django.db import connection
from apps.ledger.models import LedgerAccount, LedgerEntry, LedgerReport
from apps.income.models import IncomeSheet
from apps.claims.models import Claim

names = set(connection.introspection.table_names())
cur = connection.cursor()
cols = lambda t: {c.name for c in connection.introspection.get_table_description(cur, t)}
print("ACCOUNT_TABLE", "ledger_ledgeraccount" in names)
print("ENTRY_COL", "account_id" in cols("ledger_ledgerentry"))
print("REPORT_COLS", {"opening_balance", "closing_balance", "legacy"} <= cols("ledger_ledgerreport"))
print("SHEET_COL", "account_id" in cols("income_incomesheet"))
print("CLAIM_COL", "account_id" in cols("claims_claim"))
print("DEFAULT_ACCOUNTS", LedgerAccount.objects.filter(is_default=True).count())
print("NULL_ENTRY_ACCOUNTS", LedgerEntry.objects.filter(account__isnull=True).count())
print("ENTRY_COUNT", LedgerEntry.objects.count())
print("ENTRY_SUM", sum(e.amount for e in LedgerEntry.objects.all()))
print("LEGACY_REPORTS", LedgerReport.objects.filter(legacy=True).count())
```
- 预期：`ACCOUNT_TABLE True`、`ENTRY_COL True`、`REPORT_COLS True`、`SHEET_COL True`、`CLAIM_COL True`；`DEFAULT_ACCOUNTS 1`；`NULL_ENTRY_ACCOUNTS 0`；`ENTRY_COUNT/ENTRY_SUM` 与空表或迁移前一致（部署前库若为空：0/0）；`LEGACY_REPORTS` = 迁移前报表数。
- 回滚: ROLLBACK-006

### DEPLOY-007: 启动后端并检查日志
```powershell
ssh $OCAP_DEST "sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend && systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID; for u in $AUX; do sudo systemctl start \$u; done"
ssh $OCAP_DEST "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -30"
```
- 预期：`active`；日志无 `Traceback`、`ERROR`、`Unknown column`、`no such column`、`doesn't exist`。
- 回滚: ROLLBACK-007

### DEPLOY-008: 后端只读验证
```powershell
ssh $OCAP_DEST 'for p in ledger/accounts/summary ledger/reports admin/ledger/accounts; do curl -s -o /dev/null -w "$p=%{http_code}\n" http://127.0.0.1:9000/api/v1/$p; done'
```
- 预期：三个路径均 `401`（新路由已加载且鉴权生效）；`404` 说明代码未覆盖或未重启 → 停止回滚。
- 回滚: ROLLBACK-008

### DEPLOY-009: 替换 Web 静态目录
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap/web && rm -rf ocap.new && mkdir ocap.new && tar xzf /tmp/frontend_dist_${SHA}_<TS>.tar.gz -C ocap.new && rm -rf ocap.old && mv ocap ocap.old && mv ocap.new ocap && echo WEB_SWAPPED && ls -l ocap/index.html && find ocap -type f | wc -l && sha256sum ocap/index.html"
```
- 预期：`WEB_SWAPPED`；文件数 = 本地 dist；`index.html` SHA256 = 本地。`mv ocap ocap.old` 后失败 → ROLLBACK-009（优先 `mv ocap.old ocap`）。
- 回滚: ROLLBACK-009

### DEPLOY-010: 部署后验证与人工清单
- 执行下方 V-01~V-11 与 M-01~M-05。
- 回滚: ROLLBACK-010

## 回滚步骤（逆序）

### ROLLBACK-010: 只读验证回滚
- 无操作；失败项定位到 ROLLBACK-009（前端）或 ROLLBACK-006 起（后端/数据）。

### ROLLBACK-009: 恢复旧 Web 静态产物
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap/web && if [ -d ocap.old ]; then rm -rf ocap && mv ocap.old ocap && echo WEB_RESTORED_BY_SWAP; else rm -rf ocap && tar xzf /home/yangyang/ocap/snapshots/web-<TS>.tar.gz -C /home/yangyang/ocap/web && echo WEB_RESTORED_BY_SNAPSHOT; fi; sha256sum ocap/index.html"
```
- 核验：`tar tzf .../web-<TS>.tar.gz | grep -c '^web/ocap/index.html$'` 须为 `1`；恢复后 SHA256 = PRE-09。

### ROLLBACK-008: 只读验证回滚
- 无操作；执行 ROLLBACK-007 与 ROLLBACK-005。

### ROLLBACK-007: 停止后端
```powershell
ssh $OCAP_DEST "sudo systemctl stop ocap-backend; systemctl is-active ocap-backend || true"
```

### ROLLBACK-006: 迁移回滚（默认人工）
- 类型：`[MANUAL_ROLLBACK_REQUIRED]`
- 只读判定（写 `ledger_rollback_check.py` 执行）：
```python
from apps.ledger.models import LedgerAccount, LedgerEntry
from apps.income.models import IncomeSheet
from apps.claims.models import Claim
print("ACCOUNTS", LedgerAccount.objects.count())
print("ENTRIES", LedgerEntry.objects.count())
print("SHEETS_WITH_ACCOUNT", IncomeSheet.objects.filter(account__isnull=False).count())
print("CLAIMS_WITH_ACCOUNT", Claim.objects.filter(account__isnull=False).count())
```
  - 仅当 `ACCOUNTS=1`（只有迁移默认账户）、`SHEETS_WITH_ACCOUNT=0`、`CLAIMS_WITH_ACCOUNT=0`、且部署后未新增流水时，才允许反向：
```powershell
ssh $OCAP_DEST 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate ledger 0004 --noinput; venv/bin/python manage.py migrate claims 0004 --noinput; venv/bin/python manage.py migrate income 0005 --noinput'
```
    说明：先回退依赖方（income/claims）再回退 ledger；`ledger 0005` 反转为 noop，`0004` 反向会删除账户表并丢失回填归属——**只在上述只读条件全部满足时**执行，且执行后必须用 `ledger-<TS>.sql` 恢复流水数据。
  - 任一条件不满足 → 停止自动回滚，人工选项：保留新代码前滚修复，或按 `ledger-<TS>.sql` 全表恢复（会丢弃部署后新增数据）。

### ROLLBACK-005: 恢复后端代码快照
```powershell
ssh $OCAP_DEST "cd /home/yangyang/ocap && tar xzf snapshots/backend-<TS>.tar.gz -C /home/yangyang/ocap && test -f backend/manage.py && test -x backend/venv/bin/python && sha256sum backend/.env"
```
- 预期：`.env` SHA256 = PRE-09；快照为叠加覆盖，不删除本地文件。必须与 ROLLBACK-006 的判定一起决定顺序。

### ROLLBACK-004: 恢复停机前状态
```powershell
ssh $OCAP_DEST "sudo systemctl start ocap-backend; for u in $AUX; do sudo systemctl start \$u; done; systemctl is-active ocap-backend"
```
- 仅在“只停服、未覆盖代码/未迁移”时执行。

### ROLLBACK-003: 清理远端暂存
```powershell
ssh $OCAP_DEST "rm -rf /tmp/ocap_backend_stage_<TS> /tmp/ocap_web_stage_<TS> /tmp/backend_<SHA>_<TS>.tar.gz /tmp/frontend_dist_<SHA>_<TS>.tar.gz"
```

### ROLLBACK-002: 清理本地制品
```powershell
Remove-Item -Recurse -Force "$SCRATCH"
```

### ROLLBACK-001: 锚点处置
- 快照、哈希清单、迁移计划与转储保留 ≥ 7 天；回滚完成前不得删除。

## 不可逆步骤汇总

| 步骤 | 不可逆点 | 处置 |
|---|---|---|
| DEPLOY-006 | 0005 回填 + 0006 非空：反向 0004 会删除账户表与归属 | 部署前 5 表转储；反向前只读判定；不满足则 `[MANUAL_ROLLBACK_REQUIRED]` |
| DEPLOY-006 | MySQL DDL 非事务 | 失败不盲目重试；`showmigrations` + schema check + 转储人工核对 |
| DEPLOY-006 | 旧报表被标记 `legacy=true` | 反向 noop 不会清除标记；如需恢复列表语义，人工 SQL 更新（低风险） |
| DEPLOY-009 | 浏览器缓存旧静态资源 | 验证时强刷（Ctrl+F5）；`ocap.old` 保留至验证通过 |
| 迁移后新增账户/流水 | 回滚会丢失部署后数据 | 优先前滚修复；确需回滚先导出新增数据 |

## 部署后验证

| 编号 | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `systemctl is-active ocap-backend` | `active` |
| V-02 | 日志无新错误 | `journalctl -u ocap-backend --since '-5 min' \| grep -cE 'Traceback|ERROR|Unknown column|no such column'` | `0` |
| V-03 | 结构校验 | `ledger_schema_check.py` | 5 个布尔全 `True` |
| V-04 | 回填完整 | 同上 | `DEFAULT_ACCOUNTS 1`、`NULL_ENTRY_ACCOUNTS 0` |
| V-05 | 总额不变（M-01） | 同上 `ENTRY_SUM` vs 转储前统计 | 差额 `0.00` |
| V-06 | 账户汇总路由 | `curl ... /api/v1/ledger/accounts/summary` | `401` |
| V-07 | 报表路由 | `curl ... /api/v1/ledger/reports` | `401` |
| V-08 | 管理端账户路由 | `curl ... /api/v1/admin/ledger/accounts` | `401` |
| V-09 | Web 首页 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | `200` |
| V-10 | 新文案在产物 | `grep -rl "账户余额" /home/yangyang/ocap/web/ocap/assets \| head -1` | 非空 |
| V-11 | 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200` |

### 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 预期结果 | 环境 |
|---|---|---|---|---|
| M-01 | US-327 / AC-406-03/04 | 迁移前后核对流水条数与金额合计；重复执行回填 | 总额差额 0.00；默认账户唯一；重复执行无新增 | 目标机 MySQL |
| M-02 | AC-401-06 | 报表页筛选后刷新浏览器 | 回到「全部」第 1 页 | 浏览器 |
| M-03 | AC-402-03 | 360px 视口打开浮层 | 无横向滚动 | 浏览器 |
| M-04 | AC-402-04 | 开启“减少动态效果” | 浮层无位移动画 | 浏览器 |
| M-05 | AC-408-04 | 汇总接口失败时打开主页 | 卡片显示失败与重试，其他区块正常 | 浏览器 |
| M-06 | AC-404-01/02 | 管理端新建/改名/设默认/停用账户 | 列表与余额正确，重复账户号被拒 | 浏览器 + 管理员 |
| M-07 | AC-407-01/02 | 录入收入表时默认账户预选；如已接通选择器则改选账户 | 生效流水归属所选账户 | 浏览器 + 业委会账号 |
