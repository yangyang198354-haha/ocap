---
name: ocap-deploy
description: 把 ocap 后端（Django/gunicorn）和 Web 前端（Vue SPA 静态产物）部署到树莓派测试环境，或按 tar 快照锚点回滚。用于"部署到测试环境/树莓派""更新测试机""回滚测试环境"。不适用：生产环境（画像 P7 中不存在）、微信小程序构建与发布（RU-4）、Freeark 自身的部署、任何容器化部署。skill 本身不构成部署授权，必须有用户当轮明确授权。
---

# ocap-deploy：ocap 测试环境部署与回滚

依据：已批准的 `project_workspace/ocap/deployment/deployment_plan.md`（1.0.0）、`cicd_pipeline.md`（1.1.0），以及 `deployment_report.md`（1.0.0）的实际执行经验。步骤编号 DEPLOY-NNN / ROLLBACK-NNN 与计划一一对应。

## 0. 授权与安全（先读）

- 部署只能在用户**当轮**消息明确授权后执行（画像 P7：测试环境"部署需用户确认=是"）。skill 被加载、被引用、出现在文档里，都不构成授权。没有授权就只做预检的阅读与方案说明，不连接目标机。
- 不写入任何凭据值。`.env` 只引用路径 `/home/yangyang/ocap/backend/.env` 与键名（如 `DB_SSL_DISABLED`、`SMS_GATEWAY_BACKEND`、`WECHAT_*`），不 `cat` 它，不把内容贴进输出或文档。
- 画像 P8 禁用，不得使用：
  - Docker / 任何容器化方案；
  - pscp 逐文件上传（必须整包 tar 后 scp）；
  - 提交 `makemigrations` 全量产物（迁移必须手写、单 app 范围）；
  - 测试连接生产数据库（本项目无生产环境）。
- 回滚不得使用 `git reset --hard`、`git clean`、`git stash`（目标机无 git，也不应有）；只用 tar 快照解包。
- 画像 P9：子代理不得 ssh / 部署，由主会话在用户授权后执行。

## 1. 适用范围与前置条件

- 范围：后端代码 + 依赖 + 迁移 + 重启；前端构建产物替换；按需更新 nginx。不含小程序（RU-4）、不含定时任务 RU-2（见 §9）。
- 前置：
  1. 待部署提交已 push 到 `origin/main`：`git rev-parse HEAD` 与 `git ls-remote origin main` 哈希一致，且本地工作树干净。
  2. 能通过 SSH 免密登录目标机并有 sudo。
  3. 目标机 `/home/yangyang/ocap/backend/.env` 已存在（含 `DB_SSL_DISABLED=1`、数据库连接、`SMS_GATEWAY_BACKEND=console`）。
  4. 本地迁移无漂移（见 §4 第 7 项）。

## 2. 接入方式与变量

SSH/scp 目标写成变量，先设置再执行。两种接入方式二选一：

```bash
# 方式 A：内网（开发机在 192.168.31.x 网段）
OCAP_HOST=192.168.31.51
OCAP_PORT=22

# 方式 B：外网
# 注意：此地址与端口由用户于 2026-11-08 提供；PM 当时测试连接被拒绝。
# 使用前必须先确认端口可达（例如 nc -zv -w 5 ai-freeark.xin 9999），不可达则停止并向用户确认，不要反复重试。
# OCAP_HOST=ai-freeark.xin
# OCAP_PORT=9999

OCAP_USER=yangyang
OCAP_SSH="ssh -p $OCAP_PORT $OCAP_USER@$OCAP_HOST"
OCAP_SCP="scp -P $OCAP_PORT"          # scp 的端口参数是大写 -P
OCAP_DEST="$OCAP_USER@$OCAP_HOST"
```

引号规则（出错会让回滚静默失效）：

- `$OCAP_SSH '<远端命令>'`：单引号内的 `$VAR` 在**远端**展开（通常为空）。远端命令里要用本地变量（尤其是锚点 `TS`）时，用双引号包住远端命令，或先 `echo` 出完整命令核对再执行。
- `$OCAP_SSH` 不加引号使用（依赖分词），不要写成 `"$OCAP_SSH"`。
- 远端命令里自己要展开的东西（如 `$(date ...)`、远端环境变量）在双引号中写 `\$`。
- scp 目标写 `"$OCAP_DEST:/tmp/"`。

## 3. 环境常量与同机共存约束

