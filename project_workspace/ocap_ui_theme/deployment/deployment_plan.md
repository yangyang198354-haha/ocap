<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-09T22:40:00+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.claude/agents/project_profile.md</file>
    <file>.claude/skills/ocap-deploy/SKILL.md</file>
    <file>project_workspace/ocap_ui_theme/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_ui_theme/architecture/module_design.md</file>
    <file>project_workspace/ocap_ui_theme/development/implementation_plan.md</file>
    <file>project_workspace/ocap_ui_theme/testing/e2e_test_report.md</file>
    <file>project_workspace/ocap_ui_theme/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap/deployment/deployment_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划（PHASE_11a）：ocap 多风格界面 + DEF-001 修复 → 测试环境

> 本版为 DRAFT，仅计划。编写过程未连接任何目标环境、未执行 ssh/scp/push/commit。E2 须用户当轮明确授权（画像 P7：测试环境"部署需用户确认=是"）。以上期 `project_workspace/ocap/deployment/` 为基线（上期锚点 `20261108234853`，已 DEPLOYED_SUCCESSFULLY）。

## 变更摘要

测试门控：phase_status GROUP_D 已 APPROVED（GR-D-002 PASS_WITH_CONDITIONS）；PM 复跑基线：后端 244 OK、frontend 122、miniprogram 69、themes-check rc=0。

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端（账号风格偏好，MOD-023） | `backend/apps/accounts/{models,services,urls,views}.py`；新增 `GET/PUT /api/v1/me/theme`（IsMember；管理员令牌 403，匿名 401） | **新增 `accounts/0002_user_theme_key.py`**：单个 `AddField theme_key CharField(max_length=32, null=True, blank=True)`，手写、单 app、依赖 `accounts/0001_initial`；可空列，无需回填 | 无 | RU-1 `ocap-backend.service`（须重启） |
| 后端（DEF-001 修复） | `backend/apps/residency/views.py:116` `AppealAdminSerializer.__init__(self, rows, many=False, context=None)` | 无 | 无 | 同 RU-1 |
| 后端依赖 | `backend/requirements.txt` 无改动（`git diff c0d1f0a HEAD` 与工作树均为空） | 无 | 无 | 不需 `pip install` |
| Web 前端 | `frontend/src/**`（含 `src/theme/`、`shared/api.js`、`index.html` 内联首屏脚本）；生成物 `frontend/src/theme/generated/` | 无 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | RU-3 静态目录 `web/ocap` |
| 风格定义/构建脚本 | `themes/`、`scripts/themes/` | 无 | 仅开发机/CI 运行，**不上传目标机**（architecture_design 部署视图） | 无 |
| nginx | 无改动 | 无 | 无 | 不动（DEPLOY-007/008 不存在于本计划） |
| systemd timer `ocap-run-due-jobs` | 无改动（上期已装） | 无 | 无 | 不动；部署后仅核验仍 active |
| 小程序 RU-4 | `miniprogram/**` | 无 | **不在本次部署范围**（见下） | 无 |

**小程序不在本次部署范围**：小程序构建在本机基线即失败（CR-007，`build:mp-weixin` 缺 manifest.json 报 ENOENT），且小程序发布方式不在画像 P7。需用户在具备完整 uni-app 工具链与微信开发者工具的环境中自行构建、上传、真机验证（MV-04）。后端新接口 `/me/theme` 部署后向后兼容，旧版小程序不受影响。

## 目标环境与策略

- **环境**：测试（画像 P7，树莓派 `raspberrypi`，用户 `yangyang`，密钥认证）。生产环境不存在，未设计。
  - 外网（执行用）：`ssh -p 57279 yangyang@47.109.197.217`，`scp -P 57279`；首次连接须核对主机 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致则停止上报。内网备选 `yangyang@192.168.31.51:22`。`ai-freeark.xin:9999` 不可用，不得使用。
  - 目标目录 `/home/yangyang/ocap/{backend,web,snapshots}`；入口：内网 `http://192.168.31.51:8090/ocap/`，外网 `https://ai-freeark.xin/ocap/`。
