<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-08T23:45:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>.claude/agents/project_profile.md</file>
    <file>project_workspace/ocap/architecture/architecture_design.md</file>
    <file>project_workspace/ocap/architecture/module_design.md</file>
    <file>project_workspace/ocap/development/implementation_plan.md</file>
    <file>project_workspace/ocap/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap/deployment/deployment_report.md</file>
    <file>.claude/skills/ocap-deploy/SKILL.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划（PHASE_11a DEPLOYMENT_PLANNING）— 1.1.0 增量

> 1.0.0 → 1.1.0 变更：新增 DEPLOY-009/ROLLBACK-009（systemd timer，CR-018）；预检新增 SECRET_KEY 非空、迁移状态、版本标识；SSH 入口改为 57279 通道；"提交已 push"改为"本地 HEAD/工作树打包"（用户未授权 push）；DEPLOY-001 改为单一锚点 `TS`；部署后验证新增 timer、DEF-006 登录接口检查。本版为 DRAFT，等待 PM 门控与用户部署授权，本次编写未连接任何目标环境。

## 变更摘要

自上次部署（`a7d7fcd`，DEPLOYED_SUCCESSFULLY）以来，代码经 CR-011~024、DEF-005、DEF-006 返工（`git diff --stat a7d7fcd HEAD`：86 个文件），后端 278/278 测试通过。

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/**`（排除 `venv/`、`.env`、`__pycache__/`、`var/`、`db.sqlite3`）；含 CR-024（缺 `DJANGO_SECRET_KEY` 拒绝启动）、DEF-006（验证码达错误上限作废）、`run_due_jobs` 增加季报/年报生成（CR-018） | **无新增迁移文件**。claims/income/ledger 三个 `0003` 迁移相对 `a7d7fcd` 为改写（PM 已用 AST 比对确认与原文件等价）；目标机已应用同名迁移，`migrate` 预期 `No migrations to apply` | 无 | RU-1 `ocap-backend.service` |
| 后端依赖 | `backend/requirements.txt` | 无 | `pip install -r` | 同 RU-1 |
| 前端 | `frontend/src/**`（含 `shared/api.js` 契约修正） | 无 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | RU-3 静态目录 |
| 定时任务 RU-2 | 新增 `deploy/systemd/ocap-run-due-jobs.{service,timer}` | 无 | 无 | **新增** `ocap-run-due-jobs.timer`（DEPLOY-009） |
| 反向代理 | `/etc/nginx/sites-available/ocap`、`sites-enabled/freeark` 的 `^~ /ocap/` 段 | 无 | 无 | RU-5 nginx（预计无改动，DEPLOY-007/008 默认跳过） |
| 小程序 RU-4 | `miniprogram/**` | 无 | 不含 | 微信平台发布（本计划不含） |

## 目标环境与策略

- **环境**：测试环境（画像 P7）——树莓派 `raspberrypi`，用户 `yangyang`，密钥认证。
  - 外网（本次执行用）：`ssh -p 57279 yangyang@47.109.197.217`；scp 用 `scp -P 57279`。通道为阿里云 VPS + frp → Pi:22。**首次连接须核对主机 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`**（`ssh-keygen -lf` 或连接提示），不一致则停止并上报，不得接受。
  - 内网备选：`yangyang@192.168.31.51:22`。
  - `ai-freeark.xin:9999` **不可用**（2026-11-08 实测 Connection refused，画像 P7），不得使用。
  - 访问入口：内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`。
- **策略**：`recreate`（单实例、无冗余；画像 P7 为单机物理部署，无第二套环境与流量切换）。预计停机：后端重启 1–3 秒；nginx 如有改动 reload 毫秒级；前端静态替换无停机；timer 安装无停机。
- **部署需用户确认**：是。执行 E2 前 PM 须在 invocation 的 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名“测试环境”。
- **同机共存约束**：目标机同时运行 Freeark（uvicorn:8000、nginx 80/8080、frpc、`freeark-*` 服务与 timer）。本计划只允许改动：`/home/yangyang/ocap/**`、`/etc/nginx/sites-available/ocap`、`/etc/nginx/sites-enabled/freeark` 的 `location ^~ /ocap/` 段、`ocap-backend.service`、新增 `/etc/systemd/system/ocap-run-due-jobs.{service,timer}`。**禁止**重启/停止 `freeark-*`；禁止触碰 Freeark 代码与数据库。单元名前缀 `ocap-`，与 Freeark 不冲突。
- **版本标识（无 push）**：用户未授权 push。部署对象为**本地 HEAD + 工作树**打包。E2 开始时记录 `git rev-parse HEAD` 与 `git status --short`（摘要：已修改/未跟踪文件数及清单）作为部署版本标识，写入 deployment_report。部署完成后建议用户提交并推送（commit/push 由用户确认后由主会话执行，子代理不执行，画像 P9）。因目标机与远端无提交号对应，回滚锚点仍为时间戳 `TS` + tar 快照。

## 预检清单

SSH 变量（先设置再用，见 ocap-deploy skill §2）：`OCAP_SSH="ssh -p 57279 yangyang@47.109.197.217"`，`OCAP_SCP="scp -P 57279"`，`OCAP_DEST=yangyang@47.109.197.217`。

| # | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 主机指纹 | 首次连接核对 ED25519 指纹 | = `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` |
| 2 | 版本标识已记录（替代“已 push”） | 本地：`git rev-parse HEAD`；`git status --short` | 已记录 HEAD 哈希与改动摘要；`git diff --name-only a7d7fcd` 中的文件与 implementation_plan 范围一致 |
| 3 | 本地回归 | `backend/`：`python manage.py test --settings=config.test_settings` | 278/278 通过（测试用 venv，画像 P4） |
| 4 | 迁移无漂移 | `backend/`：`python manage.py makemigrations --check --dry-run --settings=config.test_settings` | 退出码 0（产物不得提交） |
| 5 | 无新增迁移文件 | 本地：`git diff --name-status a7d7fcd HEAD -- backend/apps \| grep migrations` | 仅 3 条 `M`（claims/income/ledger 的 `0003`），**无 `A`**；PM 已 AST 比对等价。出现 `A` → 停止，回报 |
| 6 | 目标机迁移状态 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan > /tmp/mig_before.txt; grep -c "^\[ \]" /tmp/mig_before.txt'` | 未应用条数为 `0`（grep 无匹配时输出 0 且退出码 1，属预期）。非 0 → 停止，说明有未应用迁移，回报 PM |
| 7 | `DJANGO_SECRET_KEY` 非空（只检查，不打印） | `$OCAP_SSH 'grep -Eq "^DJANGO_SECRET_KEY=.+" /home/yangyang/ocap/backend/.env && echo SECRET_KEY_SET'` | 输出 `SECRET_KEY_SET`。（PM 已于 2026-11-08 只读核验过非空；E2 仍须复核。代码缺该键会拒绝启动，失败则不得进入 DEPLOY-002）。不要 `cat .env` |
| 8 | `DJANGO_ALLOWED_HOSTS` 非空 | 同上，键名换为 `DJANGO_ALLOWED_HOSTS` | `ALLOWED_HOSTS_SET`（默认已收敛为 localhost，缺失会导致外网 400） |
| 9 | `.env` 为 systemd 可读格式 | `$OCAP_SSH 'grep -Ec "^(export |[[:space:]]*#|[[:space:]]*$|[A-Z_]+=)" /home/yangyang/ocap/backend/.env; wc -l < /home/yangyang/ocap/backend/.env'`（两数相等） | 无 `export ` 前缀的非法行（`EnvironmentFile` 不支持 `export`）；若有 `export` 行 → 停止回报（不打印内容） |
| 10 | timer 单元尚不存在（保证 ROLLBACK-009 为严格逆操作） | `$OCAP_SSH 'systemctl list-unit-files "ocap-run-due-jobs*" --no-legend'` | 无输出。已存在 → 停止，回报 PM 评估 |
| 11 | 目标机目录 | `$OCAP_SSH 'ls -la /home/yangyang/ocap'` | 仅 `backend/`、`web/`、`snapshots/` |
| 12 | 磁盘 / 内存 | `df -h /home`；`free -m` | 可用 ≥ 2 GB / ≥ 500 MB |
| 13 | 端口归属 | `ss -ltn` | 9000 仅 ocap；8090 ocap nginx；8000/8080/80 非 ocap |
| 14 | 依赖可装 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && venv/bin/pip install --dry-run -r requirements.txt'` | 需先完成 DEPLOY-002 才能使用新 requirements；预检阶段仅验证 venv 可用（`venv/bin/python -V`），dry-run 在 DEPLOY-003 前执行 |
| 15 | nginx 语法 | `$OCAP_SSH 'sudo nginx -t'` | `syntax is ok` / `test is successful` |
| 16 | Freeark 基线 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/"` | `200` |
| 17 | 目标机本地状态不被触碰 | 本次变更仅覆盖 `backend/` 源码、`web/ocap/` 静态、新增 2 个 unit；`.env`、`venv/`、`snapshots/` 被排除或不涉及 | 打包命令含 `--exclude='.env' --exclude='venv'`（DEPLOY-002） |
| 18 | 回滚锚点 | DEPLOY-001 生成 `TS` | 快照可 `tar tzf` 列出 |

预检 1–13 或 DEPLOY-001 失败、目标机尚无变更 → 停止，报告 `DEPLOYMENT_FAILED`，无需回滚。

## 部署步骤

### DEPLOY-001: 生成回滚锚点与快照
- 组件：RU-1、RU-3、RU-5
- 位置：目标机（`TS` 在本地取得一次，全程复用）
- 命令：
  ```bash
  TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
  $OCAP_SSH "mkdir -p /home/yangyang/ocap/snapshots \
   && sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend \
   && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web \
   && sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS \
   && sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS"
  $OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/*-$TS.tar.gz /etc/nginx/sites-available/*.bak_$TS"
  ```
  双引号使 `$TS` 在本地展开（有意）。
- 预期：2 份 tar 快照 + 2 份 nginx 备份，大小非零；`TS` 记入 deployment_report
- 回滚：ROLLBACK-001

### DEPLOY-002: 打包并上传后端代码
- 组件：RU-1
- 位置：开发机 → 目标机
- 命令：
  ```bash
  tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
      -czf /tmp/ocap_backend.tar.gz -C backend .
  sha256sum /tmp/ocap_backend.tar.gz
  $OCAP_SCP /tmp/ocap_backend.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
  ```
- 预期：源码更新；`venv/` 与 `.env` 未被覆盖；本地与目标机 `sha256sum` 一致。解包只覆盖/新增，不删除已移除的旧文件（无害）
- 回滚：ROLLBACK-002

### DEPLOY-003: 同步后端依赖
- 位置：目标机
- 命令：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && venv/bin/pip install --dry-run -r requirements.txt && venv/bin/pip install -r requirements.txt'`
- 预期：退出码 0（`Requirement already satisfied` 或 `Successfully installed …`）
- 回滚：ROLLBACK-003

### DEPLOY-004: 执行数据库迁移
- 组件：RU-6（MySQL，库 `ocap`，主机见 `.env`）
- 位置：目标机（加载 `.env`）
- 命令：
  ```bash
  $OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py showmigrations --plan > /tmp/mig_after.txt; diff /tmp/mig_before.txt /tmp/mig_after.txt && echo MIGRATION_STATE_UNCHANGED'
  ```
- 预期：`No migrations to apply`（自 a7d7fcd 无新增迁移）；`MIGRATION_STATE_UNCHANGED`。若出现 `Applying …`，说明与预检 5/6 的假设不符：记录并报告，已应用的迁移视为目标机已变更，按 ROLLBACK-004 流程暂停等人
- 回滚：ROLLBACK-004 `[MANUAL_ROLLBACK_REQUIRED: 迁移逆向可能丢数据；本次预期为无迁移可应用]`

### DEPLOY-005: 重启后端服务
- 组件：RU-1 `ocap-backend.service`
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
  $OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
  ```
- 预期：`active`；日志无 `Traceback` / `ImproperlyConfigured`（后者表示 SECRET_KEY 缺失）
- 回滚：ROLLBACK-005

### DEPLOY-006: 构建并替换前端静态
- 位置：开发机 → 目标机
- 命令：
  ```bash
  VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
  tar -czf /tmp/frontend_dist.tar.gz -C frontend/dist .
  $OCAP_SCP /tmp/frontend_dist.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
  ```
- 预期：`web/ocap/index.html` 存在，资源路径以 `/ocap/assets/` 开头
- 回滚：ROLLBACK-006

### DEPLOY-007: 更新 nginx 配置（仅配置有改动时；默认跳过）
- 位置：目标机；要点见 ocap-deploy skill §5 DEPLOY-007（`^~ /ocap/` 不可省）
- 命令：改动后 `$OCAP_SSH 'sudo nginx -t'`
- 预期：`syntax is ok`；校验失败不得 reload，直接 ROLLBACK-007
- 回滚：ROLLBACK-007

### DEPLOY-008: reload nginx（随 007）
- 命令：`$OCAP_SSH 'sudo systemctl reload nginx && systemctl is-active nginx'`
- 预期：`active`；不得 `restart`
- 回滚：ROLLBACK-008

### DEPLOY-009: 安装 ocap-run-due-jobs timer（CR-018）
- 组件：RU-2；单元名 `ocap-run-due-jobs.{service,timer}`，与 `freeark-*` 无冲突
- 位置：开发机 → 目标机（放在最后：新代码已就位、后端已验证再启用定时任务）
- 命令：
  ```bash
  # 开发机仓库根：整包 tar 上传（画像 P8 禁止逐文件 pscp）
  tar -czf /tmp/ocap_systemd.tar.gz -C deploy/systemd ocap-run-due-jobs.service ocap-run-due-jobs.timer
  $OCAP_SCP /tmp/ocap_systemd.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'rm -rf /tmp/ocap_systemd && mkdir /tmp/ocap_systemd && tar xzf /tmp/ocap_systemd.tar.gz -C /tmp/ocap_systemd \
    && sudo install -m 644 /tmp/ocap_systemd/ocap-run-due-jobs.service /tmp/ocap_systemd/ocap-run-due-jobs.timer /etc/systemd/system/ \
    && sudo systemd-analyze verify /etc/systemd/system/ocap-run-due-jobs.service /etc/systemd/system/ocap-run-due-jobs.timer \
    && sudo systemctl daemon-reload \
    && sudo systemctl enable --now ocap-run-due-jobs.timer'
  $OCAP_SSH 'systemctl is-enabled ocap-run-due-jobs.timer; systemctl is-active ocap-run-due-jobs.timer; systemctl list-timers --no-pager | grep ocap-run-due-jobs'
  ```
- 预期：`enabled`、`active`；list-timers 有 NEXT 时间；`verify` 无错误。`enable --now` 只针对 timer，service 不 enable
- 回滚：ROLLBACK-009

## 回滚步骤（逆序）

执行前核验锚点（必须）：
```bash
TS=<DEPLOY-001 记录的值>
echo "$TS" | grep -Eq '^[0-9]{14}$' || { echo "TS 非法，停止"; }
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/freeark.bak_$TS"
```
四个文件均存在才继续。下列远端命令凡含 `$TS` 均用双引号（本地展开），执行前先 `echo` 核对。

### ROLLBACK-009: 卸载 timer（逆 DEPLOY-009）
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl disable --now ocap-run-due-jobs.timer; sudo systemctl stop ocap-run-due-jobs.service; \
    sudo rm -f /etc/systemd/system/ocap-run-due-jobs.timer /etc/systemd/system/ocap-run-due-jobs.service; \
    sudo systemctl daemon-reload; sudo systemctl reset-failed "ocap-run-due-jobs*"'
  $OCAP_SSH 'systemctl list-unit-files "ocap-run-due-jobs*" --no-legend | wc -l'
  ```
- 变量取值与核验：无本地变量；单元名固定。预检 10 已保证部署前不存在该单元，故删除即回到部署前状态
- 预期：核验输出 `0`；`systemctl list-timers` 无 ocap-run-due-jobs。必须先于 ROLLBACK-002（防止旧代码被定时调用）

### ROLLBACK-008: 撤销 reload 影响
- 类型：正式回滚；reload 无持久状态，真正恢复由 ROLLBACK-007 完成

### ROLLBACK-007: 恢复 nginx 配置（仅当执行过 DEPLOY-007）
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH "sudo cp /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap \
   && sudo cp /etc/nginx/sites-available/freeark.bak_$TS /etc/nginx/sites-enabled/freeark \
   && sudo nginx -t && sudo systemctl reload nginx"
  $OCAP_SSH "curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/"
  ```
- 预期：`nginx -t` 通过；8080 返回 200

### ROLLBACK-006: 恢复上一版前端静态
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap"
  $OCAP_SSH 'ls -l /home/yangyang/ocap/web/ocap/index.html'
  ```
- 预期：旧版 `index.html` 存在；只动 `web/`

### ROLLBACK-004: 撤销迁移 `[MANUAL_ROLLBACK_REQUIRED: 删表/删字段不可恢复，迁移后写入的数据会丢失；确认无业务数据或已 mysqldump 后由人决定]`
- 类型：紧急止血（必须收尾）
- 命令：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate <app> <上一个迁移名>'`
- 变量取值与核验：`<app>`、`<上一个迁移名>` 取自 `/tmp/mig_before.txt`（DEPLOY-004 前保存）；与 `mig_after` diff 后逆序逐个 app 执行
- 说明：必须在旧代码恢复**之前**执行，故实际顺序为 004 → 002 → 005。本次预期无迁移，此步通常不需要
- 收尾：`showmigrations --plan` 与 `mig_before.txt` 一致

### ROLLBACK-003: 卸载新增依赖（通常不需要）
- 恢复 backend 快照时 `venv/` 随快照回到旧状态；需单独处理时按 requirements 差异 `venv/bin/pip uninstall -y <包>`

### ROLLBACK-002: 恢复后端代码（禁止 git reset / clean；目标机无 git）
- 命令：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap"
  ```
- 预期：源码回到锚点版本；`.env` 与 `venv/` 随快照恢复

### ROLLBACK-005: 重启回旧代码（在 ROLLBACK-002 之后）
- 命令：`$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'`；`journalctl -u ocap-backend -n 30 --no-pager`
- 预期：`active`，无 Traceback

### ROLLBACK-001: 无需执行
- 快照与备份保留 ≥ 7 天

## 不可逆步骤汇总

| 步骤 | 风险 | 处理 |
|---|---|---|
| DEPLOY-004 数据库迁移 | 本次预期为空操作；若实际应用了迁移，删表/字段/改类型不可逆，迁移后数据会丢失 | `[MANUAL_ROLLBACK_REQUIRED]`；预检 5/6 已确认无待应用迁移；测试库，生产化前必须 `mysqldump` |
| `run_due_jobs` 的清理/生成行为（DEPLOY-009 之后） | timer 启用后会删除过期令牌/验证码/审计（按保留期）并生成季报/年报，这些数据变更不随 ROLLBACK-009 撤销 | 清理对象均为过期数据；报表由任务幂等生成。若需撤销已生成的报表，需人工处理 `[MANUAL_ROLLBACK_REQUIRED: 已生成的季报/年报与已清理的过期数据不可由卸载 timer 恢复]`。部署后验证中手动触发的一次属于同类影响，E2 应在报告中记录其输出 |

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback` / `ERROR` / `ImproperlyConfigured` |
| timer 已注册 | `$OCAP_SSH 'systemctl list-timers --no-pager \| grep ocap-run-due-jobs'` | 有一行，NEXT 非 `n/a` |
| 手动执行一次任务 | `$OCAP_SSH 'sudo systemctl start ocap-run-due-jobs.service; echo exit=$?; systemctl show ocap-run-due-jobs.service -p Result -p ExecMainStatus'` | `exit=0`，`Result=success`，`ExecMainStatus=0`（此处 `$?` 有意在远端展开；oneshot 的 start 阻塞到结束） |
| 任务日志 | `$OCAP_SSH "sudo journalctl -u ocap-run-due-jobs.service -n 20 --no-pager"` | 无 `Traceback`；有 run_due_jobs 汇总输出 |
| DEF-006 后登录接口可用 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | 返回 `400`（凭据错误；非 5xx / 连接失败）。字段 `identifier`/`password` 依据 `accounts/views.py` LoginByPasswordView 与 `frontend/src/shared/api.js`；响应 code 应为 `LOGIN_FAILED`；不使用真实口令 |
| 管理员登录端点可达 | 同上，路径 `/api/v1/admin/auth/login` | 400/401 |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/`（或经目标机 `curl http://127.0.0.1:8090/ocap/`） | 200，`text/html` |
| 内网静态 | `GET …:8090/ocap/assets/<构建产物>.js` | 200，非空 |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态 | `GET https://ai-freeark.xin/ocap/assets/<构建产物>.js` | 200（404 → 检查 `^~ /ocap/`） |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| Freeark 未受影响 | `GET https://ai-freeark.xin/` | 200 |
| Freeark 服务 | `$OCAP_SSH 'systemctl --state=failed --no-pager'` | 无 `freeark-*` 失败单元，且无 `ocap-*` 失败单元 |
| 端口归属 | `$OCAP_SSH 'ss -ltnp'` 过滤 8000/8080/8090/9000 | 8000/8080 属 Freeark；8090/9000 属 ocap |

写库的冒烟数据必须唯一化（上表登录检查使用含 `TS` 的唯一账号名，且不会创建数据）。

## 遗留

| 问题 | 级别 | 建议 |
|---|---|---|
| 部署提交未 push，目标机版本无远端提交号对应 | MINOR | 部署后由用户确认提交并推送；deployment_report 记录 HEAD 与工作树改动摘要 |
| timer 频率 | MINOR [INFERRED] | 依据 IFC-140/ADR-013 为每分钟；与 implementation_plan“每日或每小时”建议不同。树莓派负载高可改 `OnCalendar=hourly`（见 timer 文件注释），读时惰性判定兜底 |
| 目标机无 git，回滚依赖 tar 快照 | MINOR | 沿用 |
| 小程序 RU-4 与微信真实服务未部署/未配置 | MINOR | 上线前补齐 `WECHAT_*` |
| 短信 `console` 替身 | MINOR | 画像 P7 已声明 |
