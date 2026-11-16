<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-16T19:25:19+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
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

# 部署计划：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽

> 本计划只描述步骤，不构成任何授权。子代理不得 ssh（画像 P9）；所有远端命令由 GROUP_E2（用户当轮授权后）或主会话执行，每条 ssh/scp 仍经 `.claude/settings.json` 的 ask 规则确认。凭据只写位置不写值。本计划以 `ocap_unit_sort_filters` 的五段计划与实际执行报告为模板，并吸收其偏差（见「吸收的上批偏差」）。

## 授权点总表（五个阶段各自独立授权）

每个阶段都需要**用户当轮**明确授权；PM 在该阶段 invocation 的 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true`、目标环境「测试」、阶段名与所需输入。上一阶段的授权**不延续**；每阶段结束后 PM 向用户汇报，得到新一轮授权才进入下一阶段。顺序固定 A -> B -> C -> D -> E（先归类再导出，避免导出旧结构）。

| 阶段 | 内容 | 步骤 | 写目标机状态 | 用户当轮需授权的点 | 执行人 |
|---|---|---|---|---|---|
| A 代码部署 | 快照、`residency_appeal` 备份、后端上传解包、**migrate（residency 0003）**、重启、前端替换、只读冒烟 | DEPLOY-001~006 | 是（代码 + 库结构加 1 列） | 授权把本地提交 c32684b（未推送，以本地提交打包）部署到测试环境，含执行迁移；并明确小程序发布顺序（见下） | E2 |
| B dry-run | `relocate_shops` 默认模式（只读） | DEPLOY-007 | 否 | 授权在测试机对 ocap 库执行只读 dry-run | E2 或主会话 |
| C 商铺改库 | mysqldump + `relocate_shops --apply --backup --expect-changes N` | DEPLOY-008、009 | **是（改库）** | 用户看过 B 的结果，给出确认的 N（预期 107）并授权 apply | E2 或主会话 |
| D 导出 | 创建 700 目录、`export_registry_import_file --output-dir`、服务器侧核对；**文件保留在服务器** | DEPLOY-010~012 | 是（仅新增含个人信息的导出文件） | 授权在服务器生成含个人信息的导出文件并保留（用户 2026-11-16「保存在服务器上」）；若需 `--allow-gaps` / `--allow-unrelocated` 须另行同意 | E2 或主会话 |
| E 部署后验证 | 只读冒烟、P4-1 远程 E2E（仅 `e2e_`）、人工清单 | DEPLOY-013~015 + 验证表 | 是（仅 `e2e_` 数据，测完清理） | 授权创建/清理 `e2e_` 夹具并运行远程套件 | E2（夹具/清理）+ 主会话（HTTP） |

## 变更摘要

版本标识：部署提交 = 本地 `main` 的 `c32684b380e0e3cbce66e93bb58acb5972c750b1`（73 个文件，其中产品代码 20 个，**未推送**；推送需用户另行同意，P9）。目标机当前版本 = `15ea79ea51c87d56cd1cd8113cba81007649575a`（上批阶段 A 部署，已在 origin/main，回滚基线）。工作树另有与本批无关的未提交文档改动，不属于部署内容。

**打包来源（强制）**：后端用 `git archive` 取**提交 c32684b 的 `backend/` 树**（只含已提交跟踪文件，M-DE-012）；前端在工作树构建，预检要求 `frontend/` 相对 c32684b 无差异且无未跟踪文件。不得从未提交工作树打包后端。

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 商铺归类命令 MOD-111 / 常量 MOD-112 | `registry/shops.py`、`management/commands/relocate_shops.py`（新）、`registry/ordering.py`、`registry/underground.py` | 无（刻意不做迁移，ADR-107） | 无 | `ocap-backend` 重启；命令一次性，随代码到达，**不自动执行** |
| 导出命令 MOD-113 | `registry/exporting.py`、`management/commands/export_registry_import_file.py`（新增 `--output-dir`、位置守卫、未归类守卫） | 无 | 无 | 同上，一次性 |
| 清册追加 / 姓名比对 MOD-114 | `registry/ownership.py`（新） | 无 | 无 | `ocap-backend` 重启 |
| 认证 / 申诉 / 附件 MOD-115 | `residency/views.py`、`residency/models.py`、`residency/apps.py`、`migrations/0003_appeal_owner_name.py`（新） | **有：residency 0003（AddField owner_name，NOT NULL default ""，可逆）** | 无 | `ocap-backend` 重启 |
| 席位生效 MOD-116 | `committee/effective.py`（新）、`committee/services.py`、`committee/views.py`、`accounts/directory.py`、`accounts/views.py` | 无 | 无 | 同上 |
| Web 前端 MOD-117 | `AdminAppeals.vue`、`AdminSeats.vue`、`parts/ProofThumbs.vue`（新）、`Units.vue`、`UnitCascader.vue`、`shared/api.js` | — | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 静态目录 `/home/yangyang/ocap/web/ocap` 替换，nginx 不动 |
| 小程序 MOD-118 | `UnitPicker.vue`、`pages/units/index.vue`、`utils/api.js` | — | **用户用 HBuilderX/微信开发者工具构建、提交审核、发布（画像 P7 之外）** | 无服务端运行单元 |
| 新依赖 | 无（requirements、package.json 未变） | — | **跳过 pip install**，预检证明 | — |
| nginx / systemd / timer / Freeark | 不改 | — | — | 不触碰 |

数据迁移：有 1 项（见下）；测试环境数据修正（商铺 107 条）不走迁移，由阶段 C 单独授权执行。

**迁移要点（M-DE-005 的修正应用）**：`Appeal.owner_name` 为 `CharField(blank=True, default="")`，即 **NOT NULL**。Django 在 MySQL 上加列后会去掉列级 DEFAULT，旧代码（15ea79e）的 `Appeal.objects.create(...)` 不带该列，在 MySQL 严格模式下会失败 [INFERRED：Django MySQL 后端行为与严格模式，未在目标机实测；预检 PRE-A15 只读核对 `sql_mode`]。因此与"可空列只回退代码"的做法不同，**回滚必须执行 `migrate residency 0002`，且在恢复旧代码之前**。

## 目标环境与策略

- 环境：测试（画像 P7，树莓派；外网 SSH `-p 57279 yangyang@47.109.197.217`，首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报；内网 `192.168.31.51:22`）。画像中不存在其他环境，不设计晋升。
- 策略：**recreate**（单实例 gunicorn，无冗余，画像允许）。理由：无多实例/两套环境；后端重启约 2~5 秒不可用，前端为静态目录替换，迁移加一列在千行级表上瞬时完成。
- 预计停机：阶段 A 约 2~5 秒（重启）+ 解包到重启之间旧进程继续服务新文件的短暂混合窗口 [INFERRED，数秒]；阶段 B、D、E 无停机；阶段 C 为单个事务，数秒内完成 [INFERRED，随 N 而定]，服务不重启。

### 小程序发布顺序与兼容性（阶段 A 授权前须由用户确认）

事实（代码可核）：新后端 `POST /certifications` 缺 `name` 返回 `400 NAME_REQUIRED`（`residency/views.py:CertificationView`）；`POST /appeals` 缺 `owner_name` 同样 `400 NAME_REQUIRED`。**旧版小程序两个接口都不带新字段 → 部署新后端后，旧版小程序的"认证"与"申诉"都会收到 400**（其余功能不受影响）。新版小程序对旧后端：多发的 `name`/`owner_name` 被旧后端忽略，认证行为回到旧逻辑，申诉不受影响 [INFERRED：未实测，旧后端对 OWNER_NOT_MATCHED 的新错误码处理在新版小程序上未验证]。

| 顺序 | 做法 | 过渡期影响 | 评价 |
|---|---|---|---|
| **推荐 R1** | (1) 用户先构建新版小程序，**提交审核、审核通过后先不发布**（或先发体验版）；(2) 执行阶段 A 并通过验证；(3) 阶段 A 验证通过后**立即发布**新版；(4) 用体验版/新版真机验证认证与申诉 | 阶段 A 完成到新版发布之间（通常数分钟，取决于用户操作）：旧版小程序用户做认证/申诉得 400；微信客户端对旧版用户在下次冷启动时才切换到新版，**个别用户可能在更长时间内仍用旧版**（[INFERRED]，微信缓存策略以微信官方为准） | 窗口可控、可预期；测试环境用户少（上批报告：有效绑定 2 条）影响小 |
| R2 | 先发布新版小程序，再执行阶段 A | 旧后端 + 新版小程序期间：认证无姓名核对（姓名被忽略），申诉无产权人名字入库；新版在旧后端上的错误提示路径未验证 | 无 400 窗口，但行为未经验证，不推荐 |
| R3 | 阶段 A 与发布同一时间窗口手工配合 | 同 R1，窗口最短 | 需用户在线配合 |

附加说明：
1. **小程序构建在开发机不可用**（`uni build -p mp-weixin` 工具链既有问题，GR-C-001-F03、M-SD-006）。构建须由用户用 HBuilderX 或微信开发者工具完成；构建产物 `VITE_API_BASE` 指向哪个后端由用户构建时决定 [INFERRED：本计划不知道小程序正式版当前指向测试环境还是其他后端；若正式版不指向本测试后端，则旧版 400 的过渡影响只涉及指向它的体验版/开发版]。
2. 小程序发布不是 DEPLOY 步骤，无 ROLLBACK 命令；撤回方式 = 用户在微信公众平台把小程序版本回退到上一线上版本（人工）。若 A 阶段回滚了后端而新版小程序已发布：新版小程序对旧后端见上 R2 的兼容性说明。
3. AC-201-01：小程序申诉资料本批仅图片，pdf 仅 Web（OQ-06 已确认），人工清单 M-01 由用户确认接受（e2e_test_report）。

### SSH 通道与本地变量（所有阶段通用；M-DE-009/010、上批偏差）

```bash
# 套接字目录必须短路径（M-DE-010）；本地打包目录用 mktemp，使用前必须校验非空，不得写到 / 下
CM=$(mktemp -d /tmp/ocs.XXXX)
SCRATCH=$(mktemp -d /tmp/ocpkg.XXXX)
[ -n "$CM" ] && [ -d "$CM" ] && [ -n "$SCRATCH" ] && [ -d "$SCRATCH" ] && echo "DIRS_OK" || echo "DIRS_EMPTY_STOP"
OCAP_SSH="ssh -p 57279 -o ControlMaster=auto -o ControlPath=$CM/%C -o ControlPersist=10m yangyang@47.109.197.217"   # 内网改 -p 22 yangyang@192.168.31.51
OCAP_SCP="scp -P 57279 -o ControlPath=$CM/%C"
OCAP_DEST="yangyang@47.109.197.217"

