# ocap-deploy — ocap 测试环境部署 Skill

> 项目专用部署指南，固化自已批准的 `project_workspace/ocap/deployment/deployment_plan.md`（v1.0.0）与 `cicd_pipeline.md`（v1.1.0）。
> 目标环境：树莓派 `192.168.31.51`，用户 `yangyang`，本机 SSH 免密；对外经 Freeark 的 frp 通道暴露为 `https://ai-freeark.xin/ocap/`。
> 本 skill 不处理生产环境（画像 P7 无生产环境）。

## 1. 适用范围与前置条件

- **范围**：把 ocap 后端（Django）与前端（Vue SPA 静态产物）部署到测试环境；更新 nginx 配置；不包含微信小程序发布（RU-4）。
- **前置**：
  1. 本地工作树干净，待部署提交已 push 到 `origin/main`（`git rev-parse HEAD` 与 `git ls-remote origin main` 哈希一致）。
  2. 本机可免密 SSH 到 `yangyang@192.168.31.51`，且有 sudo 权限。
  3. 目标机 `/home/yangyang/ocap/backend/.env` 已存在（含 `DB_SSL_DISABLED=1`、数据库连接、`SMS_GATEWAY_BACKEND=console`）。
  4. Freeark 服务正常（基线 `curl http://127.0.0.1:8080/` 返回 200）。

## 2. 环境常量

| 项 | 值 |
|---|---|
| 目标机 | `yangyang@192.168.31.51` |
| 部署根目录 | `/home/yangyang/ocap` |
| 后端目录 | `/home/yangyang/ocap/backend` |
| 前端静态目录 | `/home/yangyang/ocap/web/ocap` |
| 快照目录 | `/home/yangyang/ocap/snapshots` |
| 后端服务 | `ocap-backend.service`（gunicorn `127.0.0.1:9000`） |
| nginx 站点 | `/etc/nginx/sites-available/ocap`（监听 `8090`） |
| Freeark nginx | `/etc/nginx/sites-enabled/freeark`（仅改 `^~ /ocap/` 段） |
| 数据库 | MySQL `192.168.31.98:3306`，库 `ocap` |
| 前端 base | `/ocap/`；API base `/ocap/api/v1` |

## 3. 同机共存硬约束（不得违反）

- 只允许改动：`/home/yangyang/ocap/**`、`/etc/nginx/sites-available/ocap`、`/etc/nginx/sites-enabled/freeark` 中的 `location ^~ /ocap/` 段、`ocap-backend.service`。
- **禁止**：重启/停止任何 `freeark-*` 服务；改动 Freeark 代码、数据库或其 nginx 中 `/ocap/` 以外的段；占用 8000/8080/80 端口。
- 改 nginx 前必须备份；用 `reload` 而非 `restart`。

## 4. 预检（在目标机执行）

```bash
# 1. 磁盘与内存
df -h /home          # 可用 ≥ 2G
free -m              # 可用 ≥ 500M

# 2. 端口归属（8000/8080 属 Freeark，8090/9000 属 ocap）
ss -ltn

# 3. 环境变量文件存在
test -f /home/yangyang/ocap/backend/.env && echo OK

# 4. 依赖可安装、迁移可执行
cd /home/yangyang/ocap/backend
venv/bin/pip install --dry-run -r requirements.txt
venv/bin/python manage.py showmigrations --plan

# 5. nginx 语法
sudo nginx -t

# 6. Freeark 基线
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/   # 期望 200
```

## 5. 部署步骤

### STEP 1 — 生成回滚快照（目标机）

```bash
mkdir -p /home/yangyang/ocap/snapshots
TS=$(date +%Y%m%d%H%M%S)
sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend
sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web
sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS
sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS
echo "ANCHOR_TS=$TS"
```
记下 `$TS`，作为回滚锚点。

### STEP 2 — 打包并上传后端（开发机 → 目标机）

```bash
# 开发机仓库根
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
    -czf /tmp/ocap_backend.tar.gz -C backend .
scp /tmp/ocap_backend.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
```

### STEP 3 — 同步依赖（目标机）

```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && venv/bin/pip install -r requirements.txt'
```

### STEP 4 — 执行迁移（目标机，不可逆，标 MANUAL_ROLLBACK_REQUIRED）

