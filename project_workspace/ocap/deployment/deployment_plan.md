<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-08T11:22:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.trae/sdlc/project_profile.md</file>
    <file>project_workspace/ocap/architecture/architecture_design.md</file>
    <file>project_workspace/ocap/architecture/module_design.md</file>
    <file>project_workspace/ocap/development/implementation_plan.md</file>
    <file>project_workspace/ocap/testing/test_plan.md</file>
    <file>project_workspace/ocap/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划（PHASE_11a DEPLOYMENT_PLANNING）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 | `backend/**`（排除 `venv/`、`.env`、`__pycache__/`、`var/`、`db.sqlite3`） | 有 16 个迁移（14 个 `0001_initial` + `polls/0002` + 其他），全新库首跑；增量若无新迁移则跳过 | 无（Python 源码） | RU-1 `ocap-backend.service` |
| 后端依赖 | `backend/requirements.txt` | 无 | `pip install -r` | 同 RU-1（安装后重启） |
| 前端 | `frontend/src/**`、`vite.config.js` | 无 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | RU-3 静态目录 `/home/yangyang/ocap/web/ocap`（无需重启进程） |
| 反向代理 | `/etc/nginx/sites-available/ocap`、`/etc/nginx/sites-enabled/freeark` | 无 | 无 | RU-5 nginx（`reload`） |
| 小程序 RU-4 | `miniprogram/**` | 无 | `npm run build:mp-weixin` | 微信平台发布（本计划不含） |
| 定时任务 RU-2 | `apps/jobs/**` | 无 | 无 | **测试环境未部署** `ocap-scheduler.timer`（缺口，见“遗留”） |

## 目标环境与策略

