<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T00:53:36+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>2.0.0</version>
  <input_files><file>architecture/architecture_design.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>testing/e2e_test_report.md</file><file>project_workspace/ocap_registry_import/phase_status.md</file><file>.trae/skills/ocap-deploy/SKILL.md</file><file>.claude/skills/ocap-deploy/SKILL.md</file><file>deployment/deployment_report.md</file><file>testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：业主清册导入增强 → 测试环境（树莓派）

> 1.1.0 修订：在末尾新增「增量重部署 R2（提交 a0a0b3a，DEF-007~012）」一节。首次部署（DEPLOY-001~008，1.0.0）已于 2026-11-10 执行完毕（见 deployment_report.md），其正文原样保留作历史与回滚参考；R2 的步骤编号为 R2-DEPLOY-NNN / R2-ROLLBACK-NNN，与 1.0.0 编号不冲突。

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


---

# 增量重部署 R2（提交 a0a0b3a，DEF-007~012）

## R2-1 变更摘要与适用性判定

依据：implementation_plan 2.0.0「缺陷修复（DEF-007~012）」、`git diff --name-status 567b137 a0a0b3a -- backend frontend`、deployment_report 1.0.0（目标机现状：迁移 0001~0004 已应用，openpyxl 已装，gunicorn `--timeout 90` 与 nginx `proxy_read_timeout 90s` 已生效，gunicorn 4 workers）。

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 registry | `apps/registry/{import_spec,import_template,importing,views}.py`（均为修改） | 无 | 无 | `ocap-backend.service` |
| 后端 residency | `apps/residency/auto_bind.py`（修改） | 无 | 无 | 同上 |
| 前端 Web | `frontend/src/admin/registryImport.js`（修改） | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` | 静态目录 `/home/yangyang/ocap/web/ocap` |
| 测试文件（随 backend 打包，运行期不引用） | `backend/tests/{e2e,integration,unit}` 下 3 个新增文件；`frontend/tests/*` 不进入构建产物 | 无 | 无 | 无 |
| 不涉及 | `backend/requirements.txt`、`.env` 键、`deploy/systemd/*`、nginx 配置、gunicorn 参数、小程序、`.github/workflows/ci.yml` | — | — | — |

CI 影响：`cicd_pipeline.md` 1.0.0 无需变更。ci.yml 不动；本次仅测试规模增加（后端 342、前端 128、小程序 69，PM 复跑于 a0a0b3a），无新依赖、新服务、新环境变量。

## R2-2 原计划步骤适用性

| 原步骤 | R2 | 理由 |
|---|---|---|
| DEPLOY-001 快照 | 适用（改为 R2-DEPLOY-001，精简） | 需要新回滚锚点；nginx/unit 无改动，不再备份它们 |
| DEPLOY-002 registry 三表 mysqldump | 跳过 | 无迁移、无表结构变更；新代码只读写既有表的既有列，回滚只回代码，不需要数据恢复点。导入产生的业务数据属于正常使用，不由部署回滚撤销 |
| DEPLOY-003 gunicorn/nginx 参数 | 跳过 | 1.0.0 已落地 `--timeout 90` 与 `proxy_read_timeout 90s`，R2 不改；R2-PRE-007 只读复核仍然生效 |
| DEPLOY-004 打包上传后端 | 适用（R2-DEPLOY-002），改用 `git archive` 从提交 a0a0b3a 打包 | 保证不含未跟踪文件 |
| DEPLOY-005 依赖 | 跳过 | requirements.txt 自 1.0.0 部署后无变化（`git diff 567b137 a0a0b3a -- backend/requirements.txt` 应为空，R2-PRE-004 核验） |
| DEPLOY-006 迁移 | 跳过 | 无新迁移文件（`git diff --name-status 567b137 a0a0b3a -- backend/apps | grep migrations` 无输出）；以 `showmigrations` 只读确认无待执行迁移作为预检（R2-PRE-006）。**R2 不执行 `migrate`** |
| DEPLOY-007 前端 | 适用（R2-DEPLOY-003） | registryImport.js 变更需重新构建 |
| DEPLOY-008 重启 | 适用（R2-DEPLOY-004） | 加载新 Python 代码 |

## R2-3 目标环境与策略

- 环境：测试（树莓派，画像 P7 唯一环境；部署需用户确认=是，授权见 phase_status 2026-11-11T00:51:07 DEPLOY_AUTH 条目，E2 调用时仍须 PM 在 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名「测试」）。
- 连接：本次由 Claude 主会话云主机执行，走外网通道，不使用内网 192.168.31.51 作 SSH 目标。首次连接核对主机 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报。
- 策略：`recreate`（单实例，理由同 1.0.0）。预计停机：仅 `ocap-backend` 重启，约 5~15 秒 `[INFERRED]`（上次 `restart`+启动检查整体 < 60 秒）；前端静态替换为秒级，nginx 不 reload，Freeark 不受影响。
- 回滚偏好：tar 快照恢复 + 重启（目标机无 git）；禁止 `git reset/clean/stash`。
- 同机共存约束：不触碰 Freeark 服务/端口/目录/库、nginx 其他段、VPS frp 配置；不 `cat .env`，不写入凭据。

连接变量（bash，沿用 ocap-deploy SKILL §2 写法）：

```bash
OCAP_HOST=47.109.197.217
OCAP_PORT=57279
OCAP_USER=yangyang
OCAP_SSH="ssh -p $OCAP_PORT $OCAP_USER@$OCAP_HOST"      # 使用时不加引号
OCAP_SCP="scp -P $OCAP_PORT"                            # scp 端口为大写 -P
OCAP_DEST="$OCAP_USER@$OCAP_HOST"
REL=a0a0b3a                                             # 本次发布提交
```

引号规则：含本地变量（`$TS`）的远端命令一律用双引号；远端自己展开的变量写 `\$`；单引号中的 `$VAR` 在远端展开（常为空）。执行前对含变量的命令先 `echo` 核对。

## R2-4 预检清单

任一关键项失败 → 停止，不产生任何目标机变更，报 `DEPLOYMENT_FAILED`。

| ID | 检查项 | 命令（bash） | 通过标准 |
|---|---|---|---|
| R2-PRE-001 | 本地 HEAD 即发布版本 | 仓库根：`git rev-parse HEAD`（取前 7 位） | 完整哈希以 `a0a0b3a` 开头 |
| R2-PRE-002 | 与远端一致 | `git ls-remote origin main` | 输出哈希 = 上一项完整哈希 |
| R2-PRE-003 | 打包范围无本地脏文件 | `git status --porcelain --untracked-files=all -- backend frontend` | 无输出（`project_workspace/` 下未提交文档不影响打包，因后端用 `git archive`；前端因要在工作树构建而要求干净） |
| R2-PRE-004 | 无迁移、无依赖变化 | `git diff --name-status 567b137 $REL -- backend/apps | grep -c migrations`；`git diff --name-only 567b137 $REL -- backend/requirements.txt deploy .github` | 第一条为 `0`；第二条无输出 |
| R2-PRE-005 | 迁移无漂移（开发机） | `cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings`（PM 会话 venv，Django 5.2.x） | 退出码 0 |
| R2-PRE-006 | 目标机迁移已全部应用（只读） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan > /tmp/ocap_mig_r2_before.txt; grep -c "^\[ \]" /tmp/ocap_mig_r2_before.txt; grep "registry" /tmp/ocap_mig_r2_before.txt'` | 未应用条数 `0`；registry 0001~0004 均为 `[X]`。非 0 → 停止，**不**执行 `migrate`，交回开发 |
| R2-PRE-007 | 1.0.0 参数仍有效（只读） | `$OCAP_SSH 'systemctl cat ocap-backend \| grep -- --timeout; sudo grep -n proxy_read_timeout /etc/nginx/sites-available/ocap'` | `--timeout 90` 与 `proxy_read_timeout 90s` 仍在 |
| R2-PRE-008 | 磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | 可用磁盘 ≥ 2 GB；可用内存 ≥ 500 MB |
| R2-PRE-009 | 端口归属与 Freeark 基线 | `$OCAP_SSH 'ss -ltn; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/; systemctl --state=failed --no-pager'` | 8000/8080/80 属 Freeark，9000/8090 属 ocap；8080 返回 200；无 failed 单元 |
| R2-PRE-010 | env 与回滚目录（不打印内容） | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -w /home/yangyang/ocap/snapshots && echo SNAP_OK'` | `ENV_OK` 与 `SNAP_OK` |
| R2-PRE-011 | 运行时目录体量（决定快照范围） | `$OCAP_SSH 'du -sh /home/yangyang/ocap/backend /home/yangyang/ocap/backend/venv /home/yangyang/ocap/backend/var 2>&1'` | 记录各项大小；`backend/var`（`MEDIA_ROOT`，settings.py:86）与 `venv` 排除出快照，见下 |
| R2-PRE-012 | 回滚锚点（版本）记录 | 在 R2-DEPLOY-001 之前：`$OCAP_SSH 'ls -l --time-style=long-iso /home/yangyang/ocap/backend/apps/registry/importing.py /home/yangyang/ocap/web/ocap/index.html; ls /home/yangyang/ocap/web/ocap/assets \| head -3'` | 记录当前文件时间与前端资源哈希，作为回滚后核对基线；R2 之前的目标机版本 = 1.0.0 部署的提交 567b137（deployment_report.md:19）；ANCHOR_TS=20261110232450 是 1.0.0 部署前的更早锚点，不用于 R2 回滚 |

**GR-B 遗留（快照膨胀）**：目标机 `backend/` 含 `venv/`、`.env`、可能含 `var/attachments`（用户上传附件，会随使用增长）。R2 快照只含代码，使用 `--exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__`，使其大小为 MB 级且不随附件膨胀；这些目录在 R2 中不被修改，故无需快照。相应地，**回滚用「叠加解包」而不是 `rm -rf backend`**，以免误删 `var/`、`venv/`、`.env`。

## R2-5 部署步骤

### R2-DEPLOY-001: 生成回滚快照（目标机）

- 组件：目标机后端代码与前端静态（引 architecture_design 部署视图）
- 位置：目标机（经外网 SSH）
- 命令（`TS` 在本地取一次并复用）：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
echo "$TS" | grep -Eq '^[0-9]{14}$' || { echo "TS 非法，停止"; exit 1; }
$OCAP_SSH "sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap \
  --exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__ backend \
 && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web \
 && ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz \
 && tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | grep -c 'apps/registry/importing.py'"
```
- 预期：`ANCHOR_TS=<14 位>`；两个快照存在且大小 > 0（backend 预期远小于 1.0.0 的 26 MB，约 1 MB 量级 `[INFERRED]`）；最后一行 `1`
- 回滚：R2-ROLLBACK-001（无操作）
- 说明：nginx 与 systemd unit R2 不改，不再备份；既有 1.0.0 备份保留。

### R2-DEPLOY-002: 从提交打包并上传后端（开发机 → 目标机）

- 位置：开发机 → 目标机
- 命令：
```bash
# 仓库根；git archive 只含已提交的跟踪文件，不含未跟踪文件，且无 .env/venv/var
git archive --format=tar.gz -o /tmp/ocap_backend_$TS.tar.gz $REL:backend
sha256sum /tmp/ocap_backend_$TS.tar.gz
tar tzf /tmp/ocap_backend_$TS.tar.gz | grep -Ec '(^|/)(\.env|venv/|var/)'      # 期望 0
$OCAP_SCP /tmp/ocap_backend_$TS.tar.gz "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/ocap_backend_$TS.tar.gz && tar xzf /tmp/ocap_backend_$TS.tar.gz -C /home/yangyang/ocap/backend && test -f /home/yangyang/ocap/backend/.env && echo ENV_KEPT"
```
- 预期：两端 SHA256 一致；排除检查输出 `0`；`ENV_KEPT`；解包仅覆盖/新增（不删除旧文件，R2 无删除文件，`git diff --name-status` 无 `D`）
- 回滚：R2-ROLLBACK-002

### R2-DEPLOY-003: 构建并替换前端静态（开发机 → 目标机）

- 位置：开发机（构建）→ 目标机
- 命令：
```bash
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
tar -czf /tmp/frontend_dist_$TS.tar.gz -C frontend/dist .
sha256sum /tmp/frontend_dist_$TS.tar.gz
$OCAP_SCP /tmp/frontend_dist_$TS.tar.gz "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/frontend_dist_$TS.tar.gz && rm -rf /home/yangyang/ocap/web/ocap/* && tar xzf /tmp/frontend_dist_$TS.tar.gz -C /home/yangyang/ocap/web/ocap && ls /home/yangyang/ocap/web/ocap/index.html"
```
- 预期：构建退出码 0；SHA256 一致；`index.html` 存在，`assets/` 出现新哈希文件；`index.html` 中资源以 `/ocap/assets/` 开头
- 回滚：R2-ROLLBACK-003
- 说明：构建在工作树进行，故 R2-PRE-003 要求 `frontend/` 干净、HEAD = a0a0b3a。

### R2-DEPLOY-004: 重启 ocap-backend 并确认存活（目标机）

- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend'
$OCAP_SSH 'sudo journalctl -u ocap-backend -n 40 --no-pager'
```
- 预期：`active`；日志无 `Traceback`/`OperationalError`，出现 gunicorn 启动与 4 个 worker
- 回滚：R2-ROLLBACK-004
- 顺序说明：先解包后端代码、再换前端、最后重启，使重启前新旧代码并存时间最短；后端新旧版本对 API 契约兼容（仅修缺陷，无路由/字段变更），前端先于重启更新无兼容风险。

## R2-6 回滚步骤（逆序，锚点为 R2-DEPLOY-001 的 `TS`）

执行前核验（必须）：

```bash
TS=<R2-DEPLOY-001 记录的值>
echo "$TS" | grep -Eq '^[0-9]{14}$' || { echo "TS 非法，停止"; }
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz"
$OCAP_SSH "tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | grep -c 'backend/manage.py'"   # 期望 1
```
两个文件存在且 manage.py 计数为 1 才继续；下面远端命令均用双引号使 `$TS` 在本地展开，执行前可先 `echo` 核对。触发条件：任一 R2-DEPLOY 步骤失败且目标机已有变更 → 立即停止后续步骤，从失败步骤起逆序回滚；回滚后重跑相关验证。禁止 `git reset` / `git clean` / `git stash`。

### R2-ROLLBACK-004: 重启后端以加载回滚后的代码（回滚 R2-DEPLOY-004）

- 类型：正式回滚（无状态步骤，须在 R2-ROLLBACK-002 之后执行）
- 命令：`$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend; sudo journalctl -u ocap-backend -n 30 --no-pager'`
- 变量与核验：无变量
- 预期：`active`，日志无 Traceback

### R2-ROLLBACK-003: 恢复前端静态（回滚 R2-DEPLOY-003）

- 类型：正式回滚
- 命令：
```bash
$OCAP_SSH "sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html"
```
- 变量与核验：`TS` 见回滚前核验；快照内含 `web/ocap/`，只动 `web/`
- 预期：旧 `index.html` 恢复，其资源哈希与 R2-PRE-012 记录一致

### R2-ROLLBACK-002: 恢复后端代码（回滚 R2-DEPLOY-002）

- 类型：正式回滚（叠加解包；不删除目录，保护 `venv/`、`.env`、`var/`）
- 命令：
```bash
$OCAP_SSH "tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap && test -f /home/yangyang/ocap/backend/.env && echo ENV_KEPT"
# 清理 R2 新增、旧版本中不存在的 3 个测试文件（运行期不引用，删除仅为恢复一致）
$OCAP_SSH 'cd /home/yangyang/ocap/backend && rm -f tests/e2e/test_registry_import_scale_journeys.py tests/integration/test_registry_import_xlsx_defects.py tests/unit/test_registry_import_defects.py'
```
- 变量与核验：`TS` 见核验块；恢复后核对 `ls -l --time-style=long-iso apps/registry/importing.py` 的时间与 R2-PRE-012 记录一致（确认文件确实变化回旧版）
- 预期：`ENV_KEPT`；随后执行 R2-ROLLBACK-004
- 说明：快照不含 `venv/`、`var/`、`.env`，三者 R2 未改动，回滚也不触碰

### R2-ROLLBACK-001: 快照保留（回滚 R2-DEPLOY-001）

- 类型：无操作；快照保留 ≥ 7 天，清理需用户确认

## R2-7 不可逆步骤汇总

本次 R2 **无不可逆步骤**，无 `[MANUAL_ROLLBACK_REQUIRED]`：无迁移、无数据备份/恢复、无外部系统调用、无 nginx/systemd 改动。备注：部署后由用户执行的 M-04~M-06 正式导入会写入业务库（清册数据），属于验收性使用，**不由部署回滚撤销**；若需清理由用户另行决定（建议使用可识别的测试数据或接受数据入库）。

## R2-8 部署后验证

沿用 V-01~V-07，V-03 改写，V-08 新增，V-09 以后原条目（引擎级抽样 V-09、V-10 Freeark、V-11 静态）仍沿用；R2 不重复 V-08（旧版「xlsx 模板可用」）与 V-09（引擎级 20000 行），以新的 V-08 与人工项 M-04~M-06 代替。远端含 `$TS` 的命令用双引号。

| ID | 检查项 | 命令 / URL | 成功标准 |
|---|---|---|---|
| V-01 | 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| V-02 | 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 Traceback / OperationalError |
| V-03（改） | 迁移状态 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations registry; venv/bin/python manage.py showmigrations --plan \| grep -c "^\[ \]"'` | registry 0001~0004 全部 `[X]`；未应用条数 `0` |
| V-04 | 内网前端 | `curl -s -o /dev/null -w '%{http_code}' http://192.168.31.51:8090/ocap/`（由目标机本地执行：`$OCAP_SSH 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/ocap/'`；云主机不在内网，无法直连 192.168.31.51） | 200 |
| V-05 | 外网前端 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | 200 |
| V-06 | SPA 回退 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/admin/login` | 200 |
| V-07 | 导入 spec 路由生效且需认证 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/api/v1/admin/registry/import/spec` | 401 或 403，非 404/5xx |
| V-08（新） | 下载 xlsx 模板接口需认证 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/api/v1/admin/registry/import/template` | 401 或 403（未认证不得返回 200 文件），非 404/5xx |
| V-10 | Freeark 未受影响 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/`；`$OCAP_SSH 'systemctl --state=failed --no-pager'` | 200；无 `freeark-*`、`ocap-*` failed |
| V-11 | 新静态资源 | 取 `index.html` 引用的 `/ocap/assets/<hash>.js` 请求 `https://ai-freeark.xin/ocap/assets/<hash>.js` | 200，且 hash 与 R2-PRE-012 的旧哈希不同（证明已换新包） |
| V-12 | 代码版本已生效（只读） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && grep -c "number_format" apps/registry/import_template.py'`（DEF-007 特征） | 计数 ≥ 1（567b137 版本中为 0，已用 `git show 567b137:backend/apps/registry/import_template.py` 核实，可区分新旧） |

> 有认证的接口行为（模板文本格式、合并单元格、dry_run 等）已由自动化用例在开发环境覆盖；部署后不使用真实管理员口令发起写入请求，由人工项承担。

### 人工验证项 M-04~M-06（用户在页面执行，PM 只读记录）

来源：e2e_test_report 2.0.0 人工清单 M-04~M-06；GR-C-002-F03（xlsx 普通模式读取的内存峰值）与 GR-D-002 条件。执行方：用户在 `https://ai-freeark.xin/ocap/admin` 登录后，于「业主清册」页面使用 20000 行 xlsx（≤ 5 MB）：

| ID | 操作 | 期望（引 e2e_test_report） |
|---|---|---|
| M-04 | 20000 行合法 xlsx 正式导入 | 20000 行全部处理，合计 20000，≤ 60 秒返回 |
| M-05 | 同一文件点击预检并观察「处理中」状态 | 60 秒内显示预检结果，清册无变化 |
| M-06 | 含约 2000 行非法的 20000 行 xlsx 正式导入 | 60 秒内显示结果，合计 20000、失败约 2000，可下载错误清单，「处理中」消失 |

PM 只读记录（不写业务库、不触发导入）：用户开始每次操作前 PM 在远端启动采样，操作结束后读取结果。

```bash
# 采样前基线
$OCAP_SSH 'systemctl show ocap-backend -p MemoryCurrent -p MemoryPeak -p MemoryMax; free -m; ps -eo pid,rss,cmd --sort=-rss | grep "[g]unicorn" | head -6'
# 导入期间每 2 秒采样 gunicorn 各 worker RSS 之和（KB），最长 90 秒，输出峰值
$OCAP_SSH 'peak=0; for i in $(seq 1 45); do s=$(ps -eo rss,cmd | grep "[g]unicorn" | awk "{t+=\$1} END{print t+0}"); [ "$s" -gt "$peak" ] && peak=$s; sleep 2; done; echo PEAK_RSS_KB=$peak'
# 采样后
$OCAP_SSH 'systemctl show ocap-backend -p MemoryCurrent -p MemoryPeak; free -m; sudo journalctl -u ocap-backend --since "-10 min" --no-pager | grep -Ei "Traceback|WORKER TIMEOUT|killed|oom" | tail -5'
```

记录项：每次操作的接口耗时（由用户读页面或浏览器开发者工具 Network）、`PEAK_RSS_KB`、`MemoryCurrent` / `MemoryPeak`（若输出 `[not set]` 或 `infinity`，说明 cgroup 内存统计未开启，以 `ps` RSS 与 `free -m` 为准并在报告注明）、journal 中是否出现 `WORKER TIMEOUT` / OOM。通过判据 `[INFERRED]`：任意操作 ≤ 60 秒；样本期间 `free -m` 的 available 不低于 100 MB 且无 OOM kill；超出则记 `DEPLOYED_WITH_ISSUES`，由用户决定是否回滚。M-04~M-06 结论回填 e2e_test_report 的人工清单（由 test-engineer/PM 按流程更新，本计划不改测试文档）。

## R2-9 执行顺序摘要

R2-PRE-001~012 → R2-DEPLOY-001（快照）→ 002（后端）→ 003（前端）→ 004（重启）→ V-01~V-12 → 人工 M-04~M-06。预计自动化部分耗时 5~10 分钟（含前端构建）`[INFERRED]`。

## R2-10 自检与开放项

- R2-DEPLOY-001~004 各有 R2-ROLLBACK，逆序为 004→003→002→001；无不可逆步骤。
- 变量 `TS`、`REL` 的取值方式与核验均已写出；远端命令含本地变量处使用双引号。
- 未使用 Docker、pscp、git reset/clean/stash、目标机生成迁移；不触碰 Freeark；不 cat `.env`。
- `[INFERRED]` 汇总：停机时长 5~15 秒；backend 快照 MB 级；自动化部分耗时；M-04~M-06 内存与可用内存判据（100 MB）。
- 注意：`git archive $REL:backend` 要求本地对象库含 a0a0b3a（R2-PRE-001 已核验）；上次 1.0.0 的 `/tmp/ocap_backend_<TS>.tar.gz` 目标机残留文件不影响（TS 不同）。
