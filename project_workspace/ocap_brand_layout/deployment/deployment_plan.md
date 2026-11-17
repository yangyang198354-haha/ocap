<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-17T09:22:30+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/cicd_pipeline.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：品牌更名 Cyber@红枫岭 + Web 左侧导航布局（仅 Web 静态产物）

> 本计划只描述步骤，不构成授权。子代理 E1 未连接任何目标机、未执行 ssh/scp/部署命令（画像 P9）；E2 须用户当轮授权，且每条 ssh/scp 仍经 `.claude/settings.json` 的 ask 规则确认。凭据只写位置不写值。本计划沿用 `ocap_owner_auth_v2` 已批准计划的 SSH 通道、变量与快照做法，并吸收其教训（M-DE-003/009/010/011/013/022/023/029）。

## 授权条件（E2 开始前全部满足，否则 BLOCKED）

1. `phase_status` 中 GROUP_E1 已 APPROVED；本计划版本 = APPROVED 版本。
2. E2 invocation 的 `special_instructions` 含 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名 **测试**（画像 P7 唯一环境，部署需用户确认=是）。
3. 用户已知晓**待部署内容尚未提交**（见「变更摘要·版本标识」），并同意以本地工作树构建的产物部署（画像 P9：提交、push 由用户决定，skill §0 允许以本地工作树打包）。若 PM 在 E2 之前已提交，E2 在报告中改记新的 HEAD，计划不变。
4. 本批单阶段授权（无改库、无导出个人信息），不需要 `ocap_owner_auth_v2` 式的多阶段拆分。

## 变更摘要

后端、数据库、迁移、systemd、nginx 配置、`api.js` 两份契约文件**全部不变**（module_design「受影响的运行单元」；`git status --short -- backend deploy frontend/package.json frontend/package-lock.json miniprogram/package.json` 本地核对输出 0 行）。

