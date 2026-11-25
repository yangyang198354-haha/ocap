<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-25T13:06:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap_role_home/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_role_home/architecture/module_design.md</file>
    <file>project_workspace/ocap_role_home/testing/e2e_test_report.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — ocap_role_home（测试环境）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| Web 前端 | `frontend/src/portal/Home.vue`、`frontend/src/stores/auth.js`、`frontend/src/shared/style.css` | 无 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | nginx 静态目录整体替换 |
| 主题产物 | 未修改 `themes/*.theme.json` | 无 | 不需要重新生成（CI 仍做一致性校验） | 无 |
| 微信小程序 | `miniprogram/pages/index/index.vue`、`miniprogram/store/auth.js` | 无 | `UNI_INPUT_DIR=. npx uni build -p mp-weixin` | 仅构建验证；上传发布由用户执行，不在本次范围 |
| Django 后端 | 无变更 | 无 | 无 | 不重启、不迁移 |

## 目标环境与策略

- 目标环境：画像 P7 的**测试环境**（树莓派，内网 nginx `8090`，外网 frp `443`）；生产环境在画像中不存在，不设计晋升。
- 策略：**recreate（前端静态目录整体替换 + 原子改名）**。
  - 选择理由：单实例、后端与数据层均无变更；静态目录可整体交换，无需多版本共存或流量切换能力；比 rolling/blue-green/canary 更简单且不引入画像中不存在的设施。
  - 预计停机：`mv` 两次调用之间的毫秒级窗口，预计 0–5 秒；后端与数据库不受影响。