- **策略**：`recreate`（单实例、无冗余、无第二套环境；画像 P7 单机物理部署）。预计停机：`ocap-backend` 重启 1–3 秒；前端静态替换窗口为 `rm` 与 `tar xzf` 之间的数秒（旧 index 引用的哈希资源可能短暂 404）；nginx 不动。迁移为单个可空列 AddField，MySQL 上为元数据级/秒级变更 [INFERRED：表小，未实测]。
- **授权**：E2 前 PM 须在 invocation 的 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名"测试"（P7 环境名）。授权只认用户当轮消息，不认任何文件。
- **同机共存约束**（P7/P8）：只允许改 `/home/yangyang/ocap/**` 与 `ocap-backend` 服务；不动 Freeark 的服务、端口（80/8000/8080）、目录、库、nginx 配置；不重启 `freeark-*`；无 Docker、无 pscp、不在目标机生成迁移。
- **版本标识（无 push）**：E2 开始记录 `git rev-parse HEAD`（当前 `8597cef…`）与 `git status --short` 完整清单。部署对象 = 本地工作树，含大量未提交/未跟踪改动，提交与推送由用户确认后由主会话执行（P9）。**提醒**：推送 main 只触发 CI（不部署），但建议部署验证通过后再提交，使远端提交号与目标机内容对应。
- **保留的本地状态**：目标机 `backend/.env`、`backend/venv/`、`snapshots/`、`web/` 以外内容不被覆盖（打包排除 `.env`、`venv`）。

## 变量约定（E2 先设置再用）

```bash
OCAP_HOST=47.109.197.217; OCAP_PORT=57279; OCAP_USER=yangyang          # 内网：192.168.31.51 / 22
OCAP_SSH="ssh -p $OCAP_PORT $OCAP_USER@$OCAP_HOST"                     # 使用时不加引号
OCAP_SCP="scp -P $OCAP_PORT"
OCAP_DEST="$OCAP_USER@$OCAP_HOST"
```

引号规则：`$OCAP_SSH '…'` 单引号内的 `$VAR` **在远端展开**（用于 `.env` 加载后的 `$DB_*`、`$?`）；`$OCAP_SSH "…"` 双引号内的 `$TS` **在本地展开**（有意），远端要展开的写 `\$`。每条含 `$TS` 的命令执行前先核验 `echo "$TS"` 为 14 位数字。

## 预检清单

任一项失败（目标机尚无变更）→ 停止，`DEPLOYMENT_FAILED`，无需回滚。

| # | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 授权与环境名 | 核对 invocation | 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与"测试"，计划版本 = phase_status APPROVED 版本 |
| 2 | 主机指纹 | `ssh-keyscan -p 57279 -t ed25519 47.109.197.217 \| ssh-keygen -lf -` | = `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` |
| 3 | 版本标识 | 本地 `git rev-parse HEAD`；`git status --short` | 已完整记录；`themes/`、`scripts/themes/`、`frontend/src/theme/`、`miniprogram/theme/`、迁移 `0002` 均在清单中且存在于磁盘 |
| 4 | 后端全量回归 | `cd backend && python manage.py test --settings=config.test_settings`（测试用 venv，画像 P4） | `Ran 244 tests … OK`（零新增失败；数量不得少于 244） |
| 5 | 系统检查 + 编译 | `python manage.py check --settings=config.test_settings`；仓库根 `python -m compileall -q backend` | `no issues`；退出码 0 |
| 6 | 迁移无漂移 | `cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings`（Django 5.2.x，禁 6.x） | `No changes detected`，退出码 0；产物不提交 |
| 7 | 迁移文件合规 | `grep -c "Generated by Django" backend/apps/accounts/migrations/0002_user_theme_key.py`；`ls backend/apps/accounts/migrations/` | 计数 `0`；仅 `0001_initial`、`0002_user_theme_key`（P6、CR-023） |
| 8 | 风格定义校验 | 仓库根 `node scripts/themes/build.mjs --strict --check` | rc=0 |
| 9 | 前端测试 | `cd frontend && npx vitest run --passWithNoTests` | 122 passed，0 failed |
| 10 | 小程序测试（仅回归，不部署） | `cd miniprogram && npx vitest run --passWithNoTests` | 69 passed，0 failed |
| 11 | 前端构建 | 见 DEPLOY-006（构建在预检阶段先跑一次，产物保留） | 退出码 0；`frontend/dist/index.html` 含 `data-theme` 与 `/ocap/assets/` |
| 12 | 目标机磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | 可用磁盘 ≥ 2 GB；可用内存 ≥ 500 MB |
| 13 | 目标机服务状态（只读） | `$OCAP_SSH 'systemctl is-active ocap-backend nginx; systemctl list-timers --no-pager \| grep ocap-run-due-jobs; systemctl --state=failed --no-pager'` | `active`/`active`；timer 在列；无 `freeark-*`、`ocap-*` 失败单元 |
| 14 | 端口归属 | `$OCAP_SSH 'ss -ltnp'` | 9000、8090 属 ocap；80/8000/8080 属 Freeark |
| 15 | Freeark 基线 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/"` | `200` |
| 16 | nginx 语法（只读） | `$OCAP_SSH 'sudo nginx -t'` | `syntax is ok` |
| 17 | `.env` 存在且关键键非空（不打印值） | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && grep -Eq "^DJANGO_SECRET_KEY=.+" /home/yangyang/ocap/backend/.env && echo SECRET_KEY_SET'` | `SECRET_KEY_SET`；不 `cat .env` |
| 18 | 目标机迁移基线 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan > /tmp/mig_before.txt; grep -c "^\[ \]" /tmp/mig_before.txt'` | 未应用条数 `0`（grep 无匹配输出 0 且退出码 1 属预期）；`/tmp/mig_before.txt` 作为 ROLLBACK-004 依据。非 0 → 停止回报 |
| 19 | 数据库备份工具与权限 | `$OCAP_SSH 'command -v mysqldump'` | 有输出。无 → 停止，请用户决定（见 DEPLOY-001 备注）[INFERRED：Pi 上是否装有 mysqldump 未知] |
| 20 | requirements 未变 | 本地 `sha256sum backend/requirements.txt`；`$OCAP_SSH 'sha256sum /home/yangyang/ocap/backend/requirements.txt'` | 两值相同 → 跳过 pip；不同 → 停止回报（本计划未覆盖依赖变更） |
| 21 | 目标机本地状态不被触碰 | 核对 DEPLOY-002 打包命令 | 含 `--exclude='.env' --exclude='venv'`；`.env`、`venv/` 不在上传范围 |

## 部署步骤

### DEPLOY-001: 回滚锚点、快照与数据库备份
- 组件：RU-1、RU-3、RU-6（MySQL 库 `ocap`）
- 位置：目标机；`TS` 在本地取一次并全程复用
- 命令：
  ```bash
  TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
  echo "$TS" | grep -Eq '^[0-9]{14}$' || echo "TS 非法，停止"
  $OCAP_SSH "mkdir -p /home/yangyang/ocap/snapshots \
   && sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend \
   && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web"
  # 数据库备份：$TS 本地展开；\$DB_* 与 .env 在远端加载展开；密码经 MYSQL_PWD 传入，不出现在命令行/输出
  $OCAP_SSH "cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a \
   && umask 077 && MYSQL_PWD=\"\$DB_PASSWORD\" mysqldump -h \"\$DB_HOST\" -P \"\${DB_PORT:-3306}\" -u \"\$DB_USER\" \
      --single-transaction --no-tablespaces --skip-ssl \"\$DB_NAME\" > /home/yangyang/ocap/snapshots/db-$TS.sql"
  $OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/*-$TS.tar.gz /home/yangyang/ocap/snapshots/db-$TS.sql; tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | head -3; tail -c 200 /home/yangyang/ocap/snapshots/db-$TS.sql | grep -c 'Dump completed'"
  ```
