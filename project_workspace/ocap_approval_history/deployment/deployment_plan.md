<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-27T10:18:09.8607259+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/cicd_pipeline.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>.agents/skills/ocap-deploy/SKILL.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — 审批与同住人申请历史记录

> 本文件仅为计划，不构成部署授权。未执行 SSH/scp、目标机预检或任何部署命令。GROUP_E2 当前为 NOT_AUTHORIZED。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| Django/DRF 后端 | `backend/apps/approval/views.py`、`backend/apps/residency/views.py`、`backend/apps/residency/urls.py` | 无 | 无需依赖安装；发布隔离 `REF` 的后端包 | 重启 `ocap-backend` |
| Vue 3 Web | `frontend/src/portal/Tasks.vue`、`frontend/src/portal/units/UnitsReview.vue`、`frontend/src/shared/api.js` | 无 | `VITE_API_BASE=/ocap/api/v1`，`npm run build -- --base=/ocap/` | 替换 `/home/yangyang/ocap/web/ocap` |
| 申请人记录 | 既有 `ResidentApplicationMineView`、`UnitsApplicationRecords.vue` | 无 | 随上述单元回归 | 不改查询或权限 |
| CI | `.github/workflows/ci.yml` 不变 | 无 | 现有全量测试/构建自动覆盖 | 无 |
| 数据库/nginx/小程序/timer/Freeark | 本批不变 | 无 | 不构建或发布小程序 | 不迁移、不改 nginx、不操作 Freeark/timer |

## 目标环境与策略

- 目标环境：**测试（内网）**，树莓派 `192.168.31.51`，nginx `8090`。测试（外网）仅作同一发布的可选复验，须当轮授权明确包含该环境。
- 策略：**recreate**：单实例后端解包后重启；Web 先解包到 `ocap.new.$TS`，校验后原子交换，旧目录保留为 `ocap.old.$TS`。不引入画像不存在的 rolling/blue-green/canary 设施。
- 停机：后端重启及静态交换存在服务窗口，时长以实际部署报告为准，不预先估计。
- 回滚：静态目录换回；后端用同一时间戳的代码快照覆盖恢复并重启。快照不含 `.env`、`venv/`、`var/`，避免回滚覆盖运行状态；本批新增文件在旧代码中无引用，可保留。

## 预检清单

| # | 检查项 | 命令（位置） | 通过标准 |
|---|---|---|---|
| P-01 | E2 授权 | 核对本次 invocation 的 `special_instructions` | 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与“测试（内网）”；计划版本已是 APPROVED；未授权则全部停止 |
| P-02 | 隔离版本 | 开发机：`$REF='<完整提交SHA>'; $BASE='<基线SHA>'; $SRC='<该提交的干净工作树路径>'; git -C $SRC rev-parse HEAD; git -C $SRC status --porcelain` | HEAD=$REF；`status` 无输出；`REF`/`BASE` 均经 `git cat-file -t` 验证为 commit |
| P-03 | 范围隔离 | `git -C $SRC diff --name-only $BASE $REF` | 只含本批产品、测试和文档；当前混合工作树中的收入表软删除等无关改动不得进入制品，否则停止 |
| P-04 | 提交与 CI | 按画像 P9 由用户确认后 commit/push；查看该 `REF` 的 GitHub Actions | backend/frontend/miniprogram 均 success；未授权 push 时不得自行推送，可用已确认的本地隔离 `REF` |
| P-05 | 测试门控 | 查 `phase_status.md` 与三份测试报告 | GROUP_D=APPROVED、GR-GROUP_D-001=PASS；critical path=2/2；报告版本 1.0.0 |
| P-06 | 无迁移/依赖变化 | `git -C $SRC diff --name-only $BASE $REF -- backend/requirements.txt 'backend/apps/*/models.py' 'backend/apps/*/migrations/'` | 无输出；不得在目标机生成迁移 |
| P-07 | SSH 与基础资源 | 仅授权后：`ssh yangyang@192.168.31.51 "echo SSH_OK; df -h /home; free -m"` | `SSH_OK`；可用磁盘 ≥2GB、内存 ≥500MB（既有 ocap-deploy 预检阈值） |
| P-08 | 服务基线 | `ssh ... "systemctl is-active ocap-backend; sudo nginx -t; ss -ltn"` | `active`；nginx 校验通过；9000/8090 仅 ocap，80/8000/8080 仍属 Freeark |
| P-09 | 本地状态基线 | `ssh ... "test -f /home/yangyang/ocap/backend/.env; test -d /home/yangyang/ocap/backend/venv; test -d /home/yangyang/ocap/backend/var; sha256sum /home/yangyang/ocap/backend/.env"` | 均存在；只记录 `.env` 哈希，不读取内容；本计划不写入这三项 |
| P-10 | 构建与制品内容 | 在 `$SRC/frontend` 执行生产构建；PowerShell `Select-String -Path frontend/dist/assets/* -Pattern '暂无已处理记录','暂无已通过的同住人申请'` | 构建退出码 0；两项文案均至少命中 1；`index.html` 引用资产存在 |
| P-11 | Freeark 基线 | `ssh ... "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/"` | 200；不修改或重启任何 `freeark-*` |