| 组件 | 文件（概要） | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| Web 前端（MOD-119~128，130） | `frontend/index.html`（标题）、`frontend/src/{brand,layout,stores,portal,admin,router,shared}`（新增 34 个源文件，修改约 30 个，删除 `theme/AdminThemeSwitcher.vue`）、随包字体 `frontend/src/brand/fonts/OcapBrand-subset.woff2`（12044 B） | 无 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`（见预检 PRE-05，**必须带 `VITE_API_BASE`**） | 静态目录 `/home/yangyang/ocap/web/ocap` 替换；nginx 不动、不 reload；后端**不重启** |
| 风格定义与生成物（MOD-130） | `themes/*.theme.json|web.css|mp.css`、`frontend/src/theme/generated/themes.css`（随构建进入 `dist`） | 无 | 开发机已 `build.mjs --strict`，部署前复核 `--check` | 随前端产物 |
| 小程序（MOD-129） | `miniprogram/pages.json`、`pages/login/index.vue`、`miniprogram/theme/generated/themes.scss` | — | **不在本次部署范围**：`build:mp-weixin` 在本机基线即失败（GR-C-001-F04），小程序发布不在画像 P7；由用户在微信开发者工具构建/预览（MV-03） | 无服务端运行单元 |
| 测试代码 | `frontend/tests/*`、`miniprogram/tests/*` | — | 不部署 | — |
| 后端 / DB / systemd / nginx / Freeark | 无变化 | 无 | — | 不触碰（画像 P7、P8） |

**版本标识（部署前必须记录）**：本地 `git rev-parse HEAD`（计划编制时 = `3df752be4fa2914c30bd73389f7d19215b53ab92`）；本批产品代码**均未提交**（工作树相对 HEAD：`git status --short` 在 frontend/miniprogram/themes/scripts 范围内 44 个修改 + 1 个暂存删除 + 20 个未跟踪项，其中 11 个 `frontend/tests/*.spec.js`、1 个 `miniprogram/tests/brand_login.spec.js` 为新测试）。所以 HEAD 不能单独定位版本，**定位依据 = `git status --short` 摘要 + 本地 `frontend/dist/index.html` 的 SHA256 + `frontend_dist.tar.gz` 的 SHA256**（M-DE-006）。计划编制时本地构建（带 `VITE_API_BASE`）的参考值：`dist/index.html` SHA256 `b451dab9…65c6`，1039 B，入口 `index-DoXyBgF2.js`、`index-C-LMq4Cp.css`，`dist` 共 69 个文件、2.3 MB，字体 `assets/OcapBrand-subset-c41YCxaj.woff2`（SHA256 `c02ca28c…2109`，与 `frontend/src/brand/fonts/OcapBrand-subset.woff2` 一致）。E2 以自己的构建为准，工作树若又有变化则值会不同，不是阻断项，但必须记录。

**命令与调用指令的差异（请 PM 注意）**：invocation 写的构建命令为 `npm run build -- --base=/ocap/`。本地实测，缺少 `VITE_API_BASE` 时产物把接口前缀写成默认 `/api/v1`（`frontend/src/shared/http.js:8`；`dist` 入口 js 中不含 `/ocap/api/v1`，`grep -c` = 0），部署后所有接口请求会打到 `/api/v1/*` 而 404；带 `VITE_API_BASE=/ocap/api/v1`（CI 与 ocap-deploy skill DEPLOY-006 的写法）则含该串（`grep -c` = 1）。本计划一律使用带变量的写法。

## 目标环境与策略

- 环境：**测试**（画像 P7；树莓派；外网 SSH `-p 57279 yangyang@47.109.197.217`，首次连接核对 ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，不一致即停止上报；内网 `192.168.31.51:22`）。生产为"无"，不设计晋升；`ai-freeark.xin:9999` 不可用，不使用。
- 策略：**recreate**（单实例静态目录整体替换，画像允许）。理由：无多实例/两套环境，不具备 rolling、blue-green、canary 的前提；变更仅为静态文件，无数据与后端状态。通过"先在目标机 `/tmp` 暂存并校验，再在同一文件系统内 `rm` + `cp -a` 替换"把不一致窗口压到最短。
- 预计停机：前端静态目录替换窗口 < 数秒 [INFERRED，无实测]；后端、数据库**零停机**（不重启）。已打开旧页面的浏览器标签引用的旧哈希 chunk 在替换后会 404（回退为 index.html），用户刷新即恢复，属 SPA 部署的通性影响 [INFERRED]。
- 回滚偏好：画像未写。因变更未提交，"在源头 revert 后重新部署"不适用；采用"切回上一版本制品"（目标机 `web-<TS>.tar.gz` 快照），符合 skill §7，不用 `git reset --hard` / `git clean` / `git stash`。

### SSH 通道与本地变量（沿用上批，M-DE-009/010/023）

```bash
# 套接字目录必须短路径；本地临时目录用 mktemp，使用前校验非空，不得写到 / 下
CM=$(mktemp -d /tmp/ocs.XXXX)
SCRATCH=$(mktemp -d /tmp/ocpkg.XXXX)
[ -n "$CM" ] && [ -d "$CM" ] && [ -n "$SCRATCH" ] && [ -d "$SCRATCH" ] && echo "DIRS_OK" || echo "DIRS_EMPTY_STOP"
OCAP_SSH="ssh -p 57279 -o ControlMaster=auto -o ControlPath=$CM/%C -o ControlPersist=10m yangyang@47.109.197.217"   # 内网改 -p 22 yangyang@192.168.31.51
OCAP_SCP="scp -P 57279 -o ControlPath=$CM/%C"
OCAP_DEST="yangyang@47.109.197.217"

# 建连重试：只重试"建连"，以显式标记判定；连上后一次性完成只读预检
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

- 连续 8 次建连失败即停止汇报。已开始的**非幂等**命令（`rm`、`cp -a`）失败时先只读核对状态，不盲目重试。
- `$OCAP_SSH` 不加引号使用。远端命令要用本地值（`TS`、`OWN`）时一律**双引号**，并在执行前 `echo` 完整命令核对；远端要自己展开的 `$` 在双引号里写 `\$`；单引号命令内的 `$VAR` 在远端展开，只在本意如此时使用。多行远端脚本用 `$OCAP_SSH bash -s -- "$TS" <<'EOF' … EOF`（本计划命令块不嵌套 heredoc）。
- `TS` 在 DEPLOY-001 取一次并全程复用（M-DE-003）；跨会话时由 PM 写入 invocation，不依赖 shell 状态。
- 结束清理：先 `echo "$CM" "$SCRATCH"` 确认非空且以 `/tmp/ocs.`、`/tmp/ocpkg.` 开头，再 `ssh -O exit -o ControlPath=$CM/%C yangyang@47.109.197.217; rm -rf "$CM" "$SCRATCH"`。

## 预检清单

先在仓库根设定本地变量（预检与 DEPLOY-002 共用）：
```bash
cd /root/myproject/ocap
git rev-parse HEAD; git status --short | wc -l            # 记录 HEAD 与变更条数
```

### 开发机（只读 + 本地构建，不触碰目标机）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-01 版本标识已记录 | `git rev-parse HEAD`；`git status --short -- frontend miniprogram themes scripts \| awk '{print $1}' \| sort \| uniq -c` | 已记录（输出写入报告）；未提交是已知状态，不是阻断项 |
| PRE-02 后端/依赖/部署模板零改动 | `git status --short -- backend deploy frontend/package.json frontend/package-lock.json miniprogram/package.json \| wc -l` | `0`（非 0 → 停止上报：本计划假设后端不变、无新依赖） |
| PRE-03 无游离文件 | `git ls-files --others --exclude-standard frontend miniprogram themes scripts \| grep -vE '^(frontend/(src\|tests)/\|miniprogram/tests/)'` | 无输出（`frontend/dist` 已 gitignore，`git check-ignore frontend/dist` 有输出）；`frontend/src` 下未跟踪文件应为本批 34 个新源文件（`git ls-files --others --exclude-standard frontend/src \| wc -l` = 34） |
| PRE-04 风格生成物无漂移 | `node scripts/themes/build.mjs --check --strict; echo EXIT=$?` | `EXIT=0`（计划编制时已实测 0） |
| PRE-05 前端 vitest 全绿 | `(cd frontend && npx vitest run --passWithNoTests 2>&1 \| tail -6)`；可选：`(cd miniprogram && npx vitest run --passWithNoTests 2>&1 \| tail -6)` | 前端 `Test Files 37 passed (37)`、`Tests 438 passed (438)`（计划编制时实跑，耗时约 200 秒，勿用短超时）；小程序 16 个文件/119 条（PM 在 GR-D-002 实跑，E2 可选复跑）。有失败 → 停止，不部署 |
| PRE-06 构建与产物核验 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/ 2>&1 \| tail -3`；然后 `ls frontend/dist/assets \| grep -c '^OcapBrand-subset-.*\.woff2$'`；`grep -o '<title>[^<]*' frontend/dist/index.html`；`grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js`；`grep -o 'url(/ocap/assets/OcapBrand-subset-[^)]*)' frontend/dist/assets/index-*.css`；`sha256sum frontend/dist/assets/OcapBrand-subset-*.woff2 frontend/src/brand/fonts/OcapBrand-subset.woff2` | 构建 `✓ built`（大 chunk 提示不算失败）；woff2 个数 `1`；标题 `<title>Cyber@红枫岭`；`/ocap/api/v1` 计数 ≥ 1；CSS 含 `url(/ocap/assets/OcapBrand-subset-<hash>.woff2)`；两个 SHA256 相同（计划编制时 `c02ca28c…2109`）。把 `dist/index.html` 的 SHA256、`dist` 文件数记入报告 |

### 目标机（只读；`ocap_connect` 成功后一次性完成）

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-07 可达与指纹 | `ocap_connect`；核对 `known_hosts` 中该端口 ED25519 指纹 | `CONNECT_OK`；指纹与画像 P7 一致 |
| PRE-08 磁盘/内存 | `$OCAP_SSH 'df -h /home; free -m'` | /home 可用 ≥ 2 GB；可用内存 ≥ 500 MB |
| PRE-09 端口归属 | `$OCAP_SSH 'ss -ltn'` | 8000/8080/80 非 ocap 占用；9000/8090 仅 ocap |
| PRE-10 目录与必须保留的本地状态 | `$OCAP_SSH 'ls -la /home/yangyang/ocap /home/yangyang/ocap/web; test -f /home/yangyang/ocap/backend/.env && echo ENV_OK; test -d /home/yangyang/ocap/backend/venv && echo VENV_OK; test -d /home/yangyang/ocap/backend/var && echo VAR_OK; ls -l /home/yangyang/ocap/snapshots \| tail -15'` | `backend/ web/ snapshots/`（可能另有上批 `ocap_exports/` 同级目录，仅记录）；三个 OK（`.env`、`venv`、`var` 本批**不触碰**）；`snapshots/` 内上批备份（含个人信息的 `ocapdb-*.sql`、`shops-*.jsonl`、`residency_appeal-*.sql`、`underground-*.jsonl`）**存在，本计划任何步骤不得删除**（上批两份保留至 2026-11-23） |
| PRE-11 web/ocap 当前属主（M-DE-013） | `$OCAP_SSH 'stat -c "%U:%G %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html'` | 记录（上批为 yangyang:yangyang，sudo 写法仍兼容）；记为 `OWN`，格式须匹配 `^[a-z_][a-z0-9_-]*:[a-z_][a-z0-9_-]*$` |
| PRE-12 后端当前状态与"未重启"基线 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'` | `active`；记录 `ActiveEnterTimestamp`、`MainPID` 为基线（部署后须不变，证明后端未重启） |
| PRE-13 nginx 与 Freeark 基线 | `$OCAP_SSH 'sudo nginx -t; curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/'` | `syntax is ok`；`200` |
| PRE-14 SPA 回退与 woff2 MIME 的**只读**前置核对（OQ-B05） | `$OCAP_SSH 'sudo grep -n "try_files" /etc/nginx/sites-available/ocap'`；`$OCAP_SSH 'grep -c woff2 /etc/nginx/mime.types; sudo grep -nE "woff|types" /etc/nginx/sites-available/ocap /etc/nginx/sites-enabled/freeark; echo GREP_DONE'` | `location /ocap/` 含 `try_files $uri $uri/ /ocap/index.html`；`mime.types` 对 woff2 计数 ≥ 1（预期映射 `font/woff2`）；`ocap` 与 `freeark` 站点内没有对 `woff` 的特殊 `types`/正则覆盖（有则记录并在报告中说明）。**仅读取，不修改任何 nginx 文件**。结果为预判，真实结论以部署后 V-08 为准 |
| PRE-15 当前线上页面基线（供回滚核对） | `$OCAP_SSH 'cd /home/yangyang/ocap/web/ocap && sha256sum index.html && grep -o "assets/[^\"]*" index.html'`；`curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/` | 记录旧 `index.html` SHA256 与旧入口文件名；公网 `200 text/html` |

## 部署步骤

### DEPLOY-001: 生成回滚锚点并快照 Web 静态目录
- 组件：`/home/yangyang/ocap/web`（architecture_design 部署视图：Web 前端静态文件）。后端不触碰，故**不做 backend 快照**、不改 nginx，故不备份 nginx 配置（与 skill DEPLOY-001 相比有意缩减，理由：本批对二者零写入）。
- 位置：目标机；`TS` 在本地取一次
- 命令：
```bash
TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S'); echo "ANCHOR_TS=$TS"
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_FORMAT_OK || echo TS_BAD_STOP
$OCAP_SSH bash -s -- "$TS" <<'EOF'
set -e
TS="$1"; A=/home/yangyang/ocap
mkdir -p $A/snapshots
sudo tar czf $A/snapshots/web-$TS.tar.gz -C $A web
# 逐文件哈希清单：回滚后逐项核对（只含静态资源哈希，无个人信息）
cd $A/web/ocap && find . -type f -print0 | sort -z | xargs -0 sha256sum > $A/snapshots/webhash-$TS.sha256
ls -l $A/snapshots/web-$TS.tar.gz $A/snapshots/webhash-$TS.sha256
wc -l $A/snapshots/webhash-$TS.sha256
tar tzf $A/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html$'
sha256sum $A/snapshots/web-$TS.tar.gz
EOF
```
- 预期：输出 `ANCHOR_TS`、`TS_FORMAT_OK`；快照非零大小；哈希清单行数 = 旧 `web/ocap` 文件数；`grep -c` 输出 `1`（快照含 `web/ocap/index.html`）；SHA256 记入报告。快照与哈希清单保留 ≥ 7 天。失败且目标机无变更 → `DEPLOYMENT_FAILED`，无需回滚。
- 回滚: ROLLBACK-001

### DEPLOY-002: 开发机构建并打包前端产物
- 组件：Web 前端（MOD-119~128、130）
- 位置：开发机
- 命令：
```bash
echo "$SCRATCH"                                                   # 必须非空且为 /tmp/ocpkg.*
VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/
[ "$(ls frontend/dist/assets | grep -c '^OcapBrand-subset-.*\.woff2$')" = "1" ] && echo WOFF2_PRESENT || echo WOFF2_MISSING_STOP
grep -c '/ocap/api/v1' frontend/dist/assets/index-*.js           # 须 >= 1
tar -czf "$SCRATCH/frontend_dist_$TS.tar.gz" -C frontend/dist .
sha256sum "$SCRATCH/frontend_dist_$TS.tar.gz" frontend/dist/index.html
find frontend/dist -type f | wc -l                               # 记录文件数，DEPLOY-003 暂存目录须一致
```
- 预期：`✓ built`；`WOFF2_PRESENT`；`/ocap/api/v1` 计数 ≥ 1；打包 SHA256、`index.html` SHA256、文件数记入报告。不使用 pscp 逐文件上传（P8）、不使用容器。失败 → 目标机仅多了快照，`DEPLOYMENT_FAILED`。
- 回滚: ROLLBACK-002

### DEPLOY-003: 上传、校验并在目标机暂存
- 位置：开发机 → 目标机（`/tmp` 下，文件名含 `TS`，避免与他物冲突）
- 命令：
```bash
$OCAP_SCP "$SCRATCH/frontend_dist_$TS.tar.gz" "$OCAP_DEST:/tmp/"
$OCAP_SSH "sha256sum /tmp/frontend_dist_$TS.tar.gz"               # 须与 DEPLOY-002 本地值一致
$OCAP_SSH "rm -rf /tmp/ocap_web_stage_$TS && mkdir /tmp/ocap_web_stage_$TS && tar xzf /tmp/frontend_dist_$TS.tar.gz -C /tmp/ocap_web_stage_$TS && ls /tmp/ocap_web_stage_$TS/index.html && ls /tmp/ocap_web_stage_$TS/assets | grep -c '^OcapBrand-subset-.*\.woff2\$' && find /tmp/ocap_web_stage_$TS -type f | wc -l && sha256sum /tmp/ocap_web_stage_$TS/index.html"
```
- 预期：两端 tar SHA256 一致；暂存目录含 `index.html`；woff2 个数 `1`；文件数 = DEPLOY-002 记录值；暂存 `index.html` SHA256 = 本地 `dist/index.html`。任一不符 → 停止（目标机 `web/ocap` 尚未改动），按 ROLLBACK-003 清理暂存，报告 `DEPLOYMENT_FAILED`。
- 注意：`$` 在双引号中已为本地展开（`$TS`）；`grep` 模式末尾的 `\$` 保证远端收到字面 `$`。执行前 `echo` 完整命令核对。
- 回滚: ROLLBACK-003

### DEPLOY-004: 替换 Web 静态目录（唯一改动线上的步骤）
- 组件：`/home/yangyang/ocap/web/ocap`（nginx 站点 `ocap`，root `/home/yangyang/ocap/web`；Freeark 经 `^~ /ocap/` 反代，均不改）
- 位置：目标机；`OWN` 取自 PRE-11
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap/* && sudo cp -a /tmp/ocap_web_stage_$TS/. /home/yangyang/ocap/web/ocap/ && sudo chown -R $OWN /home/yangyang/ocap/web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && find /home/yangyang/ocap/web/ocap -type f | wc -l && sha256sum /home/yangyang/ocap/web/ocap/index.html"
echo "$CMD"                                   # 核对 TS、OWN 已展开且 OWN 形如 yangyang:yangyang
$OCAP_SSH "$CMD"
```
- 预期：`index.html` 存在；文件数 = 本地 `dist` 文件数；`index.html` SHA256 = 本地值；资源路径以 `/ocap/assets/` 开头。`rm -rf web/ocap/*` 同时清除旧哈希资源（与 skill DEPLOY-006 一致）。`ls -l` 或 `find` 失败而 `rm` 已执行 → 目标机已有变更，**立即**从 ROLLBACK-004 起逆序回滚。
- 回滚: ROLLBACK-004

### DEPLOY-005: 验证通过后清理临时文件
- 位置：目标机；**仅在「部署后验证」全部通过（或 PM 决定保留现状）之后执行**；验证失败需回滚时先保留暂存，回滚完成后再清理
- 命令：
```bash
CMD="rm -rf /tmp/ocap_web_stage_$TS && rm -f /tmp/frontend_dist_$TS.tar.gz && ls /tmp/ocap_web_stage_$TS /tmp/frontend_dist_$TS.tar.gz 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 预期：两项均 `No such file or directory`。只删本次上传的两个路径（带 `TS`，不用通配符），不删 `snapshots/` 下任何文件。
- 回滚: ROLLBACK-005

## 回滚步骤（逆序）

**执行前核验变量（所有回滚通用）**：
```bash
TS=<DEPLOY-001 记录的 ANCHOR_TS>
echo "$TS" | grep -Eq '^[0-9]{14}$' && echo TS_OK || echo TS_BAD_STOP
$OCAP_SSH "ls -l /home/yangyang/ocap/snapshots/web-$TS.tar.gz /home/yangyang/ocap/snapshots/webhash-$TS.sha256"
$OCAP_SSH "tar tzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz | grep -c '^web/ocap/index.html\$'"      # 须为 1
```
快照与哈希清单都存在且计数为 1 才继续。远端命令一律双引号使 `$TS` 在本地展开，执行前 `echo` 完整命令核对。**禁止** `git reset --hard`、`git clean`、`git stash`、覆盖式 rsync；**不动** `backend/`（含 `.env`、`venv`、`var`）、`snapshots/` 中任何既有文件、nginx、Freeark。回滚不需要重启或 reload 任何服务。

### ROLLBACK-005: 回滚 DEPLOY-005
- 类型：无操作（临时文件已清理是预期终态；需要时可从本地 `$SCRATCH` 重新上传）。

### ROLLBACK-004: 回滚 DEPLOY-004（恢复旧 Web 静态目录）
- 类型：正式回滚（切回上一版本制品）；DEPLOY-004 之后的第一个回滚动作
- 命令：
```bash
CMD="sudo rm -rf /home/yangyang/ocap/web/ocap && sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web/ocap && ls -l /home/yangyang/ocap/web/ocap/index.html && cd /home/yangyang/ocap/web/ocap && sha256sum -c /home/yangyang/ocap/snapshots/webhash-$TS.sha256 | grep -v ': OK'; echo HASH_CHECK_DONE; find /home/yangyang/ocap/web/ocap -type f | wc -l"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` = DEPLOY-001 的 `ANCHOR_TS`；上节核验通过。仅解包快照内的 `web/ocap`（不触碰 `web/` 下其他内容）。
- 预期：`index.html` 存在；输出中**只出现** `HASH_CHECK_DONE`，不得有非 `OK` 行（否则回滚未生效，停止并报告 `ROLLBACK_FAILED`）；文件数 = 旧文件数（webhash 清单行数）；`curl -s -m 15 -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` 为 `200`，`index.html` SHA256 = PRE-15 记录的旧值。
- 收尾：回滚完成后执行 ROLLBACK-003 清理暂存；上述验证全部通过后目标机即与部署前一致。

### ROLLBACK-003: 回滚 DEPLOY-003（清理暂存与上传文件）
- 类型：正式回滚
- 命令：
```bash
CMD="rm -rf /tmp/ocap_web_stage_$TS && rm -f /tmp/frontend_dist_$TS.tar.gz && ls /tmp/ocap_web_stage_$TS /tmp/frontend_dist_$TS.tar.gz 2>&1"
echo "$CMD"; $OCAP_SSH "$CMD"
```
- 变量取值与核验：`TS` 须通过格式校验（14 位数字），路径写全、无通配符；预期两项 `No such file or directory`。

### ROLLBACK-002: 回滚 DEPLOY-002（本地构建与打包）
- 类型：无目标机操作。`frontend/dist` 是 gitignore 的构建产物，无需处理；本地 `$SCRATCH` 在结束清理时随之删除（先校验非空且前缀正确）。

### ROLLBACK-001: 回滚 DEPLOY-001
- 类型：无操作。快照 `web-$TS.tar.gz` 与 `webhash-$TS.sha256` 保留 ≥ 7 天，不删除。

## 不可逆步骤汇总

**无** `[MANUAL_ROLLBACK_REQUIRED]` 项。本批无数据迁移、无外部系统调用、无通知发送、无个人信息文件生成。说明：
- 浏览器本地存储新增键 `ocap_admin_name`（module_design「数据迁移」）仅存在于用户浏览器，回退到旧前端后无人读取，无残留风险。
- 仅有的"只能前进"现象是 SPA 旧页面 chunk 失效（刷新即恢复），不是数据问题。
- 小程序发布不是 DEPLOY 步骤，无 ROLLBACK 命令（见下）。

## 部署后验证

执行时机：DEPLOY-004 完成后、DEPLOY-005 之前。公网检查在**主会话/开发机**用 `curl -m 15`（M-DE-022：不用 `pkill -f`；内网地址 `192.168.31.51:8090` 外网不可达，改在目标机内 `curl 127.0.0.1:8090`）。本地值 `LOCAL_INDEX_SHA`、`W`（woff2 文件名）、`WSHA` 取自 DEPLOY-002 / PRE-06 记录；`W` 用 `ls frontend/dist/assets | grep '^OcapBrand-subset-.*\.woff2$'` 取，须恰好 1 个。**SPA 回退陷阱（M-DE-029）**：`/ocap/` 下任何不存在的路径都会返回 200 + `index.html`，所以静态资源与字体的判据是"内容类型 + 大小 + SHA256"，**不是 200 状态码**。

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| V-01 后端未重启、仍存活 | `$OCAP_SSH 'systemctl is-active ocap-backend; systemctl show ocap-backend -p ActiveEnterTimestamp -p MainPID'` | `active`；`ActiveEnterTimestamp`、`MainPID` 与 PRE-12 相同（证明本批没有重启后端） |
| V-02 后端日志无新错误 | `$OCAP_SSH "sudo journalctl -u ocap-backend --since '-5 min' --no-pager \| grep -ciE 'Traceback\|ERROR'"` | 输出 `0`（本批不改后端，仅做基线确认） |
| V-03 线上 index.html = 本地构建 | `curl -s -m 15 https://ai-freeark.xin/ocap/ \| sha256sum`；对照本地 `sha256sum frontend/dist/index.html` | 两者相同 |
| V-04 内网入口 | `$OCAP_SSH 'curl -s -m 15 -o /dev/null -w "%{http_code} %{content_type}\n" http://127.0.0.1:8090/ocap/'`（等价内网 `http://192.168.31.51:8090/ocap/`） | `200 text/html` |
| V-05 公网入口 | `curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/` | `200 text/html`，大小 = 本地 `dist/index.html` 字节数（计划编制时 1039） |
| V-06 页面标题 | `curl -s -m 15 https://ai-freeark.xin/ocap/ \| grep -o '<title>[^<]*</title>'` | `<title>Cyber@红枫岭</title>` |
| V-07 入口 js/css | 对 `index.html` 引用的 `/ocap/assets/index-*.js`、`index-*.css` 各：`curl -s -m 15 -o "$SCRATCH/a" -w '%{http_code} %{content_type} %{size_download}\n' <URL>`；`sha256sum "$SCRATCH/a"` | `200`；`javascript` / `text/css`（不是 `text/html`）；SHA256 = 本地 `dist` 同名文件 |
| V-08 **woff2 字体与 Content-Type（OQ-B05）** | 公网：`curl -s -m 15 -o "$SCRATCH/w.woff2" -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap/assets/$W`；`sha256sum "$SCRATCH/w.woff2"`；内网：目标机 `curl -sI -m 15 http://127.0.0.1:8090/ocap/assets/$W`（`$W` 在本地展开，用双引号） | `200`；`Content-Type` 为 `font/woff2`（首选）；大小 `12044`；SHA256 = `c02ca28c…2109`（= `WSHA`）；**不得是 `text/html`**（那表示 SPA 回退，文件没部署上）。若 Content-Type 不是 `font/woff2`，按下节「woff2 类型异常处理」，状态记 `DEPLOYED_WITH_ISSUES`（字体照常可用的情形也如实记） |
| V-09 CSS 引用字体路径正确 | `curl -s -m 15 https://ai-freeark.xin/ocap/assets/<index-*.css> \| grep -o 'url(/ocap/assets/OcapBrand-subset-[^)]*)'` | 输出与 V-08 的 `$W` 一致 |
| V-10 新路由深链刷新可达（只读，对应 nginx history fallback） | 对下列路径各：`curl -s -m 15 -o "$SCRATCH/d" -w '%{http_code} %{content_type} %{size_download}\n' https://ai-freeark.xin/ocap<路径>`：`/me/profile`、`/units/review`、`/resolutions/mine`、`/admin/finance/limit`、`/admin/users/registered`、`/admin/content/services/prompts`、`/admin/login`、`/login`；并 `sha256sum "$SCRATCH/d"` | 8 条均 `200 text/html`，大小与 SHA256 均 = `index.html`（证明回退由 `try_files … /ocap/index.html` 提供；刷新后由前端路由与守卫接管，未登录者会被前端重定向到登录页，这不是服务端问题）。PRE-14 的 `try_files` 读取结果一并写入报告 |
| V-11 接口前缀与鉴权（只读、无令牌、无写入） | `curl -s -m 15 -o /dev/null -w '%{http_code} %{content_type}\n' https://ai-freeark.xin/ocap/api/v1/me` | `401`（或 `403`），内容类型为 JSON；**不是** `404` 或 `text/html`（证明产物使用的 `/ocap/api/v1` 前缀由后端响应；`GET /me` 在 module_design 对外接口表中，`IsMember` 鉴权） |
| V-12 Freeark 与端口未受影响 | `curl -s -m 15 -o /dev/null -w '%{http_code}\n' https://ai-freeark.xin/`；`$OCAP_SSH 'systemctl --state=failed --no-pager; ss -ltn'` | `200`；无 `freeark-*`、`ocap-*` 失败单元；8000/8080 属 Freeark，8090/9000 属 ocap |
| V-13 目标机落盘状态 | `$OCAP_SSH 'stat -c "%U:%G %a %n" /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html; find /home/yangyang/ocap/web/ocap -type f \| wc -l; ls -l /home/yangyang/ocap/snapshots/web-*.tar.gz \| tail -3'` | 属主 = `OWN`；`index.html` 权限为 nginx 可读（644）；文件数 = 本地 `dist`（69）；本次快照存在 |
| V-14 本地状态未被触碰 | `$OCAP_SSH 'test -f /home/yangyang/ocap/backend/.env && test -d /home/yangyang/ocap/backend/venv && test -d /home/yangyang/ocap/backend/var && echo LOCAL_STATE_INTACT; ls -l /home/yangyang/ocap/snapshots/ \| grep -E "ocapdb-registry-20261116134900.sql\|underground-20261116134900.jsonl"'` | `LOCAL_STATE_INTACT`；上批两份保留备份仍在 |

全部通过 → `DEPLOYED_SUCCESSFULLY`（交付最终状态仍受人工验证项影响，见下）；部分失败 → `DEPLOYED_WITH_ISSUES`，列失败项，由用户决定是否回滚（不自行回滚，除非步骤本身失败，按 E2 规则）。

### woff2 类型异常处理（OQ-B05，只给建议，E2 不执行）

| 观察 | 含义 | 建议（须用户确认后由人或另行授权的步骤执行） |
|---|---|---|
| `200 font/woff2`，大小与 SHA256 一致 | 正常 | 无 |
| `200`，`application/font-woff2`、`font/woff`、`application/octet-stream` 等非 `font/woff2`，大小与 SHA256 一致 | 文件已部署，浏览器一般仍会按字体解码（同源、`@font-face` 对 MIME 容忍度高 [UNSOURCED]，以 MV-05 目视为准）；`mime.types` 未映射或有覆盖 | 先在 PRE-14 结果中定位来源。`/ocap/` 静态资源由 **ocap 站点（8090，`/etc/nginx/sites-available/ocap`）** 响应，Freeark 层只反代透传（`^~ /ocap/` 前缀块）。优先方案：在 ocap 站点 `server` 块内增加 `types { font/woff2 woff2; }`（或在 `mime.types` 补一行），按 skill §3 只允许改 ocap 站点，**改前先备份**（`sudo cp -a /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_<TS>`）、`sudo nginx -t`、`sudo systemctl reload nginx`（不得 restart）。**不得擅自改 Freeark nginx**（画像 P7：修改前须备份并经用户确认）；若根因在 Freeark 层，只报告不改 |
| `200 text/html`，大小 = index.html | 字体文件未到位或路径错误（SPA 回退） | 回查 DEPLOY-003/004 的文件数与 `dist` 清单；确认 `$W` 取值正确；仍异常则回滚 |
| `404`/其他 | 站点未配置或前缀块异常 | 回查 `^~ /ocap/` 与 `sites-enabled/freeark`（只读），上报用户 |

## P4-1 远程 HTTP 用例：本批不适用

- 画像 P4-1 的远程用例（`backend/tests/remote/`，经公开入口、只用 `e2e_` 账号）验证的是**后端 API 与前后端契约**。本批后端、`api.js` 两份契约文件零改动（PRE-02 核对），契约由本地 `frontend/tests/layout_contract.spec.js`（6/6）与既有后端契约测试守护；因此**不运行远程套件、不创建/清理 `e2e_` 夹具、不登录任何账号**，E2 在本批只发无令牌的只读 GET（V-03~V-12）。
- 若用户希望在部署后仍跑一次远程套件作额外回归：须另行授权，并按 `ocap_owner_auth_v2` 计划阶段 E 的做法（M-DE-020：夹具循环放入同一 `trap cleanup EXIT` 调用、口令经 stdin、遵守 `Remote` 的 GET 护栏与 WRITE_ALLOWLIST），本计划不含。

## 人工验证清单（部署后由用户执行，**不由部署脚本执行**）

来源：`testing/e2e_test_report.md`（1.0.0 APPROVED）人工验证清单。E2 在报告中只引用，不代为验收；这 5 项未全部完成前，最终交付状态至多 DELIVERED_WITH_ISSUES（GR-D-002-F01）。建议在 DEPLOY-004 完成并通过 V-01~V-14 后，用户用**强制刷新**（Ctrl+F5，避免旧缓存的 `index.html`）在公网入口 `https://ai-freeark.xin/ocap/` 执行；写操作超出 P4-1 的部分不做，浏览均为只读。

| 编号 | 对应 AC | 做法（摘要，详见 e2e_test_report） | 期望 | 执行人 / critical path |
|---|---|---|---|---|
| MV-01 | AC-218-01~04、219-01/03、220-04、230-03、231-01、227-04、209-04 | 视口 1366×768、1920×1080、2560×1440、3840×2160（及 1280×720、4K 缩放 150%）下浏览用户端与管理端各页及登录页；DevTools 在 767↔768 宽度间拖动 | 无横向滚动；内容区占用宽度 ≥ 90%；1366×768 下 9 项一级菜单无需滚动；767/768 切换时底栏与侧栏/抽屉不同时出现；登录页配图不覆盖表单 | 用户；critical path |
| MV-02 | AC-219-02、231-02 | 1366×768 打开 AdminRegistry、AdminSeats、AdminUsers（注册用户）表格与"新增专有部分"弹窗；用户端决议列表/收入表/我的房屋各二级页 | 无横向滚动、控件不重叠、弹窗完整可见（AdminRegistry 静态余量仅约 20px，OQ-B07，重点看） | 用户；critical path |
| MV-03 | AC-228-01 | **小程序，不在本次部署内**：在微信开发者工具（或真机）分别设置本地风格记忆 neon/bento/terminal，打开 `pages/login/index` | 三版均显示 `Cyber@红枫岭` 与 CSS 配图，无错位/缺失，无远程字体请求 | 用户；非 critical path（Should Have） |
| MV-04 | AC-209-05(4)、227-01 | 三种设备风格记忆下依次打开 `/ocap/login`、`/ocap/register`、`/ocap/admin/login`，按"科技感观察清单"逐项判断 | 4 项全部为"是"，用户确认有赛博科技感（验收人为用户） | 用户；critical path |
| MV-05 | AC-209-03、227-04 | DevTools 阻断 `OcapBrand-subset-*.woff2`（或离线）后刷新三个登录页；正常加载时目视品牌名字形。**Content-Type 部分已由 E2 在 V-08 以只读 HTTP 核对**，用户只需做目视与断网回退 | 阻断后回退系统字体、表单完整、无乱码、无字体相关弹窗；正常时为得意黑风格字形 | 用户；critical path |

## 小程序说明（不在本次部署范围）

- 小程序的 `pages.json`、登录页与生成样式已改（MOD-129），jsdom 层 15 条用例通过；`npm run build:mp-weixin` 在本机基线即失败（`@dcloudio/uni-mp-weixin/dist/uni.compiler.js not found` 等，GR-C-001-F04，改动前同样失败），画像 P7 也没有小程序发布环境，因此本计划**不构建、不发布、不上传**小程序，也无 ROLLBACK。
- 后端不变，新旧小程序与后端的接口契约完全一致，小程序发布时序不受本次 Web 部署影响（对比 `ocap_owner_auth_v2` 的 R1/R2/R3 顺序问题，本批不存在）。
- 用户在微信开发者工具中自行构建、预览并按 MV-03 核对；要正式发布则按微信公众平台流程，撤回 = 回退到上一线上版本（人工，无命令）。

## 自检记录

- 每个 DEPLOY（001~005）均有对应 ROLLBACK（001~005），按编号逆序排列；回滚实际执行顺序为 004 → 003（收尾清理）；无 `[MANUAL_ROLLBACK_REQUIRED]` 项（无迁移、无数据写入）。
- 依赖顺序：基础设施/数据层/服务层无变化，仅"快照 → 构建打包 → 上传暂存校验 → 替换静态 → 验证 → 清理"。
- 环境仅为画像 P7 的「测试」；策略 recreate 已写理由；无 Docker、pscp、makemigrations 产物、目标机生成迁移、Freeark 或 nginx 改动（woff2 异常处理仅为建议，需用户确认并备份）。
- 回滚不使用 reset/clean/stash/覆盖式 rsync，不动 `backend/`、`.env`、`venv`、`var` 与既有快照；变量 `TS`、`OWN`、`W`、`WSHA` 均写了取值来源与核验方法；远端命令使用双引号并要求先 `echo`；不含嵌套 heredoc；`SCRATCH`/`CM` 先 `mktemp` 并校验非空。
- `[INFERRED]` 项汇总：静态目录替换窗口 < 数秒；旧页面 chunk 失效的用户影响；`@font-face` 对非 `font/woff2` MIME 的容忍度（标 `[UNSOURCED]`，以 MV-05 为准）；`/ocap/api/v1/me` 无令牌返回 401/403（来自 `IsMember` 与既有部署计划，未在目标机实测，V-11 以实测为准）；上批 `ocap_exports/` 目录是否存在于部署根同级（仅记录）。
- 本地只读/构建核验（E1 阶段，非目标环境）：`node scripts/themes/build.mjs --check --strict` 退出码 0；前端 vitest 37 文件 / 438 条通过；带 `VITE_API_BASE` 构建成功，woff2 带哈希进入 `dist`，CSS 引用路径正确。`frontend/dist` 为构建副产物（gitignore）。
- 子代理 E1 未执行 ssh/scp/commit/push，未安装依赖、未联网。