- **环境**：测试环境（画像 P7）——树莓派 `192.168.31.51`，用户 `yangyang`，SSH 免密；对外经 Freeark 的 frp 通道暴露为 `https://ai-freeark.xin/ocap/`。
- **策略**：`recreate`（单实例、无冗余）。理由：画像 P7 为单机物理部署，无第二套环境与流量切换能力；重启窗口秒级，测试环境可接受停机。
- **预计停机**：后端重启 1–3 秒；nginx reload 毫秒级；前端静态替换无停机。
- **部署需用户确认**：是（画像 P7）。执行 E2 前必须在 invocation 的 `special_instructions` 中出现 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名“测试环境”。
- **同机共存约束**：目标机同时运行 Freeark（`uvicorn:8000`、nginx `80/8080`、`frpc`、11 个 `freeark-*` 服务 + 2 个 timer）。本计划只允许改动：`/home/yangyang/ocap/**`、`/etc/nginx/sites-available/ocap`、`/etc/nginx/sites-enabled/freeark` 中的 `location ^~ /ocap/` 段、`ocap-backend.service`。**禁止**重启/停止 `freeark-*`、禁止改 Freeark 代码与数据库。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| 待部署提交已在远端 | `git -C <本地仓库> rev-parse HEAD` 与 `git ls-remote origin main` | 哈希一致 |
| 目标机回滚锚点 | `sudo tar czf /home/yangyang/ocap/snapshots/backend-$(date +%Y%m%d%H%M%S).tar.gz -C /home/yangyang/ocap backend` | 快照文件存在且 `tar tzf` 可列出 |
| 目标机无本地未纳入快照的改动 | `ls -la /home/yangyang/ocap` | 仅 `backend/`、`web/`、`snapshots/` |
| 磁盘 | `df -h /home` | 可用 ≥ 2 GB |
| 内存 | `free -m` | 可用 ≥ 500 MB（ocap 约 250 MB） |
| 端口未被他人占用 | `ss -ltn` | 9000 仅由 ocap gunicorn 持有；8090 由 ocap nginx 持有；**8000/8080/80 不得被 ocap 占用** |
| 环境变量文件存在 | `test -f /home/yangyang/ocap/backend/.env` | 存在（凭据只读不打印） |
| 依赖可安装 | `venv/bin/pip install --dry-run -r requirements.txt` | 退出码 0 |
| 迁移可执行 | `venv/bin/python manage.py showmigrations --plan` | 无语法/依赖错误 |
| nginx 配置语法 | `sudo nginx -t` | `syntax is ok` / `test is successful` |
| Freeark 当前健康（基线） | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/` | `200` |

## 部署步骤

### DEPLOY-001: 生成目标机回滚快照
- 组件：RU-1、RU-3
- 位置：目标机
- 命令：
  ```bash
  mkdir -p /home/yangyang/ocap/snapshots
  sudo tar czf /home/yangyang/ocap/snapshots/backend-$(date +%Y%m%d%H%M%S).tar.gz -C /home/yangyang/ocap backend
  sudo tar czf /home/yangyang/ocap/snapshots/web-$(date +%Y%m%d%H%M%S).tar.gz -C /home/yangyang/ocap web
  sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$(date +%Y%m%d%H%M%S)
  sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$(date +%Y%m%d%H%M%S)
  ```
- 预期：三份快照 + 两份 nginx 备份，路径记录为回滚锚点
- 回滚：ROLLBACK-001

### DEPLOY-002: 上传并解包后端代码
- 组件：RU-1
- 位置：开发机 → 目标机
- 命令：
  ```bash
  # 开发机仓库根
  tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
      -czf /tmp/ocap_backend.tar.gz -C backend .
  scp /tmp/ocap_backend.tar.gz yangyang@192.168.31.51:/tmp/
  ssh yangyang@192.168.31.51 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
  ```
- 预期：源码更新，`venv/` 与 `.env` 未被覆盖
- 回滚：ROLLBACK-002

### DEPLOY-003: 同步后端依赖
- 组件：RU-1
- 位置：目标机
- 命令：
  ```bash
  cd /home/yangyang/ocap/backend && venv/bin/pip install -r requirements.txt
  ```
- 预期：`Successfully installed …` 或 `Requirement already satisfied`；无报错
- 回滚：ROLLBACK-003

### DEPLOY-004: 执行数据库迁移
- 组件：RU-6（MySQL 192.168.31.98:3306 / 库 `ocap`）
- 位置：目标机（需加载 `.env`，其中含 `DB_SSL_DISABLED=1`）
- 命令：
  ```bash
  cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput
  ```
- 预期：`No migrations to apply` 或 `Applying … OK`
- 回滚：ROLLBACK-004
- `[MANUAL_ROLLBACK_REQUIRED: 迁移的逆向操作；删除表/字段会丢失数据]`

### DEPLOY-005: 重启后端服务
- 组件：RU-1 `ocap-backend.service`
- 位置：目标机
- 命令：
  ```bash
  sudo systemctl restart ocap-backend
  sleep 2
  systemctl is-active ocap-backend
  ```
- 预期：`active`；`journalctl -u ocap-backend -n 30` 无 Traceback
- 回滚：ROLLBACK-005

### DEPLOY-006: 构建并替换前端静态文件
- 组件：RU-3
- 位置：开发机 → 目标机
- 命令：
  ```powershell
  # 开发机仓库根
  $env:VITE_API_BASE='/ocap/api/v1'
  npm --prefix frontend run build -- --base=/ocap/
  tar -czf frontend_dist.tar.gz -C frontend\dist .
  scp frontend_dist.tar.gz yangyang@192.168.31.51:/tmp/
  ```
  ```bash
  ssh yangyang@192.168.31.51 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
  ```
- 预期：`/home/yangyang/ocap/web/ocap/index.html` 存在；`index.html` 中资源以 `/ocap/assets/` 开头
- 回滚：ROLLBACK-006

### DEPLOY-007: 更新 nginx 站点配置
- 组件：RU-5
- 位置：目标机
- 命令：
  ```bash
  # /etc/nginx/sites-available/ocap：监听 8090，root /home/yangyang/ocap/web，
  #   location = / → 302 /ocap/；location /ocap/api/ 与 /api/ → 127.0.0.1:9000；
  #   location /ocap/ → try_files $uri $uri/ /ocap/index.html
  # /etc/nginx/sites-enabled/freeark 增加（必须 ^~，否则被 js/css 静态正则抢走）：
  #   location ^~ /ocap/ { proxy_pass http://127.0.0.1:8090; proxy_set_header Host $host; ... }
  sudo nginx -t
  ```
- 预期：`syntax is ok`、`test is successful`
- 回滚：ROLLBACK-007

### DEPLOY-008: reload nginx
- 组件：RU-5
- 位置：目标机
- 命令：`sudo systemctl reload nginx && systemctl is-active nginx`
- 预期：`active`；不执行 `restart`（避免中断 Freeark 长连接）
- 回滚：ROLLBACK-008

## 回滚步骤（逆序）

### ROLLBACK-008: 撤销 reload 影响
- 类型：正式回滚
- 命令：`sudo systemctl reload nginx`
- 预期：`active`
- 说明：reload 本身无持久状态，真正恢复配置由 ROLLBACK-007 完成

### ROLLBACK-007: 恢复 nginx 配置
- 类型：正式回滚
- 命令：
  ```bash
  sudo cp /etc/nginx/sites-available/ocap.bak_<锚点时间戳> /etc/nginx/sites-available/ocap
  sudo cp /etc/nginx/sites-available/freeark.bak_<锚点时间戳> /etc/nginx/sites-enabled/freeark
  sudo nginx -t && sudo systemctl reload nginx
  ```
- 变量取值与核验：`<锚点时间戳>` 取 DEPLOY-001 记录值；执行前 `ls -l /etc/nginx/sites-available/*.bak_*` 核对存在
- 预期：`nginx -t` 通过；`curl http://127.0.0.1:8080/` 返回 200（Freeark 恢复）

### ROLLBACK-006: 恢复上一版前端静态
- 类型：正式回滚
- 命令：
  ```bash
  sudo rm -rf /home/yangyang/ocap/web/ocap
  sudo tar xzf /home/yangyang/ocap/snapshots/web-<锚点时间戳>.tar.gz -C /home/yangyang/ocap
  ```
- 预期：`/home/yangyang/ocap/web/ocap/index.html` 为旧版（比对文件哈希）
- 注意：只覆盖 `web/`，不触碰 `backend/`

### ROLLBACK-005: 重启回旧代码
- 类型：正式回滚
- 命令：恢复代码后 `sudo systemctl restart ocap-backend`
- 预期：`active`；`journalctl -u ocap-backend -n 30` 无 Traceback

### ROLLBACK-004: 撤销迁移
- 类型：紧急止血（必须收尾）
- 命令：按迁移清单逆序 `venv/bin/python manage.py migrate <app> <上一个迁移名>`（需先加载 `.env`）
- `[MANUAL_ROLLBACK_REQUIRED: 本次为全新库首跑与增量模型；删除表/字段不可恢复，执行前必须确认该库无业务数据或已备份]`
- 预期：`showmigrations` 回到锚点状态
- 收尾：确认应用与数据库结构一致，再重启 RU-1

### ROLLBACK-003: 卸载新增依赖
- 类型：紧急止血（通常不需要）
- 命令：按 `requirements` 与快照中的 `pip freeze` 差异 `venv/bin/pip uninstall -y <包>`
- 预期：旧代码可导入（`manage.py check` 通过）
- 收尾：下次正常部署时重新 `pip install -r`

### ROLLBACK-002: 恢复后端代码
- 类型：正式回滚（快照解包，禁止 `git reset` / `git clean`，目标机无 git）
- 命令：
  ```bash
  sudo rm -rf /home/yangyang/ocap/backend
  sudo tar xzf /home/yangyang/ocap/snapshots/backend-<锚点时间戳>.tar.gz -C /home/yangyang/ocap
  ```
- 预期：源码回到锚点版本；`.env` 与 `venv/` 随快照恢复
- 收尾：`systemctl restart ocap-backend` 并确认 `active`

### ROLLBACK-001: 无需执行
- 快照与备份本身不改变运行状态；锚点保留至少 7 天后再清理

## 不可逆步骤汇总

| 步骤 | 风险 | 处理 |
|---|---|---|
| DEPLOY-004 数据库迁移 | 建表/加字段可逆；删表/删字段/改类型不可逆，且迁移后写入的数据会丢失 | 执行前确认库为测试库；生产化前必须先备份（`mysqldump`）并单独评审 |

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端进程存活 | `systemctl is-active ocap-backend` | `active` |
| 后端日志无新错误 | `sudo journalctl -u ocap-backend --since '-5 min'` | 无 `Traceback` / `ERROR` |
| 内网 API | `POST http://192.168.31.51:8090/ocap/api/v1/admin/auth/login` | 200 且返回 token |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | 200，`Content-Type: text/html` |
| 内网静态资源 | `GET http://192.168.31.51:8090/ocap/assets/<构建产物>.js` | 200，非空 |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态资源 | `GET https://ai-freeark.xin/ocap/assets/<构建产物>.js` | 200（若 404，检查 `^~ /ocap/` 是否被静态正则抢走） |
| 外网 API | `POST https://ai-freeark.xin/ocap/api/v1/admin/auth/login` | 200 且返回 token |
| 门户登录 | `POST …/api/v1/auth/login/password` | 200 且返回 token |
| 前端 SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200 且返回 `index.html` |
| **Freeark 未受影响** | `GET https://ai-freeark.xin/` | 200 |
| **Freeark 服务未受影响** | `systemctl --state=failed --no-pager` | 无 `freeark-*` 失败单元 |
| 端口归属 | `ss -ltnp \| grep -E ':(8000\|8080\|8090\|9000)'` | 8000/8080 属 Freeark，8090/9000 属 ocap |

## 遗留

| 问题 | 级别 | 建议 |
|---|---|---|
| RU-2 `ocap-scheduler.timer` 未在测试环境创建，`run_due_jobs` 不会自动执行 | MINOR（测试环境） | 补齐 `ocap-scheduler.service` + `.timer`，纳入 DEPLOY-005 与 ROLLBACK-005 |
| 目标机无 git 仓库，回滚依赖 tar 快照 | MINOR | 建议改为 `git clone` 部署以便用提交号做锚点 |
| 小程序 RU-4 与微信真实服务未部署/未配置 | MINOR | 上线前按 `WECHAT_*` 环境变量补齐并完成提审 |