## 部署步骤

> 以下命令仅在未来 E2 授权后执行。PowerShell 中先设置 `$TS=Get-Date -Format 'yyyyMMddHHmmss'`，并复用预检的 `$REF`、`$SRC`。远端命令用双引号让本地 `$TS` 展开；执行前先输出完整命令核对，禁止空锚点。

### DEPLOY-001: 记录锚点并生成代码/Web 快照

- 组件：后端代码与 Web 静态目录（architecture_design 部署视图）。
- 位置：目标机。
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; mkdir -p /home/yangyang/ocap/snapshots; sudo tar --exclude=.env --exclude=venv --exclude=var --exclude=__pycache__ -czf /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz -C /home/yangyang/ocap/backend .; sudo tar -czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap/web ocap; test -s /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz; test -s /home/yangyang/ocap/snapshots/web-$TS.tar.gz; sha256sum /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz; echo ANCHOR_TS=$TS"
```
- 预期：两个快照非空并记录 SHA256；`TS` 为 14 位数字；服务尚未改变。
- 回滚：ROLLBACK-001。

### DEPLOY-002: 从隔离 REF 打包、覆盖后端并重启

- 组件：Django/DRF 后端（MOD-228、230）。
- 位置：开发机 → 目标机。
- 命令：
```powershell
$BACKEND_PKG="ocap-approval-history-$REF-$TS-backend.tar.gz"
git -C $SRC archive --format=tar.gz -o $BACKEND_PKG "${REF}:backend"
Get-FileHash -Algorithm SHA256 $BACKEND_PKG
scp $BACKEND_PKG yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 "set -e; sudo tar xzf /tmp/$BACKEND_PKG -C /home/yangyang/ocap/backend; sudo systemctl restart ocap-backend; systemctl is-active ocap-backend"
```
- 预期：包来自 `${REF}:backend`；后端解包成功且服务为 `active`；不执行 migrate/pip，不触碰 `.env`、`venv/`、`var/`。
- 回滚：ROLLBACK-002。

### DEPLOY-003: 从同一 REF 构建并打包 Web

- 组件：Vue 3 Web（MOD-229、231）。
- 位置：开发机隔离工作树。
- 命令：
```powershell
$env:VITE_API_BASE='/ocap/api/v1'
npm --prefix "$SRC/frontend" run build -- --base=/ocap/
$WEB_PKG="ocap-approval-history-$REF-$TS-web.tar.gz"
tar -czf $WEB_PKG -C "$SRC/frontend/dist" .
Get-FileHash -Algorithm SHA256 $WEB_PKG
```
- 预期：构建退出码 0；Web tar 非空且 SHA256 已记录；目标机尚未改变。
- 回滚：ROLLBACK-003。

### DEPLOY-004: 上传并解包到 Web 暂存目录

- 组件：Web 静态产物。
- 位置：开发机 → 目标机 `/home/yangyang/ocap/web/ocap.new.$TS`。
- 命令：
```powershell
scp $WEB_PKG yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 "set -e; rm -rf /home/yangyang/ocap/web/ocap.new.$TS; mkdir -p /home/yangyang/ocap/web/ocap.new.$TS; tar xzf /tmp/$WEB_PKG -C /home/yangyang/ocap/web/ocap.new.$TS; test -s /home/yangyang/ocap/web/ocap.new.$TS/index.html; chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap.new.$TS; echo WEB_STAGED"
```
- 预期：`WEB_STAGED`；`index.html` 与 assets 存在。只清理本次自建暂存目录，不碰线上 `ocap`。
- 回滚：ROLLBACK-004。

### DEPLOY-005: 原子替换 Web 静态目录

- 组件：nginx 静态站。
- 位置：目标机。
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; cd /home/yangyang/ocap/web; test -d ocap; test -d ocap.new.$TS; mv ocap ocap.old.$TS; mv ocap.new.$TS ocap; chown -R yangyang:yangyang ocap; echo WEB_SWAPPED"
```
- 预期：`WEB_SWAPPED`；新目录生效，旧目录完整保留；无需 nginx reload。
- 回滚：ROLLBACK-005。