# 建连重试：只重试"建连"，用显式成功标记判定，不依赖 grep -c 的返回码；连上后一次性完成各阶段只读预检
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
- 连续 8 次失败即停止汇报，不继续。已开始的**非幂等**命令（migrate、apply、tar 覆盖、rm）失败时先只读核对状态，不盲目重试。
- 多行远端脚本一律 `$OCAP_SSH bash -s -- "$TS" <<'EOF' … EOF`：脚本内用 `$1` 取本地值；`'EOF'` 防止本地展开。单行远端命令要用本地值时用双引号，执行前先 `echo` 完整命令核对；`$OCAP_SSH` 不加引号使用。本计划文档中的命令块不嵌套 heredoc；需要内嵌 Python 的地方用文件 + stdin（见 DEPLOY-012），E2 用 Write 工具创建文件，不用 heredoc。
- 跨阶段携带的值（`TS`、`TS2`、`TS3`、`N`、导出文件名、备份路径）由 PM 写进下一阶段的 `special_instructions`，不依赖 shell 状态。
- 结束时关闭连接并清理：`ssh -O exit -o ControlPath=$CM/%C yangyang@47.109.197.217; rm -rf "$CM" "$SCRATCH"`（先 echo 两个变量确认非空且路径以 `/tmp/ocs.`、`/tmp/ocpkg.` 开头再删）。

## 预检清单

### 阶段 A 预检（开发机 + 目标机，均只读）

先设定本地变量：
```bash
C=c32684b380e0e3cbce66e93bb58acb5972c750b1
PREV=15ea79ea51c87d56cd1cd8113cba81007649575a
MLIST=$(git diff --diff-filter=M --name-only $PREV $C -- backend/apps | sed 's#^backend/##')    # 被修改的产品源码（回滚核对用）
ALIST=$(git diff --diff-filter=A --name-only $PREV $C -- backend | sed 's#^backend/##' | grep -E '^(apps|tests|config)/')   # 本批新增文件（回滚时删除）
echo "$MLIST" | wc -l; echo "$ALIST" | wc -l      # 记录条数；两者均须非零
```

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-A01 待部署提交与版本标识 | 开发机：`git cat-file -t $C`；`git merge-base --is-ancestor $PREV $C && echo ANCESTOR_OK`；`git ls-remote origin main`（仅记录） | `commit`；`ANCESTOR_OK`；**未推送不是阻断项**（用户未授权 push，ocap-deploy §0）；部署后建议用户推送 |
| PRE-A02 前端与提交一致 | `git diff --quiet $C -- frontend && echo SAME`；`git status --short -- frontend backend miniprogram deploy` | `SAME`；后者无未跟踪/未提交行（有则停止交用户） |
| PRE-A03 迁移无漂移与手写核对（M-DE-002） | `cd backend && <Django 5.2 venv>/bin/python manage.py makemigrations --check --dry-run --settings=config.test_settings`；`git show $C:backend/apps/residency/migrations/0003_appeal_owner_name.py \| grep -c "Generated by Django"`（本条只看输出数字，不依赖退出码） | 漂移检查退出码 0；若报告本批无关 app 的既有漂移，在基线 `$PREV` 的临时 worktree 中确认同样存在后，只要求 residency 无漂移；`grep -c` 输出 `0`。不用 Django 6.x |
| PRE-A04 无依赖与构建配置变化、无删除文件 | `git diff --name-only $PREV $C -- backend/requirements.txt frontend/package.json frontend/package-lock.json miniprogram/package.json deploy`（期望空）；`git diff --diff-filter=D --name-only $PREV $C -- backend frontend`（期望空） | 两者均无输出（解包不会删除旧文件，故无删除是前提；否则计划需补删除步骤，停止上报） |
| PRE-A05 目标机可达与指纹 | `ocap_connect`；确认 `known_hosts` 中该端口 ED25519 指纹 | 输出 `CONNECT_OK`；指纹与 P7 一致 |
| PRE-A06 磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | /home 可用 ≥ 2 GB；可用内存 ≥ 500 MB |
| PRE-A07 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| PRE-A08 目录、本地状态与保留备份 | `$OCAP_SSH 'ls -la /home/yangyang/ocap; ls -l /home/yangyang/ocap/snapshots/ocapdb-registry-20261116134900.sql /home/yangyang/ocap/snapshots/underground-20261116134900.jsonl; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -d /home/yangyang/ocap/backend/venv && echo VENV_OK; test -d /home/yangyang/ocap/backend/var && echo VAR_OK'` | 部署根仅 `backend/ web/ snapshots/`；两份上批备份**存在**（用户要求保留到 2026-11-23，本计划任何步骤不得删除它们）；三个 OK（`.env`、`venv`、`var` 为必须保留的本地状态，本计划不触碰） |
| PRE-A09 `.env` 关键键 | `$OCAP_SSH 'grep -Eq "^DJANGO_SECRET_KEY=.+" /home/yangyang/ocap/backend/.env && echo SECRET_KEY_SET'` | `SECRET_KEY_SET`（不 cat） |
| PRE-A10 迁移基线 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations residency'` | 显示 0001、0002 均 `[X]`，**无 0003**（证明目标机尚未应用，ROLLBACK-004 为严格逆操作）；再用 `showmigrations --plan` 记录全局状态（未应用条数 0：用 `... \| grep -Ec "^\[ \]"` 取数字，不依赖退出码） |
| PRE-A11 web/ocap 属主（M-DE-013） | `$OCAP_SSH 'stat -c "%U %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html'` | 记录属主（上批为 yangyang，sudo 仍兼容） |
| PRE-A12 nginx 与 Freeark 基线 | `$OCAP_SSH 'sudo nginx -t; curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'` | `syntax is ok`；`200` |
| PRE-A13 当前版本记录与新增文件确证（M-DE-006） | 修改文件哈希：`printf '%s\n' "$MLIST" \| $OCAP_SSH 'cd /home/yangyang/ocap/backend && xargs sha256sum'`；新增文件不存在：`printf '%s\n' "$ALIST" \| $OCAP_SSH 'cd /home/yangyang/ocap/backend && while IFS= read -r f; do [ -e "$f" ] && echo "EXISTS $f"; done; echo ABSENT_CHECK_DONE'` | 哈希全部输出并记入报告；新增检查只出现 `ABSENT_CHECK_DONE`，无 `EXISTS` 行（若有 EXISTS，ROLLBACK-003 的删除清单不安全，停止上报） |
| PRE-A14 e2e_fixture 命令存在（供阶段 E） | `$OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/jobs/e2e_fixture.py'` | 存在；不存在则回报 PM |
| PRE-A15 mysqldump、表名与 SQL 模式 | `$OCAP_SSH 'command -v mysqldump'`；`$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.residency.models import Appeal,Membership;print(Appeal._meta.db_table,Membership._meta.db_table);from django.db import connection;c=connection.cursor();c.execute(\"SELECT @@sql_mode\");print(\"sql_mode_strict\",\"STRICT\" in c.fetchone()[0])"'` | 有 mysqldump 路径；打印 `residency_appeal residency_membership`（[INFERRED] 预期值，以实测填入 DEPLOY-002）；记录 `sql_mode_strict` 值（True 即证实回滚必须 migrate 0002） |
| PRE-A16 小程序顺序已由用户选定 | PM 在 invocation 写明所选顺序 R1/R2/R3 | 已写明；未写明则停止，不假设 |