```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput'
```
期望：`No migrations to apply` 或 `Applying … OK`。

### STEP 5 — 重启后端服务（目标机）

```bash
ssh yangyang@192.168.31.51 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
sudo journalctl -u ocap-backend -n 30 --no-pager   # 无 Traceback
```

### STEP 6 — 构建并上传前端（开发机 → 目标机）

PowerShell（开发机仓库根）：
```powershell
$env:VITE_API_BASE='/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
tar -czf frontend_dist.tar.gz -C frontend\dist .
scp frontend_dist.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
```

### STEP 7 — 更新 nginx（目标机，按需）

仅当 nginx 配置有改动时执行。`/etc/nginx/sites-available/ocap` 要点：
- `listen 8090; root /home/yangyang/ocap/web;`
- `location = /` → `302 /ocap/;`
- `location /ocap/api/` 与 `location /api/` → `proxy_pass http://127.0.0.1:9000;`
- `location /ocap/` → `try_files $uri $uri/ /ocap/index.html;`

`/etc/nginx/sites-enabled/freeark` 增加（必须 `^~`，否则被 `.js/.css` 静态正则抢走）：
```nginx
location ^~ /ocap/ {
    proxy_pass http://127.0.0.1:8090;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

校验：
```bash
sudo nginx -t
```

### STEP 8 — reload nginx（目标机）

```bash
ssh yangyang@192.168.31.51 'sudo systemctl reload nginx && systemctl is-active nginx'
```

## 6. 部署后验证

| 检查 | 命令 / URL | 期望 |
|---|---|---|
| 后端存活 | `systemctl is-active ocap-backend` | `active` |
| 后端日志 | `journalctl -u ocap-backend --since '-5 min'` | 无 Traceback/ERROR |
| 内网 API 登录 | `POST http://192.168.31.51:8090/ocap/api/v1/admin/auth/login` | 200 + token |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | 200, text/html |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态 | `GET https://ai-freeark.xin/ocap/assets/<hash>.js` | 200 |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200, 返回 index.html |
| Freeark 未受影响 | `GET https://ai-freeark.xin/` | 200 |
| Freeark 服务 | `systemctl --state=failed --no-pager` | 无 `freeark-*` 失败 |

## 7. 回滚（逆序执行，用 STEP 1 的 `$TS`）

```bash
# 8→ reload（无状态，真正恢复由 7 完成）
sudo systemctl reload nginx

# 7→ 恢复 nginx 配置
sudo cp /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap
sudo cp /etc/nginx/sites-available/freeark.bak_$TS /etc/nginx/sites-enabled/freeark
sudo nginx -t && sudo systemctl reload nginx

# 6→ 恢复前端静态
sudo rm -rf /home/yangyang/ocap/web/ocap
sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap

# 5→ 重启后端
sudo systemctl restart ocap-backend

# 4→ 撤销迁移（不可逆，需人工确认库无业务数据或已备份）
cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a
venv/bin/python manage.py migrate <app> <上一个迁移名>   # 按迁移清单逆序

# 3→ 卸载新增依赖（通常不需要）
venv/bin/pip uninstall -y <差异包>

# 2→ 恢复后端代码（快照解包，禁止 git reset/clean）
sudo rm -rf /home/yangyang/ocap/backend
sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap
sudo systemctl restart ocap-backend

# 1→ 快照本身无需回滚，保留 ≥ 7 天
```

任一步失败且目标机已有变更 → 立即停止，从失败步骤逆序回滚，并报告当前状态。

## 8. 已知缺口

- **RU-2 定时任务**：测试环境未创建 `ocap-scheduler.timer`，`run_due_jobs` 不会自动执行。补齐时新增 `ocap-scheduler.service` + `.timer`，纳入 STEP 5 与回滚。
- **目标机无 git**：回滚依赖 tar 快照，锚点为时间戳；建议后续改为 `git clone` 部署以便用提交号做锚点。
- **小程序 RU-4**：本 skill 不含微信小程序构建与提审发布。
- **短信/微信真实服务**：测试环境 `SMS_GATEWAY_BACKEND=console`，微信未配置；上线前补齐 `WECHAT_*` 环境变量。
