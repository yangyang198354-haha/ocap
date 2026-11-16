<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-16T12:55:00+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/cicd_pipeline.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/test_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：选房排序统一、地下车位归属修正与后台清册过滤器

> 本计划只描述步骤，不构成任何授权。子代理不得 ssh（画像 P9）；所有远端命令由 GROUP_E2（用户当轮授权后）或主会话执行，每条 ssh/scp 仍经 `.claude/settings.json` 的 ask 规则确认。凭据只写位置不写值。

## 授权点总表（五个阶段各自独立授权）

每个阶段都需要**用户当轮**明确授权；PM 在该阶段 invocation 的 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true`、目标环境名「测试」、阶段名与所需输入。上一阶段的授权**不延续**到下一阶段；每阶段结束后 PM 向用户汇报结果，得到用户新一轮授权才进入下一阶段。顺序固定 A → B → C → D → E（先改库再导出，避免 AC-187-05 并存问题）。

| 阶段 | 内容 | 步骤 | 是否写目标机状态 | 用户当轮需授权的点 | 执行人 |
|---|---|---|---|---|---|
| A 代码部署 | 快照、后端上传解包、重启、前端替换、只读冒烟 | DEPLOY-001~004 | 是（代码） | 授权把本地提交 15ea79e（未推送，以本地提交打包）部署到测试环境 | E2 |
| B dry-run | relocate_underground_parking 默认模式 | DEPLOY-005 | 否（只读，零写） | 授权在测试机对 ocap 库执行只读 dry-run | E2 或主会话 |
| C 库内修正（AUTH-02） | mysqldump 备份 + `--apply --backup --expect-changes N` | DEPLOY-006、007 | **是（改库）** | 用户看过 B 的结果后，给出确认的 N 值并授权 apply | E2 或主会话 |
| D 导出（AUTH-01） | 只读导出到目标机 0600 临时路径 → scp 取回 → 删除临时文件 | DEPLOY-008~010 | 否（仅临时文件） | 授权导出含个人信息的文件到仓库根（已 gitignore，不提交）；若需 `--allow-gaps` 须另行同意 | 主会话（取回含个人信息的文件） |
| E 部署后验证 | 只读冒烟、MV-04/05 人工清单、P4-1 远程 HTTP E2E | DEPLOY-011~013 + 验证表 | 是（仅 `e2e_` 数据） | 授权创建/清理 `e2e_` 夹具并运行远程套件 | E2（夹具/清理）+ 主会话（HTTP 测试） |

## 变更摘要

版本标识：部署提交 = 本地 `main` 的 `15ea79ea51c87d56cd1cd8113cba81007649575a`（共 40 文件，**尚未推送**；推送需用户另行同意，P9）。工作树另有与本批无关的未提交改动（`project_workspace/**` 文档、`_kb_inbox.jsonl`），不属于部署内容。

**打包来源（强制）**：后端用 `git archive` 取**提交 15ea79e 的 `backend/` 树**（只含已提交跟踪文件，M-DE-012，不受工作树杂项影响）；前端在工作树构建，预检要求 `frontend/` 相对 15ea79e 无差异且无未跟踪文件。不得从未提交工作树打包后端。

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 选房排序（MOD-104/105） | `backend/apps/registry/ordering.py`（新）、`registry/services.py` | 无 | 无 | `ocap-backend` 重启 |
| 房屋列表排序（MOD-106） | `backend/apps/identity/services.py`、`residency/housing.py` | 无 | 无 | 同上 |
| 清册过滤接口（MOD-107） | `registry/views.py`、`registry/urls.py`（新路由 `admin/registry/units/filter-options`） | 无 | 无 | 同上 |
| 后台清册页（MOD-108） | `frontend/src/admin/AdminRegistry.vue`、`frontend/src/shared/api.js` | — | `npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 静态目录 `/home/yangyang/ocap/web/ocap` 替换，nginx 不动 |
| 地下车位修正命令（MOD-109，AUTH-02） | `registry/underground.py`、`management/commands/relocate_underground_parking.py`（新） | 无（**刻意不做迁移**，ADR-101） | 无 | 无（一次性命令，随代码到达，**不自动执行**） |
| 导出命令（MOD-110，AUTH-01） | `registry/exporting.py`、`management/commands/export_registry_import_file.py`（新）、`registry/import_template.py` | 无 | 无 | 无（同上） |
| 小程序 | 无源码改动 | — | 不需重新发布（服务端排序，RU-4 不纳入） | 无 |
| 新依赖 | 无（`requirements.txt` 未变） | — | **跳过 pip install**（预检用 diff 证明 requirements 未变） | — |

数据迁移：无；预检仍核对目标机无未应用迁移。

## 目标环境与策略

- 环境：测试（画像 P7，树莓派；外网 SSH `-p 57279 yangyang@47.109.197.217`，首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报；内网 `192.168.31.51:22`）。画像中不存在其他环境，不设计晋升。
- 策略：**recreate**（单实例 gunicorn，无冗余，画像允许）。理由：无多实例/两套环境；后端重启约 2~5 秒不可用，前端为静态目录替换。
- 预计停机：阶段 A 约 2~5 秒（后端重启）；阶段 B/D 无停机；阶段 C 为单个事务内更新，数秒内完成 [INFERRED，随 `would_change` 数而定]；阶段 E 无停机。

### SSH 通道与本地变量（所有阶段通用；M-DE-009/010）

```bash
# 套接字目录必须短路径（M-DE-010），不要放进长的会话临时目录
CM=$(mktemp -d /tmp/ocs.XXXX)
SCRATCH=$(mktemp -d /tmp/ocpkg.XXXX)        # 本地打包临时目录；先 echo "$SCRATCH" 确认非空，再使用
OCAP_SSH="ssh -p 57279 -o ControlMaster=auto -o ControlPath=$CM/%C -o ControlPersist=10m yangyang@47.109.197.217"   # 内网改 -p 22 yangyang@192.168.31.51
OCAP_SCP="scp -P 57279 -o ControlPath=$CM/%C"
OCAP_DEST="yangyang@47.109.197.217"
[ -n "$SCRATCH" ] && [ -d "$SCRATCH" ] || echo "变量为空，停止"
```
- 只对「建连」失败重试（至多 3 次）；已开始的非幂等命令（apply、tar 覆盖、rm）失败时先只读核对状态，不盲目重试。
- 多行远端脚本一律 `$OCAP_SSH bash -s -- "$TS" <<'EOF' … EOF`：脚本内用 `$1` 取本地值；`'EOF'` 防止本地展开，远端自己的 `$VAR` 在远端展开。单行远端命令要用本地值时用双引号，执行前先 `echo` 完整命令核对。`$OCAP_SSH` 不加引号使用。
- 跨阶段携带的值（`TS`、`TS2`、`TS3`、备份路径、N）由 PM 写进下一阶段的 `special_instructions`，不依赖 shell 状态。

## 预检清单

### 阶段 A 预检（开发机 + 目标机，均只读）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-A01 待部署提交与版本标识 | 开发机：`git cat-file -t 15ea79ea51c87d56cd1cd8113cba81007649575a`；`git merge-base --is-ancestor 15ea79e HEAD && echo ANCESTOR_OK`；`git ls-remote origin main`（仅记录） | 类型 `commit`；`ANCESTOR_OK`；**未推送不是阻断项**（用户未授权 push；部署后建议用户推送，ocap-deploy §0） |
| PRE-A02 前端与提交一致 | `git diff --quiet 15ea79e -- frontend && echo SAME`；`git status --short -- frontend backend miniprogram deploy` | `SAME`；后者无未跟踪/未提交行（有则停止，交用户处理） |
| PRE-A03 迁移无漂移（M-DE-002） | `cd backend && <Django 5.2 venv>/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings` | 退出码 0（No changes detected）；不用 Django 6.x |
| PRE-A04 requirements 未变 | `git diff --quiet 3ffd868 15ea79e -- backend/requirements.txt && echo REQ_SAME`（基线取 ocap_product_review 最近一次部署的提交，以其部署报告记录为准，`3ffd868` 为 [INFERRED]） | `REQ_SAME`；否则停止，计划需补 pip 步骤 |
| PRE-A05 目标机可达与指纹 | `$OCAP_SSH 'echo OK'` | `OK`；指纹与 P7 一致 |
| PRE-A06 磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | /home 可用 ≥ 2 GB；可用内存 ≥ 500 MB |
| PRE-A07 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| PRE-A08 目标机目录与本地状态 | `$OCAP_SSH 'ls -la /home/yangyang/ocap; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -d /home/yangyang/ocap/backend/venv && echo VENV_OK; test -d /home/yangyang/ocap/backend/var && echo VAR_OK'` | 仅 `backend/ web/ snapshots/`；三个 OK（`.env`、`venv`、`var` 为必须保留的本地状态，本计划只覆盖源码文件，不触碰它们） |
| PRE-A09 `.env` 关键键 | `$OCAP_SSH 'grep -Eq "^DJANGO_SECRET_KEY=.+" /home/yangyang/ocap/backend/.env && echo SECRET_KEY_SET'` | `SECRET_KEY_SET`（不 cat） |
| PRE-A10 无未应用迁移 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan > /tmp/mig_before.txt; grep -c "^\[ \]" /tmp/mig_before.txt'` | 输出 `0` |
| PRE-A11 web/ocap 属主（M-DE-013） | `$OCAP_SSH 'stat -c "%U %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html'` | 记录属主（可能为 root，则前端替换须用 sudo）；先核实再动手，避免半删除状态 |
| PRE-A12 nginx 与 Freeark 基线 | `$OCAP_SSH 'sudo nginx -t; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'` | `syntax is ok`；`200` |
| PRE-A13 当前版本记录（回滚锚点补充，M-DE-006） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && sha256sum apps/registry/services.py apps/registry/views.py apps/registry/urls.py apps/identity/services.py apps/residency/housing.py apps/registry/import_template.py; ls apps/registry/ordering.py apps/registry/underground.py apps/registry/exporting.py 2>&1'` | 记录哈希；三个新文件应报 `No such file`（证明为本批新增，ROLLBACK-002 可安全删除） |
| PRE-A14 e2e_fixture 命令存在（供阶段 E） | `$OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/jobs/e2e_fixture.py'` | 存在（来自 ocap_product_review 部署）；不存在则回报 PM [INFERRED] |

### 阶段 B/C/D 预检（目标机，只读；在对应阶段开始时执行）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-B01 阶段 A 已完成 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && ls apps/registry/underground.py apps/registry/exporting.py && systemctl is-active ocap-backend'` | 文件存在；`active` |
| PRE-B02 命令可加载 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --help >/dev/null && venv/bin/python manage.py export_registry_import_file --help >/dev/null && echo CMD_OK'` | `CMD_OK` |
| PRE-C01 mysqldump 可用 | `$OCAP_SSH 'command -v mysqldump'` | 有路径输出；无则 BLOCKED，请用户选择替代（如 `manage.py dumpdata` 写 0600 文件，须用户同意）[INFERRED] |
| PRE-C02 表名核对 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.models import RegistryUnit,RegistryOwner,RegistryPhone as P;from apps.residency.models import Membership as M;print(RegistryUnit._meta.db_table,RegistryOwner._meta.db_table,P._meta.db_table,M._meta.db_table)"'` | 打印四个真实表名（预期 `registry_registryunit` 等，模型无自定义 db_table [INFERRED]）；以此输出填入 DEPLOY-006 |
| PRE-C03 备份目录空间与路径不存在 | `$OCAP_SSH 'df -h /home/yangyang/ocap/snapshots; ls /home/yangyang/ocap/snapshots/ \| tail -5'` | 可用 ≥ 500 MB；本次将用的 `underground-$TS2.jsonl` 不存在（命令对已存在路径退出码 3） |
| PRE-C04 dry-run 结果已获用户确认 | PM 在 invocation 提供 N 与确认 | N 等于最近一次 dry-run 的 `would_change`，且 `conflicts=0`；用户已看过楼层写法清单 |
| PRE-D01 gaps | 阶段 B/C 结果 | 无 gaps；若有，命令默认退出码 2 不落盘，须用户另行同意 `--allow-gaps` |
| PRE-D02 本地落点安全（主会话） | 仓库根：`git check-ignore -v registry_import_underground_parking.xlsx`；`ls registry_import_underground_parking.* 2>&1` | 命中 `.gitignore`；目标文件不存在（存在则请用户决定，不静默覆盖） |

## 部署步骤

### 阶段 A：代码部署（授权点 A）

#### DEPLOY-001: 生成回滚锚点并快照
- 组件：后端目录、Web 静态目录、nginx 配置（本批不改 nginx，仍备份）；ROLLBACK-002/004 的锚点
- 位置：目标机；`TS` 在本地取得一次，之后所有步骤复用（M-DE-003）
- 命令：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
mkdir -p $A/snapshots
sudo tar czf $A/snapshots/backend-$TS.tar.gz -C $A backend
sudo tar czf $A/snapshots/web-$TS.tar.gz -C $A web
sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS
sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS
ls -l $A/snapshots/*-$TS.tar.gz /etc/nginx/sites-available/*.bak_$TS
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz
EOF
```
- 预期：输出 `ANCHOR_TS`，2 份 tar（非零大小）+ 2 份 nginx 备份 + 2 个 SHA256，记入报告。快照保留 ≥ 7 天。失败且目标机无变更 → DEPLOYMENT_FAILED，无需回滚。
- 回滚: ROLLBACK-001

#### DEPLOY-002: 打包提交 15ea79e 的后端、上传并解包
- 组件：Django 后端 MOD-104~110（`ocap-backend`）
- 位置：开发机 → 目标机
- 命令：
```bash
C=15ea79ea51c87d56cd1cd8113cba81007649575a
echo "$SCRATCH"                                                  # 必须非空
git archive --format=tar.gz -o "$SCRATCH/ocap_backend_$C.tar.gz" "$C:backend"
sha256sum "$SCRATCH/ocap_backend_$C.tar.gz"
$OCAP_SCP "$SCRATCH/ocap_backend_$C.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/ocap_backend_$C.tar.gz"                # 与本地一致方可继续
$OCAP_SSH "tar xzf /tmp/ocap_backend_$C.tar.gz -C /home/yangyang/ocap/backend"
```
- 预期：两端 SHA256 一致；解包无错误；仅覆盖/新增源码，`.env`、`venv/`、`var/` 未被触碰（`git archive` 不含它们）；解包不会删除旧文件（本批无文件删除，核对：`git show --diff-filter=D --name-only --format= 15ea79e -- backend` 应为空）。验证：
  `$OCAP_SSH 'cd /home/yangyang/ocap/backend && ls apps/registry/ordering.py apps/registry/underground.py apps/registry/exporting.py apps/registry/management/commands/relocate_underground_parking.py apps/registry/management/commands/export_registry_import_file.py && grep -c "filter-options" apps/registry/urls.py && test -f .env && test -d venv && echo LOCAL_STATE_INTACT'`
- 回滚: ROLLBACK-002

#### DEPLOY-003: 重启后端服务
- 组件：systemd `ocap-backend`
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'
$OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
```
- 预期：`active`；日志无 `Traceback`/`ERROR`。**不 `migrate`（本批无迁移）、不 pip install（requirements 未变）**。不触碰任何 `freeark-*` 服务。
- 回滚: ROLLBACK-003

#### DEPLOY-004: 构建并替换 Web 前端
- 组件：Vue SPA（MOD-108，`AdminRegistry.vue`、`api.js`）
- 位置：开发机构建；目标机替换
- 命令：
```bash
# 开发机仓库根（已通过 PRE-A02）
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
tar -czf "$SCRATCH/frontend_dist.tar.gz" -C frontend/dist . && sha256sum "$SCRATCH/frontend_dist.tar.gz"
$OCAP_SCP "$SCRATCH/frontend_dist.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/frontend_dist.tar.gz"
# web/ocap 属主若为 root（PRE-A11）须 sudo；只替换 web/ocap 内容
$OCAP_SSH 'sudo rm -rf /home/yangyang/ocap/web/ocap/* && sudo tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html'
```
- 预期：两端 SHA256 一致；`index.html` 存在，资源路径以 `/ocap/assets/` 开头。
- 回滚: ROLLBACK-004

### 阶段 B：relocate_underground_parking dry-run（授权点 B，只读）

#### DEPLOY-005: 地下车位修正命令 dry-run
- 组件：MOD-109 / AUTH-02 的预演模式（无 `--apply` 即只读，`CaptureQueriesContext` 测试证明零写）
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --list-limit 200; echo "EXIT=$?"'
```
- 预期输出（不含姓名、手机号）：`total_units`、`candidates`、`already_target`、`would_change`、`conflicts`、`old_building|…`、`floor|<写法>|<数>|recognized/unrecognized` 清单、`negative_floor_non_parking`、`other_building_negative_parking`、`conflict|…`、`move|id|旧标识|新标识`；退出码 0。
- **汇报给用户的内容与停止条件（GR-D-001-F02、OQ-02）**：
  1. `would_change` 与 `move` 明细（核对均为 1 栋下负层车位）；
  2. 楼层写法清单：**若负层写成 `-1`/`-2`（含 `-`），导出自检会拒绝落盘（TC-INT-620），须先汇报用户并由用户决定处理方式，不自行继续**；
  3. 出现 `unrecognized` 写法（如 `B1`）→ 会漏改，汇报并请用户决定；
  4. `conflicts>0`（标识或四元组冲突）→ 停止，不得进入阶段 C；
  5. `negative_floor_non_parking` 或 `other_building_negative_parking` 非 0 → 汇报，由用户确认其不属于修正范围。
- 回滚: ROLLBACK-005（无操作，只读）；执行前后命令自身输出的 `total_units` 应相同。

### 阶段 C：库内地下车位归属修正（授权点 C，**改库**）

#### DEPLOY-006: 备份 ocap 库相关表（mysqldump 级，apply 之前）
- 组件：数据层保护；只备份 `ocap` 库涉及的表，**不碰 Freeark 库**；凭据从目标机 `backend/.env`（DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME）读取，不写值；口令经 `MYSQL_PWD` 环境变量传给 mysqldump，不进 argv/ps
- 位置：目标机；`TS2` 本地取一次
- 命令：
```bash
TS2=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "DATA_TS=$TS2"
$OCAP_SSH bash -s -- "$TS2" <<'EOF'
set -e
TS2="$1"; A=/home/yangyang/ocap
umask 077
cd $A/backend && set -a && . ./.env && set +a
[ "$DB_NAME" = "ocap" ] || { echo "DB_NAME 不是 ocap，停止"; exit 9; }
export MYSQL_PWD="$DB_PASSWORD"
# 表名以 PRE-C02 输出为准；下列为预期值 [INFERRED]
mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl --single-transaction --no-tablespaces \
  "$DB_NAME" registry_registryunit registry_registryowner registry_registryphone residency_membership \
  > $A/snapshots/ocapdb-registry-$TS2.sql
unset MYSQL_PWD
chmod 600 $A/snapshots/ocapdb-registry-$TS2.sql
ls -l $A/snapshots/ocapdb-registry-$TS2.sql
grep -c '^INSERT INTO' $A/snapshots/ocapdb-registry-$TS2.sql
tail -n 2 $A/snapshots/ocapdb-registry-$TS2.sql
sha256sum $A/snapshots/ocapdb-registry-$TS2.sql
EOF
```
- 预期：非零大小、权限 0600、末尾为 `-- Dump completed`、每表有 INSERT、SHA256 已记录。`--skip-ssl`（M-DE-008：测试 MySQL 自签证书）。失败 → 不进入 DEPLOY-007，DEPLOYMENT_FAILED（库未变）。该文件含业主姓名/手机号，仅留目标机 0600，不传出、不入库；保留期由用户决定。
- 回滚: ROLLBACK-006（无操作；备份保留）

#### DEPLOY-007: relocate_underground_parking --apply
- 组件：MOD-109（事务内更新、同事务写审计、提交前核对计数/绑定/未受影响记录指纹）
- 位置：目标机
- 前置：DEPLOY-005 刚执行过且 `conflicts=0`；`N` = 用户确认的 `would_change`；`BK` 路径不存在
- 命令：
```bash
BK=/home/yangyang/ocap/snapshots/underground-$TS2.jsonl
# 独立计数（只读，前后各一次，把 BEFORE 改 AFTER 再跑）
CNT='cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.models import RegistryUnit as U,RegistryOwner as O,RegistryPhone as P;print(\"units\",U.objects.count(),\"owners\",O.objects.count(),\"phones\",P.objects.count(),\"underground\",U.objects.filter(building=\"地下车位\").count())"'
$OCAP_SSH "$CNT"
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --apply --backup $BK --expect-changes $N --list-limit 200; echo EXIT=\$?"
echo "$CMD"                                  # 核对 BK 与 N 已展开、EXIT 的 $ 已转义
$OCAP_SSH "$CMD"
$OCAP_SSH "$CNT"
$OCAP_SSH "stat -c '%a %s %n' $BK"           # 权限应为 600
```
- 预期：退出码 0；命令输出的 `before_*`/`after_*`（units、owners、phones、active_memberships）逐项相等，`differences=0`；独立计数前后 units/owners/phones 相等，`underground` 后 = 前 + N；备份存在、权限 600。其后再执行一次 DEPLOY-005 dry-run，期望 `would_change=0`（幂等）。
- 退出码：1 参数错误；2 冲突/`--expect-changes` 不符/核对失败（事务已回滚，库保持修正前，上报，无需回滚）；3 备份文件问题（库未触碰）。
- **[MANUAL_ROLLBACK_REQUIRED: 回滚 = `--restore` 按备份写回原值（含 updated_at），属第二次改库，须用户决定；apply 之后产生的新认证/绑定按 unit_id 不受影响，其展示会回到旧楼栋名；整库级兜底为 DEPLOY-006 的 mysqldump，属覆盖式恢复，会丢弃备份之后所有写入，仅由人评估后执行]**
- 回滚: ROLLBACK-007

### 阶段 D：导出导入文件（授权点 D，只读导出，含个人信息）

#### DEPLOY-008: export_registry_import_file 只读导出到目标机 0600 临时路径
- 组件：MOD-110 / AUTH-01（命令全程只读：不 save/update/delete、不写审计；stdout 不含姓名、手机号）
- 位置：目标机；`TS3` 本地取一次；`X=/home/yangyang/ocap/snapshots/export_$TS3.xlsx`
- 命令：
```bash
TS3=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); X=/home/yangyang/ocap/snapshots/export_$TS3.xlsx
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && umask 077 && venv/bin/python manage.py export_registry_import_file --output $X; echo EXIT=\$?; stat -c '%a %s %n' $X; sha256sum $X"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：退出码 0；`diff_*=0`、`precheck_rows_failed=0`、`gaps_units=0`、`gaps_unnamed_owners=0`；因阶段 C 已执行，`relocated_units=0`、`precheck_would_create_*` 均为 0（AC-187-05）；文件权限 `600`，SHA256 记录。退出码 2（gaps/冲突/自检失败，未落盘）→ 汇报用户，**不自行加 `--allow-gaps`**；退出码 3（目标已存在）→ 先只读核对，再换 `TS3` 重试。
- 回滚: ROLLBACK-008

#### DEPLOY-009: 主会话 scp 取回到仓库根（不提交）
- 位置：开发机（主会话）
- 命令：
```bash
# 仓库根；先核对 PRE-D02
umask 077
$OCAP_SCP "$OCAP_DEST:$X" ./registry_import_underground_parking.xlsx
sha256sum ./registry_import_underground_parking.xlsx           # 与 DEPLOY-008 的 SHA256 一致
chmod 600 ./registry_import_underground_parking.xlsx
git check-ignore -v registry_import_underground_parking.xlsx    # 命中 .gitignore
git status --short | grep registry_import_underground_parking || echo NOT_TRACKED_OK
```
- 预期：SHA256 两端一致；被 `.gitignore` 忽略；**不 `git add`、不提交、不推送、不上传到其他位置**（文件含业主姓名与手机号，仓库为 PUBLIC；用户 2026-11-16 决定不入库）。
- 回滚: ROLLBACK-009

#### DEPLOY-010: 删除目标机临时导出文件
- 位置：目标机
- 命令：`CMD="rm -f $X; ls $X 2>&1"; echo "$CMD"; $OCAP_SSH "$CMD"`（执行前核对路径含 `export_$TS3.xlsx` 且仅此一个文件）
- 预期：`No such file or directory`。**DEPLOY-009 的本地 SHA256 核对通过之前不得执行。**
- 回滚: ROLLBACK-010

### 阶段 E：部署后验证与远程 E2E（授权点 E）

只读冒烟与 MV 清单不写目标机状态，随授权点 A 执行（见「部署后验证」）；下面三步写入 `e2e_` 数据，须阶段 E 单独授权。远程用例按画像 P4-1：只经 `https://ai-freeark.xin/ocap/`，只用 `e2e_` 账号，不修改非 `e2e_` 数据与清册。阶段 C 之后地下车位记录已改楼栋，夹具选「空闲」房屋，setup 前先只读列出将占用的房屋 id 供用户确认（P-DE-002）。

#### DEPLOY-011: 夹具 setup（目标机创建 `e2e_` 账号）
- 命令（口令经 stdin 传远端，不进 argv）：
```bash
OCAP_E2E_PASSWORD=$(python3 -c 'import secrets;print("E2e"+secrets.token_hex(10)+"x9")')   # 本地生成，不写文件、不输出
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.jobs.e2e_fixture import _free_units; print([(u.id, u.specific_part) for u in _free_units(3, set())])"'   # 只读，请用户确认
printf '%s' "$OCAP_E2E_PASSWORD" | $OCAP_SSH 'IFS= read -r OCAP_E2E_PASSWORD; export OCAP_E2E_PASSWORD; cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'
```
- 预期：退出 0；status 显示 e2e 账号与基线 `registry_counts`（记为 `REGISTRY_BASE`，须与阶段 C 之后的清册计数一致）。
- 回滚: ROLLBACK-011

#### DEPLOY-012: 运行远程 HTTP E2E
- 位置：主会话（HTTP，不经 SSH，不直连库）
- 命令：
```bash
OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD="$OCAP_E2E_PASSWORD" \
  python3 backend/tests/remote/run_remote.py -v 2>&1 | tee "$SCRATCH/e2e_remote_$TS.log"; echo "RUN_EXIT=${PIPESTATUS[0]}"
```
  （慢网络加 `OCAP_E2E_SLOW=1`；不设置 `OCAP_E2E_ALLOW_LOCAL`；请求用超时参数，不用 `pkill -f` 杀后台进程，P-DE-004。）
- 预期：本批相关行为（选房排序、/me 与 /me/housing 顺序一致）通过。**既有问题单列**：ocap_product_review 的 DEF-B（远程用例期望文案过期）可能仍失败，在报告中标「既有」，不计入本批判定；子代理无测试代码写权限，不修改用例。失败项逐条记录用例号与响应摘要，不含口令。
- 回滚: ROLLBACK-012

#### DEPLOY-013: 夹具 cleanup（测完必做，DEPLOY-012 失败也要做）
- 命令：
```bash
F="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture"
echo "$F"                                   # 核对含 OCAP_E2E_FIXTURE=1
$OCAP_SSH "$F cleanup"                       # 默认 dry-run：核对 would_delete 仅为 e2e_ 数据
$OCAP_SSH "$F cleanup --execute"
$OCAP_SSH "$F status"
```
- 预期：`--execute` 退出 0；status 的 e2e 计数为 0；`registry_counts` 与 `REGISTRY_BASE` 逐项相同。不一致或出现非 `e2e_` 数据变化 → 立即停止上报，**不得自行修复清册**。
- 回滚: ROLLBACK-013

## 回滚步骤（逆序）

**执行前核验变量（所有回滚通用）**：
```bash
TS=<DEPLOY-001 的 ANCHOR_TS>; TS2=<DEPLOY-006 的 DATA_TS>
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo "$TS2" | grep -Eq '^[0-9]{14}$' || echo "变量非法，停止"
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/underground-$TS2.jsonl"
```
文件须全部存在才继续（若只回滚阶段 A，则不要求 `underground-$TS2.jsonl`）。远端命令一律双引号使 `$TS` 在本地展开，执行前 `echo` 完整命令核对。**禁止** `git reset --hard`、`git clean`、`git stash`、覆盖式 rsync（`.env`/`venv`/`var` 是目标机本地状态）。

**数据与代码的回滚顺序（关键）**：先还原数据（ROLLBACK-007，`--restore` 依赖本批新代码），再回滚代码（ROLLBACK-002/003）。旧代码可正常读取已修正的楼栋值，因此**默认只回滚代码、保留库内修正**，除非用户明确要求还原数据（M-DE-005 同理）。

### ROLLBACK-013: 回滚 DEPLOY-013
- 类型：无操作。`e2e_` 数据被清理是预期终态，不恢复。

### ROLLBACK-012: 回滚 DEPLOY-012
- 类型：无操作（写入由 DEPLOY-013 清理）。若中途中断：直接执行 DEPLOY-013。

### ROLLBACK-011: 回滚 DEPLOY-011
- 类型：正式回滚
- 命令：执行 DEPLOY-013（先 dry-run 再 `--execute`）。
- 变量取值与核验：`F` 为本地拼接的完整远端命令，echo 核对含 `OCAP_E2E_FIXTURE=1`；cleanup 不需要口令。

### ROLLBACK-010: 回滚 DEPLOY-010
- 类型：无法回滚的设计性删除（一次性临时文件）。需要时重新执行 DEPLOY-008~010；本地已取回的文件不受影响。

### ROLLBACK-009: 回滚 DEPLOY-009
- 类型：正式回滚（本地文件）
- 命令：`rm -f ./registry_import_underground_parking.xlsx`（仓库根，相对路径固定；仅在用户要求撤销或校验失败时），随后 `ls registry_import_underground_parking.* 2>&1` 核对。

### ROLLBACK-008: 回滚 DEPLOY-008
- 类型：正式回滚（临时文件）
- 命令：`CMD="rm -f /home/yangyang/ocap/snapshots/export_$TS3.xlsx; ls /home/yangyang/ocap/snapshots/export_$TS3.xlsx 2>&1"; echo "$CMD"; $OCAP_SSH "$CMD"`
- 变量取值与核验：`TS3` 取自 DEPLOY-008，必须为 14 位数字，echo 核对路径后执行。命令只读，无其他状态。

### ROLLBACK-007: 回滚 DEPLOY-007（还原地下车位归属）
- 类型：正式回滚（二次改库，须用户决定）
- **[MANUAL_ROLLBACK_REQUIRED: 还原即改库，需用户明确同意。数据风险：被改记录的全部列写回修正前原值；apply 之后依赖新楼栋名的展示会回到旧楼栋名；apply 之后其他表的变化不被撤销]**
- 命令（先还原 dry-run，再 apply）：
```bash
BK=/home/yangyang/ocap/snapshots/underground-$TS2.jsonl
$OCAP_SSH "cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --restore $BK; echo EXIT=\$?"          # 只读，待还原条数应等于当时的 N
$OCAP_SSH "cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --restore $BK --apply; echo EXIT=\$?"
```
- 变量取值与核验：`TS2` 取自 DEPLOY-006 输出；`stat -c %a $BK` 为 600；命令先校验备份 sha256，失败退出码 3 且库未变。
- 预期：`restored=N`、`differences=0`、前后计数相等；随后 DEPLOY-005 dry-run 重新出现原 `would_change`。
- restore 失败时：用 `ocapdb-registry-$TS2.sql` 整表导入属覆盖式恢复，会丢弃备份之后所有写入，仅由人评估后执行，本计划不提供自动命令。

### ROLLBACK-006: 回滚 DEPLOY-006
- 类型：无操作。备份保留（含个人信息，0600；保留期由用户决定，到期由人删除）。

### ROLLBACK-005: 回滚 DEPLOY-005
- 类型：无操作（只读）。

### ROLLBACK-004: 回滚 DEPLOY-004（恢复前端）
- 类型：正式回滚
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` 取 DEPLOY-001 的 `ANCHOR_TS`，快照须存在；执行后 `index.html` 存在，外网 `GET /ocap/` 为 200。只动 `web/`。

### ROLLBACK-003: 回滚 DEPLOY-003（重启回旧代码）
- 类型：正式回滚；**须在 ROLLBACK-002 恢复代码之后**执行。
- 命令：`$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 2 && systemctl is-active ocap-backend'`，再 `sudo journalctl -u ocap-backend -n 30 --no-pager` 确认无 Traceback。

### ROLLBACK-002: 回滚 DEPLOY-002（恢复后端代码，叠加解包，M-DE-011）
- 类型：正式回滚
- 命令：
```bash
# 叠加解包：把快照中的旧源码覆盖回去；不 rm -rf backend，避免丢失 DEPLOY-001 之后产生的 var/ 数据
CMD="sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap --exclude=backend/.env --exclude=backend/venv --exclude=backend/var"
echo "$CMD"; $OCAP_SSH "$CMD"
# 移除本批新增的 5 个文件（旧代码不引用；PRE-A13 已证明快照中不存在）
$OCAP_SSH 'cd /home/yangyang/ocap/backend && rm -f apps/registry/ordering.py apps/registry/underground.py apps/registry/exporting.py apps/registry/management/commands/relocate_underground_parking.py apps/registry/management/commands/export_registry_import_file.py'
# 核验：与 PRE-A13 记录的哈希一致
$OCAP_SSH 'cd /home/yangyang/ocap/backend && sha256sum apps/registry/services.py apps/registry/views.py apps/registry/urls.py apps/identity/services.py apps/residency/housing.py apps/registry/import_template.py; test -f .env && test -d venv && echo LOCAL_STATE_INTACT'
```
- 变量取值与核验：`TS` 同上；删除列表仅含本批新增的 5 个非测试文件（与 implementation_plan 改动清单一致，单引号命令内无本地变量，路径全为字面量）；哈希必须与 PRE-A13 一致，否则回滚未生效，停止上报。其后执行 ROLLBACK-003。
- 禁止：`git reset --hard`、`git clean`、覆盖式 rsync。

### ROLLBACK-001: 回滚 DEPLOY-001
- 类型：无操作。快照与 nginx 备份保留 ≥ 7 天，不删除。

## 不可逆步骤汇总

| 步骤 | 性质 | 标记 |
|---|---|---|
| DEPLOY-007 apply | 改库；可由 `--restore` 逆向（备份 sha256 校验），但还原本身是第二次改库，且不撤销 apply 之后的其他写入 | **[MANUAL_ROLLBACK_REQUIRED]**（ROLLBACK-007，须用户决定） |
| DEPLOY-010 删除临时导出文件 | 删除不可恢复，设计即一次性（可重新导出） | 已在 ROLLBACK-010 说明 |
| DEPLOY-013 清理 `e2e_` 数据 | 删除不可恢复，预期终态 | 已在 ROLLBACK-013 说明 |
| DEPLOY-006 备份文件、DEPLOY-009 本地文件 | 含个人信息文件 | 属保管问题：目标机 0600、本地 0600 + gitignore；保留期由用户决定 |
| 迁移 / 外部系统调用 / 通知 | 本批无 | — |

## 部署后验证

阶段 A 完成后立即执行（只读，随授权点 A）：

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback`/`ERROR` |
| 新路由存在且鉴权 | 目标机上 `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/admin/registry/units/filter-options`（无令牌） | `401` 或 `403`（404 说明新代码未生效） |
| 选房接口鉴权 | 目标机上 `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/units/options`（无令牌） | `401`/`403`（非 5xx） |
| 登录接口可用 | `$OCAP_SSH "curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400` |
| 无未应用迁移 | `showmigrations --plan`（同 PRE-A10） | `0` |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/`（或从目标机 `curl -m 10`） | 200，`text/html` |
| 外网前端与静态 | `GET https://ai-freeark.xin/ocap/`；`GET https://ai-freeark.xin/ocap/assets/<本次构建 js>` | 均 200；静态 404 → 检查 `^~ /ocap/` |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| 新前端已替换 | 取外网 `index.html` 引用的 js 文件名，与本地 `frontend/dist/index.html` 引用一致 | 一致 |
| Freeark 未受影响 | `GET https://ai-freeark.xin/`；`$OCAP_SSH 'systemctl --state=failed --no-pager'` | 200；无 `freeark-*`、`ocap-*` 失败单元 |
| 端口归属 | `$OCAP_SSH 'ss -ltnp'` 过滤 8000/8080/8090/9000 | 8000/8080 属 Freeark，8090/9000 属 ocap |
| 命令未被自动执行 | `$OCAP_SSH 'ls /home/yangyang/ocap/snapshots/underground-*.jsonl 2>&1'` | 阶段 A 结束时 `No such file`（两条命令未被执行） |

阶段 B/C/D 各自成功标准见对应 DEPLOY。阶段 C 之后的接口验证（只读；管理员/用户会话由用户提供或从其保管处读取，口令不写入任何文件）：

| 检查项 | 方法 | 成功标准 |
|---|---|---|
| 选房第一级 | 登录用户 `GET /ocap/api/v1/units/options` | 楼栋按自然序，“地下车位”排在编号楼栋之后；1 栋下不再出现负层 |
| 地下车位逐级 | `…/units/options?building=地下车位` | 楼层、车位号按 AC-184 规定的自然序 |
| 后台过滤器 | 管理员 `GET …/admin/registry/units?building=地下车位&unit_type=PARKING`（或页面操作） | count = 阶段 B 的 `would_change` + 原已在目标楼栋的车位数（`already_target`） |

人工验证清单（来自 e2e_test_report，纳入本计划）：

| 编号 | 对应阶段 | 做法 | 期望 |
|---|---|---|---|
| MV-01 | 阶段 B、D | DEPLOY-005 看写法清单；DEPLOY-008 导出并核对 `diff_*=0`、`precheck_rows_failed=0` | 与合成用例一致；含“-”楼层或 gaps 按 O-01 汇报用户 |
| MV-02 | 阶段 B、C | dry-run → apply（DEPLOY-007）→ 抽查 → 必要时 ROLLBACK-007 | 总数、绑定数前后相等；被识别记录楼栋为“地下车位”；冲突整批停止 |
| MV-03 | 阶段 C（MySQL 并发） | 本计划**不主动制造并发写入**（会在测试库触发真实批量导入，越出授权范围）；仅在用户另行指示时，由用户在 apply 窗口自行触发导入观察事务回滚 | 唯一约束报错使整个事务回滚；未做则标「待人工验证」，不阻断部署 |
| MV-04 | 阶段 A 后 | 用户用真实浏览器打开后台“业主清册”，展开类型/楼栋/单元下拉并制造空结果 | 无英文 “select”“No Data”，下拉与空状态为中文 |
| MV-05 | 阶段 C 后 | 用户用小程序真机与 Web 各打开“选择房屋”，比较四级顺序 | 逐项相同，地下车位排在最后（阶段 C 之前尚无该楼栋，故须在其后验证） |

阶段 E 的 P4-1 远程 E2E 标准见 DEPLOY-012/013；DEF-B 若仍失败，在报告「遗留问题」单列为既有失败，不影响本批 DEPLOYED_SUCCESSFULLY 判定。

状态判定：各阶段验证全部通过 → 该阶段 DEPLOYED_SUCCESSFULLY；失败按 E2 规则处理（尚无变更 → DEPLOYMENT_FAILED；已有变更 → 从失败步起逆序回滚；`[MANUAL_ROLLBACK_REQUIRED]` 步骤失败 → 暂停等人工）。

## 自检记录
- 每个 DEPLOY（001~013）均有 ROLLBACK 且逆序排列；需人工的步骤已标注。
- 环境仅为画像 P7 的「测试」；策略 recreate 已写理由；无 Docker、pscp、makemigrations 产物、目标机生成迁移、Freeark 改动。
- 回滚不使用 reset/clean/stash/覆盖式同步；变量 `TS/TS2/TS3/BK/X/N` 均写了取值来源与核验；远端引号规则已说明。
- `[INFERRED]` 项：数据库表名（PRE-C02 实测核对）、mysqldump 是否安装（PRE-C01）、阶段 C 耗时、`3ffd868` 作 requirements 比对基线、`--list-limit 200`、e2e_fixture 在目标机存在（PRE-A14）。
- 子代理未执行 ssh/scp/commit/push。
