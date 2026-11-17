<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-17T22:30:38+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
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

# 部署计划：身份与房屋页改版 + 手机号匹配清册引导（后端含迁移 + Web 前端 + 小程序人工上传）

> 本计划只描述步骤，不构成授权。E1 未连接任何目标机、未执行 ssh/scp/部署命令（画像 P9）；E2 须用户当轮授权，每条 ssh/scp 仍经 `.claude/settings.json` 的 ask 规则确认。凭据只写位置不写值（`backend/.env`、`OCAP_E2E_PASSWORD` 只引用名称）。沿用 `ocap_brand_layout`（已执行成功）的通道、变量、快照与前端替换做法，并吸收 M-DE-003/005/006/009/010/011/013/016/020/022/023/028/029/034/035。

## 授权条件（E2 开始前全部满足，否则 BLOCKED）

1. `phase_status` 中 GROUP_E1 已 APPROVED；本计划版本 = APPROVED 版本。
2. E2 invocation 的 `special_instructions` 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名 **测试**（画像 P7 唯一环境，部署需用户确认=是）。
3. 用户已知晓待部署内容**尚未提交**，同意以本地工作树打包（画像 P9、skill §0）。
4. 可选的 DEPLOY-010~012（远程只读 HTTP 探测，需创建 `e2e_` 夹具）须在授权中**单独**写明；未写明则跳过，V-19/V-20 标"未执行"，不得标 SUCCESS。夹具会临时占用真实专有部分，须先看 DEPLOY-010 预览并经用户确认（M-DE-020）。
5. MANUAL-01（小程序体验版）不由 E2 执行。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端 MOD-132/133/134 | 修改 10：`apps/accounts/views.py`、`apps/identity/{services,views}.py`、`apps/residency/{apps,auto_bind,housing,models,services,urls,views}.py`；新建 3：`apps/registry/display.py`、`apps/residency/phone_match.py`、`apps/residency/migrations/0004_phone_match_prompt.py` | `residency 0004_phone_match_prompt`：手写 CreateModel `PhoneMatchPrompt`，依赖 `residency.0003_appeal_owner_name`、`accounts.0003_adminaccount_theme_key`；可逆（`migrate residency 0003`）；不回填、不改其它表 | 无构建；依赖不变（`git diff HEAD -- backend/requirements.txt` 为空） | systemd `ocap-backend` 停止→更新→迁移→启动（需重启） |
| Web 前端 MOD-135/136/137 | 修改约 12、新建 `portal/parts/RegistryMatchPanel.vue`、删除 `portal/me/MeIdentity.vue`、`shared/api.js` 新增 3 个 meApi | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` | 静态目录 `/home/yangyang/ocap/web/ocap` 替换；nginx 不动、不 reload |
| 小程序 MOD-138 | `pages/units/index.vue`、`pages/phone/index.vue`、`pages/index/index.vue`、`utils/api.js`、新建 `components/RegistryMatchCard.vue` | — | **不在本次自动部署范围**（`build:mp-weixin` 在本机基线即失败；画像 P7 无小程序发布环境） | 无服务端单元；人工上传体验版（MANUAL-01，`[MANUAL]`） |
| 测试代码 | `backend/tests/**`、`frontend/tests/**`、`miniprogram/tests/**` | — | 后端 tar 一并带上 `backend/tests`（与既往部署一致，不影响运行）；前端/小程序测试不部署 | — |
| nginx / Freeark / systemd 单元 / `.env` / 依赖 / 定时任务 | 无变化 | — | — | 不触碰（module_design「受影响的运行单元」；画像 P7、P8） |

**版本标识（部署前必须记录）**：计划编制时本地 `HEAD = c5ed0ab95c1ba101a9a16704b92dc516f8b7913e`；本批改动均未提交（`git status --short`：52 个 M、1 个 D、17 个 `??`；产品文件中未跟踪为 `backend/apps/registry/display.py`、`backend/apps/residency/phone_match.py`、`backend/apps/residency/migrations/0004_phone_match_prompt.py`、`frontend/src/portal/parts/RegistryMatchPanel.vue`、`miniprogram/components/RegistryMatchCard.vue`，其余为新测试与文档）。HEAD 不能单独定位版本，**定位依据 = `git status --short` 摘要 + 后端 tar SHA256 + 前端 tar SHA256 + 本地 `dist/index.html` SHA256**（M-DE-006）。E2 以自己打包时的值为准并记入报告；若 PM 在 E2 前已提交，改记新 HEAD，计划不变。

**与 invocation 的差异（请 PM 注意）**：invocation 写"Web 前端重建 --base=/ocap/"，未写 `VITE_API_BASE`。缺该变量时产物接口前缀为 `/api/v1`，部署后接口全 404（M-DE-034，`frontend/src/shared/http.js:8`；CI 与 skill DEPLOY-006 都带变量）。本计划一律使用 `VITE_API_BASE=/ocap/api/v1`，并以 `grep -c "/ocap/api/v1" frontend/dist/assets/index-*.js` ≥ 1 为预检门槛。

## 目标环境与策略

- 环境：**测试**（画像 P7；树莓派；外网 SSH `-p 57279 yangyang@47.109.197.217`，首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报；内网 `192.168.31.51:22`）。生产为"无"，不设计晋升与其它环境；`ai-freeark.xin:9999` 不可用，不使用。
- 策略：**recreate**（画像允许）。理由：单实例 gunicorn、无两套环境与按比例分流，不具备 rolling/blue-green/canary 前提。后端采用"停服务 → 覆盖代码 → 迁移 → 启动"的短窗口（M-DE-016）：迁移只新增空表，旧进程在内存中的旧代码可继续运行，但解包期间新旧文件混合有被 gunicorn 重载 worker 导入的风险，故先停服务。顺序为**后端先于 Web**：新后端兼容旧前端（`auto_bound` 恒 `[]`、`/me/housing` 只增字段），而新前端调用 `/me/registry-matches*` 在旧后端上会 404。
- 预计停机：后端约 1~3 分钟（停止到启动，含迁移与 MV-04 往返）[INFERRED，无实测]；前端静态替换窗口 < 数秒 [INFERRED]。旧页面浏览器标签引用的旧哈希 chunk 在替换后 404 回退为 index.html，刷新即恢复 [INFERRED]。
- 回滚偏好：画像未写。变更未提交，"源头 revert 后重新部署"不适用；采用"切回上一版本制品"（`backend-<TS>.tar.gz` / `web-<TS>.tar.gz` 快照），符合 skill §7。**回滚顺序：先 `migrate residency 0003`，再还原代码**（旧代码没有 0004 文件，无法反向迁移，skill §7 ROLLBACK-004 注）。
- 小程序时序：**小程序体验版在后端 DEPLOY-007 验证通过后再上传**（MANUAL-01）。新小程序在旧后端上会 404；旧小程序在新后端上只是不再静默自动绑定（行为变化，不报错）。

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

- 只重试"建连"；连续 8 次失败即停止汇报。已开始的**非幂等**命令（`rm`、`cp -a`、`migrate`、`systemctl stop/start`）失败时先只读核对状态，不盲目重试。
- `$OCAP_SSH` 不加引号使用。远端命令要用本地值（`TS`、`OWN`、`W`）时一律**双引号**，执行前 `echo` 完整命令核对；远端要自己展开的 `$` 在双引号里写 `\$`；单引号命令内的 `$VAR` 在远端展开，只在本意如此时使用。多行远端脚本用 `$OCAP_SSH bash -s -- "$TS" <<'EOF' … EOF`，本计划命令块不嵌套 heredoc。
- `TS` 在 DEPLOY-001 取一次并全程复用（M-DE-003）；跨会话由 PM 写入 invocation，不依赖 shell 状态。
- 结束清理：先 `echo "$CM" "$SCRATCH"` 确认非空且以 `/tmp/ocs.`、`/tmp/ocpkg.` 开头，再 `ssh -O exit -o ControlPath=$CM/%C yangyang@47.109.197.217; rm -rf "$CM" "$SCRATCH"`。

## 预检清单

### 开发机（只读 + 本地构建，不触碰目标机）

先 `cd /root/myproject/ocap`。

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-A01 版本标识已记录 | `git rev-parse HEAD`；`git status --short \| awk '{print $1}' \| sort \| uniq -c` | 已记录（输出写入报告）；未提交是已知状态，不是阻断项 |
| PRE-A02 改动范围与计划一致 | `git status --short -- deploy frontend/package.json frontend/package-lock.json miniprogram/package.json backend/requirements.txt \| wc -l`；`git status --short -- backend \| grep -v tests` | 第一条 `0`（非 0 → 停止上报：计划假设无新依赖、无 systemd 模板改动）；第二条恰为本计划列出的 10 个 M + 3 个 `??` 后端文件（出现别的文件 → 停止，让 PM 判定是否仍属本批） |
| PRE-A03 迁移文件合规（P6/P8） | `head -3 backend/apps/residency/migrations/0004_phone_match_prompt.py`；`grep -c "Generated by Django" backend/apps/residency/migrations/0004_phone_match_prompt.py` | 头注释为手写说明；计数 `0`；`ls backend/apps/residency/migrations backend/apps/accounts/migrations` 中 residency 最新为 0003→0004、accounts 最新为 `0003_adminaccount_theme_key`（与 0004 的 dependencies 一致） |
| PRE-A04 迁移无漂移（scoped） | `(cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings residency accounts; echo EXIT=$?)` | `EXIT=0`、`No changes detected`。**不得用 Django 6.x**（P4）；产物不得提交（P8）；若 `manage.py` 对限定 app 不支持则改看全量输出中不含 residency/accounts。非 0 → 停止交回开发 |
| PRE-A05 测试基线 | 后端 `(cd backend && python manage.py test --settings=config.test_settings)`（本机需 PM 的 venv）；前端 `(cd frontend && npx vitest run --passWithNoTests 2>&1 \| tail -6)`（约 255 秒，勿用短超时）；小程序可选 | 后端 1025 通过；前端 41 文件 482 条；小程序 18 文件 135 条（GROUP_D 报告值）。本机缺依赖无法复跑时，如实标"引用 GROUP_D 报告、未复跑"，不得标 PASS。有失败 → 停止 |
| PRE-A06 风格生成物无漂移 | `node scripts/themes/build.mjs --check --strict; echo EXIT=$?` | `EXIT=0` |
| PRE-A07 前端构建与产物核验（M-DE-034） | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/ 2>&1 \| tail -3`；`grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js`；`grep -l 'registry-matches' frontend/dist/assets/*.js \| wc -l`；`grep -o '<title>[^<]*' frontend/dist/index.html` | `✓ built`；前缀计数 ≥ 1；`registry-matches` 命中文件数 ≥ 1（新接口随产物发布）；标题与上批一致（`Cyber@红枫岭`）；记录 `sha256sum frontend/dist/index.html` 与 `find frontend/dist -type f \| wc -l` |
| PRE-A08 无游离未跟踪产品文件 | `git ls-files --others --exclude-standard backend frontend/src miniprogram \| grep -v tests` | 恰 5 个：`backend/apps/registry/display.py`、`backend/apps/residency/phone_match.py`、`backend/apps/residency/migrations/0004_phone_match_prompt.py`、`frontend/src/portal/parts/RegistryMatchPanel.vue`、`miniprogram/components/RegistryMatchCard.vue`（后端 3 个随 tar 打包，务必在包内，见 DEPLOY-003） |

### 目标机（只读；`ocap_connect` 成功后一次性完成）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-T01 可达与指纹 | `ocap_connect`；核对 `known_hosts` 中该端口 ED25519 指纹 | `CONNECT_OK`；指纹与画像 P7 一致 |
| PRE-T02 磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | /home 可用 ≥ 2 GB；可用内存 ≥ 500 MB |
| PRE-T03 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| PRE-T04 目录与必须保留的本地状态 | `$OCAP_SSH 'ls -la /home/yangyang/ocap /home/yangyang/ocap/web; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -d /home/yangyang/ocap/backend/venv && echo VENV_OK; test -d /home/yangyang/ocap/backend/var && echo VAR_OK; sha256sum /home/yangyang/ocap/backend/.env; ls -l /home/yangyang/ocap/snapshots \| tail -20'` | 三个 OK；记录 `.env` 的 SHA256 为 `ENV_SHA`（只记哈希，不 `cat`；V-17 部署后须相同）；`snapshots/` 内既有备份（含个人信息的 `ocapdb-*.sql`、`shops-*.jsonl`、`residency_appeal-*.sql`、`underground-*.jsonl` 等）**存在，本计划任何步骤不得删除** |
| PRE-T05 属主（M-DE-013） | `$OCAP_SSH 'stat -c "%U:%G %n" /home/yangyang/ocap/backend /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html'` | 记录；`web/ocap` 属主记为 `OWN`，须匹配 `^[a-z_][a-z0-9_-]*:[a-z_][a-z0-9_-]*$`；backend 目录对 `yangyang` 可写 |
| PRE-T06 后端基线 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'` | `active`；记录时间戳与 PID（V-01 须不同，证明已重启到新代码） |
| PRE-T07 依赖未变 | 本地 `sha256sum backend/requirements.txt`；`$OCAP_SSH 'sha256sum /home/yangyang/ocap/backend/requirements.txt'` | 两端相同（则 DEPLOY 中**不**执行 `pip install`）。不同 → 停止上报（计划假设依赖不变）；若用户确认需同步依赖，另加 `venv/bin/pip install --dry-run -r requirements.txt` 门控并扩展计划，不得现场自行加步骤 |
| PRE-T08 迁移基线（M-DE-028 门控前置） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations residency accounts && venv/bin/python manage.py showmigrations --plan \| grep -c "^\[ \]"'` | residency 仅 0001~0003 为 `[X]`，无 0004；accounts 0001~0003 `[X]`；未应用计数 `0`。若 0004 已在目标机库中存在（有人提前迁移）→ 停止上报 |
| PRE-T09 `PhoneMatchPrompt` 表尚不存在 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.db import connection as c; print(\"TABLE_EXISTS\", \"residency_phonematchprompt\" in c.introspection.table_names())"'` | `TABLE_EXISTS False`（保证 ROLLBACK-005 为严格逆操作） |
| PRE-T10 nginx 与 Freeark 基线 | `$OCAP_SSH 'sudo nginx -t; curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'` | `syntax is ok`；`200` |
| PRE-T11 当前线上页面基线 | `$OCAP_SSH 'cd /home/yangyang/ocap/web/ocap && sha256sum index.html && grep -o "assets/[^\"]*" index.html'`；`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/` | 记录旧 `index.html` SHA256 与入口文件名；公网 `200 text/html` |
| PRE-T12 `e2e_` 夹具前提（仅当授权 DEPLOY-010~012） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'` | 全 0，无遗留 `e2e_` 数据；记录输出中的清册计数为 `REGISTRY_BASE`。非 0 → 停止并上报（M-DE-020） |

## 部署步骤

### DEPLOY-001: 生成回滚锚点并快照后端、Web、迁移状态
- 组件：`/home/yangyang/ocap/backend`（不含 `venv`、`var`、`.env`）、`/home/yangyang/ocap/web`（architecture_design 部署视图：后端 + Web 静态）。不改 nginx，故不备份 nginx 配置（与 skill DEPLOY-001 相比有意缩减，理由：本批对 nginx 零写入）。
- 位置：目标机；`TS` 在本地取一次
- 命令：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_FORMAT_OK || echo TS_BAD_STOP
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
mkdir -p $A/snapshots
# 排除 venv、var、.env：既防快照膨胀，也保证回滚"叠加解包"不会触碰本地状态（M-DE-011）
sudo tar czf $A/snapshots/backend-$TS.tar.gz --exclude='backend/venv' --exclude='backend/var' --exclude='backend/.env' --exclude='__pycache__' -C $A backend
sudo tar czf $A/snapshots/web-$TS.tar.gz -C $A web
cd $A/web/ocap && find . -type f -print0 | sort -z | xargs -0 sha256sum > $A/snapshots/webhash-$TS.sha256
cd $A/backend && find . -type f -not -path './venv/*' -not -path './var/*' -not -path '*/__pycache__/*' -not -name '.env' -print0 | sort -z | xargs -0 sha256sum > $A/snapshots/backendhash-$TS.sha256
set -a && . ./.env && set +a
venv/bin/python manage.py showmigrations --plan > $A/snapshots/migplan-$TS.txt
ls -l $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz $A/snapshots/webhash-$TS.sha256 $A/snapshots/backendhash-$TS.sha256 $A/snapshots/migplan-$TS.txt
wc -l $A/snapshots/webhash-$TS.sha256 $A/snapshots/backendhash-$TS.sha256
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -c '^backend/manage.py$'
tar tzf $A/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html$'
tar tzf $A/snapshots/backend-$TS.tar.gz | grep -cE 'backend/(\.env|venv/|var/)' || true   # 期望输出 0；grep 无匹配退出码 1，须 || true 以免 set -e 中断
sha256sum $A/snapshots/backend-$TS.tar.gz $A/snapshots/web-$TS.tar.gz
grep -c 'residency.0004' $A/snapshots/migplan-$TS.txt || true
EOF
```
- 预期：输出 `ANCHOR_TS`、`TS_FORMAT_OK`；5 个文件非零大小；两份哈希清单行数 = 旧文件数；`manage.py` 与 `index.html` 计数各 `1`；排除项计数 `0`（快照不含 `.env`/`venv`/`var`）；`residency.0004` 计数 `0`（迁移基线）；两个 tar 的 SHA256 记入报告。快照与清单保留 ≥ 7 天。失败且目标机无变更 → `DEPLOYMENT_FAILED`，无需回滚。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建并打包后端与前端
- 组件：后端（MOD-132~134）、Web 前端（MOD-135~137）
- 位置：开发机
- 命令：
```bash
echo "$SCRATCH"                                                       # 必须非空且为 /tmp/ocpkg.*
tar --exclude='__pycache__' --exclude='venv' --exclude='.env' --exclude='var' --exclude='db.sqlite3' \
    -czf "$SCRATCH/backend_$TS.tar.gz" -C backend .
tar tzf "$SCRATCH/backend_$TS.tar.gz" | grep -E '^\./apps/(registry/display\.py|residency/phone_match\.py|residency/migrations/0004_phone_match_prompt\.py)$'
tar tzf "$SCRATCH/backend_$TS.tar.gz" | grep -cE '(^|/)\.env$|^\./venv/|^\./var/'    # 须 0
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js               # 须 >= 1
grep -l 'registry-matches' frontend/dist/assets/*.js | wc -l        # 须 >= 1
tar -czf "$SCRATCH/frontend_dist_$TS.tar.gz" -C frontend/dist .
sha256sum "$SCRATCH/backend_$TS.tar.gz" "$SCRATCH/frontend_dist_$TS.tar.gz" frontend/dist/index.html
find frontend/dist -type f | wc -l                                   # 记录文件数
```
- 预期：后端包含 3 个新增文件（3 行输出）；排除项计数 `0`；`✓ built`；两个计数 ≥ 1；两个 tar 与 `index.html` 的 SHA256、`dist` 文件数记入报告。不使用 pscp 逐文件上传、不使用容器（P8）。失败 → 目标机仅多了快照，`DEPLOYMENT_FAILED`。
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并在目标机暂存
- 位置：开发机 → 目标机（`/tmp`，文件名含 `TS`）
- 命令：
```bash
$OCAP_SCP "$SCRATCH/backend_$TS.tar.gz" "$SCRATCH/frontend_dist_$TS.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz"      # 须与 DEPLOY-002 本地值一致
$OCAP_SSH "rm -rf /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && mkdir /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && tar xzf /tmp/backend_$TS.tar.gz -C /tmp/ocap_backend_stage_$TS && tar xzf /tmp/frontend_dist_$TS.tar.gz -C /tmp/ocap_web_stage_$TS && ls /tmp/ocap_backend_stage_$TS/manage.py /tmp/ocap_backend_stage_$TS/apps/residency/phone_match.py /tmp/ocap_backend_stage_$TS/apps/registry/display.py /tmp/ocap_backend_stage_$TS/apps/residency/migrations/0004_phone_match_prompt.py && ls -a /tmp/ocap_backend_stage_$TS | grep -c '^\.env\$' ; find /tmp/ocap_web_stage_$TS -type f | wc -l && sha256sum /tmp/ocap_web_stage_$TS/index.html"
```
- 预期：两端 SHA256 一致；暂存后端含 `manage.py` 与 3 个新文件、`.env` 计数 `0`；暂存前端文件数 = DEPLOY-002 `dist` 文件数，`index.html` SHA256 = 本地。任一不符 → 停止（目标机运行目录尚未改动），按 ROLLBACK-003 清理暂存，报告 `DEPLOYMENT_FAILED`。
- 注意：`$` 在双引号中已为本地展开（`$TS`）；`\$` 保证远端收到字面 `$`。执行前 `echo` 完整命令核对。
- 回滚: ROLLBACK-003

### DEPLOY-004: 停止后端并覆盖后端代码（线上首个变更点）
- 组件：`/home/yangyang/ocap/backend`（systemd `ocap-backend`）
- 位置：目标机
- 命令：
```bash
CMD="sudo systemctl stop ocap-backend; systemctl is-active ocap-backend; cp -a /tmp/ocap_backend_stage_$TS/. /home/yangyang/ocap/backend/ && ls -l /home/yangyang/ocap/backend/apps/residency/phone_match.py /home/yangyang/ocap/backend/apps/registry/display.py /home/yangyang/ocap/backend/apps/residency/migrations/0004_phone_match_prompt.py && test -f /home/yangyang/ocap/backend/.env && test -d /home/yangyang/ocap/backend/venv && test -d /home/yangyang/ocap/backend/var && sha256sum /home/yangyang/ocap/backend/.env"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：`is-active` 输出 `inactive`；3 个新文件存在；`.env`/`venv`/`var` 仍在，`.env` SHA256 = `ENV_SHA`（暂存包不含 `.env`，`cp -a` 不会覆盖）。解包只覆盖与新增，**不删除**目标机已有文件：本批后端无删除文件（`git status` 只有前端 `MeIdentity.vue` 被删），故无需清理旧文件。`stop` 已执行而 `cp` 失败 → 目标机已有变更，**立即**从 ROLLBACK-004 起回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 数据库迁移 residency 0004（目标机 MySQL）
`[MANUAL_ROLLBACK_REQUIRED: 仅当回滚时 residency_phonematchprompt 表已有行。表只存 user、status、时间戳，不含手机号与清册信息（ADR-128），但"已选不是 / 已确认"状态一旦丢失无法恢复；表为空时回滚自动执行，见 ROLLBACK-005]`
- 组件：数据层（module_design「数据迁移」）；`PhoneMatchPrompt` 新表，不改其它表
- 位置：目标机；迁移由开发机手写入库，不在目标机生成（P8）
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --plan | grep -E "^[a-z_]+\.[0-9]{4}_"'
```
  **门控（M-DE-028）**：输出必须**恰为一行** `residency.0004_phone_match_prompt`，否则停止，不执行 `migrate`（说明目标机库状态与预期不符），按 ROLLBACK-004 起回滚代码。通过后执行：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate --noinput 2>&1 | tail -8; venv/bin/python manage.py showmigrations residency accounts'
```
- 预期：`Applying residency.0004_phone_match_prompt... OK`；`showmigrations residency` 中 0004 为 `[X]`。MySQL 自签证书由 `.env` 的 `DB_SSL_DISABLED` 处理，不改。`migrate` 失败（含部分应用）→ 目标机已有变更，从 ROLLBACK-005 起逆序回滚。
- 回滚: ROLLBACK-005

### DEPLOY-006: MV-04 迁移往返验证（MySQL，表为空时）
- 目的：GR-D-001 condition / MV-04：在测试环境 MySQL 上验证 0004 可逆且可重迁。**仅当 `PhoneMatchPrompt` 行数 = 0 时执行**（后端仍停止，无用户写入；行数非 0 → 跳过往返，只记录原因并标 MV-04 部分完成，不得删表）。
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.db import connection as c; from apps.residency.models import PhoneMatchPrompt as P; print(\"BEFORE_TABLE\", \"residency_phonematchprompt\" in c.introspection.table_names(), \"ROWS\", P.objects.count())"'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency 0003 --noinput 2>&1 | tail -4'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.db import connection as c; print(\"AFTER_BACK_TABLE\", \"residency_phonematchprompt\" in c.introspection.table_names())"'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency --noinput 2>&1 | tail -4; venv/bin/python manage.py showmigrations residency; venv/bin/python manage.py shell -c "from django.db import connection as c; from apps.residency.models import PhoneMatchPrompt as P; print(\"AFTER_FWD_TABLE\", \"residency_phonematchprompt\" in c.introspection.table_names(), \"ROWS\", P.objects.count())"'
```
- 预期：依次输出 `BEFORE_TABLE True ROWS 0` → 回退 `Unapplying residency.0004… OK` 与 `AFTER_BACK_TABLE False` → 重迁 `Applying residency.0004… OK`、`showmigrations` 0004 `[X]`、`AFTER_FWD_TABLE True ROWS 0`。单引号命令内的 `$`、转义引号均在远端解释，无本地变量。**终态必须是 0004 已应用**；往返中途失败（如回退成功、重迁失败）→ 先只读查询状态，再重试一次 `migrate residency`（幂等）；仍失败 → 从 ROLLBACK-005 起回滚。此往返不改其它表（`showmigrations --plan` 与 DEPLOY-005 之后一致，用 `diff` 比对：`showmigrations --plan` 输出与 `migplan-$TS.txt` 的差异仅为 `residency.0004` 一行）。
- 回滚: ROLLBACK-006

### DEPLOY-007: 启动后端并查看日志
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend && systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'
$OCAP_SSH "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -30"
```
- 预期：`active`；`ActiveEnterTimestamp`、`MainPID` 与 PRE-T06 不同；日志无 `Traceback`、无 `ERROR`、无 `no such table`/`doesn't exist`。失败 → 从 ROLLBACK-007 起逆序回滚。
- 回滚: ROLLBACK-007

### DEPLOY-008: 替换 Web 静态目录
- 组件：`/home/yangyang/ocap/web/ocap`（nginx 站点 `ocap`；Freeark `^~ /ocap/` 反代，均不改）
- 位置：目标机；`OWN` 取自 PRE-T05。**仅在 V-01~V-06（后端部分）通过后执行**，否则新前端会在旧/故障后端上不可用。
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap/* && sudo cp -a /tmp/ocap_web_stage_$TS/. /home/yangyang/ocap/web/ocap/ && sudo chown -R $OWN /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && find /home/yangyang/ocap/web/ocap -type f | wc -l && sha256sum /home/yangyang/ocap/web/ocap/index.html"
echo "$CMD"          # 核对 TS、OWN 已展开且 OWN 形如 yangyang:yangyang
$OCAP_SSH "$CMD"
```
- 预期：`index.html` 存在；文件数 = 本地 `dist`；`index.html` SHA256 = 本地。`rm` 已执行而后续失败 → 目标机已有变更，**立即**从 ROLLBACK-008 起逆序回滚。
- 回滚: ROLLBACK-008

### DEPLOY-009: 验证通过后清理临时文件
- 位置：目标机；**仅在「部署后验证」全部通过（或 PM 决定保留现状）之后执行**；需要回滚时先保留暂存，回滚完成后再清理
- 命令：
```bash
CMD="rm -rf /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS && rm -f /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz && ls /tmp/ocap_backend_stage_$TS /tmp/ocap_web_stage_$TS /tmp/backend_$TS.tar.gz /tmp/frontend_dist_$TS.tar.gz 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：四项均 `No such file or directory`。只删带 `TS` 的本次上传路径（无通配符），不删 `snapshots/` 下任何文件。
- 回滚: ROLLBACK-009

### DEPLOY-010: （可选，须单独授权）夹具只读预览
- 目的：夹具会把 3 个空闲住宅专有部分临时绑给 `e2e_` 账号（M-DE-020）。先只读列出将占用的真实对象，供用户确认。
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.jobs.e2e_fixture import _free_units; print([(u.id, u.specific_part) for u in _free_units(3, set())])"'
```
- 预期：输出 3 个 `(id, 坐落)`，**不含姓名/手机号**；用户确认后才进入 DEPLOY-011；用户未确认 → 跳过 010~012。
- 回滚: ROLLBACK-010

### DEPLOY-011: （可选）夹具 setup → 只读 HTTP 探测 → cleanup（同一次调用，M-DE-020）
- 目的：GR-D-001 condition：按 P4-1 只经公开入口、仅 `e2e_` 账号，验证 `GET /api/v1/me/registry-matches` 返回结构（不含姓名/手机号）与 `GET /api/v1/me/housing` 新字段。**只发 GET，不改动清册**。
- 位置：开发机（探测）+ 目标机（夹具）；口令只在进程内存或 stdin，不进 argv、不写文件
- 做法：E2 用 Write 工具在 `$SCRATCH` 写 `e2e_probe.sh` 与 `e2e_probe.py`（不用 Bash heredoc，M-DE-023），脚本结构：
  1. `trap cleanup EXIT`，`cleanup` 执行 `$OCAP_SSH "$F cleanup --execute"`（`F` 为单引号字符串 `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture`，无 `$` 变量，在双引号中展开为本地值）；
  2. `OCAP_E2E_PASSWORD=$(python3 -I -c 'import secrets;print(secrets.token_urlsafe(18))')`（仅本地 shell 变量，不 echo）；
  3. setup：`printf '%s' "$OCAP_E2E_PASSWORD" | $OCAP_SSH 'IFS= read -r OCAP_E2E_PASSWORD; export OCAP_E2E_PASSWORD; cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 0 --bulk-resolutions 0'`；
  4. 探测：`OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD="$OCAP_E2E_PASSWORD" python3 -I "$SCRATCH/e2e_probe.py"`，`e2e_probe.py` 先 `ast.parse` 自检，复用 `backend/tests/remote/remote_client.py` 的 `Config`/`Remote`（遵守 GET 护栏）；
  5. 探测断言（全部为 GET，输出只打印通过/失败与计数，不打印响应体）见 V-19。
- 预期：探测 exit 0；脚本结束时 cleanup 自动运行（无论探测成败）。注意：夹具账号手机号为 `1990000xxxx` 预留号段，不在业主清册中，所以**只能验证结构与"无匹配"路径，不能验证真实匹配与确认流程**；真实匹配（含 `registry_match.pending=true`、确认认证）由 GROUP_D 的 1025 条后端用例覆盖，远程验证需改动清册或使用真实业主手机号，超出 P4-1，写入遗留问题。
- 回滚: ROLLBACK-011

### DEPLOY-012: （可选）夹具清理后核对
- 位置：目标机
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture status'
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from apps.residency.models import PhoneMatchPrompt as P; print(\"PROMPT_ROWS\", P.objects.count())"'
```
- 预期：`status` 全 0，清册计数 = `REGISTRY_BASE`；`PROMPT_ROWS` = DEPLOY-006 记录的 0（或如实记录期间真实用户产生的行数，不是失败）。
- 回滚: ROLLBACK-012

### MANUAL-01: `[MANUAL]` 小程序上传体验版（不由 E2 执行）
- 条件：DEPLOY-007 与 V-01~V-08 通过后。
- 操作：用户在自己的微信开发者工具/uni-app 构建环境构建 `miniprogram/`（本机基线 `build:mp-weixin` 失败，故不在计划内构建，构建方式由用户环境决定 [INFERRED]），上传体验版；E2 只在报告中引用，不代为验收。
- 回退：无命令。撤回 = 在微信公众平台不提交审核、改选上一体验版/线上版本（人工）。服务端无对应回滚动作。

## 回滚步骤（逆序）

**执行前核验变量（所有回滚通用）**：
```bash
TS=<DEPLOY-001 记录的 ANCHOR_TS>
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_OK || echo TS_BAD_STOP
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/backend-$TS.tar.gz /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/webhash-$TS.sha256 /home/yangyang/ocap/snapshots/backendhash-$TS.sha256 /home/yangyang/ocap/snapshots/migplan-$TS.txt"
$OCAP_SSH "tar tzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz | grep -c '^backend/manage.py\$'; tar tzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html\$'"      # 各须为 1
```
5 个文件都存在且两个计数为 1 才继续。远端命令一律双引号使 `$TS` 在本地展开，执行前 `echo` 完整命令核对。**禁止** `git reset --hard`、`git clean`、`git stash`、覆盖式 rsync、`rm -rf backend`；**不动** `backend/.env`、`backend/venv`、`backend/var`（附件）、`snapshots/` 中任何既有文件、nginx、Freeark。回滚只用到 `systemctl` 对 `ocap-backend` 的操作，不重启 nginx 与任何 `freeark-*` 服务。

### ROLLBACK-012: 回滚 DEPLOY-012
- 无操作（只读核对）。

### ROLLBACK-011: 回滚 DEPLOY-011（清理 `e2e_` 夹具）
- 类型：正式回滚（兜底；探测脚本自身的 `trap` 已清理时此步为复核）
- 命令：
```bash
F='cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture'
echo "$F"
$OCAP_SSH "$F cleanup --execute"
$OCAP_SSH "$F status"
```
- 变量取值与核验：`F` 为常量字符串，无 `$`；`status` 须全 0 且清册计数 = `REGISTRY_BASE`。夹具删除只作用于 `e2e_` 前缀用户及其数据（`PhoneMatchPrompt.user` 为 CASCADE，随之删除）；不触碰清册与非 `e2e_` 数据。

### ROLLBACK-010: 回滚 DEPLOY-010
- 无操作（只读预览）。

### ROLLBACK-009: 回滚 DEPLOY-009
- 无操作（临时文件已清理是预期终态；需要时可从本地 `$SCRATCH` 重新上传）。

### ROLLBACK-008: 回滚 DEPLOY-008（恢复旧 Web 静态目录）
- 类型：正式回滚（切回上一版本制品）
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && cd /home/yangyang/ocap/web/ocap && sha256sum -c /home/yangyang/ocap/snapshots/webhash-$TS.sha256 | grep -v ': OK'; echo HASH_CHECK_DONE; find /home/yangyang/ocap/web/ocap -type f | wc -l"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` = DEPLOY-001 的 `ANCHOR_TS`；上节核验通过。仅解包快照内 `web/ocap`。
- 预期：输出中**只出现** `HASH_CHECK_DONE`，不得有非 `OK` 行（否则 `ROLLBACK_FAILED`）；文件数 = 哈希清单行数；公网 `index.html` SHA256 = PRE-T11 旧值（`curl -s -m 15 https://ai-freeark.xin/ocap/ | sha256sum`）。

### ROLLBACK-007: 回滚 DEPLOY-007（停止后端，为迁移回退腾出窗口）
- 类型：正式回滚
- 命令：`$OCAP_SSH 'sudo systemctl stop ocap-backend; systemctl is-active ocap-backend'`
- 预期：`inactive`。该步在 ROLLBACK-005/004 之前执行，避免新代码在表被删除/文件被替换期间服务请求。

### ROLLBACK-006: 回滚 DEPLOY-006（往返验证）
- 类型：无独立操作。往返的终态要么是"0004 已应用"（由 ROLLBACK-005 回退到 0003 覆盖），要么是中途状态（同样由 ROLLBACK-005 的 `migrate residency 0003` 收敛，该命令幂等）。

### ROLLBACK-005: 回滚 DEPLOY-005（撤销迁移 residency 0004）
`[MANUAL_ROLLBACK_REQUIRED: 仅当 PhoneMatchPrompt 行数 > 0 时。回退会 DROP 表，已选"不是/已确认"状态无法恢复；先按下列命令转储该表（只含 user_id/status/时间戳）并由人确认。行数 = 0 时下列命令自动执行，无需人工]`
- 类型：正式回滚；**必须在 ROLLBACK-004 恢复旧代码之前执行**（旧代码没有 0004 文件，无法反向迁移）。顺序固定为 007 → 005 → 004。
- 命令：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.db import connection as c; from apps.residency.models import PhoneMatchPrompt as P; t=\"residency_phonematchprompt\" in c.introspection.table_names(); print(\"TABLE\", t, \"ROWS\", P.objects.count() if t else 0)"'
```
  - `ROWS` > 0 → **暂停**，返回 BLOCKED 等人决定（不自行处理）。人确认后先转储再回退（`--skip-ssl`：测试库自签证书，M-DE-008）：
```bash
CMD="cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && MYSQL_PWD=\"\$DB_PASSWORD\" mysqldump -h \"\$DB_HOST\" -P \"\${DB_PORT:-3306}\" -u \"\$DB_USER\" --skip-ssl \"\$DB_NAME\" residency_phonematchprompt > /home/yangyang/ocap/snapshots/residency_phonematchprompt-$TS.sql && ls -l /home/yangyang/ocap/snapshots/residency_phonematchprompt-$TS.sql"
echo "$CMD"; $OCAP_SSH "$CMD"
```
    （双引号内 `\$` 使 `DB_*` 在远端从 `.env` 展开，`$TS` 在本地展开；口令经环境变量传给 mysqldump，不进 argv；输出不得打印变量值。）
  - `ROWS` = 0 或已转储并经人确认后执行：
```bash
$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py migrate residency 0003 --noinput 2>&1 | tail -4; venv/bin/python manage.py showmigrations residency; venv/bin/python manage.py shell -c "from django.db import connection as c; print(\"TABLE_EXISTS\", \"residency_phonematchprompt\" in c.introspection.table_names())"'
```
- 预期：`Unapplying residency.0004… OK`（或已是 0003 时 `No migrations to apply`）；`showmigrations` 中 0004 为 `[ ]`；`TABLE_EXISTS False`。
- **可选的更保守做法（M-DE-005，由人选择）**：若表已有行且人决定不丢失状态，可跳过本步，仅回退代码；旧代码不引用该表，残留表与迁移记录无害（Django 对库中已应用而磁盘上缺失的迁移不报错，只在 `showmigrations` 中不显示）。此时 DEPLOY 总结须写明"库中残留 0004 与空/有数据的 `residency_phonematchprompt`"。

### ROLLBACK-004: 回滚 DEPLOY-004（恢复后端代码并启动）
- 类型：正式回滚（叠加解包，不删除目录；M-DE-011）
- 命令：
```bash
CMD="sudo tar xzf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap && rm -f /home/yangyang/ocap/backend/apps/registry/display.py /home/yangyang/ocap/backend/apps/residency/phone_match.py /home/yangyang/ocap/backend/apps/residency/migrations/0004_phone_match_prompt.py && cd /home/yangyang/ocap/backend && sha256sum -c /home/yangyang/ocap/snapshots/backendhash-$TS.sha256 | grep -v ': OK'; echo HASH_CHECK_DONE; test -f .env && test -d venv && test -d var && sha256sum .env"
echo "$CMD"; $OCAP_SSH "$CMD"
$OCAP_SSH 'sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend'
$OCAP_SSH "sudo journalctl -u ocap-backend --since '-3 min' --no-pager | tail -20"
```
- 变量取值与核验：`TS` 同上；`rm -f` 的 3 个路径是固定常量（本批新增的 3 个后端文件，来自 PRE-A08），不是通配符，也不是 `git clean`；解包用 `sudo`（快照由 `sudo tar` 生成，可能含 root 属主文件）。解包后旧代码的 `__pycache__` 残留的新文件 `.pyc` 无害（无对应源文件时 Python 不加载）。
- 预期：输出**只出现** `HASH_CHECK_DONE`（备份清单逐文件均 `OK`，说明代码已回到部署前；清单不含 `venv/var/.env`，故不校验它们）；`.env` SHA256 = `ENV_SHA`；`active`；日志无 `Traceback`。**核对未落盘的新文件**：`$OCAP_SSH 'ls /home/yangyang/ocap/backend/apps/residency/phone_match.py /home/yangyang/ocap/backend/apps/registry/display.py 2>&1'` 应为 `No such file or directory`。非 `OK` 行 → 停止，`ROLLBACK_FAILED`。

### ROLLBACK-003: 回滚 DEPLOY-003（清理暂存与上传文件）
- 类型：正式回滚；命令同 DEPLOY-009，预期四项 `No such file or directory`；`TS` 须通过格式校验，路径写全、无通配符。

### ROLLBACK-002: 回滚 DEPLOY-002（本地构建与打包）
- 类型：无目标机操作。`frontend/dist` 为 gitignore 的构建产物；本地 `$SCRATCH` 在结束清理时删除（先校验非空且前缀正确）。

### ROLLBACK-001: 回滚 DEPLOY-001
- 类型：无操作。快照、哈希清单、`migplan-$TS.txt` 保留 ≥ 7 天，不删除。

## 不可逆步骤汇总

| 步骤 | 说明 | 标记 |
|---|---|---|
| DEPLOY-005 / ROLLBACK-005 | 迁移 `residency 0004` 回退会 DROP `residency_phonematchprompt`；仅在该表已有行时有数据损失（状态数据，不含个人信息），表为空自动回滚 | `[MANUAL_ROLLBACK_REQUIRED]`（条件触发） |
| 部署后用户操作 | 用户在新代码下选"不是/确认"产生的关系（`Membership`）与审计记录不随代码回滚撤销；回滚代码不会取消已确认的产权认证 | 记录为遗留事项，非 DEPLOY 步骤 |
| MANUAL-01 | 小程序体验版上传，无命令回滚 | `[MANUAL]` |

无外部系统调用、无通知发送、无个人信息文件生成。

## 部署后验证

执行时机：后端类（V-01~V-08、V-15~V-17）在 DEPLOY-007 之后、DEPLOY-008 之前；前端类（V-09~V-14）在 DEPLOY-008 之后；V-19/V-20 在 DEPLOY-011/012 之后；均在 DEPLOY-009 之前。公网检查在开发机/主会话用 `curl -m 15`（M-DE-022：不用 `pkill -f`；内网 `192.168.31.51:8090` 外网不可达，改在目标机内 `curl 127.0.0.1:8090`）。**SPA 回退陷阱（M-DE-029）**：`/ocap/` 下不存在的静态路径也返回 200 + `index.html`，静态资源的判据是"内容类型 + 大小 + SHA256"，不是 200。

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| V-01 后端已重启并存活 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'` | `active`；时间戳与 PID 均不同于 PRE-T06 |
| V-02 后端日志无新错误 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager \| grep -ciE 'Traceback\|ERROR'"` | 输出 `0` |
| V-03 迁移已应用（MV-04） | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py showmigrations residency \| tail -4; venv/bin/python manage.py showmigrations --plan \| grep -c "^\[ \]"'` | `0004_phone_match_prompt` 为 `[X]`；未应用计数 `0`（MV-04：DEPLOY-006 的往返记录在报告中） |
| V-04 新表存在且无其它表变化 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.db import connection as c; print(\"TABLE\", \"residency_phonematchprompt\" in c.introspection.table_names())"; venv/bin/python manage.py showmigrations --plan \| diff - /home/yangyang/ocap/snapshots/migplan-'"$TS"'.txt'` | `TABLE True`；`diff` 仅显示 `residency.0004` 一行差异（此处单引号段后接 `"$TS"` 由本地展开；执行前 `echo` 核对） |
| V-05 新路由已解析 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py shell -c "from django.urls import resolve; [print(p, resolve(p).func.view_class.__name__) for p in (\"/api/v1/me/registry-matches\", \"/api/v1/me/registry-matches/confirm\", \"/api/v1/me/registry-matches/dismiss\", \"/api/v1/me/housing\")]"'` | 依次 `RegistryMatchesView`、`RegistryMatchesConfirmView`、`RegistryMatchesDismissView`、`MyHousingView` |
| V-06 接口鉴权（无令牌、只读） | `curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type}\n' https://ai-freeark.xin/ocap/api/v1/me/registry-matches`；同样对 `/me/housing` | 均 `401`（或 `403`），JSON；**不是** `404`/`text/html`（证明前缀与路由生效） |
| V-07 登录接口可用（错误凭据，唯一化） | `$OCAP_SSH "curl -s -m 15 -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"identifier\":\"nobody_$TS\",\"password\":\"wrong\"}' http://127.0.0.1:9000/api/v1/auth/login/password"` | `400`（`LOGIN_FAILED`）；不创建数据 |
| V-08 后端上线文件与本地一致 | `$OCAP_SSH 'cd /home/yangyang/ocap/backend && sha256sum apps/residency/phone_match.py apps/registry/display.py apps/residency/migrations/0004_phone_match_prompt.py apps/residency/views.py apps/accounts/views.py'`；对照本地 `sha256sum` 同名文件 | 逐项相同 |
| V-09 线上 index.html = 本地构建 | `curl -s -m 15 https://ai-freeark.xin/ocap/ \| sha256sum`；对照本地 `sha256sum frontend/dist/index.html` | 相同 |
| V-10 入口与静态资源 | 内网：`$OCAP_SSH 'curl -s -m 15 -o /dev/null -w "%{http_code} %{content_type}\n" http://127.0.0.1:8090/ocap/'`；公网：`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/`；对 `index.html` 引用的 `/ocap/assets/index-*.js`、`index-*.css` 各：`curl -s -m 15 -o "$SCRATCH/a" -w '%{http_code} %{content_type} %{size_download}\n' <URL>` 并 `sha256sum "$SCRATCH/a"` | 入口 `200 text/html`，大小 = 本地 `dist/index.html`；js `200` 含 `javascript`、css `200 text/css`（不是 `text/html`）；SHA256 = 本地 `dist` 同名文件 |
| V-11 新前端含新接口与正确前缀 | `$OCAP_SSH 'grep -l "registry-matches" /home/yangyang/ocap/web/ocap/assets/*.js \| wc -l; grep -c "/ocap/api/v1" /home/yangyang/ocap/web/ocap/assets/index-*.js'` | 第一个 ≥ 1；第二个 ≥ 1（M-DE-034） |
| V-12 新旧地址深链刷新可达 | 对下列路径各：`curl -s -m 15 -o "$SCRATCH/d" -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap<路径>` 并 `sha256sum "$SCRATCH/d"`：`/me/identity`、`/units`、`/units/pick`、`/units/applications`、`/units/review`、`/units/appeal`、`/units/appeals` | 7 条均 `200 text/html`，大小与 SHA256 = `index.html`（证明 `try_files … /ocap/index.html`；旧地址 `/units/review` 的重定向由前端路由完成，未登录者会被前端引到登录页，非服务端问题） |
| V-13 目标机落盘状态 | `$OCAP_SSH 'stat -c "%U:%G %a %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html; find /home/yangyang/ocap/web/ocap -type f \| wc -l; ls -l /home/yangyang/ocap/snapshots/web-*.tar.gz /home/yangyang/ocap/snapshots/backend-*.tar.gz \| tail -4'` | 属主 = `OWN`；`index.html` 权限 644；文件数 = 本地 `dist`；本次快照存在 |
| V-14 旧前端文件已清除 | `$OCAP_SSH 'ls /home/yangyang/ocap/web/ocap/assets \| grep -c "MeIdentity"'` | `0`（旧 `MeIdentity` chunk 随 `rm -rf web/ocap/*` 清除；新产物无该组件） |
| V-15 Freeark 与端口未受影响 | `curl -s -m 15 -o /dev/null -w '%{http_code}\n' https://ai-freeark.xin/`；`$OCAP_SSH 'systemctl --state=failed --no-pager; ss -ltn'` | `200`；无 `freeark-*`、`ocap-*` 失败单元；8000/8080 属 Freeark，8090/9000 属 ocap |
| V-16 本地状态未被触碰 | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && test -d /home/yangyang/ocap/backend/venv && test -d /home/yangyang/ocap/backend/var && echo LOCAL_STATE_INTACT; sha256sum /home/yangyang/ocap/backend/.env; ls -l /home/yangyang/ocap/snapshots/ \| grep -cE "ocapdb-\|underground-\|shops-\|residency_appeal-"'` | `LOCAL_STATE_INTACT`；`.env` SHA256 = `ENV_SHA`；上批个人信息备份仍在（计数 ≥ PRE-T04 记录值）；`var/` 附件目录未被替换 |
| V-17 依赖与 `.env` 键未变 | `$OCAP_SSH 'sha256sum /home/yangyang/ocap/backend/requirements.txt'` | = 本地 `requirements.txt` SHA256（= PRE-T07 值） |
| V-18 MV-04 往返记录 | DEPLOY-006 的输出 | 记录 `BEFORE_TABLE True ROWS 0` → `AFTER_BACK_TABLE False` → `AFTER_FWD_TABLE True ROWS 0`；若因表非空而跳过，如实标"部分完成" |
| V-19 （可选，DEPLOY-011）`e2e_` 账号只读探测 | `e2e_probe.py`（GET，经 `https://ai-freeark.xin/ocap/api/v1`）：(a) `e2e_guest` 与 `e2e_owner_a` 登录后 `GET /me/registry-matches` → 200，键集合恰为 `{pending,total,units}`，`pending=false`、`total=0`、`units=[]`；(b) 同一请求附加查询串 `?phone=13800000000` 结果与不带时完全相同（接口忽略入参）；(c) 响应文本不含 11 位连续数字；(d) `e2e_owner_a` `GET /me/housing` → 每个 `units[]` 项含非空字符串 `unit_type_label` 与 `area_display`，且键中无姓名/手机号字段；(e) `e2e_guest` `GET /me/housing` → `units=[]` | 全部通过；输出只含通过/失败与计数，不含响应体、口令、令牌；未授权则标"未执行" |
| V-20 （可选，DEPLOY-012）夹具清理 | DEPLOY-012 输出 | `status` 全 0；清册计数 = `REGISTRY_BASE`；脚本日志含 `cleanup` 已执行 |

全部通过 → `DEPLOYED_SUCCESSFULLY`（交付最终状态仍受下列人工项影响）；部分失败 → `DEPLOYED_WITH_ISSUES`，列失败项，由用户决定是否回滚（不自行回滚，除非步骤本身失败，按 E2 规则）。

## 人工验证清单（部署后由用户执行，**不由部署脚本执行**）

来源：`testing/e2e_test_report.md`（1.0.0 APPROVED）与 GR-D-001 condition。E2 在报告中只引用，不代为验收；未全部完成前最终交付状态至多 DELIVERED_WITH_ISSUES（协议 §K）。建议用**强制刷新**在公网入口 `https://ai-freeark.xin/ocap/` 执行；浏览为只读，写操作超出 P4-1 的部分不做。

| 编号 | 对应 AC | 做法（摘要） | 期望 | 执行人 |
|---|---|---|---|---|
| MV-01 | AC-242-01~06、TC-MP-*、TC-E2E-920/921 | MANUAL-01 上传体验版后，用微信账号登录 → 绑定匹配清册的手机号 → 观察是否跳转"我的房屋"并出现引导卡片 → 折叠/展开、取消勾选、确认/"不是"（测试环境短信为 console 替身，验证码由服务日志只读获取） | 与 TC-E2E-920/921 一致；`uni.navigateTo` 真实栈正常；三套风格无错位 | 用户（微信开发者工具 + 真机/体验版）；会写数据，须用户自己的清册手机号，**不属于 P4-1，E2 不代做** |
| MV-02 | AC-235-02、TC-WEB-915 | 产权业主有待审批时，主页点"待审批同住人申请：N" | 进入"我的身份与房屋"页，底部"待我审批的同住人申请"卡片滚动进入可视区域 | 用户（真实浏览器，宽屏与窄屏） |
| MV-03 | AC-233-02/05、AC-236-04、TC-INT-971 | 宽屏：右上角"我的身份与房屋"与左侧二级项各点一次；浏览器后退；窄屏查看切换条与"我的"总览 | 地址栏分别为 `/me/identity`、`/units`，页面一致，后退一次回到点击前页面；左侧高亮正确；窄屏切换条 5 项 | 用户（真实浏览器 + 真实视口） |
| MV-04 | `residency 0004_phone_match_prompt` | 由 **E2 在 DEPLOY-005/006 + V-03/V-04/V-18** 执行（测试机 MySQL 迁移前进、回退、重迁） | 见 V-18 | E2 |

## 自检记录

- 每个 DEPLOY（001~012）均有对应 ROLLBACK（001~012），按编号逆序排列；回滚实际执行顺序固定为 012 → 011 → … → 008 → 007（停后端）→ 005（先 `migrate residency 0003`）→ 004（再还原代码并启动）→ 003（清暂存）；ROLLBACK-006 为"由 005 覆盖"的无独立操作。MANUAL-01 无命令回滚，已显式标注。
- 不可逆/不可自动回滚项：ROLLBACK-005 条件性 `[MANUAL_ROLLBACK_REQUIRED]`（表有行时）；已列于汇总表。
- 依赖顺序：基础设施无变化 → 数据层（DEPLOY-005/006）→ 服务层（004、007）→ 前端（008）→ 清理；后端先于前端，小程序最后（MANUAL-01）。
- 环境仅为画像 P7「测试」；策略 recreate 已写理由；无 Docker、pscp 逐文件、makemigrations 产物、目标机生成迁移、Freeark 或 nginx 改动。
- 回滚不使用 reset/clean/stash/覆盖式 rsync/`rm -rf backend`；不动 `.env`、`venv`、`var`、既有快照；变量 `TS`、`OWN`、`ENV_SHA`、`REGISTRY_BASE` 均写了取值来源与核验方法；远端命令用双引号并要求先 `echo`；`\$` 与单引号嵌套已标注；`SCRATCH`/`CM` 先 `mktemp` 并校验非空；`mysqldump` 口令经环境变量，不进 argv，输出不含凭据。
- `[INFERRED]` 汇总：后端停机约 1~3 分钟；前端替换窗口 < 数秒；旧页面 chunk 失效的用户影响；小程序构建方式取决于用户环境；`/me/registry-matches` 无令牌返回 401 与 `/me/housing` 一致（来自 `IsMember`，V-06 以实测为准）。
- 遗留/风险：(1) 远程无法验证真实匹配与确认（需改清册或用真实手机号，超出 P4-1），仅验证结构与路由，真实路径靠本地 1025 条用例与 MV-01；(2) 本批未提交且 CI 未跑，版本以 SHA256 定位；(3) CR-003/GR-D-001-F02 观察项（手动认证提示仍显示"户主"）为既有行为，不在本批部署范围。
- 子代理 E1 未执行 ssh/scp/commit/push，未安装依赖、未联网；只读取了仓库文件，并做了本地 `git status`/`ls` 只读核对。
