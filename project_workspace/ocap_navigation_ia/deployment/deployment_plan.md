<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T12:58:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>project_workspace/ocap_navigation_ia/development/implementation_plan.md</file>
    <file>project_workspace/ocap_navigation_ia/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — 导航信息架构整合（Web 静态增量）

> 本计划仅针对画像 P7 的测试环境（内网 `192.168.31.51:8090`、外网 `https://ai-freeark.xin/ocap/`）。画像无生产环境。
> **本计划不构成部署授权**；E2 必须由用户单独下达部署指令。

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| Web 前端 | `frontend/src/layout/menus.js`、`PortalUserMenu.vue`、`Me.vue`、`Units.vue`、`UnitsIdentity.vue`、`router/index.js`、`me/MePhone.vue`、`shared/style.css` + 新增测试 | 无 | Vite（`--base=/ocap/`，`VITE_API_BASE=/ocap/api/v1`） | Web 静态目录替换；**后端不重启** |
| 后端 | 仅 `backend/tests/integration/*` 测试文件（契约测试适配拆分） | 无 | 不需要 | **无**（运行时代码零改动） |
| 微信小程序 | `miniprogram/pages/{units,me,phone,email,cancel}`、`utils/{menu,api,confirm}.js`、`pages.json` | 无 | `npm run build:mp-weixin`（本地） | **不发布**（RU-4：小程序提审/发布不在本 skill 范围） |

结论：本次只需替换 Web 前端静态产物；数据库无迁移，后端无重启。

## 目标环境与策略

- 环境：测试（内网 + 外网，同一树莓派，经 Freeark frp 暴露）。
- 策略：**静态目录原子交换（recreate 变体，无停机）**。理由：单实例、无容器、静态资源可短时并存；新目录先落到 `ocap.new.<TS>`，校验后一次 `mv` 切换，失败用 `ocap.old.<TS>` 换回。
- 预计停机：0（后端不重启；静态目录切换为毫秒级 `mv`）。
- 不在本计划内：微信小程序发布、nginx 配置改动（本次无路由前缀变化，`location ^~ /ocap/` 已存在）、数据迁移。

## 预检清单

| # | 检查项 | 命令（位置） | 通过标准 |
|---|---|---|---|
| P-01 | 待部署提交已在远端（P9：commit/push 由用户执行） | 开发机：`git rev-parse HEAD`；`git ls-remote origin main` | 两哈希一致；工作区无未提交改动（当前未满足，**需用户先授权并提交/推送**） |
| P-02 | 免密 SSH | 开发机：`ssh yangyang@192.168.31.51 'echo OK'` | 输出 `OK` |
| P-03 | 磁盘/内存 | 目标机：`df -h /home`；`free -m` | `/home` 可用 ≥ 2G；内存可用 ≥ 500M |
| P-04 | 端口归属 | 目标机：`ss -ltn` | 8090/9000 属 ocap；8000/8080/80 属 Freeark（不得占用） |
| P-05 | 后端 env 存在 | 目标机：`test -f /home/yangyang/ocap/backend/.env && echo OK` | `OK`（不读取内容） |
| P-06 | 后端健康基线 | 目标机：`systemctl is-active ocap-backend` | `active` |
| P-07 | nginx 语法基线 | 目标机：`sudo nginx -t` | `syntax is ok` / `test is successful` |
| P-08 | Freeark 基线 | 目标机：`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/` | `200` |
| P-09 | 前端目录事实 | 目标机：`ls -ld /home/yangyang/ocap/web /home/yangyang/ocap/web/ocap` | 存在且属主 `yangyang:yangyang` |
| P-10 | 制品正确性 | 开发机：构建产物 `grep -rl '我的认证与申述' frontend/dist/assets` | 至少 1 个命中 |
| P-11 | 快照锚点 | 见 DEPLOY-001 | `ANCHOR_TS` 与快照文件已记录 |

## 部署步骤

> 记 `TS` 为本次时间戳（`yyyyMMddHHmmss`）。以下命令在 PowerShell 中执行；`$TS` 先赋值：`$TS = Get-Date -Format 'yyyyMMddHHmmss'`。
> 远端命令使用双引号，确保 `$TS` 在远端展开为实际值（不要用单引号包住变量）。