### 阶段 B/C/D 预检（目标机，只读；在对应阶段开始时执行）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-B01 阶段 A 已完成 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && ls apps/registry/shops.py apps/registry/management/commands/relocate_shops.py apps/residency/migrations/0003_appeal_owner_name.py && systemctl is-active ocap-backend'` | 文件存在；`active` |
| PRE-B02 命令可加载 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_shops --help >/dev/null && venv/bin/python manage.py export_registry_import_file --help >/dev/null && echo CMD_OK'` | `CMD_OK`（仅 `--help`） |
| PRE-C01 阶段 B 结果已获用户确认 | PM 在 invocation 提供 N 与确认 | N 等于最近一次 dry-run 的 `would_change`（预期 107）且 `conflicts=0`；用户已看过旧楼栋分布与新标识样例 |
| PRE-C02 表名核对 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.models import RegistryUnit,RegistryOwner,RegistryPhone as P;from apps.residency.models import Membership as M,Appeal as A;print(RegistryUnit._meta.db_table,RegistryOwner._meta.db_table,P._meta.db_table,M._meta.db_table,A._meta.db_table)"'` | 打印五个真实表名（预期 `registry_registryunit registry_registryowner registry_registryphone residency_membership residency_appeal`；上批实测前四个）；以输出填入 DEPLOY-008 |
| PRE-C03 备份空间与路径不存在 | `$OCAP_SSH 'df -h /home/yangyang/ocap/snapshots; ls /home/yangyang/ocap/snapshots/ \| tail -8'` | 可用 ≥ 500 MB；本次将用的 `shops-$TS2.jsonl`、`ocapdb-registry-$TS2.sql` 不存在（命令对已存在路径退出码 3）；上批两份备份仍在 |
| PRE-C04 清册只读基线 | 见 DEPLOY-009 的 `CNT`（前计数） | 记录 units/owners/phones、商铺楼栋数、类型为商铺且不在"商铺"楼栋的条数（预期 = N）、有效绑定数、申诉总数/待审数 |
| PRE-D01 阶段 C 已完成且无未归类 | `CNT` 中 `shop_type_outside=0` | 为 0；否则导出命令退出码 2（`pending_shop_units>0`），**不加 `--allow-unrelocated`**，上报 |
| PRE-D02 导出落点安全 | `$OCAP_SSH 'ls -ld /home/yangyang/ocap_exports 2>&1; ls /home/yangyang/ocap_exports 2>&1; find /home/yangyang/ocap -name "registry_import_*" 2>/dev/null \| wc -l'` | 目录尚不存在，或已存在且属 yangyang、权限 700；既有文件仅记录不覆盖；部署根内 `registry_import_*` 个数为 0 |
| PRE-E01 夹具前提 | `e2e_fixture status` 全 0 | 无遗留 `e2e_` 数据；记录 `registry_counts` 为 `REGISTRY_BASE`，须与阶段 C 之后的计数一致 |

## 部署步骤

### 阶段 A：代码部署（授权点 A）

#### DEPLOY-001: 生成回滚锚点并快照
- 组件：后端目录、Web 静态目录、nginx 配置（本批不改 nginx，仍备份）；ROLLBACK-003/006 的锚点
- 位置：目标机；`TS` 在本地取一次，之后所有步骤复用（M-DE-003）
- 命令：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_FORMAT_OK || echo TS_BAD_STOP
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
# 把 PRE-A13 的"修改文件哈希"落盘到目标机，供回滚核对（内容仅文件哈希，不含个人信息）
printf '%s\n' "$MLIST" | $OCAP_SSH "cd /home/yangyang/ocap/backend && xargs sha256sum > /home/yangyang/ocap/snapshots/prehash-$TS.sha256 && wc -l /home/yangyang/ocap/snapshots/prehash-$TS.sha256"
```
- 预期：输出 `ANCHOR_TS`、`TS_FORMAT_OK`，2 份 tar（非零大小）+ 2 份 nginx 备份 + 2 个 SHA256 + `prehash-$TS.sha256` 行数 = `MLIST` 条数，记入报告。快照保留 ≥ 7 天。失败且目标机无变更 -> DEPLOYMENT_FAILED，无需回滚。
- 回滚: ROLLBACK-001

#### DEPLOY-002: 迁移前备份 `residency_appeal` 表
- 组件：数据层保护（只备份被迁移的表；不碰 Freeark 库）；凭据从目标机 `backend/.env`（DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME）读取，不写值；口令经 `MYSQL_PWD` 环境变量传 mysqldump，不进 argv/ps
- 位置：目标机；复用 `TS`
- 命令：
```bash
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
umask 077
cd $A/backend && set -a && . ./.env && set +a
[ "$DB_NAME" = "ocap" ] || { echo "DB_NAME 不是 ocap，停止"; exit 9; }
export MYSQL_PWD="$DB_PASSWORD"
# 表名以 PRE-A15 输出为准；下列为预期值 [INFERRED]
mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl --single-transaction --no-tablespaces \
  "$DB_NAME" residency_appeal > $A/snapshots/residency_appeal-$TS.sql
unset MYSQL_PWD
chmod 600 $A/snapshots/residency_appeal-$TS.sql
ls -l $A/snapshots/residency_appeal-$TS.sql
tail -n 2 $A/snapshots/residency_appeal-$TS.sql
sha256sum $A/snapshots/residency_appeal-$TS.sql
echo DUMP_DONE
EOF
```
- 预期：非零大小、权限 0600、末行 `-- Dump completed`、输出 `DUMP_DONE`；SHA256 记录。`--skip-ssl`（M-DE-008：测试 MySQL 自签证书）。失败 -> 不进入 DEPLOY-003，DEPLOYMENT_FAILED（目标机仅多了快照与备份，库与代码未变）。
- 回滚: ROLLBACK-002（无操作；备份保留）

#### DEPLOY-003: 打包提交 c32684b 的后端、上传并解包
- 组件：Django 后端 MOD-111~116（`ocap-backend`）
- 位置：开发机 -> 目标机
- 命令：
```bash
C=c32684b380e0e3cbce66e93bb58acb5972c750b1
echo "$SCRATCH"                                                  # 必须非空且为 /tmp/ocpkg.* 
git archive --format=tar.gz -o "$SCRATCH/ocap_backend_$C.tar.gz" "$C:backend"
sha256sum "$SCRATCH/ocap_backend_$C.tar.gz"
$OCAP_SCP "$SCRATCH/ocap_backend_$C.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/ocap_backend_$C.tar.gz"                # 与本地一致方可继续
$OCAP_SSH "tar xzf /tmp/ocap_backend_$C.tar.gz -C /home/yangyang/ocap/backend"
```
- 预期：两端 SHA256 一致；解包无错误；仅覆盖/新增源码，`.env`、`venv/`、`var/` 未被触碰（`git archive` 不含它们）；无删除（PRE-A04）。验证：
  `$OCAP_SSH 'cd /home/yangyang/ocap/backend && ls apps/registry/shops.py apps/registry/ownership.py apps/committee/effective.py apps/registry/management/commands/relocate_shops.py apps/residency/migrations/0003_appeal_owner_name.py && test -f .env && test -d venv && test -d var && echo LOCAL_STATE_INTACT'`
- 注意：此时旧 gunicorn 进程仍在内存中运行旧代码，文件已是新代码；直到 DEPLOY-005 重启之前，旧进程懒加载未导入的模块有数秒的新旧混合风险 [INFERRED]，因此 DEPLOY-003~005 须连续执行，不在中间停留。
- 回滚: ROLLBACK-003

#### DEPLOY-004: 执行迁移 residency 0003（改库结构）
- 组件：数据层；`residency.Appeal.owner_name` AddField（NOT NULL，default ""）
- 位置：目标机
- **[MANUAL_ROLLBACK_REQUIRED: 回滚 = `migrate residency 0002_closed_status` 会 DROP COLUMN owner_name，迁移后提交的申诉的"产权人名字"随之丢失（不可恢复，除非在回滚前另行 mysqldump，见 ROLLBACK-004）；迁移后已"通过"的申诉对清册的追加不随列回退，须管理员在清册页手工处理]**
- 命令：
```bash
# 1) 只读计划，必须只含 residency.0003（用显式标记判定，不依赖 grep -c 返回码）
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan > /tmp/mig_plan.txt; cat /tmp/mig_plan.txt; n=$(grep -E "^[a-z_]+\.[0-9]{4}_" /tmp/mig_plan.txt | wc -l); echo "PLAN_LINES=$n"; grep -E "^residency\.0003_appeal_owner_name" /tmp/mig_plan.txt | wc -l | sed "s/^/PLAN_HAS_0003=/"'
# 2) 仅当 PLAN_LINES=1 且 PLAN_HAS_0003=1 才继续
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput; echo EXIT=$?'
# 3) 核对
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations residency; venv/bin/python manage.py shell -c "from django.db import connection as k;print([c.name for c in k.introspection.get_table_description(k.cursor(),\"residency_appeal\")])"; rm -f /tmp/mig_plan.txt'
```
- 预期：计划恰 1 条；`Applying residency.0003_appeal_owner_name... OK`、`EXIT=0`；`showmigrations` 中 0003 为 `[X]`；列清单含 `owner_name`。若出现"检测到模型变更未生成迁移"之类提示，按 PRE-A03 处理，**不要在目标机生成迁移**（P8）。计划不为 1 条 -> 停止上报（目标机已有代码变更，按 DEPLOY-003 起逆序回滚）。
- 回滚: ROLLBACK-004

#### DEPLOY-005: 重启后端服务
- 组件：systemd `ocap-backend`
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend'
$OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'
```
- 预期：`active`；日志无 `Traceback`/`ERROR`。**不 pip install（requirements 未变）**。不触碰任何 `freeark-*` 服务。
- 回滚: ROLLBACK-005