- 预期：2 份 tar + 1 份 SQL 备份，大小非零，SQL 末尾含 `Dump completed`（计数 1）；`TS` 写入报告。nginx 不改，无需备份 nginx。备注：`--skip-ssl` 对应 `.env` 的 `DB_SSL_DISABLED` 习惯 [INFERRED]；若 mysqldump 报选项不识别（MariaDB 客户端差异）则去掉该选项重试一次，仍失败 → 停止，`DEPLOYMENT_FAILED`（此时目标机仅多了快照文件，无需回滚）。SQL 备份含业务数据，权限 600，不得读取内容到输出。快照与备份保留 ≥ 7 天。
- 回滚：ROLLBACK-001

### DEPLOY-002: 打包并上传后端代码（含 accounts/0002 与 DEF-001 修复）
- 组件：RU-1
- 位置：开发机 → 目标机
- 命令：
  ```bash
  tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
      -czf /tmp/ocap_backend.tar.gz -C backend .
  tar tzf /tmp/ocap_backend.tar.gz | grep -E 'accounts/migrations/0002_user_theme_key.py|residency/views.py'   # 两个文件必须在包内
  sha256sum /tmp/ocap_backend.tar.gz
  $OCAP_SCP /tmp/ocap_backend.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'sha256sum /tmp/ocap_backend.tar.gz'
  $OCAP_SSH 'tar xzf /tmp/ocap_backend.tar.gz -C /home/yangyang/ocap/backend'
  $OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/accounts/migrations/ && grep -n "context=None" /home/yangyang/ocap/backend/apps/residency/views.py'
  ```
- 预期：本地与目标机 sha256 一致；目标机迁移目录含 `0001_initial.py`、`0002_user_theme_key.py`；`context=None` 命中 1 行；`.env`、`venv/` 未被覆盖。解包只覆盖/新增、不删除旧文件（无害）。此时 gunicorn 仍运行旧代码（未重启），无影响。
- 回滚：ROLLBACK-002

### DEPLOY-003: 迁移前预演（只读）并应用迁移 accounts/0002（只应用，不生成）
- 组件：RU-6
- 位置：目标机（加载 `.env`；`$?`、`$DB_*` 在远端展开，故用单引号）
- 命令：
  ```bash
  $OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan'
  # 仅当 plan 恰为 accounts.0002_user_theme_key 一项时继续：
  $OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py showmigrations accounts'
  ```
- 预期：plan 仅含 `Apply … accounts.0002_user_theme_key`；`Applying accounts.0002_user_theme_key... OK`；`showmigrations accounts` 显示 `[X] 0001_initial`、`[X] 0002_user_theme_key`。plan 含其他迁移 → 停止回报（目标机尚无库变更则无需回滚）。**不得**在目标机运行 `makemigrations`。
- 数据影响：新增可空列，不改既有行；新旧代码都可并存运行。
- 回滚：ROLLBACK-003 `[MANUAL_ROLLBACK_REQUIRED: 逆向迁移 `migrate accounts 0001` 会 DROP 列 theme_key，丢失全部用户已保存的风格偏好（无法恢复，除非从 db-<TS>.sql 备份取回）；默认不执行，由用户决定]`