- 部署需用户确认：**是**（画像 P7）。GROUP_E2 必须由用户当轮明确授权测试环境，授权不得从文档或子代理输出推导。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| 待部署提交已推送 | `git rev-parse HEAD`；`git ls-remote origin <branch>`；由用户/PM 执行提交与推送（画像 P9） | `DEPLOY_SHA` 存在于远端；记录完整 SHA |
| CI 全绿（建议） | GitHub Actions 最近一次 `main` 运行 | `backend`、`frontend`、`miniprogram` 三个 job 均 success |
| 测试门控 | 查 `phase_status.md` | GROUP_D = APPROVED；GR-D-001 PASS |
| 目标机当前版本（回滚锚点） | `ssh <host> "ls -ld /home/yangyang/ocap/web/ocap && find /home/yangyang/ocap/web/ocap -type f | wc -l"` | 目录存在；记录文件数 `ANCHOR_FILES` 与 `ANCHOR_TS` |
| 锚点快照 | `ssh <host> "cp -a /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap.old-<ANCHOR_TS>"` | 目标目录存在且非空；`find .../ocap.old-<ANCHOR_TS> -type f | wc -l` = `ANCHOR_FILES` |
| 必须保留的本地状态 | `ssh <host> "ls -ld /home/yangyang/ocap/.env /home/yangyang/ocap/venv /home/yangyang/ocap/var"`；部署前后各记录 `sha256sum .env` | 三项存在；本次流程不写入、不移动；`.env` 哈希前后一致 |
| 后端存活基线 | `ssh <host> "systemctl is-active ocap-backend"`；`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | `active`；HTTP 200 |
| 磁盘空间 | `ssh <host> "df -h /home/yangyang/ocap"` | 可用 ≥ 200 MB [INFERRED] |
| 本地构建环境 | `node -v`、`npm -v`、`cd frontend && npm ci` | Node ≥ 20；`npm ci` 退出码 0 |
| 制品正确性 | 构建后 `grep -R "待我表决\|我的房屋\|公开决议" frontend/dist/assets/*.js`；检查 `dist/index.html` 引用的 assets 均存在 | 关键文案命中 ≥ 1；引用文件无缺失 |
| 小程序构建（不部署） | `cd miniprogram && UNI_INPUT_DIR=. npx uni build -p mp-weixin --outDir <临时目录>` | 输出 `DONE Build complete.`；`app.json` 可解析 |
| 变更范围确认 | `git diff --name-only <旧 SHA>..<DEPLOY_SHA>` | 仅前端源码、测试与 `project_workspace/`；无 `backend/`、无迁移、无依赖清单 |
| 授权核对 | E2 invocation 的 `special_instructions` | 含目标环境名“测试环境”；计划版本 = APPROVED 版本 |

## 部署步骤

> 变量约定：`WEB_DIR=/home/yangyang/ocap/web/ocap`、`ANCHOR_TS=<预检记录的时间戳>`、`ANCHOR_FILES=<预检记录的文件数>`、`DEPLOY_TS=<本次时间戳>`、`DEPLOY_SHA=<待部署提交>`。远程命令统一用双引号包裹，避免 `$VAR` 在远端为空（可先 `echo` 完整命令核对）。

### DEPLOY-001: 构建 Web 生产产物

- 组件：Web 前端（architecture_design 部署视图「Web 前端」）。
- 位置：开发机/CI。
- 命令：
  ```
  cd frontend
  npm ci
  VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/
  ```
- 预期：退出码 0；`frontend/dist/index.html` 与 `dist/assets/` 生成；关键文案 grep 命中。
- 回滚：ROLLBACK-001。

### DEPLOY-002: 打包并记录校验和

- 组件：Web 制品。
- 位置：开发机。
- 命令：
  ```
  cd frontend
  tar -czf /tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz -C dist .
  sha256sum /tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz | tee /tmp/ocap-web.sha256
  ```
- 预期：tar 生成；SHA256 记录成功。
- 回滚：ROLLBACK-002。

### DEPLOY-003: 上传制品到目标机

- 组件：Web 制品。
- 位置：开发机 → 目标机。
- 命令：
  ```
  scp /tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz <host>:/home/yangyang/ocap/tmp/
  ssh <host> "cd /home/yangyang/ocap/tmp && sha256sum -c /dev/stdin" < /tmp/ocap-web.sha256
  ```
- 预期：上传成功；远端校验输出 `OK`。
- 回滚：ROLLBACK-003。

### DEPLOY-004: 解包到暂存目录

- 组件：Web 静态资源。
- 位置：目标机。
- 命令：
  ```
  ssh <host> "rm -rf /home/yangyang/ocap/web/ocap.new && mkdir -p /home/yangyang/ocap/web/ocap.new && tar -xzf /home/yangyang/ocap/tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz -C /home/yangyang/ocap/web/ocap.new && find /home/yangyang/ocap/web/ocap.new -type f | wc -l"
  ```
- 预期：解包退出码 0；文件数 > 0；`ocap.new/index.html` 存在。仅删除 `ocap.new` 这一暂存目录，不触碰 `ocap`、`.env`、`venv`、`var`。
- 回滚：ROLLBACK-004。

### DEPLOY-005: 原子替换静态目录

- 组件：nginx 静态站。
- 位置：目标机。
- 命令：
  ```
  ssh <host> "mv /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap.old-${DEPLOY_TS} && mv /home/yangyang/ocap/web/ocap.new /home/yangyang/ocap/web/ocap && ls -ld /home/yangyang/ocap/web/ocap"
  ```
- 预期：两条 `mv` 均成功；`ocap` 指向新产物；旧目录保留为 `ocap.old-${DEPLOY_TS}`。无需重启后端、无需迁移、无需 nginx reload（静态文件按请求读取）。
- 回滚：ROLLBACK-005。

## 回滚步骤（逆序）

### ROLLBACK-005: 回滚 DEPLOY-005（正式回滚，恢复服务）

- 类型：正式回滚。
- 命令：
  ```
  ssh <host> "mv /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap.failed-${DEPLOY_TS} && mv /home/yangyang/ocap/web/ocap.old-${DEPLOY_TS} /home/yangyang/ocap/web/ocap && find /home/yangyang/ocap/web/ocap -type f | wc -l"
  ```
- 变量取值与核验：`DEPLOY_TS` 与 DEPLOY-005 相同；执行前 `ls -ld /home/yangyang/ocap/web/ocap.old-${DEPLOY_TS}` 必须存在且文件数 = `ANCHOR_FILES`。
- 预期：文件数等于 `ANCHOR_FILES`；`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` = 200。

### ROLLBACK-004: 回滚 DEPLOY-004

- 类型：正式回滚（清理暂存）。
- 命令：`ssh <host> "rm -rf /home/yangyang/ocap/web/ocap.new"`。
- 预期：暂存目录不存在；线上目录不变。
- 说明：只删本次自建的 `ocap.new`，不使用 `git clean`、`rm -rf` 指向 `ocap`/`var`/`venv`。

### ROLLBACK-003: 回滚 DEPLOY-003

- 类型：正式回滚（清理上传物）。
- 命令：`ssh <host> "rm -f /home/yangyang/ocap/tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz"`。
- 预期：临时 tar 不存在。

### ROLLBACK-002: 回滚 DEPLOY-002

- 类型：本地清理。
- 命令：`rm -f /tmp/ocap-web-${DEPLOY_SHA:0:8}-${DEPLOY_TS}.tar.gz /tmp/ocap-web.sha256`。
- 预期：本地临时制品删除；目标环境无变化。

### ROLLBACK-001: 回滚 DEPLOY-001

- 类型：本地清理。
- 命令：`cd frontend && rm -rf dist`。
- 预期：本地构建产物删除；目标环境无变化。需要重新部署时重新执行 DEPLOY-001。

## 不可逆步骤汇总

- 本计划在目标环境**没有不可逆步骤**：无数据库迁移、无后端重启、无数据写入；Web 静态目录替换可由 ROLLBACK-005 完整恢复。
- 不可自动回滚的外部动作（若用户另行执行）：微信小程序上传/发布到体验版或正式版属于外部可见变更，需用户在微信公众平台按既有流程处理；本计划不执行、不代为回滚。
- 清理动作 `ocap.old-${DEPLOY_TS}`、`ocap.failed-${DEPLOY_TS}` 不在部署流程内自动删除；验证通过后由用户确认再清理（保留至少 7 天）。

## 部署后验证

| 编号 | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 内网首页可达 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | 200 |
| V-02 | SPA 深链可达 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/units` | 200 |
| V-03 | 制品为新版本 | `grep -R "待我表决\|我的房屋\|公开决议" /home/yangyang/ocap/web/ocap/assets/*.js | wc -l` | ≥ 1 |
| V-04 | 入口引用完整 | 解析 `ocap/index.html` 中的 `/ocap/assets/*`，逐个 `test -f` | 全部存在 |
| V-05 | 外网入口可达 | 画像 P7 的 frp `443` 入口 + `/ocap/`（`EXTERNAL_URL`） | HTTP 200 |
| V-06 | 后端未受影响 | `systemctl is-active ocap-backend` | `active` |
| V-07 | 无新增服务端错误 | 部署前后各记录 `tail -n 50 /var/log/nginx/error.log` 行数与内容 | 无新增 5xx/上游超时 |
| V-08 | 本地状态未变 | `sha256sum /home/yangyang/ocap/.env` | 与预检记录一致 |
| V-09 | 角色化首屏人工核对 | 用三类测试账号分别打开 Web 首页（游客/产权业主/委员） | 模块与顺序符合 `deployment` 前测试报告；无统计卡/宫格；游客仅账户合计 |
| V-10 | 小程序构建已核验 | 预检的 `DONE Build complete.` 记录 | 存在；`app.json` 可解析（不发布） |

> V-09 需要真实账号，凭据不写入本文件；由用户在测试环境执行。失败判定：任一 V-01~V-08 失败 → 立即执行 ROLLBACK-005 并通知；V-09 失败 → 保持现场，按测试缺陷回流处理，不在生产/测试环境直接热修。