## 回滚步骤（逆序）

任一目标变更步骤失败即停止后续步骤；从当前已生效步骤开始按以下逆序执行。回滚前必须确认 `$TS` 与 DEPLOY-001 一致，并用 `ls -l`/`test -s` 核验快照或旧目录。

### ROLLBACK-005: 回滚 DEPLOY-005，换回旧 Web

- 类型：正式回滚。
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; cd /home/yangyang/ocap/web; test -d ocap.old.$TS; mv ocap ocap.failed.$TS; mv ocap.old.$TS ocap; curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/; echo WEB_ROLLED_BACK"
```
- 变量取值与核验：`ocap.old.$TS` 必须来自 DEPLOY-005；存在且含 `index.html`。
- 预期：HTTP 200，旧 Web 恢复；失败目录保留用于排查。

### ROLLBACK-004: 回滚 DEPLOY-004，清理暂存

- 类型：正式回滚。
- 命令：`ssh yangyang@192.168.31.51 "rm -rf /home/yangyang/ocap/web/ocap.new.$TS; rm -f /tmp/$WEB_PKG; echo WEB_STAGE_CLEANED"`。
- 变量取值与核验：路径必须含已核验的 `$TS` 与 `$WEB_PKG`，不得指向 `ocap`、`var` 或 `venv`。
- 预期：仅暂存目录和本次上传包移除。

### ROLLBACK-003: 回滚 DEPLOY-003，保留记录并清理本地产物

- 类型：本地清理，目标环境无影响。
- 命令：`Remove-Item -Force $WEB_PKG`；保留控制台 SHA256 和构建日志。
- 变量取值与核验：`$WEB_PKG` 为 DEPLOY-003 创建的单一 tar 文件，不删除 `$SRC` 或其他既有文件。
- 预期：本地临时包移除；需要重新部署时从同一 `REF` 重建。

### ROLLBACK-002: 回滚 DEPLOY-002，恢复后端代码并重启

- 类型：正式回滚。
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; test -s /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz; sudo tar xzf /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz -C /home/yangyang/ocap/backend; sudo systemctl restart ocap-backend; systemctl is-active ocap-backend; sha256sum /home/yangyang/ocap/backend/.env"
```
- 变量取值与核验：快照 SHA256 须与 DEPLOY-001 记录一致；快照排除 `.env`、`venv/`、`var/`；采用覆盖恢复，不删除目录，本批新增文件保留且旧代码不引用。
- 预期：`active`，日志无新 Traceback；`.env` 哈希与 P-09 一致。