### DEPLOY-004: 重启后端服务
- 组件：RU-1 `ocap-backend.service`
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
  $OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
  ```
- 预期：`active`；日志无 `Traceback` / `ImproperlyConfigured`。只重启 `ocap-backend`，不触碰任何 `freeark-*`。
- 回滚：ROLLBACK-004

### DEPLOY-005: 构建并替换 Web 静态
- 组件：RU-3
- 位置：开发机构建 → 目标机替换
- 命令：
  ```bash
  node scripts/themes/build.mjs --strict --check
  VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
  grep -c 'data-theme' frontend/dist/index.html          # 期望 ≥ 1
  tar -czf /tmp/frontend_dist.tar.gz -C frontend/dist .
  sha256sum /tmp/frontend_dist.tar.gz
  $OCAP_SCP /tmp/frontend_dist.tar.gz "$OCAP_DEST:/tmp/"
  $OCAP_SSH 'sha256sum /tmp/frontend_dist.tar.gz'
  $OCAP_SSH 'rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap'
  $OCAP_SSH 'ls -l /home/yangyang/ocap/web/ocap/index.html && grep -c data-theme /home/yangyang/ocap/web/ocap/index.html'
  ```
- 预期：构建退出码 0；sha256 一致；`web/ocap/index.html` 存在、含 `data-theme` 内联脚本、资源路径以 `/ocap/assets/` 开头。构建用本地 Node 22（CI 用 20，构建脚本只用内置模块）。nginx 不动（静态目录路径不变）。放在后端之后：新前端依赖的 `/me/theme` 已可用。
- 回滚：ROLLBACK-005

## 回滚步骤（逆序）

执行前核验锚点（必须）：

```bash
TS=<DEPLOY-001 记录的值>
echo "$TS" | grep -Eq '^[0-9]{14}$' || { echo "TS 非法，停止"; }
echo "ssh 命令将使用快照: backend-$TS.tar.gz / web-$TS.tar.gz / db-$TS.sql"     # 先 echo 核对
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/db-$TS.sql"
```

三个文件均存在才继续。下列远端命令凡含 `$TS` 均用双引号（本地展开）。禁止 `git reset --hard`/`git clean`/`git stash`；目标机无 git，只用 tar 快照。所有回滚均保留 `.env`（随 backend 快照恢复，内容即部署前状态）。

**实际执行顺序**：ROLLBACK-005 → [ROLLBACK-003，仅用户决定] → ROLLBACK-002 → ROLLBACK-004 → 核验。（迁移逆向必须在旧代码恢复之前，因旧代码无 0002 文件；而旧代码与"仍存在 theme_key 列"的库兼容，故迁移逆向是可选项。）

### ROLLBACK-005: 恢复上一版 Web 静态（逆 DEPLOY-005）
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap"
  $OCAP_SSH 'ls -l /home/yangyang/ocap/web/ocap/index.html; grep -c data-theme /home/yangyang/ocap/web/ocap/index.html'
  ```
- 变量取值与核验：`TS` 见上；预期旧版 `index.html` 存在且 `data-theme` 计数为 `0`（旧版无该脚本，证明已恢复）。只动 `web/`。

### ROLLBACK-004 之前：说明
回滚后端的逆序为：先恢复代码（ROLLBACK-002）再重启（ROLLBACK-004），迁移逆向（ROLLBACK-003）若执行须插在 002 之前。下面按"编号逆序"列出，执行顺序以上方"实际执行顺序"为准。

### ROLLBACK-004: 重启回旧代码（逆 DEPLOY-004；在 ROLLBACK-002 之后执行）
- 类型：正式回滚
- 命令：
  ```bash
  $OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
  $OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
  ```
- 预期：`active`，无 Traceback；`GET /api/v1/me/theme` 回到 404（旧代码无此路由）。

### ROLLBACK-003: 撤销迁移 accounts/0002（逆 DEPLOY-003）`[MANUAL_ROLLBACK_REQUIRED: 会 DROP 列 accounts_user.theme_key，所有用户已保存的界面风格偏好永久丢失（仅 db-<TS>.sql 可取回）；部署后用户可能已写入偏好。默认建议不执行：旧代码与多出的可空列兼容；由用户决定]`
- 类型：紧急止血/数据层回退（须人工确认后执行）
- 命令（必须在 ROLLBACK-002 之前执行）：
  ```bash
  $OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate accounts 0001_initial && venv/bin/python manage.py showmigrations accounts'
  ```