| 项 | 值 |
|---|---|
| 部署根 / 后端 / 前端静态 / 快照 | `/home/yangyang/ocap` / `.../backend` / `.../web/ocap` / `.../snapshots` |
| 后端服务 | `ocap-backend.service`（gunicorn `127.0.0.1:9000`） |
| ocap nginx 站点 | `/etc/nginx/sites-available/ocap`（监听 8090） |
| Freeark nginx | `/etc/nginx/sites-enabled/freeark`（只允许改 `location ^~ /ocap/` 段） |
| 数据库 | MySQL `192.168.31.98:3306`，库 `ocap` |
| 访问入口 | 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/` |
| 前端构建参数 | `VITE_API_BASE=/ocap/api/v1`，`--base=/ocap/` |

Freeark 同机共存（画像 P7，不得违反）：

- 目标机上同时运行 Freeark（uvicorn:8000、nginx:80/8080、frpc、`freeark-*` 服务与 timer）。ocap 不得占用 8000/8080/80，不得占用其服务名、代码目录、数据库库名。
- 只允许改：`/home/yangyang/ocap/**`、`/etc/nginx/sites-available/ocap`、`/etc/nginx/sites-enabled/freeark` 中的 `^~ /ocap/` 段、`ocap-backend.service`。
- 禁止重启/停止任何 `freeark-*` 服务；禁止改 Freeark 代码、数据库、nginx 中 `/ocap/` 以外的段。
- **修改 Freeark nginx 前必须先备份**（DEPLOY-001 已包含）；nginx 只用 `reload`，不用 `restart`。
- `^~` 不可省：否则 `/ocap/` 下的 `.js/.css` 会被 Freeark 的静态正则抢走，外网静态资源 404。

## 4. 预检

在目标机执行（`$OCAP_SSH '...'`，均为只读命令；需要时逐条执行）：

| # | 检查 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 提交已在远端 | 本地：`git rev-parse HEAD`；`git ls-remote origin main` | 哈希一致 |
| 2 | 磁盘 | `df -h /home` | 可用 ≥ 2 GB |
| 3 | 内存 | `free -m` | 可用 ≥ 500 MB |
| 4 | 端口归属 | `ss -ltn` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| 5 | 目标机目录 | `ls -la /home/yangyang/ocap` | 仅 `backend/`、`web/`、`snapshots/`（无未纳入快照的东西） |
| 6 | env 文件 | `test -f /home/yangyang/ocap/backend/.env && echo OK` | `OK`（不打印内容） |
| 7 | 迁移无漂移 | 本地 `backend/`：`python manage.py makemigrations --check --dry-run --settings=config.test_settings` | 退出码 0。非 0 说明模型有未反映到迁移的变更：**停止**，交回开发修复（手写 scoped 迁移，提交推送后再部署）。不得在目标机上生成迁移，也不得提交 makemigrations 全量产物 |
| 8 | 依赖可装 | `cd /home/yangyang/ocap/backend && venv/bin/pip install --dry-run -r requirements.txt` | 退出码 0 |
| 9 | 迁移可列出 | 同目录：`venv/bin/python manage.py showmigrations --plan`（需先加载 `.env`，见 DEPLOY-004） | 无报错 |
| 10 | nginx 语法 | `sudo nginx -t` | `syntax is ok` / `test is successful` |
| 11 | Freeark 基线 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/` | `200` |

预检或 DEPLOY-001 失败、目标机尚无变更 → 停止，报告 `DEPLOYMENT_FAILED`，无需回滚。

## 5. 部署步骤

### DEPLOY-001：生成回滚锚点（目标机）　回滚：ROLLBACK-001

锚点 = 时间戳 `TS`。在**本地**取得一次并在后续所有步骤复用，避免多次 `date` 产生不同值：

```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S')
echo "ANCHOR_TS=$TS"                       # 记录到会话/报告中，回滚全靠它
$OCAP_SSH "mkdir -p /home/yangyang/ocap/snapshots \
 && sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend \
 && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web \
 && sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS \
 && sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS"
# 核验：快照可列出、大小非零
$OCAP_SSH "tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | head -3; tar tzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz | head -3; ls -l /home/yangyang/ocap/snapshots/*-$TS.tar.gz /etc/nginx/sites-available/*.bak_$TS"
```

这里用双引号，`$TS` 在本地展开，是有意为之。预期：2 份 tar 快照 + 2 份 nginx 备份。快照与备份保留 ≥ 7 天。

### DEPLOY-002：打包并上传后端（开发机 → 目标机）　回滚：ROLLBACK-002

```bash
# 开发机仓库根
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
    -czf /tmp/ocap_backend.tar.gz -C backend .
$OCAP_SCP /tmp/ocap_backend.tar.gz "$OCAP_DEST:/tmp/"
$OCAP_SSH 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
```

预期：源码更新，`venv/` 与 `.env` 未被覆盖。注意：解包只覆盖与新增，**不会删除**已从仓库移除的旧文件。

### DEPLOY-003：同步依赖（目标机）　回滚：ROLLBACK-003

```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && venv/bin/pip install -r requirements.txt'
```

预期：`Requirement already satisfied` 或 `Successfully installed …`，退出码 0。

### DEPLOY-004：数据库迁移（目标机）　回滚：ROLLBACK-004
`[MANUAL_ROLLBACK_REQUIRED: 迁移的逆向操作；删除表/字段/改类型会丢失数据，迁移后写入的数据也会丢失。执行回滚前必须由人确认库内无业务数据或已 mysqldump 备份]`

```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput'
```

预期：`No migrations to apply` 或 `Applying … OK`。执行前**先记录当前迁移状态**以便回滚定位：`showmigrations --plan`（同样需先加载 `.env`）输出存入会话。若出现"检测到模型变更未生成迁移"之类提示，按 §4 第 7 项处理，不要在目标机生成迁移。

### DEPLOY-005：重启后端（目标机）　回滚：ROLLBACK-005

```bash
$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
$OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
```

预期：`active`；日志无 `Traceback`。

### DEPLOY-006：构建并替换前端静态（开发机 → 目标机）　回滚：ROLLBACK-006

```bash
# 开发机仓库根（bash；Windows PowerShell 用 $env:VITE_API_BASE='/ocap/api/v1' 设置变量，其余相同）
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
tar -czf /tmp/frontend_dist.tar.gz -C frontend/dist .
$OCAP_SCP /tmp/frontend_dist.tar.gz "$OCAP_DEST:/tmp/"
$OCAP_SSH 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
```

预期：`web/ocap/index.html` 存在，资源路径以 `/ocap/assets/` 开头。vite 对大 chunk 的体积警告不影响功能。

### DEPLOY-007：更新 nginx 配置（目标机，仅配置有改动时）　回滚：ROLLBACK-007

配置未变则跳过（上次部署即跳过）。改动前确认 DEPLOY-001 已备份。要点：

- `/etc/nginx/sites-available/ocap`：`listen 8090; root /home/yangyang/ocap/web;`；`location = /` → `302 /ocap/`；`location /ocap/api/` 与 `location /api/` → `proxy_pass http://127.0.0.1:9000;`；`location /ocap/` → `try_files $uri $uri/ /ocap/index.html;`
- `/etc/nginx/sites-enabled/freeark` 仅增加/修改：
  ```nginx
  location ^~ /ocap/ {
      proxy_pass http://127.0.0.1:8090;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  ```
- 校验：`$OCAP_SSH 'sudo nginx -t'`，预期 `syntax is ok` / `test is successful`。校验失败不得 reload，直接 ROLLBACK-007。

### DEPLOY-008：reload nginx（目标机，随 007）　回滚：ROLLBACK-008

```bash
$OCAP_SSH 'sudo systemctl reload nginx && systemctl is-active nginx'
```

预期：`active`。不得 `restart`（会中断 Freeark 连接）。

## 6. 部署后验证

| 检查 | 命令 / URL | 成功标准 |
|---|---|---|
| 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback` / `ERROR` |
| 内网 API 可达 | 目标机上 `curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:9000/api/v1/admin/auth/login`（用错误凭据，不使用真实口令） | 返回 400/401（端点可达，非 5xx/连接失败） |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | 200，`text/html` |
| 内网静态 | `GET http://192.168.31.51:8090/ocap/assets/<构建产物>.js` | 200，非空 |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态 | `GET https://ai-freeark.xin/ocap/assets/<构建产物>.js` | 200（404 → 检查 `^~ /ocap/`） |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| Freeark 未受影响 | `GET https://ai-freeark.xin/` | 200 |
| Freeark 服务 | `$OCAP_SSH 'systemctl --state=failed --no-pager'` | 无 `freeark-*` 失败单元 |
| 端口归属 | `$OCAP_SSH 'ss -ltnp'` 过滤 8000/8080/8090/9000 | 8000/8080 属 Freeark，8090/9000 属 ocap |

写库的冒烟（如登录以外的写入）数据必须唯一化。全部通过 → `DEPLOYED_SUCCESSFULLY`；部分失败 → `DEPLOYED_WITH_ISSUES`，列出失败项，由用户决定是否回滚。

## 7. 回滚（逆序；锚点为 DEPLOY-001 的 `TS`）

任一 DEPLOY 步骤失败且目标机已有变更 → 立即停止后续步骤，从失败步骤起逆序执行对应 ROLLBACK。遇 `[MANUAL_ROLLBACK_REQUIRED]` 步骤（ROLLBACK-004）→ 暂停，由人决定，不自行处理。

**执行前核验锚点变量**（必须做）：

```bash
TS=<DEPLOY-001 记录的值>
echo "$TS" | grep -Eq '^[0-9]{14}$' || { echo "TS 非法，停止"; }
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/freeark.bak_$TS"
```

四个文件都存在才继续。下面所有远端命令用双引号，使 `$TS` 在本地展开；执行前可先 `echo` 命令核对。

- **ROLLBACK-008**（对应 DEPLOY-008）：无持久状态，真正恢复由 007 完成。
- **ROLLBACK-007**（恢复 nginx）：
  ```bash
  $OCAP_SSH "sudo cp /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap \
   && sudo cp /etc/nginx/sites-available/freeark.bak_$TS /etc/nginx/sites-enabled/freeark \
   && sudo nginx -t && sudo systemctl reload nginx"
  $OCAP_SSH 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'    # 期望 200
  ```
- **ROLLBACK-006**（恢复前端；只动 `web/`）：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap"
  $OCAP_SSH 'ls -l /home/yangyang/ocap/web/ocap/index.html'
  ```
- **ROLLBACK-005**（重启回旧代码）：须在 ROLLBACK-002 恢复代码之后执行 `$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'`，并查日志无 Traceback。
- **ROLLBACK-004**（撤销迁移）`[MANUAL_ROLLBACK_REQUIRED: 删表/删字段不可恢复，迁移后写入的数据会丢失；确认库无业务数据或已 mysqldump 备份后，由人决定]`：
  ```bash
  $OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate <app> <上一个迁移名>'
  ```
  `<app>` 与 `<上一个迁移名>` 取自 DEPLOY-004 前记录的 `showmigrations --plan`，按迁移清单逆序逐个 app 执行。注意：必须在旧代码恢复**之前**执行（旧代码里没有新迁移文件，无法反向迁移）；因此实际顺序为 004 → 002 → 005。收尾：确认应用与库结构一致。
- **ROLLBACK-003**（卸载新增依赖，通常不需要）：按 requirements 差异 `venv/bin/pip uninstall -y <包>`；恢复 backend 快照时 `venv/` 已随快照回到旧状态，一般无需单独做。
- **ROLLBACK-002**（恢复后端代码；禁止 git reset / clean）：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap"
  ```
  `.env` 与 `venv/` 随快照恢复。随后执行 ROLLBACK-005 的重启。
- **ROLLBACK-001**：无需执行。

回滚失败 → 停止，写清各步骤已部署/已回滚/状态未知，交人工干预，报告 `ROLLBACK_FAILED`。

## 8. 记录要求

每个已执行步骤记录：命令、开始时间、耗时、输出尾部、结果；未执行的步骤不得标 SUCCESS。输出与报告中不含凭据。

## 9. 已知问题与缺口

已知问题（本 skill 不处理，只登记）：

1. **CR-023**：`deployment_report.md` 中提交 `c275c46` 的三个 0003 迁移（claims/income/ledger）是在部署时由 `makemigrations` 生成的产物，与画像 P6/P8"手写 scoped 迁移、不提交 makemigrations 全量产物"冲突，已登记为 CR-023。本 skill 的预检第 7 项即为避免再次发生。
2. **CR-018**：仓库中缺少 `deploy/systemd/` 目录（画像 P3 约定放 systemd 模板），`ocap-backend.service` 等 unit 的受控来源缺失，已登记为 CR-018。

其他已知缺口（来自部署计划/报告）：

- RU-2：测试环境未创建 `ocap-scheduler.timer`，`run_due_jobs` 不会自动执行。
- 目标机无 git，回滚锚点为时间戳 + tar 快照，无提交号对应。
- 短信为 `console` 替身，微信未配置，上线前需补齐 `WECHAT_*`。
- 外网 SSH 入口（`ai-freeark.xin:9999`）未经验证，见 §2。