#### DEPLOY-006: 构建并替换 Web 前端
- 组件：Vue SPA（MOD-117）
- 位置：开发机构建；目标机替换
- 命令：
```bash
# 开发机仓库根（已通过 PRE-A02）
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
tar -czf "$SCRATCH/frontend_dist.tar.gz" -C frontend/dist . && sha256sum "$SCRATCH/frontend_dist.tar.gz"
$OCAP_SCP "$SCRATCH/frontend_dist.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/frontend_dist.tar.gz"
$OCAP_SSH 'sudo rm -rf /home/yangyang/ocap/web/ocap/* && sudo tar xzf /tmp/frontend_dist.tar.gz -C /home/yangyang/ocap/web/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html'
```
- 预期：两端 SHA256 一致；`index.html` 存在，资源路径以 `/ocap/assets/` 开头；构建前后 `git status -- frontend` 干净（`dist/` 已 gitignore）。
- 收尾：删除目标机 `/tmp/ocap_backend_$C.tar.gz`、`/tmp/frontend_dist.tar.gz`（仅本次上传的两个，路径写全后执行）；本机 `$SCRATCH` 在阶段结束时清理。
- 回滚: ROLLBACK-006

### 阶段 B：relocate_shops dry-run（授权点 B，只读）

#### DEPLOY-007: 商铺归类命令 dry-run
- 组件：MOD-111 的预演模式（无 `--apply` 即只读，测试以 `CaptureQueriesContext` 证明零写）
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_shops --list-limit 200; echo "EXIT=$?"'
```
- 预期输出（只含计数与标识，不含姓名/手机号）：`total_units`、`shop_units`、`already_target`、`would_change`、`conflicts`、`second_level_values`、`foreign_in_target`、`old_building|<楼栋/门牌>|<数>` 清单、`floor|<写法>|<数>` 清单、`conflict|…`、`move|id|旧标识|新标识`；退出码 0。
- **停止条件与汇报要点（用户指令）**：
  1. **`would_change` ≠ 107，或 `conflicts` > 0 -> 立即停止并汇报，不得进入阶段 C**；
  2. 汇报：`would_change`；冲突清单（若有，含类型 `specific_part`/`tuple`/`unit_no_occupied`/`too_long`/`empty_building`）；`old_building` 旧楼栋取值分布（预期 1/2/5/6/9/10 栋及 27 个门牌型取值，PM 只读计数：商铺 107 条、单元全空）；`second_level_values`（预期 33 [INFERRED]：6 个编号楼栋 + 27 个门牌）；楼层写法清单（`floor|…`）；新标识样例（`move` 的前若干条，取 3~5 条，含 id=4347 的 `move|4347|1栋负1层1139号|商铺1栋负1层1139号`）；
  3. `foreign_in_target` ≠ 0（非商铺类型已在"商铺"楼栋）-> 汇报，由用户决定；
  4. `already_target` 预期 0（目标楼栋尚无记录）；非 0 说明此前已部分执行，汇报；
  5. 重跑一次 `--list-limit 1`，汇总计数须与第一次相同（证明只读、结果稳定，上批做法）。
- 回滚: ROLLBACK-007（无操作，只读）

### 阶段 C：商铺改库（授权点 C，**改库**）

#### DEPLOY-008: 备份 ocap 库相关表（mysqldump 级，apply 之前）
- 组件：数据层保护；只备份 `ocap` 库涉及的表，**不碰 Freeark 库**；凭据与口令传递方式同 DEPLOY-002
- 位置：目标机；`TS2` 本地取一次
- 命令：
```bash
TS2=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "DATA_TS=$TS2"
echo "$TS2" | grep -Eq '^[0-9]{14}$' && echo TS2_FORMAT_OK || echo TS2_BAD_STOP
$OCAP_SSH bash -s -- "$TS2" <<'EOF'
set -e
TS2="$1"; A=/home/yangyang/ocap
umask 077
cd $A/backend && set -a && . ./.env && set +a
[ "$DB_NAME" = "ocap" ] || { echo "DB_NAME 不是 ocap，停止"; exit 9; }
export MYSQL_PWD="$DB_PASSWORD"
# 表名以 PRE-C02 输出为准；下列为预期值 [INFERRED]
mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl --single-transaction --no-tablespaces \
  "$DB_NAME" registry_registryunit registry_registryowner registry_registryphone residency_membership residency_appeal \
  > $A/snapshots/ocapdb-registry-$TS2.sql