- 变量取值与核验：目标 `0001_initial` 取自 `/tmp/mig_before.txt`（预检 18 保存）中 accounts 的最后一项；执行后 `showmigrations accounts` 应为 `[X] 0001_initial`、`[ ] 0002_user_theme_key`，并对照 `/tmp/mig_before.txt`（`showmigrations --plan` 再 diff）一致。
- 若选择不执行：库中保留 `0002` 记录与 `theme_key` 列；下次部署再次 `migrate` 为空操作，无副作用。

### ROLLBACK-002: 恢复后端代码（逆 DEPLOY-002）
- 类型：正式回滚（禁止 git reset/clean）
- 命令：
  ```bash
  $OCAP_SSH "sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap"
  $OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/accounts/migrations/; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -x /home/yangyang/ocap/backend/venv/bin/python && echo VENV_OK'
  ```
- 预期：迁移目录仅含 `0001_initial.py`（无 0002）；`ENV_OK`、`VENV_OK`（二者随快照恢复）。随后执行 ROLLBACK-004。

### ROLLBACK-001: 无需执行（逆 DEPLOY-001）
- 快照与备份仅为新增文件；保留 ≥ 7 天。数据库级恢复（`mysql < db-<TS>.sql`）属于 `[MANUAL_ROLLBACK_REQUIRED: 会覆盖备份后写入的全部业务数据]`，仅在 ROLLBACK-003 之外出现数据损坏时由用户决定，本计划不预置命令。

## 不可逆步骤汇总

| 步骤 | 风险 | 处理 |
|---|---|---|
| DEPLOY-003 迁移 accounts/0002 | 正向安全（可空列）；逆向 DROP 列，永久丢失用户风格偏好 | `[MANUAL_ROLLBACK_REQUIRED]`；DEPLOY-001 已做 SQL 备份；默认回滚只回退代码、保留列 |
| 数据库整库恢复 | 覆盖备份后写入的全部数据 | `[MANUAL_ROLLBACK_REQUIRED]`，不预置命令 |

## 部署后验证

自动化检查由 E2 执行（`$TS` 用于唯一化，不创建数据）；失败项 → `DEPLOYED_WITH_ISSUES`，交 PM 让用户决定是否回滚。

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端服务存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志无新错误 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback` / `ERROR` / `ImproperlyConfigured` |
| 迁移已应用 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations accounts'` | `[X] 0002_user_theme_key` |
| 首页 200 且含首屏风格脚本 | `$OCAP_SSH 'curl -s -o /tmp/ocap_index.html -w "%{http_code}\n" http://127.0.0.1:8090/ocap/ && grep -c data-theme /tmp/ocap_index.html'`；外网 `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200`；`data-theme` 计数 ≥ 1；外网 200 |
| 静态资源可达 | 取 index.html 中一个 `/ocap/assets/*.js` 与 `*.css`（含 `themes` 样式）请求内网与外网 | 均 200，非空（404 → 检查 `^~ /ocap/`，本次不应变化） |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| `/me/theme` 未登录 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/me/theme"`；外网 `https://ai-freeark.xin/ocap/api/v1/me/theme` | `401`（非 404/5xx） |
| 管理员 `GET /api/v1/admin/appeals`（DEF-001） | 路由与鉴权：`$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/admin/appeals"` 期望 `401`。端到端：先经 `POST /api/v1/admin/auth/login` 用管理员凭据取令牌（凭据由用户在 E2 当轮提供、从其指定位置读取，不写入任何文件/输出），再带令牌 `GET …/admin/appeals` | 匿名 `401`；带管理员令牌 `200` 且 JSON 含 `count`、`results`（修复前为 500）。无管理员凭据时降级为只读进程内检查：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.residency.views import AppealAdminSerializer as S; print(S([], many=True, context={}).data)"'` 输出 `[]`（不再抛 TypeError），并在报告中标注"端到端未验证，交 MV 清单由用户确认" |
| 旧接口无回归（登录端点可达） | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400`（`LOGIN_FAILED`，非 5xx） |
| timer 未受影响 | `$OCAP_SSH 'systemctl is-active ocap-run-due-jobs.timer; systemctl list-timers --no-pager \| grep ocap-run-due-jobs'` | `active`，NEXT 非 `n/a` |
| Freeark 未受影响 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/"`；外网 `https://ai-freeark.xin/` | 均 `200` |
| 失败单元/端口归属 | `$OCAP_SSH 'systemctl --state=failed --no-pager; ss -ltnp'` | 无 `freeark-*`、`ocap-*` 失败单元；8000/8080 属 Freeark，8090/9000 属 ocap |