### ROLLBACK-001: 回滚 DEPLOY-001，核验并保留锚点

- 类型：无运行态逆操作；快照保留。
- 命令：`ssh yangyang@192.168.31.51 "test -s /home/yangyang/ocap/snapshots/backend-code-$TS.tar.gz; test -s /home/yangyang/ocap/snapshots/web-$TS.tar.gz; echo ANCHOR_RETAINED"`。
- 变量取值与核验：两个文件均非空；不自动删除。
- 预期：`ANCHOR_RETAINED`，供审计和后续恢复。

## 不可逆步骤汇总

- 本批无数据库迁移、外部系统写入、通知发送或 nginx 变更，**无 `[MANUAL_ROLLBACK_REQUIRED]` 步骤**。
- 后端重启与静态替换均可由 ROLLBACK-002/005 恢复；测试账号在功能冒烟中主动产生的审批数据属于业务操作，不随代码回滚删除，必须使用唯一备注并在部署报告中记录。

## 部署后验证

| # | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `ssh ... "systemctl is-active ocap-backend"` | `active` |
| V-02 | 后端日志 | `ssh ... "sudo journalctl -u ocap-backend --since '-10 min' --no-pager"` | 无新增 Traceback/ERROR |
| V-03 | handled 路由存在 | 无令牌 GET `http://127.0.0.1:9000/api/v1/approval/tasks?view=handled` | 401/403，非 404/5xx |
| V-04 | approved 路由存在 | 无令牌 GET `http://127.0.0.1:9000/api/v1/resident-applications/approved` | 401/403，非 404/5xx |
| V-05 | 内网 Web | `curl.exe -s -o NUL -w '%{http_code}' http://192.168.31.51:8090/ocap/` | 200，HTML |
| V-06 | SPA 深链与静态资源 | 请求 `/ocap/tasks`、`/ocap/units` 及 `index.html` 引用的 `/ocap/assets/*` | 全部 200，资源非空 |
| V-07 | 新制品文案 | 目标机 `grep -rl '暂无已处理记录' /home/yangyang/ocap/web/ocap/assets`；同理检查“暂无已通过的同住人申请” | 两项均至少 1 个命中 |
| V-08 | 通用审批关键旅程 | 用测试账号执行 TC-E2E-2301；意见使用 `E2E-$TS` 唯一值 | 待办移除、已处理一次、在途状态/当前步骤/完整时间线正确，历史无写按钮 |
| V-09 | 同住人与申请人旅程 | 用产权人及无产权申请人账号执行 TC-E2E-2302 | 通过记录字段完整、只显示 APPROVED；申请人仅见本人结果 |
| V-10 | 权限回归 | 用无关委员请求他人实例详情；用无产权账号查 approved | 实例详情 403 且无内容；approved 为空或仅本人当前产权范围 |
| V-11 | 本地状态与同机服务 | 比对 `.env` 哈希；`systemctl --state=failed --no-pager`；请求 Freeark 基线 | 哈希不变；无 `ocap-*`/`freeark-*` 失败；Freeark 200 |
| V-12 | 外网复验（仅另行授权时） | `curl.exe -s -o NUL -w '%{http_code}' https://ai-freeark.xin/ocap/` 与静态资源 | 200；未授权测试（外网）则标 SKIPPED，不发起请求 |

V-01～V-07 或 V-10～V-11 失败：停止并按 ROLLBACK 逆序恢复。V-08/V-09 出现产品行为缺陷：保留证据并回流 GROUP_C/D，由用户决定是否回滚；不得在目标机热修。全部实际执行结果须写入未来 E2 的 `deployment_report.md`，未执行项不得标 SUCCESS。