unset MYSQL_PWD
chmod 600 $A/snapshots/ocapdb-registry-$TS2.sql
ls -l $A/snapshots/ocapdb-registry-$TS2.sql
tail -n 2 $A/snapshots/ocapdb-registry-$TS2.sql
sha256sum $A/snapshots/ocapdb-registry-$TS2.sql
echo DUMP_DONE
EOF
```
- 预期：非零大小、权限 0600、末行 `-- Dump completed`、`DUMP_DONE`、SHA256 已记录。文件含业主姓名/手机号，仅留目标机 0600，不传出、不入库、不 cat；**保留期由用户决定**（与上批两份并存，上批两份保留至 2026-11-23，不得删除）。失败 -> 不进入 DEPLOY-009，DEPLOYMENT_FAILED（库未变）。
- 回滚: ROLLBACK-008（无操作；备份保留）

#### DEPLOY-009: relocate_shops --apply
- 组件：MOD-111（事务内更新 `building/unit_no/specific_part/updated_at`，只改类型为商铺的记录；同事务写审计；提交前核对计数/绑定/未受影响记录指纹；不改业主、手机号、认证绑定）
- 位置：目标机
- 前置：DEPLOY-007 刚执行过且 `conflicts=0`；`N` = 用户确认的 `would_change`（预期 107）；`BK` 路径不存在
- 命令：
```bash
BK=/home/yangyang/ocap/snapshots/shops-$TS2.jsonl
# 独立只读计数（前后各一次；输出只含数字，无姓名手机号）
CNT='cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.models import RegistryUnit as U,RegistryOwner as O,RegistryPhone as P;from apps.residency.models import Membership as M,Appeal as A;print(\"units\",U.objects.count(),\"owners\",O.objects.count(),\"phones\",P.objects.count(),\"shop_building\",U.objects.filter(building=\"商铺\").count(),\"shop_type_outside\",U.objects.filter(unit_type=\"SHOP\").exclude(building=\"商铺\").count(),\"active_mem\",M.objects.filter(ended_at__isnull=True).count(),\"appeals\",A.objects.count(),\"appeals_pending\",A.objects.filter(status=\"PENDING\").count())"'
$OCAP_SSH "$CNT"                                    # 前
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_shops --apply --backup $BK --expect-changes $N --list-limit 5; echo EXIT=\$?"
echo "$CMD"                                         # 核对 BK 与 N 已展开、EXIT 的 $ 已转义
$OCAP_SSH "$CMD"
$OCAP_SSH "$CNT"                                    # 后
$OCAP_SSH "stat -c '%a %s %n' $BK"                  # 权限应为 600
```
- 预期（注意上批偏差：apply 输出**没有** `differences` 行）：退出码 0；输出 `moved=N`、`backup_records=N`、`lost_origin=0`、`before_*`/`after_*`（units、owners、phones、active_memberships）逐项相等；独立计数前后 units/owners/phones/active_mem/appeals/appeals_pending 相等，`shop_building` 后 = 前 + N，`shop_type_outside` 后 = 0；备份存在、权限 600。**补证**：再执行一次 DEPLOY-007，期望 `would_change=0`、`already_target` = 前 `shop_building` + N（幂等）；只读查 id=4347 的归属：
  `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.registry.models import RegistryUnit as U;print(list(U.objects.filter(id=4347).values_list(\"building\",\"unit_no\",\"floor\",\"specific_part\")))"'` 期望 `商铺`、`1栋`、`负1`、`商铺1栋负1层1139号`（用户 Q-OA-03=A：4347 归入商铺）。`backup_sha256` 是备份正文摘要，不等于整文件 sha256（M-DE-026），两者都记录。
- 退出码：1 参数错误；2 冲突/`--expect-changes` 不符/核对失败（事务已回滚，库保持修正前，上报，无需回滚）；3 备份文件问题（库未触碰）。
- **[MANUAL_ROLLBACK_REQUIRED: 回滚 = `--restore` 按备份写回原值（含 updated_at），属第二次改库，须用户决定；apply 之后产生的新认证/绑定按 unit_id 不受影响，其展示会回到旧楼栋名；整库级兜底为 DEPLOY-008 的 mysqldump，属覆盖式恢复，会丢弃备份之后所有写入，仅由人评估后执行]**
- 回滚: ROLLBACK-009

### 阶段 D：导出导入文件（授权点 D，含个人信息；文件保留在服务器）

#### DEPLOY-010: 创建导出目录（700）
- 组件：导出落点 `/home/yangyang/ocap_exports/`（部署根的同级目录，ADR-110：部署解包、前端 `rm -rf web/ocap/*`、回滚 `rm -rf backend` 都不会触及；不破坏部署手册预检"部署根仅 backend/web/snapshots"）
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'install -d -m 700 /home/yangyang/ocap_exports/ && stat -c "%a %U %n" /home/yangyang/ocap_exports/'
```
- 预期：`700 yangyang /home/yangyang/ocap_exports/`。目录已存在时 `install -d -m 700` 会把权限置为 700（属主不变），先按 PRE-D02 核对既有内容；不得删除其中任何文件。
- 回滚: ROLLBACK-010

#### DEPLOY-011: export_registry_import_file 导出到 ocap_exports（文件保留）
- 组件：MOD-113（命令全程只读：不 save/update/delete、不写审计；stdout 不含姓名、手机号；位置守卫：目录须 700 且属当前用户、不在部署根/MEDIA_ROOT/STATIC_ROOT 内；写入为 `.part` -> `os.replace`，权限 0600）
- 位置：目标机
- 命令：
```bash
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && umask 077 && venv/bin/python manage.py export_registry_import_file --output-dir /home/yangyang/ocap_exports/; echo EXIT=\$?"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：退出码 0；`structure=shop_relocated`；`db_*` 与 `file_*` 同值，`diff_*=0`；`gaps_units=0`、`gaps_unnamed_owners=0`；`precheck_rows_failed=0`、`precheck_would_create_units/owners/phones=0`、`precheck_would_update_units=0`；`roundtrip_mismatches=0`；输出末行 `output=/home/yangyang/ocap_exports/registry_import_YYYYMMDD-HHMMSS.xlsx`（记为 `X`，写入报告与后续 invocation）。`db_units` 预期与阶段 C 前后 units 相同（上批 5742 [INFERRED，期间无导入]）。
- 失败处理：退出码 2（`pending_shop_units>0`、gaps、冲突或自检失败，未落盘）-> 汇报用户，**不自行加 `--allow-gaps` / `--allow-unrelocated`**；退出码 3（目标已存在/位置不合规）-> 先只读核对，位置不合规则回到 DEPLOY-010 核对目录权限，同一秒重复则稍后重试（A-02）。
- 回滚: ROLLBACK-011

#### DEPLOY-012: 服务器侧只读核对（权限、哈希、计数；文件不取回）
- 位置：目标机（只读）；本阶段**不 scp 取回**、不在输出中打印文件内容，因此无法按上批做法在本机解析 xlsx，改在服务器上用仅输出计数的脚本核对（M-DE-024 的服务器版）
- 命令：
```bash
X=/home/yangyang/ocap_exports/registry_import_<取自 DEPLOY-011 输出>.xlsx       # 取值后 echo 核对路径：必须以 /home/yangyang/ocap_exports/registry_import_ 开头、.xlsx 结尾、仅一个文件
$OCAP_SSH "stat -c '%a %U %s %n' /home/yangyang/ocap_exports /home/yangyang/ocap_exports/ ; stat -c '%a %U %s %n' $X; sha256sum $X; ls -1 /home/yangyang/ocap_exports | wc -l"
$OCAP_SSH "find /home/yangyang/ocap -name 'registry_import_*' | wc -l"          # 部署根内应为 0
# 计数脚本：由 E2 用 Write 工具把下方 Python 代码写入 "$SCRATCH/count_export.py"（不用 heredoc），再经 stdin 传到远端；脚本只读 A、B 两列并只输出计数
$OCAP_SSH "cd /home/yangyang/ocap/backend && venv/bin/python -I - $X" < "$SCRATCH/count_export.py"
# 站点不可取性：SPA 回退下任何 /ocap/ 路径都返回 index.html，故判据是内容类型与大小，不是 404
curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' "https://ai-freeark.xin/ocap/registry_import_<文件名>.xlsx"
```
`count_export.py` 内容（只统计，不打印任何单元格原文；不读姓名、手机号列）：
```python
import sys
from collections import Counter
from openpyxl import load_workbook

path = sys.argv[1]
wb = load_workbook(path, read_only=True, data_only=True)
ws = wb.active
rows = ws.iter_rows(values_only=True)
header = next(rows)
print("header_cols", len(header))
named = {f"{n}栋" for n in range(1, 11)} | {"地下车位", "商铺"}
by_building = Counter()
shop_rows = 0
shop_rows_empty_unit = 0
total = 0
for row in rows:
    if row is None or all(v in (None, "") for v in row):
        continue
    total += 1
    building = str(row[0]).strip() if row[0] is not None else ""   # A 列 楼栋
    unit = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""  # B 列 单元（商铺行 = 原楼栋/门牌）
    key = building if building in named else "OTHER"
    by_building[key] += 1
    if building == "商铺":
        shop_rows += 1
        if not unit:
            shop_rows_empty_unit += 1
print("data_rows", total)
for key in sorted(by_building):
    print("building", key, by_building[key])
print("shop_rows", shop_rows, "shop_rows_empty_unit", shop_rows_empty_unit)
```
- 预期：目录 `700 yangyang`；文件 `600 yangyang`，大小与 DEPLOY-011 的 `output_bytes` 一致，SHA256 记入报告；`ocap_exports` 内文件数 = 本次新增 1（若目录已有他文件，仅记录）；部署根内 `registry_import_*` 个数 0；脚本输出 `OTHER 0`（编号楼栋之外只剩"地下车位""商铺"，门牌型楼栋已全部归入商铺——AC-193-01）、`building 商铺` 行数 > 0 且 `shop_rows_empty_unit=0`、`building 地下车位` 行数 = 上批导出的 1454 [INFERRED，随期间无导入]；站点 URL 返回 `200 text/html` 且大小等于 SPA 的 index.html（**不是** xlsx 内容类型）即视为不可经站点取得。若 openpyxl 在 `-I` 模式下不可导入（venv 内应有，requirements 含 `openpyxl`），去掉 `-I` 重试并说明。
- 回滚: ROLLBACK-012

### 阶段 E：部署后验证与远程 E2E（授权点 E）

只读冒烟随授权点 A 执行（见「阶段 A 部署后验证」）；下面三步写入 `e2e_` 数据，须阶段 E 单独授权。远程用例按画像 P4-1：只经 `https://ai-freeark.xin/ocap/`，只用 `e2e_` 账号，不修改非 `e2e_` 数据与清册；套件护栏拒绝任何非 REJECT 的申诉决定（TC-E2E-337 现仅提交/驳回，GR-C-001-F02）。夹具选「空闲」房屋，setup 前先只读列出将占用的房屋 id 供用户确认（M-DE-020）；整个"setup -> 运行 -> cleanup"循环放进同一个带 `trap cleanup EXIT` 的脚本/同一次 shell 调用，口令只在进程内存或经 stdin 传入，探测脚本先 `ast.parse`，复用 `tests.remote.remote_client.Remote` 并遵守其 GET 护栏（上批阶段 E 因探测脚本错误致夹具循环 3 次的教训）。

#### DEPLOY-013: 夹具 setup（目标机创建 `e2e_` 账号）
- 命令（口令经 stdin 传远端，不进 argv）：
```bash
OCAP_E2E_PASSWORD=$(python3 -c 'import secrets;print("E2e"+secrets.token_hex(10)+"x9")')   # 本地生成，不写文件、不输出
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.jobs.e2e_fixture import _free_units; print([(u.id, u.specific_part) for u in _free_units(3, set())])"'   # 只读，请用户确认
printf '%s' "$OCAP_E2E_PASSWORD" | $OCAP_SSH 'IFS= read -r OCAP_E2E_PASSWORD; export OCAP_E2E_PASSWORD; cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'
```
- 预期：退出 0；status 显示 e2e 账号与基线 `registry_counts`（记为 `REGISTRY_BASE`，须与阶段 C 之后的清册计数一致）。
- 回滚: ROLLBACK-013

#### DEPLOY-014: 运行远程 HTTP E2E
- 位置：主会话（HTTP，不经 SSH，不直连库）
- 命令：
```bash
OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD="$OCAP_E2E_PASSWORD" \
  python3 backend/tests/remote/run_remote.py -v 2>&1 | tee "$SCRATCH/e2e_remote_$TS.log"; echo "RUN_EXIT=${PIPESTATUS[0]}"
```
  （慢网络加 `OCAP_E2E_SLOW=1`；不设置 `OCAP_E2E_ALLOW_LOCAL`；请求用超时参数，**不用 `pkill -f` 杀后台进程**，M-DE-022；日志不含口令。）
- 预期：本批相关用例通过（认证带 `name`、申诉带 `owner_name`、TC-E2E-337 提交/驳回、选房顺序）。**既有失败单列**：上批记录的 DEF-B（TC-E2E-321、324 期望"户主"而实际"产权业主"）：GR-D-001 称本批已同步测试文案 [INFERRED，E2 以实跑为准]；若仍失败标「既有」，不计入本批判定（M-DE-025：过期期望只在部署后暴露）。TC-E2E-332 慢用例本轮不启用。失败项逐条记录用例号与响应摘要，不含口令；子代理无测试代码写权限，不修改用例。
- 额外只读补证（经套件的 `Remote` 客户端，遵守其 GET 护栏，登录为 `e2e_` 账号）：`/units/options` 第一级与 `?building=商铺`、`?building=地下车位`（见「阶段 E 验证」）。
- 回滚: ROLLBACK-014

#### DEPLOY-015: 夹具 cleanup（测完必做，DEPLOY-014 失败也要做）
- 命令：
```bash
F="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture"
echo "$F"                                   # 核对含 OCAP_E2E_FIXTURE=1
$OCAP_SSH "$F cleanup"                       # 默认 dry-run：核对 would_delete 仅为 e2e_ 数据
$OCAP_SSH "$F cleanup --execute"
$OCAP_SSH "$F status"
```
- 预期：`--execute` 退出 0；status 的 e2e 计数为 0；`registry_counts` 与 `REGISTRY_BASE` 逐项相同；`residency_appeal` 总数回到阶段 C 之后的基线（用 `CNT`）。不一致或出现非 `e2e_` 数据变化 -> 立即停止上报，**不得自行修复清册**。可选：M-02 浏览器核对需要保留 `e2e_` 申诉数据的短窗口（≤30 分钟，用户在线并在授权时明示）；超时或未明示则立即 cleanup。
- 回滚: ROLLBACK-015

## 回滚步骤（逆序）

**执行前核验变量（所有回滚通用）**：
```bash
TS=<DEPLOY-001 的 ANCHOR_TS>; TS2=<DEPLOY-008 的 DATA_TS，仅回滚阶段 C 时需要>
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_OK || echo TS_BAD_STOP
echo "$TS2" | grep -Eq '^[0-9]{14}$' && echo TS2_OK || echo TS2_BAD_OR_UNUSED
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/prehash-$TS.sha256 /home/yangyang/ocap/snapshots/residency_appeal-$TS.sql /etc/nginx/sites-available/ocap.bak_$TS /etc/nginx/sites-available/freeark.bak_$TS"
# 回滚阶段 C 时另需：/home/yangyang/ocap/snapshots/shops-$TS2.jsonl
```
文件须全部存在才继续。远端命令一律双引号使 `$TS` 在本地展开，执行前 `echo` 完整命令核对。**禁止** `git reset --hard`、`git clean`、`git stash`、覆盖式 rsync、`rm -rf backend`（`.env`/`venv`/`var` 是目标机本地状态）。不得删除 `snapshots/` 下上批的 `ocapdb-registry-20261116134900.sql`、`underground-20261116134900.jsonl`（保留至 2026-11-23）。

**回滚顺序（关键，跨阶段）**：
1. 若已执行阶段 C 且需还原数据：**先 ROLLBACK-009（`--restore`，依赖本批新代码）**，再回滚代码。默认**只回滚代码、保留库内商铺归类**：旧代码 15ea79e 把"商铺"当作普通文字楼栋读取，不会报错（只是排序回到文字楼栋位置）[INFERRED：未在旧代码上实测]；除非用户明确要求还原数据。
2. 阶段 A 内的执行顺序为 **ROLLBACK-006 -> ROLLBACK-004 -> ROLLBACK-003 -> ROLLBACK-005**（前端；**撤销迁移，须在旧代码恢复之前**，因旧代码里没有 0003 迁移文件；恢复代码；重启）。下列各节按编号逆序排列，ROLLBACK-005 虽编号在前但必须在 ROLLBACK-003 之后执行（与上批 003/002 同样的例外）。
3. 导出文件（ROLLBACK-011/012）不随代码回滚删除。

### ROLLBACK-015: 回滚 DEPLOY-015
- 类型：无操作。`e2e_` 数据被清理是预期终态，不恢复。

### ROLLBACK-014: 回滚 DEPLOY-014
- 类型：无操作（写入由 DEPLOY-015 清理）。若中途中断：直接执行 DEPLOY-015。

### ROLLBACK-013: 回滚 DEPLOY-013
- 类型：正式回滚
- 命令：执行 DEPLOY-015（先 dry-run 再 `--execute`）。
- 变量取值与核验：`F` 为本地拼接的完整远端命令，echo 核对含 `OCAP_E2E_FIXTURE=1`；cleanup 不需要口令。

### ROLLBACK-012: 回滚 DEPLOY-012
- 类型：无操作（只读核对）；本地 `$SCRATCH/count_export.py` 属临时文件，阶段结束随 `$SCRATCH` 清理。

### ROLLBACK-011: 回滚 DEPLOY-011（导出文件）
- 类型：**默认不执行**：用户要求文件"保存在服务器上"，导出文件是预期终态。仅当用户明确要求撤销时才执行。
- 命令（仅在用户明确要求时）：`CMD="rm -f $X; ls $X 2>&1"; echo "$CMD"; $OCAP_SSH "$CMD"`
- 变量取值与核验：`X` 取自 DEPLOY-011 输出的 `output=` 行，必须以 `/home/yangyang/ocap_exports/registry_import_` 开头、以 `.xlsx` 结尾，echo 核对为**单个**文件路径后执行；不得使用通配符；不删除目录中其他文件。若阶段 C 数据被还原，该文件反映的是归类后的结构，**已过时**（报告注明，不自动删除，交用户决定）。
- 预期：`No such file or directory`。删除不可恢复，但可重新导出。

### ROLLBACK-010: 回滚 DEPLOY-010（导出目录）
- 类型：无操作（保留目录与既有内容；空目录无风险）。仅在用户明确要求且目录为空时：`$OCAP_SSH 'rmdir /home/yangyang/ocap_exports'`（rmdir 对非空目录失败，不会误删）。

### ROLLBACK-009: 回滚 DEPLOY-009（还原商铺归类）
- 类型：正式回滚（二次改库，须用户决定）
- **[MANUAL_ROLLBACK_REQUIRED: 还原即改库，需用户明确同意。数据风险：被改记录的全部列写回修正前原值；apply 之后依赖新楼栋名的展示会回到旧楼栋名；apply 之后其他表的变化（新认证、新申诉及其通过后对清册的追加）不被撤销；`--restore` 要求本批代码仍在目标机上，因此必须先于代码回滚]**
- 命令（先还原 dry-run，再 apply）：
```bash
BK=/home/yangyang/ocap/snapshots/shops-$TS2.jsonl
$OCAP_SSH "cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_shops --restore $BK; echo EXIT=\$?"          # 只读，待还原条数应等于当时的 N
$OCAP_SSH "cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_shops --restore $BK --apply; echo EXIT=\$?"
```
- 变量取值与核验：`TS2` 取自 DEPLOY-008 输出；`stat -c %a $BK` 为 600；命令先校验备份，失败退出码 3 且库未变。
- 预期：`restored=N`、`differences=0`、前后计数相等；随后 DEPLOY-007 dry-run 重新出现原 `would_change`（107）。
- restore 失败时：用 `ocapdb-registry-$TS2.sql` 整表导入属覆盖式恢复，会丢弃备份之后所有写入，仅由人评估后执行，本计划不提供自动命令。

### ROLLBACK-008: 回滚 DEPLOY-008
- 类型：无操作。备份保留（含个人信息，0600；保留期由用户决定，到期由人删除）。

### ROLLBACK-007: 回滚 DEPLOY-007
- 类型：无操作（只读）。

### ROLLBACK-006: 回滚 DEPLOY-006（恢复前端）
- 类型：正式回滚；阶段 A 内**最先执行**
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap && sudo chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` 取 DEPLOY-001 的 `ANCHOR_TS`，快照须存在；执行后 `index.html` 存在，外网 `GET https://ai-freeark.xin/ocap/` 为 200。只动 `web/`。

### ROLLBACK-005: 回滚 DEPLOY-005（重启回旧代码）
- 类型：正式回滚；**须在 ROLLBACK-003 恢复代码之后**执行。
- 命令：`$OCAP_SSH 'sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend'`，再 `$OCAP_SSH 'sudo journalctl -u ocap-backend -n 30 --no-pager'` 确认无 Traceback。

### ROLLBACK-004: 回滚 DEPLOY-004（撤销迁移 residency 0003）
- 类型：正式回滚；**须在 ROLLBACK-003 之前、旧代码恢复之前执行**（新代码里才有 0003 迁移文件，才能反向迁移）
- **[MANUAL_ROLLBACK_REQUIRED: `migrate residency 0002_closed_status` 执行 DROP COLUMN `owner_name`，迁移后提交的申诉的"产权人名字"永久丢失（先做 4a 备份可留存）；迁移后已"通过"的申诉对清册的追加（新增产权人姓名/号码）不随列回退，须管理员在清册页手工处理；如需撤销，先备份再由人决定]**
- 命令：
```bash
# 4a 先判定是否需要回滚：0003 显示 [X] 才继续；显示 [ ] 则迁移未应用，跳过本节
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations residency'
# 4b 回滚前再备份一次当前状态（含迁移后提交的 owner_name），文件名带 -post-
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
umask 077
cd $A/backend && set -a && . ./.env && set +a
[ "$DB_NAME" = "ocap" ] || { echo "DB_NAME 不是 ocap，停止"; exit 9; }
export MYSQL_PWD="$DB_PASSWORD"
mysqldump -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" --skip-ssl --single-transaction --no-tablespaces \
  "$DB_NAME" residency_appeal > $A/snapshots/residency_appeal-post-$TS.sql
unset MYSQL_PWD
chmod 600 $A/snapshots/residency_appeal-post-$TS.sql
tail -n 1 $A/snapshots/residency_appeal-post-$TS.sql
echo POST_DUMP_DONE
EOF
# 4c 停服务（避免新代码在列被删后访问申诉表报错），撤销迁移，核对
$OCAP_SSH 'sudo systemctl stop ocap-backend && cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency 0002_closed_status --noinput; echo EXIT=$?; venv/bin/python manage.py showmigrations residency'
```
- 变量取值与核验：`TS` 同上；迁移名 `0002_closed_status` 取自 `showmigrations residency` 在 PRE-A10 的记录；执行后 0003 显示 `[ ]`、`owner_name` 列不在 `get_table_description` 输出中。服务处于停止状态，**紧接着执行 ROLLBACK-003 与 ROLLBACK-005**（停机时长为这两步用时，约数十秒 [INFERRED]）。
- 预期：`Unapplying residency.0003_appeal_owner_name... OK`，`EXIT=0`。

### ROLLBACK-003: 回滚 DEPLOY-003（恢复后端代码，叠加解包，M-DE-011）
- 类型：正式回滚
- 命令：
```bash
# 叠加解包：把快照中的旧源码覆盖回去；不 rm -rf backend，避免丢失 DEPLOY-001 之后产生的 var/ 数据，并保护 .env/venv
CMD="sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap --exclude=backend/.env --exclude=backend/venv --exclude=backend/var"
echo "$CMD"; $OCAP_SSH "$CMD"
# 移除本批新增文件：清单来自本地 git 的 A 类文件（PRE-A13 已证明目标机原本不存在）
echo "$ALIST" | wc -l; echo "$ALIST" | grep -Evc '^(apps|tests|config)/'      # 第二个数字必须为 0
printf '%s\n' "$ALIST" | $OCAP_SSH 'cd /home/yangyang/ocap/backend && xargs -r rm -f --'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && find apps/residency/migrations -name "0003_appeal_owner_name*" -delete; ls apps/residency/migrations'
# 核对：修改文件哈希与 DEPLOY-001 落盘的一致
$OCAP_SSH "cd /home/yangyang/ocap/backend && sha256sum -c /home/yangyang/ocap/snapshots/prehash-$TS.sha256 | grep -v ': OK' ; echo HASH_CHECK_DONE; test -f .env && test -d venv && test -d var && echo LOCAL_STATE_INTACT"
```
- 变量取值与核验：`TS` 同上；`ALIST` 在本地由 `git diff --diff-filter=A --name-only $PREV $C -- backend` 取得并限定前缀 `apps|tests|config`（所有路径相对 `backend/`，不含 `.env`/`venv`/`var`），执行前核对条数与前缀检查为 0；若 shell 变量已丢失，重新按预检节命令生成。哈希核对输出中**不得**出现非 `OK` 行，只出现 `HASH_CHECK_DONE`，否则回滚未生效，停止上报。其后执行 ROLLBACK-005。
- 禁止：`git reset --hard`、`git clean`、覆盖式 rsync、`rm -rf backend`。

### ROLLBACK-002: 回滚 DEPLOY-002
- 类型：无操作。备份保留（含迁移前 `residency_appeal` 数据，0600，保留 ≥ 7 天）。

### ROLLBACK-001: 回滚 DEPLOY-001
- 类型：无操作。快照、`prehash`、nginx 备份保留 ≥ 7 天，不删除。

## 不可逆步骤汇总

| 步骤 | 性质 | 标记 |
|---|---|---|
| DEPLOY-004 migrate residency 0003 | 加列；反向 = DROP COLUMN，迁移后提交的 `owner_name` 丢失；迁移后已通过的申诉对清册的追加不随列回退 | **[MANUAL_ROLLBACK_REQUIRED]**（ROLLBACK-004，含 -post- 备份） |
| 迁移后"通过申诉"对清册的追加 | 业务写入（产权人姓名/号码追加），无自动撤销 | **[MANUAL_ROLLBACK_REQUIRED]**：管理员在清册页手工处理；本计划阶段 E 的护栏禁止测试通过申诉，故测试不会产生此类写入 |
| DEPLOY-009 apply | 改库；可由 `--restore` 逆向（备份校验），但还原本身是第二次改库，且不撤销 apply 之后的其他写入 | **[MANUAL_ROLLBACK_REQUIRED]**（ROLLBACK-009，须用户决定） |
| DEPLOY-011 导出文件 | 新增含姓名/手机号的文件，**保留在服务器**（用户要求）；删除不可恢复但可重新导出 | 保管问题：目录 700、文件 600、不在部署根与站点目录内；保留期由用户决定 |
| DEPLOY-015 清理 `e2e_` 数据 | 删除不可恢复，预期终态 | 已在 ROLLBACK-015 说明 |
| DEPLOY-002/008 备份文件 | 含个人信息文件 | 目标机 0600；保留期由用户决定；上批两份保留至 2026-11-23，不得删除 |
| 小程序发布 | 用户手工，画像外 | 撤回 = 用户在微信公众平台回退版本，无命令 |
| 外部系统调用 / 通知 | 本批无 | — |

## 阶段 A 部署后验证（只读，随授权点 A）

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| 后端存活 | `$OCAP_SSH 'systemctl is-active ocap-backend'` | `active` |
| 后端日志 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager"` | 无 `Traceback`/`ERROR` |
| 迁移已应用且无未应用项 | `showmigrations residency`；`showmigrations --plan` 取 `grep -E "^\[ \]" \| wc -l` | residency 三个均 `[X]`；未应用 0 |
| 新列存在 | DEPLOY-004 第 3 步的列清单 | 含 `owner_name` |
| 新路由与鉴权（目标机上 `curl -s -m 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/…`，无令牌） | `POST /certifications`、`POST /appeals`、`GET /admin/appeals`、`GET /units/options` | 均 `401`/`403`（非 404/5xx；404 说明新代码未生效） |
| 登录接口可用 | `$OCAP_SSH "curl -s -m 10 -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400` |
| 内网前端 | 目标机 `curl -s -m 10 http://127.0.0.1:8090/ocap/`（或 `192.168.31.51:8090`） | 200，`text/html` |
| 外网前端与静态 | `GET https://ai-freeark.xin/ocap/`；`GET https://ai-freeark.xin/ocap/assets/<本次构建 js>`（`curl -m 15`） | 均 200；静态 404 -> 检查 `^~ /ocap/` |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | 200，返回 index.html |
| 新前端已替换 | 外网 `index.html` 引用的 js 文件名 = 本地 `frontend/dist/index.html` 引用 | 一致 |
| Freeark 未受影响 | `GET https://ai-freeark.xin/`；`$OCAP_SSH 'systemctl --state=failed --no-pager'` | 200；无 `freeark-*`、`ocap-*` 失败单元 |
| 端口归属 | `$OCAP_SSH 'ss -ltn'` 过滤 8000/8080/8090/9000 | 8000/8080 属 Freeark，8090/9000 属 ocap |
| 改库命令未被自动执行 | `$OCAP_SSH 'ls /home/yangyang/ocap/snapshots/shops-*.jsonl /home/yangyang/ocap_exports 2>&1'` | 阶段 A 结束时 `No such file`（两条命令未被执行） |
| 保留备份仍在 | `ls -l` 上批两份备份 | 存在，权限 600 |

## 阶段 B/C/D 验证（各自成功标准见对应 DEPLOY，补充）

| 阶段 | 检查项 | 成功标准 |
|---|---|---|
| B | 汇总计数与停止条件 | `would_change=107` 且 `conflicts=0`；其余汇报项齐全；两次运行汇总一致 |
| C | 独立计数 + 再次 dry-run + id=4347 | 见 DEPLOY-009 预期；`shop_building` 前 + 107 = 后；`shop_type_outside=0`；`would_change=0`；4347 在商铺 |
| C | 认证绑定与申诉不受影响 | `active_mem`、`appeals`、`appeals_pending` 前后相等 |
| C | 选房第一级（只读，经 `e2e_` 账号放到阶段 E，或经授权会话） | 12 项：`1栋…10栋`（自然序）、`地下车位`、`商铺`，无门牌型楼栋；`?building=商铺` 第二级带 `level_label="楼栋/门牌"`，选项数 = `second_level_values`（预期 33 [INFERRED]）；`?building=1栋` 下无商铺 |
| D | 导出自检与服务器侧核对 | 见 DEPLOY-011/012 |

## 阶段 E 验证与人工验证清单

| 检查项 | 方法 | 成功标准 |
|---|---|---|
| 远程套件 | DEPLOY-014 | 本批新增失败 0；DEF-B 若仍失败标「既有」 |
| 选房顺序（服务端） | `e2e_` 账号只读 `GET /units/options`、`?building=商铺`、`?building=地下车位`（经 `Remote` 客户端） | 第一级 12 项且顺序正确；商铺第二级自然序（`1栋<2栋<5栋<6栋<9栋<10栋<门牌…`）；地下车位第二级楼层 `负2`、`负1` |
| 认证姓名核对（HTTP，只用 `e2e_`） | 套件覆盖：缺姓名 400、姓名/手机号不符 422 `OWNER_NOT_MATCHED`（四种失败响应一致） | 通过 |
| 清册与夹具基线 | DEPLOY-015 | `registry_counts` 与 `REGISTRY_BASE` 相同；e2e 计数 0 |

人工验证清单（来自 e2e_test_report，纳入本计划）：

| 编号 | 对应阶段 | 做法 | 期望 | 执行人 |
|---|---|---|---|---|
| M-01 | 阶段 A 前/后 | 用户确认 OQ-06：小程序申诉资料仅图片、pdf 仅 Web（已确认推迟）；若不接受另批 | 用户答复 | 用户 |
| M-02 | 阶段 E 后 | 管理员在真实浏览器打开测试环境申诉页，核对缩略图懒加载、点击弹出大图、上/下一份、pdf 预览与下载入口、关闭后页码与筛选保持；用普通用户令牌直接访问附件 URL 得 403。P4-1 限制下，E2 只能用套件产生的少量 `e2e_` 申诉（每条 1 张 png），**无法造出 20 条×5 个含 pdf 的数据**（无测试代码写权限），该部分由用户用自己的真实数据只读查看（用户自己的管理操作，不属于自动化测试）；如需保留 `e2e_` 数据窗口见 DEPLOY-015 | 缩略图数量 = 资料数；大图可切换；pdf 可预览并有下载入口；无权访问 403 无内容；无明显卡顿 | 用户（真实浏览器：Chrome/Edge 与手机浏览器） |
| M-03 | 阶段 D 后 | DEPLOY-012：目录 700、文件 600、文件名含日期、不在部署根内；站点 URL 不返回 xlsx（SPA 回退为 index.html，判据是内容类型/大小，不是 404/403） | 同左 | E2/主会话只读 |
| M-04 | 阶段 B~D 后 | 授权前确认对测试环境清册写入数为 0（阶段 B 只读；阶段 C 写入范围仅 107 条 + 审计）；`git grep` 仓库（含 `project_workspace/`）检索导出文件名与样例姓名/手机号 | 写入符合授权；检索 0 命中；报告与日志只含计数 | 主会话 |
| M-05 | 阶段 B/C | 107 条核对：dry-run 条数、旧楼栋分布、楼层写法、冲突数；apply 后 `lost_origin=0`、计数前后相等、导出预检 0 | 与 107 一致、无冲突、计数相等 | E2（命令）+ 用户确认 |
| M-06 | 阶段 A 前后 | 用户按推荐 R1 构建/审核/发布新版小程序；核对新版认证（姓名必填、不符转申诉）、申诉（产权人名字必填）、选房第一级 12 项与商铺第二级标签；旧版认证/申诉 400 的过渡期影响 | 新版可用，旧版 400 如预期 | 用户（HBuilderX/微信开发者工具、真机） |
| M-07 | 阶段 E | DEPLOY-014：远程套件通过；护栏拒绝任何非 REJECT 的申诉决定；清册与非 `e2e_` 数据无变化 | 同左 | E2 |

状态判定：各阶段验证全部通过 -> 该阶段 DEPLOYED_SUCCESSFULLY；失败按 E2 规则处理（尚无变更 -> DEPLOYMENT_FAILED；已有变更 -> 从失败步起逆序回滚；`[MANUAL_ROLLBACK_REQUIRED]` 步骤失败 -> 暂停等人工）。critical path 的待人工验证项（M-02、M-03、M-05 及 M-01 的用户决定）未完成时，终态至多 DELIVERED_WITH_ISSUES（GR-D-001 条件）。

## 吸收的上批偏差

| 上批报告记录 | 本计划的处理 |
|---|---|
| apply 输出无 `differences` 行（M-DE-026） | DEPLOY-009 预期改为 `moved`/`lost_origin=0`/`before_*`=`after_*` + 独立只读计数 + 幂等 dry-run 补证；`--restore` 才有 `differences` 行 |
| SSH 建连间歇 `Connection closed`（M-DE-009） | 统一 `ocap_connect`（显式 `CONNECT_OK` 标记，至多 8 次，只对建连重试）+ ControlMaster；已开始的非幂等命令不盲目重试 |
| 夹具探测脚本错误致夹具循环 3 次（M-DE-020） | 阶段 E 前言：同一 `trap cleanup EXIT` 调用内完成循环；探测脚本先 `ast.parse`；复用 `Remote` 并遵守 GET 护栏 |
| 嵌套 heredoc 与空变量事故（M-DE-023） | 本计划无嵌套 heredoc；`SCRATCH`/`CM` 先 `mktemp` 并校验非空；计数脚本经文件 + stdin；不在本机 `/` 下写文件 |
| 上批两份个人信息备份保留至 2026-11-23 | 预检核对其存在；回滚章节明令不得删除；遗留项提醒 |
| web/ocap 属主与计划预期不同（M-DE-013） | 沿用 `sudo` 写法并 `chown` 回 yangyang |

## 自检记录

- 每个 DEPLOY（001~015）均有对应 ROLLBACK 且按编号逆序排列；阶段 A 内实际执行顺序（006 -> 004 -> 003 -> 005）已显式写出并说明理由；需人工的步骤标注 `[MANUAL_ROLLBACK_REQUIRED]`：DEPLOY-004（ROLLBACK-004）、DEPLOY-009（ROLLBACK-009）、迁移后清册追加。
- 环境仅为画像 P7 的「测试」；策略 recreate 已写理由；无 Docker、pscp、makemigrations 产物、目标机生成迁移、Freeark 改动；小程序发布明确标为画像外的用户手工步骤。
- 回滚不使用 reset/clean/stash/覆盖式 rsync/`rm -rf backend`；变量 `TS/TS2/TS3/BK/X/N/ALIST/MLIST` 均写了取值来源与核验；远端引号规则已说明，涉及本地值的远端命令使用双引号或 `bash -s --`，单引号命令内的 `$VAR` 均为远端展开意图。
- `[INFERRED]` 项汇总：Django 在 MySQL 上去掉列级 DEFAULT 且目标库严格模式（PRE-A15 实测）；解包到重启的混合窗口时长；阶段 C 耗时；表名 `residency_appeal`；`second_level_values`=33、`db_units`=5742、地下车位导出行数 1454 的预期值；旧代码对"商铺"楼栋的兼容性；`openpyxl -I` 可用；DEF-B 在本批是否已修；小程序正式版指向的后端；微信客户端对旧版用户的切换时机。
- 子代理未执行 ssh/scp/commit/push。