## 人工验证清单（交给用户；引用 e2e_test_report 2.0.0 的 MV-01…MV-12）

自动化检查全部通过后，由用户在测试环境 Web 入口（内网 `http://192.168.31.51:8090/ocap/` 或外网 `https://ai-freeark.xin/ocap/`）用 Chrome 桌面与移动模拟完成。步骤、期望与设备以 e2e_test_report"人工验证清单"原文为准，此处只列对应关系与本次可执行性：

| 编号 | 内容 | 本次部署后是否可验 | 备注 |
|---|---|---|---|
| MV-01 | A/B/C 首页与个人中心对照设计 | 是 | critical path |
| MV-02 | 14 个用户端页 × 3 风格走查 | 是 | critical path |
| MV-03 | 管理端 9 页固定风格 B | 是 | critical path；需管理员账号 |
| MV-04 | 小程序 11 页 × 3 风格（微信开发者工具/真机） | **否，不在本次范围** | 需用户在完整 uni 工具链环境构建并上传（CR-007） |
| MV-05 | ≤767px 底部 5 项标签栏 | 是 | critical path；AC-084-02 为已知 PARTIAL |
| MV-06 | 切换风格 ≤ 1 s | 是 | critical path；注意测试环境经 frp 外网会增大 PUT 延迟，建议内网复测 |
| MV-07 | 刷新首屏无闪烁 | 是 | |
| MV-08 | 减少动态效果/低端降级 | 是（小程序部分除外） | |
| MV-09 | 点击区域 ≥44px、聚焦环 | 是（小程序部分除外） | |
| MV-10 | 状态标签灰度可辨、5 类组件 | 是（小程序部分除外） | |
| MV-11 | 系统深浅色不影响风格 | 是 | critical path |
| MV-12 | 导航高亮可辨 | 是 | |

另加补充项（对应 DEF-001）：管理员登录后打开管理端"申诉"页应能加载列表（若 E2 未能做带令牌的端到端检查）。critical path 人工项（MV-01/02/03/04/05/06/11）完成前，最终交付状态至多 DELIVERED_WITH_ISSUES（GR-D 条件）。

## 遗留与假设

| 问题 | 级别 | 说明 |
|---|---|---|
| `[INFERRED]` 迁移执行耗时 | MINOR | 可空 AddField 在小表上预计秒级，未实测 |
| `[INFERRED]` Pi 上存在 `mysqldump` 及 `--skip-ssl` 选项 | MINOR | 预检 19 验证；不满足则停止请用户决定 |
| `[INFERRED]` 目标机 `.env` 含 `DB_PORT`（缺省按 3306） | MINOR | DEPLOY-001 命令用 `${DB_PORT:-3306}` |
| 工作树含大量未提交/未跟踪文件 | MINOR | 部署对象为本地工作树；部署后由用户确认提交推送（P9）；推送 main 只触发 CI，不部署 |
| 小程序未部署 | 范围外 | 见变更摘要 |
| 前端替换窗口 | MINOR | `rm` 与解包之间数秒；沿用上期方式，测试环境可接受 |
| CR-011、CR-008、CR-007 | 沿用 | 见 e2e_test_report 缺陷/遗留 |
