<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-14T17:55:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
    <file>project_workspace/ocap_identity_display/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：用户端身份显示与认证房屋信息

> 本计划仅描述步骤。GROUP_E2 部署执行须由用户当轮明确授权；本文件不构成授权。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/apps/committee/services.py`、`backend/apps/identity/services.py` | 无 | 无 | `ocap-backend.service` |
| Web 前端 | `frontend/src/portal/Home.vue`、`frontend/src/shared/style.css` | — | `npm run build -- --base=/ocap/` | nginx 静态目录 |
| 小程序 | `miniprogram/pages/index/index.vue`、`pages/me/index.vue`、`store/auth.js` | — | 用户侧微信开发者工具 | 不纳入本计划（RU-4） |

## 目标环境与策略

- 环境：测试环境（画像 P7：树莓派 `192.168.31.51`，内网 `8090`，外网 `https://ai-freeark.xin/ocap/`）。
- 策略：**recreate**（单实例、无冗余）。后端重启造成数秒不可用；前端静态目录整体替换后再验证。
- 预计停机：后端重启约 2~5 秒；前端替换为静态文件操作，不影响 nginx 进程。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| 待部署提交已推送 | 开发机：`git rev-parse HEAD`；`git ls-remote origin main` | 两个哈希一致（push 由用户/主会话执行，画像 P9） |
| 工作树干净 | `git status --short` | 仅允许本次已确认的改动与未跟踪的项目文档 |
| 目标机可达 | `ssh yangyang@192.168.31.51 'echo OK'` | 输出 `OK` |
| 磁盘与内存 | `df -h /home`；`free -m` | 可用 ≥ 2G；可用内存 ≥ 500M |
| 端口归属 | `ss -ltn` | 8090/9000 属 ocap；8000/8080/80 属 Freeark，未被占用冲突 |
| 环境变量文件 | `test -f /home/yangyang/ocap/backend/.env && echo OK` | `OK` |
| 迁移状态 | `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan` | 无待执行迁移（本次无迁移） |
| nginx 语法 | `sudo nginx -t` | `syntax is ok` |
| Freeark 基线 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/` | `200` |

## 部署步骤

### DEPLOY-001: 生成回滚快照

- 组件：后端目录、Web 静态目录、nginx 配置（本次不改 nginx，仍一并快照）
- 位置：目标机
- 命令：
```bash
mkdir -p /home/yangyang/ocap/snapshots
TS=$(date +%Y%m%d%H%M%S)
sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend
sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web
sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS
sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS
echo "ANCHOR_TS=$TS"
sha256sum /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz
```
- 预期：输出 `ANCHOR_TS` 与两个 SHA256；记录锚点。
- 回滚：ROLLBACK-001

### DEPLOY-002: 上传并解包后端代码

- 组件：Django 后端（MOD-101）
- 位置：开发机 → 目标机
- 命令：
```bash
# 开发机仓库根
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
    -czf /tmp/ocap_backend.tar.gz -C backend .
scp /tmp/ocap_backend.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
```
- 预期：解包无错误；`/home/yangyang/ocap/backend/apps/identity/services.py` 含 `area_display`。
- 回滚：ROLLBACK-002

### DEPLOY-003: 重启后端服务

- 组件：systemd `ocap-backend`
- 位置：目标机
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
ssh yangyang@192.168.31.51 'sudo journalctl -u ocap-backend -n 30 --no-pager'
```
- 预期：`active`；日志无 Traceback/ERROR。
- 回滚：ROLLBACK-003

### DEPLOY-004: 构建并部署 Web 前端

- 组件：Vue SPA（MOD-102）
- 位置：开发机 → 目标机
- 命令（PowerShell）：
```powershell
$env:VITE_API_BASE='/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
tar -czf frontend_dist.tar.gz -C frontend\dist .
scp frontend_dist.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/web/ocap && sudo mkdir -p /home/yangyang/ocap/web/ocap && sudo tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap'
```
- 预期：`dist/index.html` 与 assets 上传成功；目录属主 `yangyang`。
- 回滚：ROLLBACK-004

## 回滚步骤（逆序）

### ROLLBACK-004: 回滚 DEPLOY-004

- 类型：正式回滚
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-'"$TS"'.tar.gz -C /home/yangyang/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web'
```
- 变量取值与核验：`$TS` 取 DEPLOY-001 输出的 `ANCHOR_TS`；执行前 `ssh ... 'ls -l /home/yangyang/ocap/snapshots/web-'"$TS"'.tar.gz'` 确认存在。注意引号，确保 `$TS` 在本地展开。
- 预期：静态目录恢复为部署前内容。

### ROLLBACK-003: 回滚 DEPLOY-003

- 类型：正式回滚
- 命令：`ssh yangyang@192.168.31.51 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'`
- 说明：恢复代码后必须重启，使旧代码生效；单独回滚本步无意义，需与 ROLLBACK-002 一起执行。

### ROLLBACK-002: 回滚 DEPLOY-002

- 类型：正式回滚（快照恢复）
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-'"$TS"'.tar.gz -C /home/yangyang/ocap && sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
```
- 变量取值与核验：同 ROLLBACK-004；执行前确认快照存在。
- 预期：后端恢复为部署前代码并处于 `active`。
- 禁止：`git reset --hard`、`git clean`、覆盖式 rsync（目标机存在本地 `.env` 等状态）。

### ROLLBACK-001: 回滚 DEPLOY-001

- 类型：无操作
- 说明：快照为只读锚点，保留 ≥ 7 天；不删除。

## 不可逆步骤汇总

无数据迁移、无外部通知、无不可逆数据写入。前端静态目录替换可通过 ROLLBACK-004 恢复；后端代码替换可通过 ROLLBACK-002 恢复。

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端存活 | `systemctl is-active ocap-backend` | `active` |
| 后端日志 | `journalctl -u ocap-backend --since '-5 min' --no-pager` | 无 Traceback/ERROR |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | 200，text/html |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态资源 | `GET https://ai-freeark.xin/ocap/assets/<本次构建的 js>` | 200 |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| 身份显示 | 用测试账号登录（手机号由用户提供），打开主页 | “当前身份”只显示一个身份，不出现“户主”；业委会职务优先 |
| 认证房屋 | 同上，查看“认证房屋”卡片 | 数量正确；每套显示名称、类型、面积；同住人房屋标注“同住人” |
| 空状态 | 游客账号或未认证账号登录 | 数量 0 + “暂无已认证房屋” |
| Freeark 未受影响 | `GET https://ai-freeark.xin/`；`systemctl --state=failed --no-pager` | 200；无 `freeark-*` 失败 |