### DEPLOY-001: 记录锚点并生成回滚快照（目标机）
- 组件：全部（快照，不改变运行态）
- 位置：目标机
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; TS=$TS; mkdir -p /home/yangyang/ocap/snapshots; sudo tar czf /home/yangyang/ocap/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap backend; sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web; sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS; sudo cp /etc/nginx/sites-enabled/freeark /etc/nginx/sites-available/freeark.bak_$TS; echo ANCHOR_TS=$TS; ls -l /home/yangyang/ocap/snapshots/*-$TS.tar.gz"
```
- 预期：打印 `ANCHOR_TS=<TS>`，两个快照文件存在。
- 回滚：ROLLBACK-001（快照本身不改变系统，无需回滚）

### DEPLOY-002: 构建 Web 前端（开发机）
- 组件：Web 前端（MOD-174~178）
- 位置：开发机
- 命令：
```powershell
$env:VITE_API_BASE='/ocap/api/v1'
npm --prefix frontend run build -- --base=/ocap/
grep -rl '我的认证与申述' frontend/dist/assets   # Git Bash；PowerShell 用 Select-String -Path frontend\dist\assets\* -Pattern '我的认证与申述'
```
- 预期：构建成功；产物中命中新文案。
- 回滚：ROLLBACK-002（仅开发机产物，目标机未变）

### DEPLOY-003: 打包并上传到暂存目录（开发机 → 目标机）
- 组件：Web 静态产物
- 位置：开发机 + 目标机 `/home/yangyang/ocap/web/ocap.new.<TS>`
- 命令：
```powershell
tar -czf frontend_dist_$TS.tar.gz -C frontend\dist .
scp frontend_dist_$TS.tar.gz yangyang@192.168.31.51:/tmp/
ssh yangyang@192.168.31.51 "set -e; rm -rf /home/yangyang/ocap/web/ocap.new.$TS; mkdir -p /home/yangyang/ocap/web/ocap.new.$TS; tar xzf /tmp/frontend_dist_$TS.tar.gz -C /home/yangyang/ocap/web/ocap.new.$TS; test -f /home/yangyang/ocap/web/ocap.new.$TS/index.html; chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap.new.$TS; echo STAGED"
```
- 预期：`STAGED`，暂存目录含 `index.html` 与 `assets/`。
- 回滚：ROLLBACK-003（删除暂存目录）

### DEPLOY-004: 原子交换静态目录并校验权限（目标机）
- 组件：Web 静态目录
- 位置：目标机
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; cd /home/yangyang/ocap/web; if [ -d ocap ]; then mv ocap ocap.old.$TS; fi; mv ocap.new.$TS ocap; chown -R yangyang:yangyang ocap; ls -ld ocap ocap.old.$TS; echo SWAPPED"
```
- 预期：`SWAPPED`；`ocap` 为新目录，`ocap.old.<TS>` 保留旧目录。
- 回滚：ROLLBACK-004

## 回滚步骤（逆序）

### ROLLBACK-004: 回退静态目录（对应 DEPLOY-004）
- 类型：正式回滚
- 命令：
```powershell
ssh yangyang@192.168.31.51 "set -e; cd /home/yangyang/ocap/web; test -d ocap.old.$TS; mv ocap ocap.failed.$TS; mv ocap.old.$TS ocap; chown -R yangyang:yangyang ocap; echo ROLLED_BACK"
```
- 变量取值与核验：`$TS` 必须与 DEPLOY-001 的 `ANCHOR_TS` 一致；执行前先 `ssh ... "ls -d /home/yangyang/ocap/web/ocap.old.$TS"` 确认存在。
- 预期：输出 `ROLLED_BACK`，`ocap` 指向旧产物。
- 备用：若旧目录缺失，用 `sudo tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap` 恢复（会覆盖 `web/ocap`，执行前确认无本地手工修改）。

### ROLLBACK-003: 清理暂存/上传文件（对应 DEPLOY-003）
- 类型：正式回滚
- 命令：
```powershell
ssh yangyang@192.168.31.51 "rm -rf /home/yangyang/ocap/web/ocap.new.$TS /tmp/frontend_dist_$TS.tar.gz; echo CLEANED"
```
- 预期：`CLEANED`。

### ROLLBACK-002: 删除开发机构建产物（对应 DEPLOY-002）
- 类型：正式回滚（目标机无影响）
- 命令：`Remove-Item -Force frontend_dist_$TS.tar.gz`
- 预期：文件不存在；`frontend/dist` 可保留或下次构建覆盖。

### ROLLBACK-001: 快照保留（对应 DEPLOY-001）
- 类型：无需回滚；快照保留 ≥ 7 天。
- 命令：无。

## 不可逆步骤汇总

- 本次**无**数据库迁移、无后端起停、无 nginx 配置变更，因此**无 `[MANUAL_ROLLBACK_REQUIRED]` 步骤**。
- 小程序发布（RU-4）不在本计划内，若未来执行需单独计划。

## 部署后验证

| # | 检查项 | 命令/URL | 成功标准 |
|---|---|---|---|
| V-01 | 内网前端 | `curl -s -o /dev/null -w '%{http_code}' http://192.168.31.51:8090/ocap/` | `200` |
| V-02 | 外网前端 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | `200` |
| V-03 | 静态资源 | 取 `index.html` 中的 `assets/index-*.js`，请求外网 URL | `200`，`content-type` 为 JS |
| V-04 | SPA 回退 | `curl -s https://ai-freeark.xin/ocap/login` | `200`，返回 `index.html` |
| V-05 | 产物含新文案 | 目标机：`grep -rl '我的认证与申述' /home/yangyang/ocap/web/ocap/assets` | 至少 1 个命中 |
| V-06 | 后端未受影响 | `ssh ... 'systemctl is-active ocap-backend'` | `active`；`journalctl -u ocap-backend --since '-5 min'` 无 Traceback |
| V-07 | Freeark 未受影响 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/`；`systemctl --state=failed --no-pager` | `200`；无 `freeark-*` 失败 |
| V-08 | 关键功能冒烟（只读） | 外网打开 `/ocap/units`、`/ocap/me`（登录态） | 三个 Tab 与分组菜单可见；无控制台错误（人工确认） |

任一步失败且目标机已发生变更 → 立即停止，从失败步骤起按逆序执行 ROLLBACK；回滚失败则报告 `ROLLBACK_FAILED` 并列出当前状态与人工建议。
