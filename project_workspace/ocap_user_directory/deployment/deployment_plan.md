<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T22:48:52.4163452+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>testing/e2e_test_report.md</file><file>../ocap_content_publish/deployment/deployment_plan.md</file></input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 部署计划（测试环境）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/apps/accounts/directory.py`（新建）、`serializers.py`、`views.py` | 无 | 无（Python 源码） | `ocap-backend` 重启 |
| 前端 | `frontend/src/admin/AdminUsers.vue`、`frontend/src/shared/format.js` | 无 | `npm ci && npm run build -- --base=/ocap/` | 替换静态 `dist/` |

**前置条件：本次改动必须由用户确认后提交并推送到 `origin/main`；部署制品只从该 commit 生成，不得打包未提交工作区。**

## 目标环境与策略

- 环境：测试环境（画像 P7），树莓派 192.168.31.51；外网入口 `https://ai-freeark.xin/ocap/`；SSH 入口 `ssh -p 57279 yangyang@47.109.197.217`。
- 策略：recreate（单实例、无冗余）；重启 gunicorn 期间短暂停机（秒级），前端静态替换无停机。
- 数据库：MySQL 192.168.31.98 库 `ocap`；本次无迁移。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-001 待部署提交已在远端 | 开发机：`git status -sb`、`git rev-parse HEAD` | 工作区干净、`main` 与 `origin/main` 同步；记录 `COMMIT` |
| PRE-002 SSH 可达与指纹 | `ssh -p 57279 yangyang@47.109.197.217 'hostname'` + `ssh-keyscan` | 主机名 raspberrypi；ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` |
| PRE-003 服务现状 | `systemctl is-active ocap-backend`；`ss -ltn \| grep -E ':(8090\|9000)\\b'` | active；8090/9000 属 ocap |
| PRE-004 资源 | `free -m`；`df -h /home` | available 内存 ≥ 500 MB；磁盘可用 ≥ 1 GB |
| PRE-005 快照锚点 | 本地执行一次 `TS=$(date +%Y%m%d%H%M%S); echo $TS` | 后续命令复用同一 `TS` |
| PRE-006 迁移对照 | `cd backend && venv/bin/python manage.py showmigrations --plan` | 本次前后无 content/accounts 新迁移（预期无变化） |
| PRE-007 前端构建 | 开发机 `cd frontend && npm ci && npm run build -- --base=/ocap/` | 退出码 0；记录 `dist/assets` 新 hash |
| PRE-008 本地状态保护 | `test -f backend/.env && test -d backend/venv && test -d backend/var` | 三项均存在；本次不触碰 |

## 部署步骤

### DEPLOY-001: 生成回滚快照与数据库备份

- 组件：目标机本地状态（画像 P7）
- 位置：目标机
- 命令（`TS` 为 PRE-005 的本地值，执行前 echo 核对）：
  ```bash
  S=/home/yangyang/ocap_snapshots/$TS
  A=/home/yangyang/ocap
  mkdir -p "$S"
  sudo tar czf "$S/backend-$TS.tar.gz" -C "$A" \
    --exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__ backend
  cp -a "$A/frontend/dist" "$S/frontend-dist-$TS"
  ( cd "$A/backend" && set -a && . ./.env && set +a && \
    mysqldump --skip-ssl -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    | gzip > "$S/ocap-$TS.sql.gz" )
  sha256sum "$S"/backend-$TS.tar.gz "$S"/ocap-$TS.sql.gz
  ```
- 预期：快照目录含 backend tar、frontend dist、SQL gz，SHA256 有输出。
- 回滚：ROLLBACK-001

### DEPLOY-002: 上传并解包后端制品

- 组件：MOD-062（后端）
- 位置：开发机 → 目标机
- 命令：
  ```bash
  git archive "$COMMIT":backend -o /tmp/ocap-backend-$TS.tar.gz
  scp -P 57279 /tmp/ocap-backend-$TS.tar.gz yangyang@47.109.197.217:/tmp/
  ssh -p 57279 yangyang@47.109.197.217 "tar xzf /tmp/ocap-backend-$TS.tar.gz -C /home/yangyang/ocap"
  ```
- 预期：`backend/apps/accounts/directory.py` 存在；`.env`、`venv`、`var` 未被覆盖。
- 回滚：ROLLBACK-003

### DEPLOY-003: 重启后端服务

- 组件：`ocap-backend`（gunicorn 127.0.0.1:9000）
- 位置：目标机
- 命令：`sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend`
- 预期：`active`；`journalctl -u ocap-backend -n 30 --no-pager` 无 Traceback。
- 回滚：ROLLBACK-002

### DEPLOY-004: 发布前端静态产物

- 组件：MOD-063（Web 后台）
- 位置：开发机 → 目标机
- 命令：
  ```bash
  cd frontend && npm ci && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/
  tar czf /tmp/ocap-frontend-$TS.tar.gz -C dist .
  scp -P 57279 /tmp/ocap-frontend-$TS.tar.gz yangyang@47.109.197.217:/tmp/
  ssh -p 57279 yangyang@47.109.197.217 \
    "rm -rf /home/yangyang/ocap/frontend/dist.new && mkdir -p /home/yangyang/ocap/frontend/dist.new && \
     tar xzf /tmp/ocap-frontend-$TS.tar.gz -C /home/yangyang/ocap/frontend/dist.new && \
     mv /home/yangyang/ocap/frontend/dist /home/yangyang/ocap/frontend/dist.old && \
     mv /home/yangyang/ocap/frontend/dist.new /home/yangyang/ocap/frontend/dist"
  ```
- 预期：外网 `/ocap/` 200，index 引用的 `AdminUsers-*.js` hash 与旧版不同。
- 回滚：ROLLBACK-004

## 回滚步骤（逆序）

### ROLLBACK-004: 回滚前端静态产物

- 类型：正式回滚
- 命令：
  ```bash
  ssh -p 57279 yangyang@47.109.197.217 \
    "rm -rf /home/yangyang/ocap/frontend/dist.failed && \
     mv /home/yangyang/ocap/frontend/dist /home/yangyang/ocap/frontend/dist.failed && \
     cp -a /home/yangyang/ocap/frontend/dist.old /home/yangyang/ocap/frontend/dist"
  ```
- 变量取值与核验：`dist.old` 为 DEPLOY-004 保留的旧目录；执行后检查 `ls -l` 时间与 index hash。
- 预期：外网 `/ocap/` 200，bundle hash 回到旧值。

### ROLLBACK-003: 恢复后端代码快照

- 类型：正式回滚
- 命令：
  ```bash
  ssh -p 57279 yangyang@47.109.197.217 \
    "tar xzf /home/yangyang/ocap_snapshots/$TS/backend-$TS.tar.gz -C /home/yangyang/ocap"
  ```
- 变量取值与核验：`TS` 为 PRE-005 值；执行前 `echo` 完整命令核对；执行后确认 `directory.py` 不再被引用（旧代码不引用该新文件，保留无害）。
- 预期：`serializers.py`、`views.py` 回到旧版本。

### ROLLBACK-002: 重启后端服务

- 类型：正式回滚
- 命令：`sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend`
- 预期：`active`，日志无 Traceback。

### ROLLBACK-001: 数据层

- 类型：无需执行（本次无迁移）
- 说明：`ocap-$TS.sql.gz` 仅作为人工兜底；若需恢复，由用户确认后执行，属不可逆覆盖。

## 不可逆步骤汇总

- 无数据库迁移，无不可逆代码操作。
- 前端 `dist.old` 与后端快照保留在目标机，确认稳定后可人工清理。

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| V-01 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | 200 |
| V-02 后端服务 | `systemctl is-active ocap-backend`；`journalctl -u ocap-backend -n 30 --no-pager` | active；无 Traceback |
| V-03 管理员接口字段 | 管理员登录后 `GET /api/v1/admin/users?page_size=5`（用户手动或带令牌） | 200；结果含 `identity_label`、`certified_units`、`real_names`、`last_login_at` |
| V-04 前端 bundle | 取 `/ocap/` 页面引用的 `AdminUsers-*.js` | 请求 200，hash 与 PRE-007 记录一致且与旧版不同 |
| V-05 页面冒烟 | 浏览器打开“账号”页 | 注册用户表出现 身份/认证/实名/上次登录 四列；空值显示“未认证/—/从未登录” |

## 部署授权

本计划为 GROUP_E1 产出，尚未执行（GROUP_E2 NOT_AUTHORIZED）。执行前需用户在本轮明确授权测试环境部署，并先完成提交与推送。
