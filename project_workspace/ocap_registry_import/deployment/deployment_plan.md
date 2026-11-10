<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-10T23:16:12+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>architecture/architecture_design.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>testing/e2e_test_report.md</file><file>project_workspace/ocap_registry_import/phase_status.md</file><file>.trae/skills/ocap-deploy/SKILL.md</file></input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：业主清册导入增强 → 测试环境（树莓派）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 registry | `apps/registry/{models,serializers,services,views,urls}.py`、新增 `import_spec.py`、`importing.py`、`import_template.py` | `0002_owner_type_area`、`0003_backfill_legacy_owners`、`0004_phone_owner_required`（手写，依赖 0001） | 无编译产物（Python 源码 + 依赖） | `ocap-backend.service`（gunicorn `127.0.0.1:9000`） |
| 后端 residency/accounts/identity | `apps/residency/{services,auto_bind}.py`、`apps/accounts/views.py`、`apps/identity/views.py` | 无 | 同上 | 同上 |
| 前端 Web | `src/admin/{AdminRegistry.vue,RegistryImportDialog.vue,registryImport.js}`、`src/portal/{Units,Register,Me}.vue`、`src/shared/api.js` | 无 | `npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 静态文件同步到 `/home/yangyang/ocap/web/ocap`；nginx 无配置变更 |
| 小程序 | `pages/units`、`pages/phone`、`utils/api.js` | 无 | 不在本计划（RU-4 提审发布另行处理） | — |
| 配置/服务单元 | 无新增 `.env` 键；`deploy/systemd/*` 不变 | — | — | 不新增 systemd 单元（RU-2 定时任务缺口维持现状） |
| 依赖 | `backend/requirements.txt` 已含 `openpyxl>=3.1,<4.0`（本次首次在目标机安装生效） | — | — | 目标机 venv |

## 目标环境与策略

- **环境**：测试（内网）`192.168.31.51`（`yangyang`，免密 SSH），库 `ocap`（MySQL `192.168.31.98:3306`）；外网经 `https://ai-freeark.xin/ocap/` 复用既有 frp 通道。画像 P7 无生产环境。
- **策略**：`recreate`（单实例、无冗余，画像 P7；blue-green/rolling 无第二套实例，canary 无分流）。重启期间后端不可用，预计停机 30–60 秒（`systemctl restart` + gunicorn 启动）；前端静态切换为秒级。
- **同机共存约束**：只改 `/home/yangyang/ocap/**`、`ocap-backend.service`、`/etc/nginx/sites-available/ocap` 与 `/etc/nginx/sites-enabled/freeark` 的 `^~ /ocap/` 段；禁止触碰/重启 `freeark-*`、Freeark 库与 nginx 其他段，不得占用 8000/8080/80。
- **回滚偏好**：目标机无 git（`ocap-deploy` §8），采用 tar 快照恢复（时间戳锚点）；禁止 `git reset/clean/stash`。

## 预检清单

> 全部在目标机或开发机执行；任一关键项失败 → 停止，不产生任何变更。凭据只从 `/home/yangyang/ocap/backend/.env` 读取，不打印值。

| ID | 检查项 | 命令 | 通过标准 |
|---|---|---|---|
| PRE-001 | 部署内容可追溯 | 开发机：`git rev-parse HEAD`、`git status --short`、`git ls-remote origin main` | 工作树干净且 HEAD 与 `origin/main` 一致；若用户批准"工作树快照"降级，则记录 HEAD + `git status` + 两个 tar 的 SHA256 代替 |
| PRE-002 | SSH 与 sudo | `ssh yangyang@192.168.31.51 'id -u && sudo -n true && echo SUDO_OK'` | 返回 uid 与 `SUDO_OK` |
| PRE-003 | 磁盘/内存 | `df -h /home`；`free -m` | 可用 ≥ 2 GB；可用内存 ≥ 500 MB |
| PRE-004 | 端口归属 | `ss -ltn` | 8000/8080/80 属 Freeark；9000 属 ocap；8090 属 ocap nginx |
| PRE-005 | 环境变量文件 | `test -f /home/yangyang/ocap/backend/.env && echo ENV_OK`；`grep -c '^DB_' .env` | `ENV_OK`，含 `DB_ENGINE/DB_NAME/DB_HOST/DB_USER/DB_PASSWORD` 等键（只看键名） |
| PRE-006 | 依赖可解析 | `cd /home/yangyang/ocap/backend && venv/bin/pip install --dry-run -r requirements.txt` | 退出码 0，可安装 `openpyxl` |
| PRE-007 | 迁移计划 | `set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations registry` | `0001` 已应用；`0002~0004` 未应用（若已应用需说明来源） |
| PRE-008 | 迁移前数据基线 | `venv/bin/python manage.py shell -c "from apps.registry.models import *; print(RegistryUnit.objects.count(), RegistryPhone.objects.count())"` | 输出可记录（作为回滚后核对基数）；命令失败则先查库连通 |
| PRE-009 | nginx 语法与容量（R2） | `sudo nginx -t`；`sudo grep -n 'client_max_body_size\|proxy_read_timeout' /etc/nginx/sites-available/ocap`；`sudo nginx -T \| grep -n 'client_max_body_size'` | 语法 OK；ocap 站点 `client_max_body_size ≥ 5m` 且 `proxy_read_timeout ≥ 90s`（否则执行 DEPLOY-003） |
| PRE-010 | gunicorn 超时（R1） | `systemctl cat ocap-backend \| grep -n 'ExecStart'`；`ps -eo cmd \| grep '[g]unicorn'` | `--timeout ≥ 90`（否则执行 DEPLOY-003） |
| PRE-011 | Freeark 基线 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/`；`systemctl --state=failed --no-pager` | 200；无 `freeark-*` failed |
| PRE-012 | 回滚锚点可写 | `test -w /home/yangyang/ocap/snapshots \|\| mkdir -p /home/yangyang/ocap/snapshots` | 目录可写 |

## 部署步骤

> `TS` 由 DEPLOY-001 生成并记录；后续所有命令使用同一个 `$TS`。远端命令中的变量均在本地先展开或写成确定值（避免 `ssh host '…$VAR…'` 在远端为空）。

### DEPLOY-001: 生成回滚快照

- 组件：目标机后端目录、前端静态、nginx 配置、systemd 单元（引 `architecture_design.md` 部署视图）
- 位置：目标机
- 命令：
```bash
ssh yangyang@192.168.31.51 'mkdir -p /home/yangyang/ocap/snapshots; TS=$(date +%Y%m%d%H%M%S); \
sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend; \
sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web; \
sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS; \
sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS; \
sudo cp /etc/systemd/system/ocap-backend.service /home/yangyang/ocap/snapshots/ocap-backend.service.bak_$TS 2>/dev/null || systemctl cat ocap-backend | sudo tee /home/yangyang/ocap/snapshots/ocap-backend.service.bak_$TS >/dev/null; \
echo ANCHOR_TS=$TS' | tee /tmp/ocap_deploy_anchor.txt
```
- 预期：输出 `ANCHOR_TS=<14 位时间戳>`；三个快照文件存在且大小 > 0
- 回滚：ROLLBACK-001

### DEPLOY-002: 备份 registry 三表（迁移前）

- 位置：目标机（读远端 MySQL，凭据取自 `.env`，不落盘明文）
- 命令：
```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a; \
mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
registry_registryunit registry_registryowner registry_registryphone \
> /home/yangyang/ocap/snapshots/registry-<TS>.sql && wc -l /home/yangyang/ocap/snapshots/registry-<TS>.sql'
```
- 预期：命令退出码 0，SQL 文件行数 > 0；无 "Using a password on the command line" 以外的新错误（若 `mysqldump` 不存在 → 降级为 `venv/bin/python manage.py dumpdata registry --indent 2 > snapshots/registry-<TS>.json`）
- 回滚：ROLLBACK-002

### DEPLOY-003: 参数调整（条件性，仅当 R1/R2 不满足）

- 组件：`ocap-backend.service`（gunicorn `--timeout`）、`/etc/nginx/sites-available/ocap`（`client_max_body_size 5m`、`proxy_read_timeout 90s`）
- 位置：目标机
- 命令：
```bash
# 仅当 R1 不满足时：非交互定位单元文件并备份
ssh yangyang@192.168.31.51 'systemctl show -p FragmentPath ocap-backend'
# 人工在目标机编辑该单元，使 gunicorn ExecStart 含 --timeout 90；交互式编辑无法由自动化安全完成
ssh yangyang@192.168.31.51 'sudo systemctl edit --full ocap-backend'
# 仅当 R2 不满足时：在 ocap 8090 站点 server 段内追加（不触碰 Freeark）
ssh yangyang@192.168.31.51 'sudo grep -q "client_max_body_size" /etc/nginx/sites-available/ocap || sudo sed -i "/server {/a\    client_max_body_size 5m;\n    proxy_read_timeout 90s;" /etc/nginx/sites-available/ocap; sudo nginx -t && sudo systemctl reload nginx'
ssh yangyang@192.168.31.51 'sudo systemctl daemon-reload && sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
```
- 预期：`nginx -t` successful；`systemctl is-active` = `active`；`systemctl cat ocap-backend | grep -- --timeout` 显示 ≥ 90
- 备注：`systemctl edit --full` 为交互操作；E2 中若 R1 不满足，执行到此暂停并请用户完成编辑（或由用户提供已修改的单元内容后由 PM 落盘），不视为失败
- 回滚：ROLLBACK-003

### DEPLOY-004: 打包并上传后端

- 位置：开发机 → 目标机
- 命令：
```bash
# 开发机仓库根（PowerShell 下用 tar 同参数）
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
    -czf /tmp/ocap_backend_<TS>.tar.gz -C backend .
Get-FileHash -Algorithm SHA256 /tmp/ocap_backend_<TS>.tar.gz    # Windows 开发机；Linux 用 sha256sum
scp /tmp/ocap_backend_<TS>.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'sha256sum /tmp/ocap_backend_<TS>.tar.gz'
ssh yangyang@192.168.31.51 'tar xzf /tmp/ocap_backend_<TS>.tar.gz -C /home/yangyang/ocap/backend'
```
- 预期：两端 SHA256 一致；解包退出码 0；`/home/yangyang/ocap/backend/.env` 仍存在
- 回滚：ROLLBACK-004

### DEPLOY-005: 同步依赖（安装 openpyxl）

- 位置：目标机
- 命令：
```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && venv/bin/pip install -r requirements.txt && venv/bin/python -c "import openpyxl; print(openpyxl.__version__)"'
```
- 预期：`pip` 退出码 0；打印 `3.1.x`
- 回滚：ROLLBACK-005（默认不卸载；向后兼容）

### DEPLOY-006: 执行迁移 0002–0004

- 位置：目标机（不可逆：结构变更 + 数据回填）
- 命令：
```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py showmigrations registry'
```
- 预期：`Applying registry.0002…OK`、`0003…OK`、`0004…OK`；`showmigrations` 四条均为 `[X]`；无 `RuntimeError: 仍有 N 条手机号未归属业主`
- 回滚：ROLLBACK-006 `[MANUAL_ROLLBACK_REQUIRED]`
- 备注：`0003` 为既有手机号回填无名业主；`0004` 成功前断言无孤儿手机号。迁移后业主/手机号行数会变化，属预期。

### DEPLOY-007: 构建并上传前端

- 位置：开发机（构建）→ 目标机（替换静态）
- 命令：
```powershell
# 开发机仓库根
$env:VITE_API_BASE='/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
tar -czf frontend_dist_<TS>.tar.gz -C frontend\dist .
scp frontend_dist_<TS>.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/web/ocap && sudo mkdir -p /home/yangyang/ocap/web/ocap && sudo tar xzf /tmp/frontend_dist_<TS>.tar.gz -C /home/yangyang/ocap/web/ocap && ls /home/yangyang/ocap/web/ocap/index.html'
```
- 预期：构建退出码 0；`index.html` 存在；`/home/yangyang/ocap/web/ocap/assets` 有新哈希文件
- 回滚：ROLLBACK-007

### DEPLOY-008: 重启后端并确认存活

- 位置：目标机
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend'
ssh yangyang@192.168.31.51 'sudo journalctl -u ocap-backend -n 40 --no-pager'
```
- 预期：`active`；日志无 `Traceback`/`OperationalError`；出现 gunicorn 启动行
- 回滚：ROLLBACK-008

## 回滚步骤（逆序）

> 全部使用 DEPLOY-001 的 `TS`；执行前核验 `/home/yangyang/ocap/snapshots/backend-$TS.tar.gz` 与 `web-$TS.tar.gz` 存在。远端命令使用已展开的具体时间戳，避免变量为空。

### ROLLBACK-008: 重启后端以加载回滚后的代码

- 类型：正式回滚（无状态步骤）
- 命令：`ssh yangyang@192.168.31.51 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend'`
- 变量与核验：无变量；在 ROLLBACK-004 完成后执行（单独执行无意义）
- 预期：`active`，日志无 Traceback

### ROLLBACK-007: 恢复前端静态（回滚 DEPLOY-007）

- 类型：正式回滚
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-<TS>.tar.gz -C /home/yangyang/ocap && ls /home/yangyang/ocap/web/ocap/index.html'
```
- 变量与核验：`<TS>` 取自 `/tmp/ocap_deploy_anchor.txt`；执行前 `test -s snapshots/web-<TS>.tar.gz`
- 预期：旧 `index.html` 恢复；浏览器加载旧资源哈希

### ROLLBACK-006: 回退迁移（回滚 DEPLOY-006）

- 类型：紧急止血 + 数据风险
- 命令：
```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate registry 0001 --noinput'
```
- 变量与核验：迁移目标固定 `0001_initial`；执行前确认 0002 之后无其他 registry 迁移
- 预期：`Unapplying registry.0004…OK`、`0003…OK`、`0.0002…OK`
- `[MANUAL_ROLLBACK_REQUIRED: 0003 的反向会删除回填的无名业主并把手机号 owner 置空；0002 反向删除 owner 表与类型/面积列，期间新导入的业主/手机号数据将丢失。仅在确认可丢数据或将以 ROLLBACK-002 恢复三表时执行]`

### ROLLBACK-005: 依赖处理（回滚 DEPLOY-005）

- 类型：一般不执行
- 命令：默认不卸载（`openpyxl` 向后兼容）；如需精确回退：`venv/bin/pip uninstall -y openpyxl`
- 预期：服务仍可启动（旧代码不引用 openpyxl）

### ROLLBACK-004: 恢复后端代码（回滚 DEPLOY-004）

- 类型：正式回滚
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-<TS>.tar.gz -C /home/yangyang/ocap && sudo test -f /home/yangyang/ocap/backend/.env && echo ENV_KEPT'
```
- 变量与核验：`<TS>` 取自锚点文件；执行前 `tar tzf snapshots/backend-<TS>.tar.gz | head` 确认包含 `backend/manage.py`
- 预期：`ENV_KEPT`；随后执行 ROLLBACK-008 重启
- 备注：快照包含 `.env` 与 venv 吗？——`backend-$TS.tar.gz` 是目标机整目录快照，包含 `.env` 与 venv，因此恢复不会丢配置；开发机打包时则排除了 `.env`

### ROLLBACK-003: 恢复参数（回滚 DEPLOY-003）

- 类型：正式回滚（仅当 DEPLOY-003 执行过）
- 命令：
```bash
ssh yangyang@192.168.31.51 'sudo cp /home/yangyang/ocap/snapshots/ocap-backend.service.bak_<TS> /etc/systemd/system/ocap-backend.service && sudo systemctl daemon-reload'
ssh yangyang@192.168.31.51 'sudo cp /etc/nginx/sites-available/ocap.bak_<TS> /etc/nginx/sites-available/ocap && sudo nginx -t && sudo systemctl reload nginx'
```
- 预期：`nginx -t` successful；`systemctl is-active nginx` = `active`
- 备注：只恢复 ocap 站点配置；Freeark 配置本次未改（备份仅作保险，不执行恢复）

### ROLLBACK-002: 恢复 registry 三表（回滚 DEPLOY-002）

- 类型：紧急止血 + 数据风险
- 命令：
```bash
ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < /home/yangyang/ocap/snapshots/registry-<TS>.sql'
```
- 变量与核验：执行前 `wc -l snapshots/registry-<TS>.sql` > 0
- 预期：导入无错误；行数与 PRE-008 基线一致
- `[MANUAL_ROLLBACK_REQUIRED: 此步会覆盖迁移后新增/修改的清册数据；仅在 ROLLBACK-006 之后执行]`

### ROLLBACK-001: 快照保留（回滚 DEPLOY-001）

- 类型：无操作（快照不改变系统状态）
- 预期：快照保留 ≥ 7 天；清理旧快照需用户确认

## 不可逆步骤汇总

| 步骤 | 不可逆内容 | 风险与缓解 |
|---|---|---|
| DEPLOY-006 / ROLLBACK-006 | 迁移 0002 结构变更、0003 无名业主回填、0004 非空收紧 | 回退会删除回填业主/owner 表并按需恢复；执行前 DEPLOY-002 已备份三表；回退仅在数据可丢或已恢复时执行 `[MANUAL_ROLLBACK_REQUIRED]` |
| DEPLOY-002 / ROLLBACK-002 | 三表 SQL 覆盖恢复 | 仅用于回滚；会覆盖迁移后数据，须人工确认 |
| 前端/后端代码替换 | 目标机上就地覆盖 | 已有 tar 快照，可完整恢复；不删除目标机 `.env`/`venv` |

## 部署后验证

| ID | 检查项 | 命令 / URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `systemctl is-active ocap-backend` | `active` |
| V-02 | 后端日志 | `journalctl -u ocap-backend --since '-5 min' --no-pager` | 无 Traceback / OperationalError |
| V-03 | 迁移状态 | `manage.py showmigrations registry` | `0001~0004` 全部 `[X]` |
| V-04 | 内网前端 | `curl -s -o /dev/null -w '%{http_code}' http://192.168.31.51:8090/ocap/` | 200 |
| V-05 | 外网前端 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | 200 |
| V-06 | SPA 回退 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/admin/login` | 200 |
| V-07 | 新路由已生效 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/api/v1/admin/registry/import/spec` | 401 或 403（未认证），非 404 |
| V-08 | xlsx 模板可用（只读） | `ssh … 'cd …/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.import_template import build_xlsx; from io import BytesIO; from openpyxl import load_workbook; d=build_xlsx(); print(len(d), d[:2]==b\"PK\"); print(load_workbook(BytesIO(d)).sheetnames)"'` | 字节数 > 0、`True`、sheetnames 含 `填写说明`（闭环 GR-D-001-F01 的 xlsx 证据） |
| V-09 | 20000 行预检抽样（只读，不写库） | 在目标机 `/tmp/ocap_perf_check.py` 生成 20000 行 csv 并调用 `read_rows` + `plan_import`（dry-run，不 `apply_plan`），计时；含 10% 错误行再跑一次 | 两次均在 60 秒内完成；记录实际秒数，回填 e2e_test_report M-04~M-06（引擎级口径，不含 HTTP/nginx） |
| V-10 | Freeark 未受影响 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/`；`systemctl --state=failed --no-pager` | 200；无 `freeark-*` failed |
| V-11 | 静态资源 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/assets/<hash>.js`（hash 取自 V-05 页面） | 200 |

> V-08/V-09 为只读核验（不写业务库），用于关闭 GR-D-001 的人工验证条件；V-09 为引擎级抽样，结论写"引擎级通过，HTTP/nginx 端到端仍以线上实测为准"。
