<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T18:12:00+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/deployment/cicd_pipeline.md</file><file>.agents/skills/ocap-deploy/SKILL.md</file><file>.trae/sdlc/project_profile.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file><file>project_workspace/ocap_history_expense_import/testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 部署计划（测试环境）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/apps/ledger/{models,views,urls,apps}.py`、`historical.py`、`core/{audit,permissions}.py` | 新增 `ledger/0007_historical_expense.py`（2 表、唯一约束、2 索引，可逆） | 无需编译 | `ocap-backend.service`（gunicorn 9000） |
| 前端 | `frontend/src/{portal/HistoricalExpenses.vue,portal/Reports.vue,router/index.js,shared/api.js}` + 测试 | — | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | `/home/yangyang/ocap/web/ocap` 静态产物 |
| 依赖 | `backend/requirements.txt` 未变（openpyxl 已有） | — | — | 无新增依赖 |
| nginx | 无变更 | — | — | 不 reload（配置未改） |
| 定时任务 | 无变更 | — | — | `ocap-run-due-jobs.timer` 已存在，不重复安装 |

## 目标环境与策略

- 环境：测试（树莓派），画像 P7 与 `ocap-deploy` skill 中的唯一可部署环境；生产不存在。
- 策略：**recreate**（单实例 gunicorn，无冗余），预计停机约 5~15 秒（重启 `ocap-backend`）。
- 选择理由：只有一套运行实例，无流量切换能力；blue-green/canary 不可用。
- 授权：画像 P7“部署需用户确认=是”；**本次 E1 不执行任何部署命令**，E2 需用户在当轮消息中明确授权“部署到测试环境”。

## 预检清单

| # | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 版本标识 | 本地：`git rev-parse HEAD; git status --short` | 已记录（未授权 push 时不要求与远端一致） |
| 2 | 迁移无漂移 | `cd backend && DJANGO_ALLOW_EPHEMERAL_SECRET=1 /tmp/ocap-venv/bin/python manage.py makemigrations --check --dry-run` | 退出码 0，输出 `No changes detected` |
| 3 | 本地测试门控 | 见 `testing/*_report.md` | GROUP_D APPROVED：后端 1218、前端 590 全通过 |
| 4 | 磁盘 | `$OCAP_SSH 'df -h /home'` | 可用 ≥ 2 GB |
| 5 | 内存 | `$OCAP_SSH 'free -m'` | 可用 ≥ 500 MB |
| 6 | 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap；9000/8090 仅 ocap |
| 7 | 目标目录 | `$OCAP_SSH 'ls -la /home/yangyang/ocap'` | 仅 `backend/`、`web/`、`snapshots/` |
| 8 | env 文件 | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && echo OK'` | `OK`（不打印内容） |
| 9 | SECRET_KEY 非空 | `$OCAP_SSH 'grep -Eq "^DJANGO_SECRET_KEY=.+" /home/yangyang/ocap/backend/.env && echo SECRET_KEY_SET'` | `SECRET_KEY_SET` |
| 10 | 迁移状态 | 目标机 `set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan` | 无报错；记录当前状态作为回滚定位 |
| 11 | 主机指纹 | 首次连接核对 ED25519 | `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` |
| 12 | Freeark 基线 | `$OCAP_SSH 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/'` | `200` |
| 13 | nginx 语法 | `$OCAP_SSH 'sudo nginx -t'` | `syntax is ok` / `test is successful` |

## 部署步骤

变量：`OCAP_HOST=47.109.197.217`、`OCAP_PORT=57279`、`OCAP_USER=yangyang`、`OCAP_SSH="ssh -p $OCAP_PORT $OCAP_USER@$OCAP_HOST"`、`OCAP_SCP="scp -P $OCAP_PORT"`、`OCAP_DEST="$OCAP_USER@$OCAP_HOST"`。

### DEPLOY-001: 生成回滚锚点（目标机）
- 组件：本地状态快照（`ocap-deploy` §5）
- 命令：
  ```bash
  TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
  $OCAP_SSH "mkdir -p /home/yangyang/ocap/snapshots \
   && sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend \
   && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web \
   && sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS \
   && sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS"
  ```
- 预期：2 份 tar 快照 + 2 份 nginx 备份，大小非零。
- 回滚：ROLLBACK-001（无需执行）。

### DEPLOY-002: 打包并上传后端（开发机 → 目标机）
- 组件：后端源码（含 0007 迁移）
- 命令：
  ```bash
  tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
      -czf /tmp/ocap_backend.tar.gz -C backend .
  $OCAP_SCP /tmp/ocap_backend.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
  ```
- 预期：源码更新；`venv/`、`.env` 未被覆盖。
- 回滚：ROLLBACK-002。

### DEPLOY-003: 同步依赖（目标机）
- 命令：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && venv/bin/pip install --dry-run -r requirements.txt && venv/bin/pip install -r requirements.txt'`
- 预期：退出码 0（预计全部 already satisfied）。
- 回滚：ROLLBACK-003。

### DEPLOY-004: 数据库迁移（目标机）
- 命令：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput'`
- 预期：`Applying ledger.0007_historical_expense... OK`（或已应用）。
- 回滚：ROLLBACK-004（`[MANUAL_ROLLBACK_REQUIRED]`）。

### DEPLOY-005: 重启后端（目标机）
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
  $OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
  ```
- 预期：`active`；日志无 `Traceback`。
- 回滚：ROLLBACK-005。

### DEPLOY-006: 构建并替换前端静态（开发机 → 目标机）
- 命令：
  ```bash
  VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
  tar -czf /tmp/frontend_dist.tar.gz -C frontend/dist .
  $OCAP_SCP /tmp/frontend_dist.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
  ```
- 预期：`web/ocap/index.html` 存在，资源路径以 `/ocap/assets/` 开头。
- 回滚：ROLLBACK-006。

### DEPLOY-007 / DEPLOY-008 / DEPLOY-009: 跳过
- nginx 配置未改（无新路由前缀/无新站点），不执行 007/008。
- `ocap-run-due-jobs.timer` 已在既有环境安装且本次无变更，不重复执行 009。
- 如目标机实际缺失 timer，按 `ocap-deploy` §5 DEPLOY-009 补做，并对应 ROLLBACK-009。

## 回滚步骤（逆序）

### ROLLBACK-006: 回滚 DEPLOY-006（前端）
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap"
  ```
- 变量核验：`echo "$TS" | grep -Eq '^[0-9]{14}$'`，并 `ls` 四份锚点文件存在。
- 预期：`web/ocap/index.html` 恢复为旧版。

### ROLLBACK-005: 回滚 DEPLOY-005（重启旧代码）
- 前置：ROLLBACK-002 恢复代码之后执行。
- 命令：`$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'`
- 预期：`active`，日志无 Traceback。

### ROLLBACK-004: 回滚 DEPLOY-004（撤销迁移）
- 类型：紧急回滚
- 命令：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate ledger 0006'`
- 执行顺序：必须**先于** ROLLBACK-002（旧代码无 0007 文件），实际顺序 004 → 002 → 005。
- [MANUAL_ROLLBACK_REQUIRED: 删除 historicalexpensebatch / historicalexpenserow 两表会丢失已导入的历史支出数据（含导入后生成/重算的报表），执行前须确认库内无业务数据或已 mysqldump 备份，由人决定]

### ROLLBACK-003: 回滚 DEPLOY-003（依赖）
- 类型：通常无需执行（无新增依赖）；如执行过 pip，恢复 backend 快照时 `venv/` 一并回到旧状态。

### ROLLBACK-002: 回滚 DEPLOY-002（后端代码）
- 命令：`$OCAP_SSH "sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap"`
- 禁止 `git reset --hard` / `git clean` / `git stash`；`.env` 与 `venv/` 随快照恢复；随后执行 ROLLBACK-005。

### ROLLBACK-001: 无需执行（锚点本身）。

## 不可逆步骤汇总

| 步骤 | 不可逆内容 | 处理 |
|---|---|---|
| DEPLOY-004 / ROLLBACK-004 | 回滚迁移将删除两张历史支出表及其数据 | `[MANUAL_ROLLBACK_REQUIRED]`：先备份（mysqldump）或确认无业务数据，由人决定 |
| 部署后用户导入的历史支出数据 | 回滚后端代码不会删除已写入台账的行；若随后回滚迁移则一并丢失 | 同上；如仅回滚前端/代码，台账数据保留 |

## 部署后验证

| 检查项 | 命令 / URL | 成功标准 |
|---|---|---|
| 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback` / `ERROR` |
| 迁移已应用 | `$OCAP_SSH 'cd ... && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations ledger'` | `[X] 0007_historical_expense` |
| 新接口鉴权生效 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/admin/ledger/historical-expenses/template"` | `401` |
| 登录接口存活 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400` |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | 200，`text/html` |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态 | `GET https://ai-freeark.xin/ocap/assets/<构建产物>.js` | 200（404 → 检查 `^~ /ocap/`） |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/reports` | 200，返回 index.html |
| Freeark 未受影响 | `GET https://ai-freeark.xin/` | 200 |
| 失败单元 | `$OCAP_SSH 'systemctl --state=failed --no-pager'` | 无 `freeark-*`、`ocap-*` 失败单元 |
| 端口归属 | `$OCAP_SSH 'ss -ltnp'` 过滤 8000/8080/8090/9000 | 归属不变 |
| 功能冒烟（授权后） | 业委会成员登录 → `/reports` 见“历史支出导入” → 下载模板 → 导入 1 行唯一化数据 → 批次列表可见 → 整批作废 | 全部成功；数据唯一化（金额/日期/用途含 `$TS`） |

> 冒烟写入的数据需唯一化并在验证后整批作废，避免污染测试库报表。
