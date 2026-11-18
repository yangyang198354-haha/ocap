<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-18T11:54:19+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/cicd_pipeline.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：申诉一次提交 / 席位授予清册业主 / 决议公开与参与人 / 清册排序等（后端含 2 个迁移 + Web 前端 + nginx 上传上限）

> 本计划只描述步骤，不构成授权。E1 未连接任何目标机、未执行 ssh/scp/部署命令（画像 P9）；E2 须用户当轮授权，每条 ssh/scp 仍经 `.claude/settings.json` 的 ask 规则确认。凭据只写位置不写值（`backend/.env`、`OCAP_E2E_PASSWORD` 只引用名称）。沿用 `ocap_identity_property`（已执行成功）的通道、变量、快照与前端替换做法，并吸收 M-DE-003/005/006/009/010/011/013/016/020/022/023/028/029/031/034/035/037 与上一批偏差 1、2。

## 授权条件（E2 开始前全部满足，否则 BLOCKED）

1. `phase_status` 中 GROUP_E1 已 APPROVED；本计划版本 = APPROVED 版本。
2. E2 invocation 的 `special_instructions` 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名 **测试**（画像 P7 唯一环境，部署需用户确认=是）。
3. 授权范围须明确包含：(a) 后端代码与 2 个迁移；(b) Web 前端静态替换；(c) **ocap 站点 nginx `client_max_body_size` 20m→60m 并 reload**（用户 2026-11-18 Q1=A 已同意，须在授权中再次写明，PM 依据用户本轮消息写入）。
4. 用户已知晓待部署内容**尚未提交**，同意以本地工作树打包（画像 P9、skill §0）；若 PM 在 E2 前已提交，改记新 HEAD。
5. 可选的 DEPLOY-012~014（远程只读 HTTP 探测，需创建 `e2e_` 夹具，画像 P4-1）须在授权中**单独**写明；未写明则跳过，V-22/V-23 标"未执行"，不得标 SUCCESS。夹具会临时占用真实专有部分，须先看 DEPLOY-012 预览并经用户确认（M-DE-020）。
6. 小程序本批不改、不上传体验版；不由 E2 执行任何小程序操作。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 MOD-139~145 | 修改 23：`apps/committee/{models,services,urls,views}.py`、`apps/core/{attachments,audit}.py`、`apps/jobs/views.py`、`apps/jobs/management/commands/run_due_jobs.py`、`apps/registry/{importing,ownership,services,urls,views}.py`、`apps/residency/{auto_bind,housing,models,phone_match,services,views}.py`、`apps/resolutions/{apps,services,urls,views}.py`；新建 4：`apps/committee/binding.py`、`apps/registry/listing.py`、`apps/committee/migrations/0002_seat_registry_holder.py`、`apps/residency/migrations/0005_membership_registry_owner.py` | ① `committee 0002_seat_registry_holder`：`Seat.user` 改可空；新增 `holder_owner`（FK→registryowner，SET_NULL）、`holder_unit_text`、`holder_name`、`bound_at`、`bind_conflict_at`；唯一约束 `uniq_seat_active_per_owner`；依赖 `committee.0001_initial`、`registry.0005_regenerate_specific_part`。② `residency 0005_membership_registry_owner`：`Membership.registry_owner`（FK 可空，SET_NULL）；依赖 `residency.0004_phone_match_prompt`、`registry.0005`。均手写、单 app、可逆；**不回填**存量（ADR-138）；既有席位 `user` 全非空 | 无构建；依赖不变（`git status --short -- backend/requirements.txt` 输出 0 行） | systemd `ocap-backend` 停止→更新→迁移→启动；`ocap-run-due-jobs.timer`（及目标机上若存在且 active 的 `ocap-content-worker.service`）在窗口内一并停止并在启动后恢复（它们加载同一份后端代码，`run_due_jobs.py` 本批改动、`expire_due` 新增清册失效步骤） |
| Web 前端 MOD-146~152 | 修改 13：`admin/{AdminRegistry,AdminSeats}.vue`、`layout/SideNav.vue`、`portal/{Polls,ResolutionDetail,Resolutions}.vue`、`portal/parts/UnitCascader.vue`、`portal/units/{UnitsAppeal,UnitsIdentity}.vue`、`shared/{api.js,style.css,voteShare.js}`、`stores/housing.js`；新建 3：`admin/parts/SeatHolderPicker.vue`、`portal/parts/ParticipantList.vue`、`shared/unitSearch.js` | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`，带 grep 门槛 | 静态目录 `/home/yangyang/ocap/web/ocap` 替换 |
| nginx（**用户 2026-11-18 Q1=A**） | 仅目标机 `/etc/nginx/sites-available/ocap` 第 5 行：`client_max_body_size 20m;` → `60m;`（理由：申诉一次提交最多 5×10MB，module_design ADR-136，GR-B-001-F01） | 无 | 无 | `sudo systemctl reload nginx`（**reload，不是 restart**）。**不得**修改 Freeark 的 `sites-enabled/freeark`（其 `/ocap/` 反代块经 PM 只读核实已为 60m，本计划只读复核）；不改其它站点与段 |
| 小程序 | 本批不改（`git status --short -- miniprogram` 输出 0 行） | — | 不构建 | 无；后端兼容性在 V-10 以只读检查确认 |
| 测试代码 | `backend/tests/**`、`frontend/tests/**`（13 个未跟踪、11 个修改） | — | 后端 tar 一并带上 `backend/tests`（与既往一致，不影响运行）；前端测试不部署 | — |
| 依赖 / `.env` / systemd 单元文件 / Freeark | 无变化 | — | — | 不触碰 |

**版本标识（部署前必须记录）**：计划编制时本地 `HEAD = c3a10ce16f3d939b6ac8a97afab32af25dfd64f8`；本批改动均未提交（`git status --short`：52 个 M、21 个 `??`；产品文件：后端 23 M + 4 `??`，前端 `src` 13 M + 3 `??`）。HEAD 不能单独定位版本，**定位依据 = `git status --short` 摘要 + 后端 tar SHA256 + 前端 tar SHA256 + 本地 `dist/index.html` SHA256**（M-DE-006）。E2 以自己打包时的值为准并记入报告。

**与 invocation 的对照**：前端构建命令按 skill 与 CI 带 `VITE_API_BASE=/ocap/api/v1`（M-DE-034，`frontend/src/shared/http.js:8`），以 `grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js` ≥ 1 为门槛。

## 目标环境与策略

- 环境：**测试**（画像 P7；树莓派；外网 SSH `-p 57279 yangyang@47.109.197.217`，首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报；内网 `192.168.31.51:22`）。生产为"无"，不设计晋升与其它环境；`ai-freeark.xin:9999` 不可用，不使用。
- 策略：**recreate**（画像允许）。理由：单实例 gunicorn，无两套环境与按比例分流，不具备 rolling/blue-green/canary 前提。后端采用"停服务 → 覆盖代码 → 迁移 → 启动"的短窗口（M-DE-016）：`Seat.user` 改可空与新增 NOT NULL 列（`holder_unit_text`、`holder_name`）在旧代码下会使席位写入失败（M-DE-028），且解包期间新旧文件混合有被 worker 导入的风险，故先停服务。顺序为**后端先于前端**：新前端调用 `POST /appeals`（multipart）、`/resolutions/{id}/participants`、`/admin/registry/unit-options`、`/admin/committee/owner-candidates` 在旧后端上会 404/不兼容；新后端对旧前端兼容（`/me/housing` 只增字段；`votes` 已无前端读取，ADR-141）。**nginx 在前端之后**：上限只影响新前端的 multipart 申诉，晚于前端改动无副作用，且任何 nginx 异常不会拖住后端上线。
- 预计停机：后端约 1~3 分钟（停止到启动，含迁移与往返验证）[INFERRED，无实测；上批实测约 57 秒，本批多 2 个迁移与定时任务停启]；前端静态替换窗口 < 数秒 [INFERRED]；nginx reload 无停机（平滑重载）[INFERRED]。
- 回滚偏好：画像未写。变更未提交，"源头 revert 后重新部署"不适用；采用"切回上一版本制品"（`backend-<TS>.tar.gz` / `web-<TS>.tar.gz` 快照 + nginx 备份），符合 skill §7。**回滚顺序固定：停后端 → 迁移回退（先 `migrate residency 0004`，再 `migrate committee 0001`，迁移文件须仍在磁盘上）→ 还原代码并删新增文件 → 启动**（M-DE-036）。**不得采用"只回退代码、保留新列"**：新列 `holder_unit_text`、`holder_name` 为 NOT NULL 且数据库无默认值，旧代码创建席位会在 MySQL 严格模式下失败（M-DE-028；与 M-DE-005 的可空列情形不同）。
- reload 对同机 Freeark 的影响：Freeark 与 ocap 共用同一个 nginx 主进程（Freeark 站点 `sites-enabled/freeark` 监听 80/8080，ocap 站点监听 8090）。`reload` 会让 master 重读全部站点配置并平滑替换 worker：已建立连接由旧 worker 处理完毕，Freeark 页面不中断，MainPID 不变；风险仅在配置语法/语义错误导致重载失败（`nginx -t` 门控已先行，失败则不 reload 且旧 worker 继续服务）。验证：reload 前后 `http://127.0.0.1:8080/` 均 200、公网 `https://ai-freeark.xin/` 200、`nginx` 的 MainPID 不变、`systemctl --state=failed` 无 `freeark-*`（V-16、V-18）。不 `restart`，不动 `freeark-*` 服务与 frpc。
- 小程序：本批不改，不需上传体验版；后端变更对小程序的影响（公开决议含进行中、`votes` 移除、`/me/housing` 新字段、`/appeals` JSON 分支保持）经 V-10 只读检查确认兼容（ADR-146）。

### SSH 通道与本地变量（沿用上批，M-DE-009/010/023）

```bash
CM=$(mktemp -d /tmp/ocs.XXXX)          # ControlPath 必须短路径
SCRATCH=$(mktemp -d /tmp/ocpkg.XXXX)   # 本地临时目录，使用前校验非空
[ -n "$CM" ] && [ -d "$CM" ] && [ -n "$SCRATCH" ] && [ -d "$SCRATCH" ] && echo "DIRS_OK" || echo "DIRS_EMPTY_STOP"
OCAP_SSH="ssh -p 57279 -o ControlMaster=auto -o ControlPath=$CM/%C -o ControlPersist=10m yangyang@47.109.197.217"   # 内网改 -p 22 yangyang@192.168.31.51
OCAP_SCP="scp -P 57279 -o ControlPath=$CM/%C"
OCAP_DEST="yangyang@47.109.197.217"
ocap_connect() {
  i=0
  while [ "$i" -lt 8 ]; do
    i=$((i+1))
    out=$($OCAP_SSH 'echo CONNECT_OK' 2>/dev/null)
    if [ "$out" = "CONNECT_OK" ]; then echo "CONNECT_OK attempt=$i"; return 0; fi
    sleep 5
  done
  echo "CONNECT_FAILED"; return 1
}
```

- 只重试"建连"；连续 8 次失败即停止汇报。已开始的**非幂等**命令（`rm`、`cp -a`、`migrate`、`systemctl stop/start`、`sed -i`）失败时先只读核对状态，不盲目重试。
- `$OCAP_SSH` 不加引号使用。远端命令要用本地值（`TS`、`OWN`、`AUX_ACTIVE`）时一律**双引号**，执行前 `echo` 完整命令核对；远端要自己展开的 `$` 在双引号里写 `\$`；单引号命令内的 `$VAR` 在远端展开，只在本意如此时使用。多行远端脚本用 `$OCAP_SSH bash -s -- "$TS" <<'EOF' … EOF`（E2 执行时的 shell 写法；本计划其它命令块不嵌套 heredoc）。
- `TS` 在 DEPLOY-001 取一次并全程复用（M-DE-003）；跨会话由 PM 写入 invocation，不依赖 shell 状态。
- 结束清理：先 `echo "$CM" "$SCRATCH"` 确认非空且以 `/tmp/ocs.`、`/tmp/ocpkg.` 开头，再 `ssh -O exit -o ControlPath=$CM/%C yangyang@47.109.197.217; rm -rf "$CM" "$SCRATCH"`。
- E2 用 **Write 工具**在 `$SCRATCH` 写下面两个辅助文件（M-DE-023、M-DE-031；不用 Bash heredoc 写文档/脚本）：
  - `$SCRATCH/mig_check_settings.py`（供 PRE-A04，M-DE-037）：两行 `from config.test_settings import *` 与 `MIGRATION_MODULES = {}`。
  - `$SCRATCH/schema_check.py`（只读，经 stdin 喂给 `manage.py shell`，只输出结构与计数，不输出任何业务值）：

```python
from django.db import connection as c
from apps.committee.models import Seat
from apps.residency.models import Membership

with c.cursor() as cur:
    seat_cols = {col.name: col.null_ok for col in c.introspection.get_table_description(cur, Seat._meta.db_table)}
    mem_cols = {col.name: col.null_ok for col in c.introspection.get_table_description(cur, Membership._meta.db_table)}
    seat_cons = c.introspection.get_constraints(cur, Seat._meta.db_table)
print("TABLES", Seat._meta.db_table, Membership._meta.db_table)
print("SEAT_USER_NULL_OK", seat_cols.get("user_id"))
new_cols = ("holder_owner_id", "holder_unit_text", "holder_name", "bound_at", "bind_conflict_at")
print("SEAT_NEW_COLS", [n for n in new_cols if n in seat_cols])
print("UNIQ_OWNER_CONSTRAINT", "uniq_seat_active_per_owner" in seat_cons)
print("MEMBERSHIP_REGISTRY_OWNER_COL", "registry_owner_id" in mem_cols)
print("SEAT_COUNT", Seat.objects.count())
print("SEAT_USER_NULL_ROWS", Seat.objects.filter(user__isnull=True).count())
print("MEMBERSHIP_COUNT", Membership.objects.count())
```

  使用方式（M-DE-031）：`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"`。脚本只用 `Seat.objects.count()` / `filter(...).count()`（`SELECT COUNT(*)`），迁移回退到旧结构时也能运行。

## 预检清单

### 开发机（只读 + 本地构建，不触碰目标机）

先 `cd /root/myproject/ocap`。

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-A01 版本标识已记录 | `git rev-parse HEAD`；`git status --short \| awk '{print $1}' \| sort \| uniq -c` | 已记录（输出写入报告）；未提交是已知状态，不是阻断项 |
| PRE-A02 改动范围与计划一致 | `git status --short -- deploy backend/requirements.txt frontend/package.json frontend/package-lock.json miniprogram \| wc -l`；`git status --short -- backend \| grep -v tests`；`git status --short -- frontend/src` | 第一条 `0`（非 0 → 停止上报：计划假设无新依赖、无 systemd 模板与小程序改动）；第二条恰为本计划列出的 23 个 M + 4 个 `??` 后端文件；第三条恰为 13 个 M + 3 个 `??`（出现别的文件 → 停止，让 PM 判定是否仍属本批） |
| PRE-A03 迁移文件合规（P6/P8） | `head -3 backend/apps/committee/migrations/0002_seat_registry_holder.py backend/apps/residency/migrations/0005_membership_registry_owner.py`；`grep -c "Generated by Django" backend/apps/committee/migrations/0002_seat_registry_holder.py backend/apps/residency/migrations/0005_membership_registry_owner.py`；`ls backend/apps/committee/migrations backend/apps/residency/migrations backend/apps/registry/migrations` | 头注释为手写说明；两个计数均 `0`；committee 最新为 0001→0002，residency 为 0004→0005，registry 最新 `0005_regenerate_specific_part`（与两个迁移的 dependencies 一致） |
| PRE-A04 迁移无漂移（scoped，M-DE-037） | 用 Write 工具写 `$SCRATCH/mig_check_settings.py`，然后 `(cd backend && PYTHONPATH="$SCRATCH" $PY manage.py makemigrations --check --dry-run --settings=mig_check_settings committee residency; echo EXIT=$?)`（`$PY` 为 PM 的 Django 5.2 venv） | `EXIT=0`、`No changes detected`。**不得用 Django 6.x**（P4）；**不得直接用 `config.test_settings`**（置空 `MIGRATION_MODULES` 会误报/抛 ValueError）；产物不得提交（P8）；非 0 → 停止交回开发。全量检查中既有 content 等 app 的漂移输出非本批，不计 |
| PRE-A05 测试基线 | 后端 `(cd backend && $PY manage.py test --settings=config.test_settings)`；前端 `(cd frontend && npx vitest run --passWithNoTests 2>&1 \| tail -6)`（约 255 秒，勿用短超时）；小程序 `(cd miniprogram && npx vitest run --passWithNoTests 2>&1 \| tail -6)` | 后端 1119 通过；前端 45 文件 531 条；小程序 18 文件 135 条（GROUP_D 报告与 PM 2026-11-18 11:43 复跑值）。本机缺依赖无法复跑时，如实标"引用 GROUP_D 报告、未复跑"，不得标 PASS。有失败 → 停止 |
| PRE-A06 风格生成物无漂移 | `node scripts/themes/build.mjs --check --strict; echo EXIT=$?` | `EXIT=0` |
| PRE-A07 前端构建与产物核验（M-DE-034） | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/ 2>&1 \| tail -3`；`grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js`；`for k in owner-candidates unit-options participants; do echo $k $(grep -l "$k" frontend/dist/assets/*.js \| wc -l); done`；`grep -o '<title>[^<]*' frontend/dist/index.html` | `✓ built`；前缀计数 ≥ 1；三个新接口关键字各命中文件数 ≥ 1（新接口随产物发布）；标题与上批一致（`Cyber@红枫岭`）；记录 `sha256sum frontend/dist/index.html` 与 `find frontend/dist -type f \| wc -l` |
| PRE-A08 无游离未跟踪产品文件 | `git ls-files --others --exclude-standard backend frontend/src miniprogram \| grep -v tests` | 恰 7 个：后端 4（`backend/apps/committee/binding.py`、`backend/apps/committee/migrations/0002_seat_registry_holder.py`、`backend/apps/registry/listing.py`、`backend/apps/residency/migrations/0005_membership_registry_owner.py`）、前端 3（`frontend/src/admin/parts/SeatHolderPicker.vue`、`frontend/src/portal/parts/ParticipantList.vue`、`frontend/src/shared/unitSearch.js`）；后端 4 个随 tar 打包，务必在包内（DEPLOY-002） |
| PRE-A09 契约与小程序兼容的本地复核（V-10 的一部分） | `(cd backend && $PY manage.py test tests.integration.test_frontend_contract tests.integration.test_owner_auth_v2_contract --settings=config.test_settings 2>&1 \| tail -4)`；`git status --short -- miniprogram \| wc -l`；`git grep -n "votes" -- miniprogram ':!miniprogram/node_modules' ':!miniprogram/tests' \| wc -l`；`git grep -nE "/appeals\|/resolutions\|/me/housing" -- miniprogram/utils/api.js` | 契约用例 `OK`；小程序改动 `0`；`votes` 引用计数记录（期望 0；非 0 须逐条判断是否读取决议 `votes` 数组，ADR-141/146）；列出小程序调用的 3 类路径供 V-10 对照 |

### 目标机（只读；`ocap_connect` 成功后一次性完成）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-T01 可达与指纹 | `ocap_connect`；核对 `known_hosts` 中该端口 ED25519 指纹 | `CONNECT_OK`；指纹与画像 P7 一致 |
| PRE-T02 磁盘/内存 | `$OCAP_SSH 'df -h /home /tmp; free -m'` | /home 可用 ≥ 2 GB；/tmp 可用 ≥ 200 MB（V-17 body 探测临时文件最大 63 MB，用后即删）；可用内存 ≥ 500 MB |
| PRE-T03 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| PRE-T04 目录与必须保留的本地状态 | `$OCAP_SSH 'ls -la /home/yangyang/ocap /home/yangyang/ocap/web /home/yangyang/ocap/backend; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -d /home/yangyang/ocap/backend/venv && echo VENV_OK; test -d /home/yangyang/ocap/backend/var && echo VAR_OK; sha256sum /home/yangyang/ocap/backend/.env; ls /home/yangyang/ocap/backend/.env.bak_* 2>/dev/null \| wc -l; ls -l /home/yangyang/ocap/snapshots \| tail -20'` | 三个 OK；记录 `.env` 的 SHA256 为 `ENV_SHA`（只记哈希，不 `cat`；V-19 部署后须相同）；记录 `.env.bak_*` 个数 `ENVBAK_N`（上批已知存在，本批快照与回滚均排除，须保持不变）；`snapshots/` 内既有备份（含个人信息的 `ocapdb-*.sql`、`shops-*.jsonl`、`residency_appeal-*.sql`、`underground-*.jsonl` 等）**存在，本计划任何步骤不得删除** |
| PRE-T05 属主（M-DE-013） | `$OCAP_SSH 'stat -c "%U:%G %n" /home/yangyang/ocap/backend /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html'` | 记录；`web/ocap` 属主记为 `OWN`，须匹配 `^[a-z_][a-z0-9_-]*:[a-z_][a-z0-9_-]*$`；backend 目录对 `yangyang` 可写 |
| PRE-T06 后端基线 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID; systemctl cat ocap-backend \| grep -E "ExecStart\|User\|WorkingDirectory"'` | `active`；记录时间戳与 PID（V-01 须不同）；记录 gunicorn 的 `--timeout`（缺省 30 s；M-DE-007，供 M-6 判读，本批不改） |
| PRE-T07 依赖未变 | 本地 `sha256sum backend/requirements.txt`；`$OCAP_SSH 'sha256sum /home/yangyang/ocap/backend/requirements.txt'` | 两端相同（则 DEPLOY 中**不**执行 `pip install`）。不同 → 停止上报（计划假设依赖不变）；若用户确认需同步依赖，另加 `venv/bin/pip install --dry-run -r requirements.txt` 门控并扩展计划，不得现场自行加步骤 |
| PRE-T08 迁移基线与表结构基线（M-DE-028 门控前置） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations committee residency registry && venv/bin/python manage.py showmigrations --plan \| grep -c "^\[ \]"'`；再运行 `schema_check.py`（见上） | committee 仅 0001 `[X]`（无 0002）；residency 0001~0004 `[X]`（无 0005）；registry 至 0005 `[X]`；未应用计数 `0`。`schema_check` 输出：`TABLES committee_seat residency_membership`（与 DEPLOY-001 转储表名一致；不同则停止修订计划）；`SEAT_USER_NULL_OK False`、`SEAT_NEW_COLS []`、`UNIQ_OWNER_CONSTRAINT False`、`MEMBERSHIP_REGISTRY_OWNER_COL False`；记录 `SEAT_BASE`、`MEM_BASE`（行数）；`SEAT_USER_NULL_ROWS 0`。若 0002/0005 已在目标机库中存在 → 停止上报 |
| PRE-T09 辅助单元基线（定时任务） | `$OCAP_SSH 'systemctl list-units "ocap-*" --all --no-legend; for u in ocap-run-due-jobs.timer ocap-content-worker.service; do echo $u $(systemctl is-active $u); done'` | 记录哪些 `ocap-*` 单元为 `active`，其中非 `ocap-backend` 的记为 `AUX_ACTIVE`（空格分隔的单元名，如 `ocap-run-due-jobs.timer`）。这些单元加载同一份后端代码，DEPLOY-004 停、DEPLOY-007 启；未列入者不动 |
| PRE-T10 转储工具与 sudo | `$OCAP_SSH 'command -v mysqldump; sudo -n true && echo SUDO_OK'` | 有 `mysqldump` 路径；`SUDO_OK`（无则 DEPLOY-001 的转储不可执行 → 停止上报，不得省略转储） |
| PRE-T11 nginx 与 Freeark 基线（含 nginx 改动前提） | `$OCAP_SSH 'sudo nginx -t 2>&1; systemctl show nginx -p MainPID -p ActiveEnterTimestamp; curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/; ls -l /etc/nginx/sites-enabled/; sudo sed -n 5p /etc/nginx/sites-available/ocap; sudo nginx -T 2>/dev/null \| grep -nE "^# configuration file\|client_max_body_size\|proxy_read_timeout\|proxy_request_buffering\|server_name\|listen \|location \^~ /ocap/"'` | `syntax is ok`；`200`；记录 nginx `MainPID` 为 `NGX_PID`；**第 5 行恰为 `client_max_body_size 20m;`**（否则停止上报：与 PM 2026-11-18 核实值不符）；记录 ocap 站点是否为 `sites-enabled` 软链；`nginx -T` 过滤输出中 Freeark 的 `client_max_body_size`（含 `/ocap/` 反代块）为 60m（只读核对，**不得修改**）；记录 `proxy_read_timeout`（供 M-6 判读）与对应 `ai-freeark.xin` 的监听端口（V-17 的 Freeark 探测用该端口；`[INFERRED]` 为 8080，以实测为准）。`nginx -T` 只过滤打印指定行，不打印证书/密钥内容 |
| PRE-T12 当前线上页面基线 | `$OCAP_SSH 'cd /home/yangyang/ocap/web/ocap && sha256sum index.html && grep -o "assets/[^\"]*" index.html'`；`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/`；`curl -s -m 15 -o /dev/null -w '%{http_code}\n' https://ai-freeark.xin/` | 记录旧 `index.html` SHA256 与入口文件名；公网 `200 text/html`；Freeark 首页 `200` |
| PRE-T13 当前上传上限实测（证明探测有效） | `$OCAP_SSH 'head -c 58000000 /dev/zero > /tmp/ocap_probe_t13.bin && curl -s -m 60 -o /dev/null -w "%{http_code} %{content_type}\n" -X POST -H "Content-Type: application/octet-stream" --data-binary @/tmp/ocap_probe_t13.bin http://127.0.0.1:8090/ocap/api/v1/appeals; rm -f /tmp/ocap_probe_t13.bin'` | 当前 20m 下返回 `413`（nginx 拒绝，未到达后端，无数据写入）。返回 401/403 → 说明上限已 ≥ 58 MB，nginx 改动无必要，停止上报；用后临时文件已删 |
| PRE-T14 `e2e_` 夹具前提（仅当授权 DEPLOY-012~014） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'` | 全 0，无遗留 `e2e_` 数据；记录输出中的清册计数为 `REGISTRY_BASE`。非 0 → 停止并上报（M-DE-020） |

## 部署步骤

### DEPLOY-001: 生成回滚锚点并快照后端、Web、迁移状态、两张表、nginx 站点配置
- 组件：`/home/yangyang/ocap/backend`（不含 `venv`、`var`、`.env`、`.env.*`）、`/home/yangyang/ocap/web`（architecture_design 部署视图：后端 + Web 静态）、MySQL 表 `committee_seat`、`residency_membership`（将被迁移改动）、`/etc/nginx/sites-available/ocap`（将被改一行）。
- 位置：目标机；`TS` 在本地取一次
- 命令：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_FORMAT_OK || echo TS_BAD_STOP
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
mkdir -p $A/snapshots
# 排除 venv、var、.env、.env.*：既防快照膨胀，也保证回滚"叠加解包"不会触碰本地状态（M-DE-011；上批偏差 1）
sudo tar czf $A/snapshots/backend-$TS.tar.gz --exclude='backend/venv' --exclude='backend/var' --exclude='backend/.env' --exclude='backend/.env.*' --exclude='__pycache__' -C $A backend
sudo tar czf $A/snapshots/web-$TS.tar.gz -C $A web
cd $A/web/ocap && find . -type f -print0 | sort -z | xargs -0 sha256sum > $A/snapshots/webhash-$TS.sha256
cd $A/backend && find . -type f -not -path './venv/*' -not -path './var/*' -not -path '*/__pycache__/*' -not -name '.env' -not -name '.env.*' -print0 | sort -z | xargs -0 sha256sum > $A/snapshots/backendhash-$TS.sha256
set -a && . ./.env && set +a
venv/bin/python manage.py showmigrations --plan > $A/snapshots/migplan-$TS.txt
# 两张将被迁移改动的表转储（只含用户 ID、席位与成员关系字段，不含手机号；测试库自签证书用 --skip-ssl，M-DE-008；口令经环境变量，不进 argv，不打印）
MYSQL_PWD="$DB_PASSWORD" mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl "$DB_NAME" committee_seat residency_membership > $A/snapshots/seat_membership-$TS.sql
chmod 600 $A/snapshots/seat_membership-$TS.sql
sudo cp -p /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS
ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/webhash-$TS.sha256 $A/snapshots/backendhash-$TS.sha256 $A/snapshots/migplan-$TS.txt $A/snapshots/seat_membership-$TS.sql /etc/nginx/sites-available/ocap.bak_$TS
wc -l $A/snapshots/webhash-$TS.sha256 $A/snapshots/backendhash-$TS.sha256
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -c '^backend/manage.py$'
tar tzf $A/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html$'
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -cE 'backend/(\.env|venv/|var/)' || true   # 期望输出 0（含 .env.bak_*）；grep 无匹配退出码 1，须 || true 以免 set -e 中断
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz
grep -c 'committee.0002\|residency.0005' $A/snapshots/migplan-$TS.txt || true
grep -c 'CREATE TABLE' $A/snapshots/seat_membership-$TS.sql
sudo diff /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS && echo NGINX_BACKUP_IDENTICAL
EOF
```
- 预期：输出 `ANCHOR_TS`、`TS_FORMAT_OK`；7 个文件非零大小；两份哈希清单行数 = 旧文件数；`manage.py` 与 `index.html` 计数各 `1`；排除项计数 **`0`**（快照不含 `.env`、`.env.bak_*`、`venv`、`var`，与上批偏差 1 不同）；迁移基线计数 `0`；转储中 `CREATE TABLE` 计数 `2`；`NGINX_BACKUP_IDENTICAL`。两个 tar 的 SHA256 记入报告。快照、清单、转储与 nginx 备份保留 ≥ 7 天。失败且目标机无变更 → `DEPLOYMENT_FAILED`，无需回滚。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建并打包后端与前端
- 组件：后端（MOD-139~145）、Web 前端（MOD-146~152）
- 位置：开发机
- 命令：
```bash
echo "$SCRATCH"                                                       # 必须非空且为 /tmp/ocpkg.*
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='.env.*' --exclude='var' --exclude='db.sqlite3' \
    -czf "$SCRATCH/backend_$TS.tar.gz" -C backend .
tar tzf "$SCRATCH/backend_$TS.tar.gz" | grep -E '^\./apps/(committee/binding\.py|registry/listing\.py|committee/migrations/0002_seat_registry_holder\.py|residency/migrations/0005_membership_registry_owner\.py)$'
tar tzf "$SCRATCH/backend_$TS.tar.gz" | grep -cE '(^|/)\.env(\.|$)|^\./venv/|^\./var/'    # 须 0
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js               # 须 >= 1
for k in owner-candidates unit-options participants; do echo $k $(grep -l "$k" frontend/dist/assets/*.js | wc -l); done   # 各须 >= 1
tar -czf "$SCRATCH/frontend_dist_$TS.tar.gz" -C frontend/dist .
sha256sum "$SCRATCH/backend_$TS.tar.gz" "$SCRATCH/frontend_dist_$TS.tar.gz" frontend/dist/index.html
find frontend/dist -type f | wc -l                                   # 记录文件数
```
- 预期：后端包含 4 个新增文件（4 行输出）；排除项计数 `0`；`✓ built`；前缀与三个关键字计数均 ≥ 1（门槛不过 → 停止，不上传）；两个 tar 与 `index.html` 的 SHA256、`dist` 文件数记入报告。不使用 pscp 逐文件上传、不使用容器（P8）。失败 → 目标机仅多了快照，`DEPLOYMENT_FAILED`。（为缩短停机窗口，E2 可在取得 `TS` 之前先构建，取得后按含 `TS` 的文件名打包/重命名，上批已采用。）
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并在目标机暂存
- 位置：开发机 → 目标机（`/tmp`，文件名含 `TS`）
- 命令：
```bash
$OCAP_SCP "$SCRATCH/backend_$TS.tar.gz" "$SCRATCH/frontend_dist_$TS.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz"      # 须与 DEPLOY-002 本地值一致
$OCAP_SSH "rm -rf /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && mkdir /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && tar xzf /tmp/backend_$TS.tar.gz -C /tmp/ocap_backend_stage_$TS && tar xzf /tmp/frontend_dist_$TS.tar.gz -C /tmp/ocap_web_stage_$TS && ls /tmp/ocap_backend_stage_$TS/manage.py /tmp/ocap_backend_stage_$TS/apps/committee/binding.py /tmp/ocap_backend_stage_$TS/apps/registry/listing.py /tmp/ocap_backend_stage_$TS/apps/committee/migrations/0002_seat_registry_holder.py /tmp/ocap_backend_stage_$TS/apps/residency/migrations/0005_membership_registry_owner.py && ls -a /tmp/ocap_backend_stage_$TS | grep -c '^\.env' ; find /tmp/ocap_web_stage_$TS -type f | wc -l && sha256sum /tmp/ocap_web_stage_$TS/index.html"
```
- 预期：两端 SHA256 一致；暂存后端含 `manage.py` 与 4 个新文件、`.env*` 计数 `0`；暂存前端文件数 = DEPLOY-002 `dist` 文件数，`index.html` SHA256 = 本地。任一不符 → 停止（目标机运行目录尚未改动），按 ROLLBACK-003 清理暂存，报告 `DEPLOYMENT_FAILED`。
- 注意：`$` 在双引号中已为本地展开（`$TS`）；`\$` 保证远端收到字面 `$`；`grep -c` 在计数为 0 时退出码 1，故其后用 `;` 而非 `&&`。执行前 `echo` 完整命令核对。
- 回滚: ROLLBACK-003

### DEPLOY-004: 停止辅助单元与后端并覆盖后端代码（线上首个变更点）
- 组件：`/home/yangyang/ocap/backend`（systemd `ocap-backend`；`AUX_ACTIVE` 中的 `ocap-run-due-jobs.timer` 等）
- 位置：目标机；`AUX_ACTIVE` 取自 PRE-T09（本地变量，双引号展开；空则循环不执行）
- 命令：
```bash
CMD="for u in $AUX_ACTIVE; do sudo systemctl stop \$u; done; timeout 30 sh -c 'while systemctl is-active --quiet ocap-run-due-jobs.service; do sleep 1; done'; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend $AUX_ACTIVE; cp -a /tmp/ocap_backend_stage_$TS/. /home/yangyang/ocap/backend/ && ls -l /home/yangyang/ocap/backend/apps/committee/binding.py /home/yangyang/ocap/backend/apps/registry/listing.py /home/yangyang/ocap/backend/apps/committee/migrations/0002_seat_registry_holder.py /home/yangyang/ocap/backend/apps/residency/migrations/0005_membership_registry_owner.py && test -f /home/yangyang/ocap/backend/.env && test -d /home/yangyang/ocap/backend/venv && test -d /home/yangyang/ocap/backend/var && sha256sum /home/yangyang/ocap/backend/.env && ls /home/yangyang/ocap/backend/.env.bak_* 2>/dev/null | wc -l"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：先停定时器再等待可能在跑的 oneshot 服务结束（至多 30 秒），然后 `ocap-backend` 与 `AUX_ACTIVE` 单元的 `is-active` 均 `inactive`；4 个新文件存在；`.env`/`venv`/`var` 仍在，`.env` SHA256 = `ENV_SHA`，`.env.bak_*` 个数 = `ENVBAK_N`（暂存包不含 `.env*`，`cp -a` 不会覆盖）。解包只覆盖与新增，**不删除**目标机已有文件：本批后端无删除文件（`git status` 无后端 `D`），故无需清理旧文件。`stop` 已执行而 `cp` 失败 → 目标机已有变更，**立即**从 ROLLBACK-004 起回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 数据库迁移 committee 0002 与 residency 0005（目标机 MySQL）
`[MANUAL_ROLLBACK_REQUIRED（条件触发）: 回滚时若 committee_seat 存在 user 为空的待绑定席位，AlterField 改回非空会失败，须人工决定转储与删除；迁移中途失败（MySQL DDL 非事务）可能留下半应用结构，须按 DEPLOY-001 的转储与 schema_check 人工核对。表为空/无待绑定席位时回滚自动执行，见 ROLLBACK-005]`
- 组件：数据层（module_design「数据迁移」）；Seat、Membership 两表
- 位置：目标机；迁移由开发机手写入库，不在目标机生成（P8）
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'
```
  **门控（M-DE-028）**：输出必须**恰为两行** `committee.0002_seat_registry_holder` 与 `residency.0005_membership_registry_owner`，否则停止，不执行 `migrate`（说明目标机库状态与预期不符），按 ROLLBACK-004 起回滚代码。通过后执行：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -10; venv/bin/python manage.py showmigrations committee residency'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
```
- 预期：`Applying committee.0002_seat_registry_holder... OK`、`Applying residency.0005_membership_registry_owner... OK`；`showmigrations` 中两者 `[X]`；`schema_check`：`SEAT_USER_NULL_OK True`、`SEAT_NEW_COLS` 含全部 5 列、`UNIQ_OWNER_CONSTRAINT True`、`MEMBERSHIP_REGISTRY_OWNER_COL True`、`SEAT_COUNT` = `SEAT_BASE`、`SEAT_USER_NULL_ROWS 0`、`MEMBERSHIP_COUNT` = `MEM_BASE`（M-7 的证据，全部记入报告）。MySQL 自签证书由 `.env` 的 `DB_SSL_DISABLED` 处理，不改。`migrate` 失败（含部分应用）→ 目标机已有变更，从 ROLLBACK-005 起逆序回滚（先只读运行 `schema_check` 与 `showmigrations` 判断状态，不盲目重试）。
- 回滚: ROLLBACK-005

### DEPLOY-006: 迁移往返验证（M-7，MySQL，仅当无待绑定席位时）
- 目的：e2e_test_report M-7"迁移成功可逆"：在测试机 MySQL 上验证 0002/0005 可回退且可重迁。后端与辅助单元仍停止，无用户写入。**仅当 `SEAT_USER_NULL_ROWS` = 0 时执行**（此时必为 0）；非 0 → 跳过往返并如实记录，M-7 标"部分完成"，不得删行。
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency 0004 --noinput 2>&1 | tail -4; venv/bin/python manage.py migrate committee 0001 --noinput 2>&1 | tail -4; venv/bin/python manage.py showmigrations committee residency'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -6; venv/bin/python manage.py showmigrations committee residency'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations --plan' > "$SCRATCH/migplan_after_$TS.txt"
```
- 预期：回退输出 `Unapplying residency.0005… OK`、`Unapplying committee.0002… OK`；中间 `schema_check`：`SEAT_USER_NULL_OK False`、`SEAT_NEW_COLS []`、`UNIQ_OWNER_CONSTRAINT False`、`MEMBERSHIP_REGISTRY_OWNER_COL False`、`SEAT_COUNT` = `SEAT_BASE`；重迁 `Applying committee.0002… OK`、`Applying residency.0005… OK`；末次 `schema_check` 与 DEPLOY-005 的预期一致。迁移计划与 `migplan-$TS.txt` 的差异仅为 `committee.0002`、`residency.0005` 两行（V-21 用 `diff` 核对）。**终态必须是 0002/0005 均已应用**；往返中途失败（如回退成功、重迁失败）→ 先只读查询状态，再重试一次 `migrate`（幂等）；仍失败 → 从 ROLLBACK-005 起回滚。此往返不改其它表。
- 回滚: ROLLBACK-006

### DEPLOY-007: 启动后端与辅助单元并查看日志
- 位置：目标机；`AUX_ACTIVE` 同 DEPLOY-004
- 命令：
```bash
CMD="sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend && systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID; for u in $AUX_ACTIVE; do sudo systemctl start \$u; done; systemctl is-active $AUX_ACTIVE"
echo "$CMD"; $OCAP_SSH "$CMD"
$OCAP_SSH "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -30"
```
- 预期：`ocap-backend` `active`，`ActiveEnterTimestamp`、`MainPID` 与 PRE-T06 不同；`AUX_ACTIVE` 各单元 `active`；日志无 `Traceback`、无 `ERROR`、无 `no such column`/`doesn't exist`/`Unknown column`。失败 → 从 ROLLBACK-007 起逆序回滚。
- 回滚: ROLLBACK-007

### DEPLOY-008: 替换 Web 静态目录
- 组件：`/home/yangyang/ocap/web/ocap`（nginx 站点 `ocap`；Freeark `^~ /ocap/` 反代，均不改）
- 位置：目标机；`OWN` 取自 PRE-T05。**仅在 V-01~V-10（后端部分）通过后执行**，否则新前端会在故障后端上不可用。
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap/* && sudo cp -a /tmp/ocap_web_stage_$TS/. /home/yangyang/ocap/web/ocap/ && sudo chown -R $OWN /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && find /home/yangyang/ocap/web/ocap -type f | wc -l && sha256sum /home/yangyang/ocap/web/ocap/index.html"
echo "$CMD"          # 核对 TS、OWN 已展开且 OWN 形如 yangyang:yangyang
$OCAP_SSH "$CMD"
```
- 预期：`index.html` 存在；文件数 = 本地 `dist`；`index.html` SHA256 = 本地。`rm` 已执行而后续失败 → 目标机已有变更，**立即**从 ROLLBACK-008 起逆序回滚。
- 回滚: ROLLBACK-008

### DEPLOY-009: 修改 ocap 站点上传上限并语法检查（用户 2026-11-18 Q1=A）
- 组件：`/etc/nginx/sites-available/ocap`（architecture_design 部署视图：nginx 站点 ocap）；**只改第 5 行，不改任何其它行、不改 Freeark**
- 位置：目标机；备份 `ocap.bak_$TS` 已在 DEPLOY-001 生成。**仅在 V-01~V-15（后端与前端）通过后执行。**
- 命令：
```bash
CMD="sudo sed -n 5p /etc/nginx/sites-available/ocap && sudo sed -i --follow-symlinks '5s/client_max_body_size 20m;/client_max_body_size 60m;/' /etc/nginx/sites-available/ocap; sudo diff /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap; sudo nginx -t 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：改前第 5 行为 `client_max_body_size 20m;`（PRE-T11 已核对）；`diff` **恰为** `5c5`、`< … 20m;`、`> … 60m;`（单行差异）；`nginx -t` 输出 `syntax is ok` 与 `test is successful`。`diff` 无输出（sed 未命中）或出现其它差异、或 `nginx -t` 失败 → **不得 reload**，立即 ROLLBACK-009（恢复备份并复测）并报告；此时 nginx 运行中的配置尚未改变（未 reload），无需 ROLLBACK-010。`--follow-symlinks` 使 ocap 站点若为 `sites-enabled` 软链时改到真实文件（M-DE-007）。
- 回滚: ROLLBACK-009

### DEPLOY-010: reload nginx（不是 restart）
- 位置：目标机；仅在 DEPLOY-009 全部预期满足后
- 命令：
```bash
$OCAP_SSH 'sudo nginx -t 2>&1 && sudo systemctl reload nginx && sleep 1 && systemctl is-active nginx && systemctl show nginx -p MainPID -p ActiveEnterTimestamp && curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/ && sudo journalctl -u nginx --since "-2 min" --no-pager | tail -8'
```
- 预期：`active`；`MainPID` = `NGX_PID`（reload 不换 master）；`127.0.0.1:8080` 返回 `200`；nginx 日志无 `emerg`/`[alert]`。reload 失败或 8080 非 200 → 从 ROLLBACK-010 起回滚（恢复备份 + nginx -t + reload）。不得 `restart`，不动 `freeark-*` 服务。
- 回滚: ROLLBACK-010

### DEPLOY-011: 验证通过后清理临时文件
- 位置：目标机；**仅在「部署后验证」全部通过（或 PM 决定保留现状）之后执行**；需要回滚时先保留暂存，回滚完成后再清理
- 命令：
```bash
CMD="rm -rf /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && rm -f /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz /tmp/ocap_probe_t13.bin /tmp/ocap_probe_v17_58m.bin /tmp/ocap_probe_v17_63m.bin && ls /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：四项均 `No such file or directory`。只删带 `TS` 的本次上传路径与三个固定名探测文件（无通配符），不删 `snapshots/` 下任何文件，不删 `ocap.bak_*`。
- 回滚: ROLLBACK-011

### DEPLOY-012: （可选，需单独授权）夹具只读预览
- 目的：夹具会把 3 个空闲住宅专有部分临时绑给 `e2e_` 账号（M-DE-020）。先只读列出将占用的真实对象，供用户确认。**默认不执行。**
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.jobs.e2e_fixture import _free_units; print([(u.id, u.specific_part) for u in _free_units(3, set())])"'
```
- 预期：输出 3 个 `(id, 坐落)`，**不含姓名/手机号**；用户确认后才进入 DEPLOY-013；用户未确认 → 跳过 012~014。
- 回滚: ROLLBACK-012

### DEPLOY-013: （可选，需单独授权）夹具 setup → 只读 HTTP 探测 → cleanup（同一次调用，M-DE-020）
- 目的：按 P4-1 只经公开入口、仅 `e2e_` 账号，对新增/改动接口做**只读 GET** 结构检查（V-22）。**不发写请求，不改清册。**
- 位置：开发机（探测）+ 目标机（夹具）；口令只在进程内存或 stdin，不进 argv、不写文件
- 做法：E2 用 Write 工具在 `$SCRATCH` 写 `e2e_probe.sh` 与 `e2e_probe.py`（M-DE-023），脚本结构：
  1. `trap cleanup EXIT`，`cleanup` 执行 `$OCAP_SSH "$F cleanup --execute"`（`F` 为单引号字符串 `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture`，无 `$` 变量）；
  2. `OCAP_E2E_PASSWORD=$(python3 -I -c 'import secrets;print(secrets.token_urlsafe(18))')`（仅本地 shell 变量，不 echo）；
  3. setup：`printf '%s' "$OCAP_E2E_PASSWORD" | $OCAP_SSH 'IFS= read -r OCAP_E2E_PASSWORD; export OCAP_E2E_PASSWORD; cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 0 --bulk-resolutions 0'`；
  4. 探测：`OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD="$OCAP_E2E_PASSWORD" python3 -I "$SCRATCH/e2e_probe.py"`，`e2e_probe.py` 先 `ast.parse` 自检，复用 `backend/tests/remote/remote_client.py` 的 `Config`/`Remote`（遵守其 GET 护栏）；
  5. 断言见 V-22。
- 预期：探测 exit 0；脚本结束时 cleanup 自动运行（无论探测成败）。限制：夹具账号手机号为 `1990000xxxx` 预留号段，不在业主清册中，所以**无法远程验证真实"认证→席位绑定"流程**（M-DE-038）；管理员接口（席位、清册排序、owner-candidates）无夹具管理员账号，不在此探测范围，其鉴权与路由由 V-05/V-06 覆盖；真实绑定靠本地用例（TC-E2E-1602/1603）与用户人工验证。
- 回滚: ROLLBACK-013

### DEPLOY-014: （可选，需单独授权）夹具清理后核对
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
```
- 预期：`status` 全 0，清册计数 = `REGISTRY_BASE`；`SEAT_COUNT` = `SEAT_BASE`（探测期间无写席位）。
- 回滚: ROLLBACK-014

## 回滚步骤（逆序）

**执行前核验变量（所有回滚通用）**：
```bash
TS=<DEPLOY-001 记录的 ANCHOR_TS>
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_OK || echo TS_BAD_STOP
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/webhash-$TS.sha256 /home/yangyang/ocap/snapshots/backendhash-$TS.sha256 /home/yangyang/ocap/snapshots/migplan-$TS.txt /home/yangyang/ocap/snapshots/seat_membership-$TS.sql /etc/nginx/sites-available/ocap.bak_$TS"
$OCAP_SSH "tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | grep -c '^backend/manage.py\$'; tar tzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html\$'"      # 各须为 1
```
7 个文件都存在且两个计数为 1 才继续。`AUX_ACTIVE`、`OWN`、`ENV_SHA` 取自 PRE-T 记录。远端命令一律双引号使 `$TS` 在本地展开，执行前 `echo` 完整命令核对。**禁止** `git reset --hard`、`git clean`、`git stash`、覆盖式 rsync、`rm -rf backend`；**不动** `backend/.env`、`backend/.env.*`、`backend/venv`、`backend/var`（附件）、`snapshots/` 中任何既有文件、Freeark 的 nginx 配置与服务。回滚只对 `ocap-backend`、`AUX_ACTIVE` 单元与 nginx（reload）做 systemctl 操作，不 `restart` nginx，不动任何 `freeark-*` 服务。

### ROLLBACK-014: 回滚 DEPLOY-014
- 无操作（只读核对）。

### ROLLBACK-013: 回滚 DEPLOY-013（清理 `e2e_` 夹具）
- 类型：正式回滚（兜底；探测脚本自身的 `trap` 已清理时此步为复核）
- 命令：
```bash
F='cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture'
echo "$F"
$OCAP_SSH "$F cleanup --execute"
$OCAP_SSH "$F status"
```
- 变量取值与核验：`F` 为常量字符串，无 `$`；`status` 须全 0 且清册计数 = `REGISTRY_BASE`。夹具删除只作用于 `e2e_` 前缀用户及其数据；不触碰清册与非 `e2e_` 数据。

### ROLLBACK-012: 回滚 DEPLOY-012
- 无操作（只读预览）。

### ROLLBACK-011: 回滚 DEPLOY-011
- 无操作（临时文件已清理是预期终态；需要时可从本地 `$SCRATCH` 重新上传）。

### ROLLBACK-010: 回滚 DEPLOY-010（恢复 nginx 配置并 reload）
- 类型：正式回滚（恢复备份 → 语法检查 → reload；reload 必须在恢复之后，故本步包含恢复动作，幂等）
- 命令：
```bash
CMD="sudo cp -p /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap && sudo diff /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap && echo NGINX_RESTORED_IDENTICAL; sudo nginx -t 2>&1 && sudo systemctl reload nginx && systemctl is-active nginx && sudo sed -n 5p /etc/nginx/sites-available/ocap && curl -s -m 10 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` = DEPLOY-001 的 `ANCHOR_TS`，上节核验通过；备份由 `sudo cp -p` 在 DEPLOY-001 生成。若 `cp` 目标是软链，`cp` 写入链接指向的真实文件（不替换软链）。
- 预期：`NGINX_RESTORED_IDENTICAL`；`syntax is ok`；`active`；第 5 行回到 `client_max_body_size 20m;`；8080 返回 `200`；不 `restart`。`nginx -t` 失败 → 停止，`ROLLBACK_FAILED`（此时运行中的 nginx 仍是旧 worker 配置，勿 restart，人工处理）。

### ROLLBACK-009: 回滚 DEPLOY-009（恢复 ocap 站点配置文件，不 reload）
- 类型：正式回滚；**仅在 DEPLOY-009 执行过而 DEPLOY-010 未执行时单独使用**（已执行 010 时，ROLLBACK-010 已包含恢复，本步退化为校验）。
- 命令：
```bash
CMD="sudo cp -p /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap && sudo diff /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap && echo NGINX_RESTORED_IDENTICAL; sudo nginx -t 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：`NGINX_RESTORED_IDENTICAL`；`syntax is ok`；未 reload，运行中的 nginx 配置本就未改变。

### ROLLBACK-008: 回滚 DEPLOY-008（恢复旧 Web 静态目录）
- 类型：正式回滚（切回上一版本制品）
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && cd /home/yangyang/ocap/web/ocap && sha256sum -c /home/yangyang/ocap/snapshots/webhash-$TS.sha256 | grep -v ': OK'; echo HASH_CHECK_DONE; find /home/yangyang/ocap/web/ocap -type f | wc -l"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` 同上；仅解包快照内 `web/ocap`。
- 预期：输出中**只出现** `HASH_CHECK_DONE`，不得有非 `OK` 行（否则 `ROLLBACK_FAILED`）；文件数 = 哈希清单行数；公网 `index.html` SHA256 = PRE-T12 旧值（`curl -s -m 15 https://ai-freeark.xin/ocap/ | sha256sum`）。

### ROLLBACK-007: 回滚 DEPLOY-007（停止后端与辅助单元，为迁移回退腾出窗口）
- 类型：正式回滚
- 命令：
```bash
CMD="for u in $AUX_ACTIVE; do sudo systemctl stop \$u; done; timeout 30 sh -c 'while systemctl is-active --quiet ocap-run-due-jobs.service; do sleep 1; done'; sudo systemctl stop ocap-backend; systemctl is-active ocap-backend $AUX_ACTIVE"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：全部 `inactive`。该步在 ROLLBACK-005/004 之前执行，避免新代码在表结构回退/文件被替换期间服务请求或定时任务写入。

### ROLLBACK-006: 回滚 DEPLOY-006（往返验证）
- 类型：无独立操作。往返的终态要么是"0002/0005 已应用"（由 ROLLBACK-005 回退覆盖），要么是中途状态（同样由 ROLLBACK-005 的 `migrate` 命令收敛，幂等）。

### ROLLBACK-005: 回滚 DEPLOY-005（撤销迁移 residency 0005、committee 0002）
`[MANUAL_ROLLBACK_REQUIRED（条件触发）: ① committee_seat 存在 user 为空的待绑定席位（含已撤销/失效的，只要 user 仍为空）时，`migrate committee 0001` 将 Seat.user 改回非空会失败；这些席位在旧代码下也会使席位读取出错。须转储后由人决定删除（见下）。② 回退会 DROP holder_owner/holder_unit_text/holder_name/bound_at/bind_conflict_at 与 residency_membership.registry_owner 列，其中的值（持有人快照、认证核对关联）无法恢复，仅可从转储与迁移前快照核对。③ 迁移中途失败导致半应用结构时，Django 迁移记录与实际结构不一致，须人工比对 schema_check 输出与 seat_membership-<TS>.sql 后再处理，不自行猜测。]`
- 类型：正式回滚；**必须在 ROLLBACK-004 恢复旧代码之前执行**（旧代码没有 0002/0005 文件，无法反向迁移）。顺序固定为 007 → 005 → 004。**不得跳过迁移回退而只回退代码**（见"目标环境与策略"）。
- 步骤 1（只读门控）：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
```
  读取 `SEAT_USER_NULL_ROWS`：
  - `0` → 直接执行步骤 3。
  - `> 0` → **暂停，返回 BLOCKED 等人决定**（不自行处理）。人确认后按步骤 2 先转储再删除，**或**选择中止回滚、保持新版本运行（人工决定）。
- 步骤 2（仅在人确认后执行；此时新代码仍在磁盘上，ORM 可用）：先转储当前席位表（含待绑定行，仅用户 ID/职位/日期/持有人快照字段，chmod 600），再删除空 user 行：
```bash
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && MYSQL_PWD=\"\$DB_PASSWORD\" mysqldump -h \"\$DB_HOST\" -P \"\${DB_PORT:-3306}\" -u \"\$DB_USER\" --skip-ssl \"\$DB_NAME\" committee_seat > /home/yangyang/ocap/snapshots/seat_pending_rollback-$TS.sql && chmod 600 /home/yangyang/ocap/snapshots/seat_pending_rollback-$TS.sql && ls -l /home/yangyang/ocap/snapshots/seat_pending_rollback-$TS.sql"
echo "$CMD"; $OCAP_SSH "$CMD"
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.committee.models import Seat; qs = Seat.objects.filter(user__isnull=True); print(\"DELETING\", qs.count()); print(\"DELETED\", qs.delete()[0])"'
```
  （双引号内 `\$` 使 `DB_*` 在远端从 `.env` 展开，`$TS` 在本地展开；口令经环境变量传给 mysqldump，不进 argv；输出不得打印变量值。删除的是"尚未绑定到任何注册用户"的席位记录；业主日后在新版本重新部署后可由管理员重新授予。对应的审计记录保留，不删除。）
- 步骤 3（`SEAT_USER_NULL_ROWS` = 0 或步骤 2 完成后）：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency 0004 --noinput 2>&1 | tail -4; venv/bin/python manage.py migrate committee 0001 --noinput 2>&1 | tail -4; venv/bin/python manage.py showmigrations committee residency'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell' < "$SCRATCH/schema_check.py"
```
- 预期：`Unapplying residency.0005… OK`、`Unapplying committee.0002… OK`（已是旧状态时 `No migrations to apply`）；`showmigrations`：`residency` 0005 与 `committee` 0002 为 `[ ]`；`schema_check`：`SEAT_USER_NULL_OK False`、`SEAT_NEW_COLS []`、`UNIQ_OWNER_CONSTRAINT False`、`MEMBERSHIP_REGISTRY_OWNER_COL False`；`SEAT_COUNT` = `SEAT_BASE`（无待绑定删除时）、`MEMBERSHIP_COUNT` = `MEM_BASE`（回滚期间无写入）。先 residency 后 committee 的顺序使步骤 1 的门控先于任何结构变更。

### ROLLBACK-004: 回滚 DEPLOY-004（恢复后端代码、删除新增文件并启动）
- 类型：正式回滚（叠加解包，不删除目录；M-DE-011）
- 命令：
```bash
CMD="sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap && sudo rm -f /home/yangyang/ocap/backend/apps/committee/binding.py /home/yangyang/ocap/backend/apps/registry/listing.py /home/yangyang/ocap/backend/apps/committee/migrations/0002_seat_registry_holder.py /home/yangyang/ocap/backend/apps/residency/migrations/0005_membership_registry_owner.py && cd /home/yangyang/ocap/backend && sha256sum -c /home/yangyang/ocap/snapshots/backendhash-$TS.sha256 | grep -v ': OK'; echo HASH_CHECK_DONE; test -f .env && test -d venv && test -d var && sha256sum .env && ls .env.bak_* 2>/dev/null | wc -l"
echo "$CMD"; $OCAP_SSH "$CMD"
CMD2="cd /home/yangyang/ocap/backend && find . -type f -path './tests/*' -not -path '*/__pycache__/*' | sort > /tmp/cur_tests_$TS.txt && awk '{print \$2}' /home/yangyang/ocap/snapshots/backendhash-$TS.sha256 | grep '^\./tests/' | sort > /tmp/old_tests_$TS.txt && comm -13 /tmp/old_tests_$TS.txt /tmp/cur_tests_$TS.txt"
echo "$CMD2"; $OCAP_SSH "$CMD2"
```
  上面第二条只**列出**快照中不存在、本批新增的 `./tests/` 下文件（应全是 `test_batch1118_*.py` 等新测试）；E2 确认列表只含 `./tests/` 路径后，执行 `$OCAP_SSH "cd /home/yangyang/ocap/backend && comm -13 /tmp/old_tests_$TS.txt /tmp/cur_tests_$TS.txt | xargs -r rm -f && rm -f /tmp/cur_tests_$TS.txt /tmp/old_tests_$TS.txt"`（路径来自快照差集且限定 `./tests/` 前缀，不是通配符，也不是 `git clean`）。随后启动：
```bash
$OCAP_SSH "sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend; for u in $AUX_ACTIVE; do sudo systemctl start \$u; done; systemctl is-active $AUX_ACTIVE"
$OCAP_SSH "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -20"
$OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/committee/binding.py /home/yangyang/ocap/backend/apps/registry/listing.py /home/yangyang/ocap/backend/apps/committee/migrations/0002_seat_registry_holder.py /home/yangyang/ocap/backend/apps/residency/migrations/0005_membership_registry_owner.py 2>&1'
```
- 变量取值与核验：`TS` 同上；`rm -f` 的 4 个路径是固定常量（本批新增的 4 个后端文件，来自 PRE-A08），不是通配符，也不是 `git clean`；解包用 `sudo`（快照由 `sudo tar` 生成，可能含 root 属主文件）。解包后旧代码的 `__pycache__` 中残留的新文件 `.pyc` 无害（无源文件时 Python 不加载）。
- 预期：输出**只出现** `HASH_CHECK_DONE`（备份清单逐文件均 `OK`，说明代码已回到部署前；清单不含 `venv/var/.env*`，故不校验它们）；`.env` SHA256 = `ENV_SHA`；`.env.bak_*` 个数 = `ENVBAK_N`；`active`；日志无 `Traceback`；最后一条 `ls` 四项均 `No such file or directory`。非 `OK` 行 → 停止，`ROLLBACK_FAILED`。

### ROLLBACK-003: 回滚 DEPLOY-003（清理暂存与上传文件）
- 类型：正式回滚；命令同 DEPLOY-011，预期四项 `No such file or directory`；`TS` 须通过格式校验，路径写全、无通配符。

### ROLLBACK-002: 回滚 DEPLOY-002（本地构建与打包）
- 类型：无目标机操作。`frontend/dist` 为 gitignore 的构建产物；本地 `$SCRATCH` 在结束清理时删除（先校验非空且前缀正确）。

### ROLLBACK-001: 回滚 DEPLOY-001
- 类型：无操作。快照、哈希清单、`migplan-$TS.txt`、`seat_membership-$TS.sql`、`ocap.bak_$TS` 保留 ≥ 7 天，不删除。

## 不可逆步骤汇总

| 步骤 | 说明 | 标记 |
|---|---|---|
| DEPLOY-005 / ROLLBACK-005 | `committee 0002` 回退：`Seat.user` 改回非空，存在 user 为空的席位时失败；人工决定转储后删除这些待绑定席位（可由管理员重新授予）；回退 DROP 5 个席位新列与 `Membership.registry_owner` 列，其值不可恢复；迁移半应用须人工核对 | `[MANUAL_ROLLBACK_REQUIRED]`（条件触发） |
| 部署后用户/管理员操作 | 管理员授予的待绑定席位、业主认证后已绑定的席位（回滚后在旧代码下为普通席位，user 非空）、`SEAT_GRANTED/SEAT_BOUND/SEAT_BIND_CONFLICT/SEAT_INVALIDATED` 审计记录、申诉与附件，不随代码回滚撤销；回滚代码不会取消已发生的认证与席位绑定 | 记录为遗留事项，非 DEPLOY 步骤 |
| 定时任务到期执行 | 新代码窗口内 `run_due_jobs` 若已执行，其 `expire_due`/`reconcile_registry_seats` 对席位的失效、到期置状态不随回滚撤销 | 同上 |
| DEPLOY-009/010 nginx | 可逆（恢复备份 + `nginx -t` + reload，ROLLBACK-010）；reload 期间已被旧 worker 接受的请求不受影响 | 可自动回滚 |

无外部系统调用、无通知发送、无个人信息文件生成（转储只含用户 ID 与席位/成员关系字段，权限 600，保留 ≥ 7 天后由用户决定清理）。

## 部署后验证

执行时机：后端类（V-01~V-10、V-21）在 DEPLOY-007 之后、DEPLOY-008 之前；前端类（V-11~V-15）在 DEPLOY-008 之后；nginx 与共存类（V-16~V-18）在 DEPLOY-010 之后；本地状态类（V-19、V-20）最后；V-22/V-23 在 DEPLOY-013/014 之后；均在 DEPLOY-011 之前。公网检查在开发机/主会话用 `curl -m 15`（M-DE-022：不用 `pkill -f`；内网 `192.168.31.51:8090` 外网不可达，改在目标机内 `curl 127.0.0.1:8090`）。**SPA 回退陷阱（M-DE-029）**：`/ocap/` 下不存在的静态路径也返回 200 + `index.html`，静态资源的判据是"内容类型 + 大小 + SHA256"，不是 200。

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| V-01 后端已重启并存活 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'` | `active`；时间戳与 PID 均不同于 PRE-T06 |
| V-02 后端日志无新错误 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager \| grep -ciE 'Traceback\|ERROR'"` | 输出 `0` |
| V-03 迁移已应用（M-7） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations committee residency \| tail -12; venv/bin/python manage.py showmigrations --plan \| grep -c "^\[ \]"'` | `committee.0002_seat_registry_holder`、`residency.0005_membership_registry_owner` 为 `[X]`；未应用计数 `0` |
| V-04 表结构事实（M-7） | 运行 `schema_check.py`（见上） | `SEAT_USER_NULL_OK True`；`SEAT_NEW_COLS` 含 5 列；`UNIQ_OWNER_CONSTRAINT True`；`MEMBERSHIP_REGISTRY_OWNER_COL True`；`SEAT_COUNT` = `SEAT_BASE`、`MEMBERSHIP_COUNT` = `MEM_BASE`；`SEAT_USER_NULL_ROWS 0`（既有席位 user 非空不受影响） |
| V-05 新路由已解析 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.urls import resolve; [print(p, resolve(p).func.view_class.__name__) for p in (\"/api/v1/resolutions/1/participants\", \"/api/v1/admin/committee/owner-candidates\", \"/api/v1/admin/committee/seats\", \"/api/v1/admin/registry/units\", \"/api/v1/admin/registry/unit-options\", \"/api/v1/appeals\", \"/api/v1/me/housing\")]"'` | 依次解析到 `ResolutionParticipantsView`、`AdminOwnerCandidatesView`、`AdminSeatListCreateView`、`AdminUnitListView`、`AdminUnitOptionsView`、`AppealListCreateView`、`MyHousingView`（均无 404） |
| V-06 接口鉴权（无令牌、只读，经公网前缀） | `for p in '/resolutions?scope=public' '/resolutions/1/participants' '/me/housing' '/admin/registry/units?sort=floor&order=asc' '/admin/registry/unit-options' '/admin/committee/owner-candidates?unit_id=1' '/admin/committee/seats'; do curl -s -m 15 -o /dev/null -w "$p %{http_code} %{content_type}\n" "https://ai-freeark.xin/ocap/api/v1$p"; done`；`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type}\n' -X POST -H 'Content-Type: application/json' -d '{}' https://ai-freeark.xin/ocap/api/v1/appeals` | 7 个 GET 与 POST 均 `401`（或 `403`）且为 JSON；**不是** `404`/`405`/`5xx`/`text/html`（证明前缀、路由与 JSON 分支入口生效）；不创建数据 |
| V-07 登录接口可用（错误凭据，唯一化） | `$OCAP_SSH "curl -s -m 15 -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400`（`LOGIN_FAILED`）；不创建数据 |
| V-08 后端上线文件与本地一致 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && sha256sum apps/committee/binding.py apps/registry/listing.py apps/committee/migrations/0002_seat_registry_holder.py apps/residency/migrations/0005_membership_registry_owner.py apps/committee/services.py apps/resolutions/views.py apps/residency/views.py apps/jobs/views.py'`；对照本地 `sha256sum` 同名文件 | 逐项相同 |
| V-09 定时任务恢复并正常执行（含时区修复与清册失效步骤） | 仅当 `AUX_ACTIVE` 含 `ocap-run-due-jobs.timer`：`$OCAP_SSH 'systemctl is-active ocap-run-due-jobs.timer; systemctl list-timers --no-pager \| grep ocap-run-due-jobs; sleep 75; systemctl show ocap-run-due-jobs.service -p Result -p ExecMainStatus; sudo journalctl -u ocap-run-due-jobs.service --since "-3 min" --no-pager \| grep -ciE "Traceback\|ERROR"'` | `active`；NEXT 非 `n/a`；等一次定时触发后 `Result=success`、`ExecMainStatus=0`；日志错误计数 `0`。不额外手动执行任务（避免多余的真实任务运行）。`AUX_ACTIVE` 为空则标"不适用" |
| V-10 小程序后端兼容（只读） | 本地：PRE-A09 输出（小程序零改动、契约用例 OK、`votes` 引用计数、调用路径清单）；线上：V-06 中 `/resolutions?scope=public`、`/me/housing`、`POST /appeals`（JSON）均为 401 JSON | 小程序调用的路径在新后端均存在且鉴权行为不变（401 而非 404/405）；小程序源码无读取决议 `votes`；结构层兼容由 GROUP_D 契约/回归用例（TC-INT-1130~1134 与小程序既有 135 条）证明，E2 不另做带令牌的线上结构检查（可选的 V-22 仅覆盖 `e2e_` 账号可读部分） |
| V-11 线上 index.html = 本地构建 | `curl -s -m 15 https://ai-freeark.xin/ocap/ \| sha256sum`；对照本地 `sha256sum frontend/dist/index.html` | 相同 |
| V-12 入口与静态资源 | 内网：`$OCAP_SSH 'curl -s -m 15 -o /dev/null -w "%{http_code} %{content_type}\n" http://127.0.0.1:8090/ocap/'`；公网：`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/`；对 `index.html` 引用的 `/ocap/assets/index-*.js`、`index-*.css` 各：`curl -s -m 15 -o "$SCRATCH/a" -w '%{http_code} %{content_type} %{size_download}\n' <URL>` 并 `sha256sum "$SCRATCH/a"` | 入口 `200 text/html`，大小 = 本地 `dist/index.html`；js `200` 含 `javascript`、css `200 text/css`（不是 `text/html`）；SHA256 = 本地 `dist` 同名文件 |
| V-13 新前端含新接口与正确前缀 | `$OCAP_SSH 'for k in owner-candidates unit-options participants; do echo $k $(grep -l "$k" /home/yangyang/ocap/web/ocap/assets/*.js \| wc -l); done; grep -c "/ocap/api/v1" /home/yangyang/ocap/web/ocap/assets/index-*.js'` | 三个关键字各 ≥ 1；前缀计数 ≥ 1（M-DE-034） |
| V-14 深链刷新可达 | 对下列路径各：`curl -s -m 15 -o "$SCRATCH/d" -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap<路径>` 并 `sha256sum "$SCRATCH/d"`：`/resolutions`、`/resolutions/mine`、`/resolutions/todo`、`/polls`、`/units/appeal`、`/admin/registry`、`/admin/seats` | 7 条均 `200 text/html`，大小与 SHA256 = `index.html`（证明 `try_files … /ocap/index.html`） |
| V-15 目标机落盘状态 | `$OCAP_SSH 'stat -c "%U:%G %a %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html; find /home/yangyang/ocap/web/ocap -type f \| wc -l; ls -l /home/yangyang/ocap/snapshots/web-*.tar.gz /home/yangyang/ocap/snapshots/backend-*.tar.gz \| tail -4'` | 属主 = `OWN`；`index.html` 权限 644；文件数 = 本地 `dist`；本次快照存在 |
| V-16 nginx 改动与 reload 结果（M-6 的服务端部分） | `$OCAP_SSH "sudo diff /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/ocap; sudo sed -n 5p /etc/nginx/sites-available/ocap; sudo nginx -t 2>&1 \| tail -2; systemctl is-active nginx; systemctl show nginx -p MainPID; sudo nginx -T 2>/dev/null \| grep -nE '^# configuration file\|client_max_body_size'"` | 差异恰为第 5 行 20m→60m；第 5 行为 `client_max_body_size 60m;`；`syntax is ok`；`active`；`MainPID` = `NGX_PID`；`nginx -T` 过滤输出中 ocap 站点为 60m、Freeark 的值与 PRE-T11 记录**完全相同**（未被改动） |
| V-17 上传上限真实生效（无令牌合成请求，不写数据；M-6 的辅助证据，不替代用户的真实上传） | `$OCAP_SSH "head -c 58000000 /dev/zero > /tmp/ocap_probe_v17_58m.bin && head -c 63000000 /dev/zero > /tmp/ocap_probe_v17_63m.bin && for u in http://127.0.0.1:8090/ocap/api/v1/appeals http://127.0.0.1:<FREEARK_PORT>/ocap/api/v1/appeals; do curl -s -m 90 -o /dev/null -w \"58M \$u %{http_code} %{content_type}\n\" -X POST -H 'Content-Type: application/octet-stream' --data-binary @/tmp/ocap_probe_v17_58m.bin \$u; done; curl -s -m 90 -o /dev/null -w '63M 8090 %{http_code}\n' -X POST -H 'Content-Type: application/octet-stream' --data-binary @/tmp/ocap_probe_v17_63m.bin http://127.0.0.1:8090/ocap/api/v1/appeals; rm -f /tmp/ocap_probe_v17_58m.bin /tmp/ocap_probe_v17_63m.bin"`（`<FREEARK_PORT>` 取 PRE-T11 记录的 `ai-freeark.xin` 监听端口） | 58 MB：ocap 站点 8090 与 Freeark 反代入口均为 `401`（或 `403`）JSON——到达后端被鉴权拒绝，**不是 413、不是 502/504**；63 MB（> 60m = 62914560 字节）经 8090 为 `413`（反证上限是 60m 而非失控放开）；对照 PRE-T13 的 413 说明改动生效。无令牌，后端不解析 body，不创建数据，临时文件用后即删 |
| V-18 Freeark 与端口未受影响 | `curl -s -m 15 -o /dev/null -w '%{http_code}\n' https://ai-freeark.xin/`；`$OCAP_SSH 'curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/; systemctl --state=failed --no-pager; ss -ltn'` | 公网首页 `200`、8080 `200`（reload 前后均 200，对照 PRE-T11/T12 与 DEPLOY-010）；无 `freeark-*`、`ocap-*` 失败单元；8000/8080 属 Freeark，8090/9000 属 ocap |
| V-19 本地状态未被触碰 | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && test -d /home/yangyang/ocap/backend/venv && test -d /home/yangyang/ocap/backend/var && echo LOCAL_STATE_INTACT; sha256sum /home/yangyang/ocap/backend/.env; ls /home/yangyang/ocap/backend/.env.bak_* 2>/dev/null \| wc -l; ls -l /home/yangyang/ocap/snapshots/ \| grep -cE "ocapdb-\|underground-\|shops-\|residency_appeal-"'` | `LOCAL_STATE_INTACT`；`.env` SHA256 = `ENV_SHA`；`.env.bak_*` 个数 = `ENVBAK_N`；既往个人信息备份仍在（计数 ≥ PRE-T04 记录值）；`var/` 附件目录未被替换 |
| V-20 依赖与 `.env` 键未变 | `$OCAP_SSH 'sha256sum /home/yangyang/ocap/backend/requirements.txt'` | = 本地 `requirements.txt` SHA256（= PRE-T07 值） |
| V-21 M-7 迁移往返记录与计划差异 | DEPLOY-006 输出；`$OCAP_SSH "cat /home/yangyang/ocap/snapshots/migplan-$TS.txt" > "$SCRATCH/migplan_before_$TS.txt"; diff "$SCRATCH/migplan_before_$TS.txt" "$SCRATCH/migplan_after_$TS.txt"` | 记录回退→重迁全过程与两次 `schema_check` 输出；计划差异仅 `committee.0002`、`residency.0005` 两行；若因待绑定席位而跳过，如实标"部分完成" |
| V-22 （可选，DEPLOY-013）`e2e_` 账号只读探测 | `e2e_probe.py`（GET，经 `https://ai-freeark.xin/ocap/api/v1`）：(a) `e2e_owner_a` 登录后 `GET /me/housing` → 200，顶层键含 `real_names`（列表）；每个 `units[]` 项含 `co_owners`（列表）；响应无 11 位连续数字；(b) `GET /resolutions?scope=public` → 200；每条无 `votes` 键；`initiator` 含 `display_name`；HALF_MAJORITY 项含 `participation={voted,expected}`；(c) 对任一可见决议 `GET /resolutions/{id}/participants` → 200，键集合恰为 `{mode,count,results}`，每项键恰为 `{display_name,avatar_url,voted_at}`；(d) `e2e_guest` 同 (a) 的 `/me/housing` → `real_names=[]`、`units=[]` | 全部通过；输出只含通过/失败与计数，不含响应体、口令、令牌；未授权则标"未执行" |
| V-23 （可选，DEPLOY-014）夹具清理 | DEPLOY-014 输出 | `status` 全 0；清册计数 = `REGISTRY_BASE`；`SEAT_COUNT` = `SEAT_BASE`；脚本日志含 `cleanup` 已执行 |

全部通过 → `DEPLOYED_SUCCESSFULLY`（交付最终状态仍受下列人工项影响）；部分失败 → `DEPLOYED_WITH_ISSUES`，列失败项，由用户决定是否回滚（不自行回滚，除非步骤本身失败，按 E2 规则）。V-17 若 8090 通过而 Freeark 反代入口返回 413，说明 Freeark 的 `/ocap/` 块未达 60m，与 PM 核实值不符：**不得自行修改 Freeark**，列为失败项交 PM/用户。

## 人工验证清单（部署后由用户执行，**不由部署脚本执行**）

来源：`testing/e2e_test_report.md`（1.0.0 APPROVED）与 GR-D-001 condition。E2 在报告中只引用，不代为验收；未全部完成前最终交付状态至多 DELIVERED_WITH_ISSUES（协议 §K，critical path 的 M-1~M-3 未完成）。建议用**强制刷新**在公网入口 `https://ai-freeark.xin/ocap/` 执行；写操作超出 P4-1 的部分由用户用自己的账号完成。

| 编号 | 对应 AC | 做法（摘要） | 期望 | 执行人 |
|---|---|---|---|---|
| M-1 | AC-252-02、AC-253-02/03/06、REQ-NFUNC-047 | 三套风格（neon/bento/terminal）下悬停并按下公开决议、我发起的、待我表决与投票/调查卡片；展开/收起左侧"我的房屋/决议"，切换选中二级项；窄屏（<768px）切换条切换选中项 | 卡片悬停抬升+阴影、按下缩放；展开/收起平滑；选中指示条出现且仅 1 项；三套风格均可见、不错位、文字可读 | 用户（桌面浏览器 + 手机宽度模拟） |
| M-2 | AC-252-05、AC-253-04 | 系统开启"减少动态效果"后重复 M-1 | 无位移与过渡动画，点击与展开/选中功能照常 | 用户 |
| M-3 | AC-252-01、AC-252-03 | 点击决议卡片空白处、状态标签、进度条、发起人文字（三个决议页与投票/调查页）；点击卡片内附件链接/按钮 | 前者进入 `/resolutions/{id}`（或 `/polls/{id}`）；附件链接/按钮只触发自身动作 | 用户 |
| M-4 | AC-252-04、AC-246-05 | 键盘：Tab 聚焦卡片并按 Enter；专有部分下拉方向键选择并回车 | 进入详情页且有可见焦点；下拉可键盘选中 | 用户（辅助） |
| M-5 | AC-250-06 | 读屏软件聚焦参与进度条 | 朗读"已参与 4 / 7，同意 3，反对 1，弃权 0" | 用户（辅助） |
| M-6 | AC-244-02（部署侧） | 部署后在真实浏览器登录，到认证申诉页，选足够多的专有部分、姓名，暂存 5 份各约 10 MB 的 jpg/png/pdf，点"提交"（会写入一条真实申诉，由用户自己的账号与后续处理负责；`e2e_` 账号走 P4-1 的范围另议） | 提交成功 201，不被 413/超时拦截（nginx ocap 站点与 Freeark `^~ /ocap/` 块均 ≥ 55 MB，gunicorn `--timeout` 见 PRE-T06 记录）；E2 的 V-16/V-17 为服务端辅助证据 | 用户（真实浏览器）；**人工** |
| M-7 | `committee 0002` / `residency 0005` | 由 **E2 在 DEPLOY-005/006 + V-03/V-04/V-21 执行并记录输出**（测试机 MySQL 迁移前进、回退、重迁） | 见 V-21；既有席位 user 非空不受影响 | E2 |
| M-8 | AC-244-03 | 真实浏览器：选 2 个文件后刷新/关闭页面，在网络面板观察 | 全程无附件上传请求；重新进入暂存区为空 | 用户 |

另：**小程序**本批不改、不需上传体验版；若用户想复核兼容，可用现有体验版打开公开决议页，预期可见进行中决议、详情不报错（`votes` 已移除，小程序不读取）；此项不属 E2。

## 自检记录

- 每个 DEPLOY（001~014）均有对应 ROLLBACK（001~014），按编号逆序排列；回滚实际执行顺序固定为 014 → 013 → … → 011（无操作）→ 010（恢复 nginx 并 reload）→ 009（校验/仅恢复文件）→ 008（还原前端）→ 007（停后端与辅助单元）→ 005（先 `migrate residency 0004`、再 `committee 0001`，含条件人工）→ 004（还原代码、删新增文件、启动）→ 003（清暂存）；ROLLBACK-006 为"由 005 覆盖"的无独立操作；ROLLBACK-010 因 reload 必须在文件恢复之后而包含恢复动作，ROLLBACK-009 退化为校验或"未 reload 时的恢复"。
- 不可逆/不可自动回滚项：ROLLBACK-005 条件性 `[MANUAL_ROLLBACK_REQUIRED]`（待绑定席位、列值丢失、迁移半应用）；已列于汇总表，并在 DEPLOY-005 处醒目标出。
- 依赖顺序：基础设施无变化 → 数据层（DEPLOY-005/006，先于任何新代码服务）→ 服务层（004、007）→ 前端（008）→ nginx（009/010）→ 清理；后端先于前端，nginx 最后。
- 环境仅为画像 P7「测试」；策略 recreate 已写理由；无 Docker、pscp 逐文件、makemigrations 产物、目标机生成迁移；Freeark 仅只读核对，nginx 仅改 ocap 自身站点第 5 行并 reload（用户 2026-11-18 Q1=A）。
- 回滚不使用 reset/clean/stash/覆盖式 rsync/`rm -rf backend`；不动 `.env`、`.env.*`、`venv`、`var`、既有快照；变量 `TS`、`OWN`、`ENV_SHA`、`ENVBAK_N`、`NGX_PID`、`AUX_ACTIVE`、`SEAT_BASE`、`MEM_BASE`、`REGISTRY_BASE` 均写了取值来源与核验方法；远端命令用双引号并要求先 `echo`；`\$` 与单引号嵌套已标注；`set -e` 脚本中 `grep -c` 计数可能为 0 处已加 `|| true`；`SCRATCH`/`CM` 先 `mktemp` 并校验非空；`mysqldump` 口令经环境变量，不进 argv，输出不含凭据。
- 快照排除 `.env`、`.env.*`、`venv`、`var`（上批偏差 1）；`makemigrations --check` 用临时 settings（上批偏差 2）；远程探测（P4-1）默认不必做，已标"可选，需单独授权"。
- `[INFERRED]` 汇总：后端停机约 1~3 分钟；前端替换与 nginx reload 窗口；表名 `committee_seat`/`residency_membership`（PRE-T08 实测门控）；`ocap-content-worker.service` 是否在目标机存在与 active（PRE-T09 实测）；Freeark 入口监听端口（PRE-T11 实测，推定 8080）；`mysqldump` 与 sudo 免密可用（PRE-T10 实测）；无令牌 58 MB POST 在 nginx 放行后由后端返回 401（V-17 以实测为准）；/tmp 空间需求 ≥ 200 MB（PRE-T02）。
- 遗留/风险：(1) 本批未提交且 CI 未跑，版本以 SHA256 定位；(2) 远程无法验证真实"认证→席位绑定"流程（夹具手机号不在清册，M-DE-038）与管理员接口的带令牌结构，靠本地 1119 条用例（TC-E2E-1602/1603 等）与用户人工验证；(3) CR-012（`claims/services.py:19,40` `decided_at.date()` 取 UTC 日期）为既有观察项，不在本批范围；(4) 目标机 `backend/` 内既有 `.env.bak_*` 含 env 内容的副本，本批排除出快照，建议用户择机确认是否保留；(5) 席位表转储与上批个人信息备份一样保留 ≥ 7 天后由用户决定清理。
- 子代理 E1 未执行 ssh/scp/commit/push，未安装依赖、未联网、未改 CI 与仓库代码；只读取了仓库文件，并做了本地 `git status`/`ls`/`head` 只读核对。
