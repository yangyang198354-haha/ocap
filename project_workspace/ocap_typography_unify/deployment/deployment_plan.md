<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-27T06:55:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/architecture_design.md</file>
    <file>.trae/skills/ocap-deploy/SKILL.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划 — Web 端字体与标题统一（仅前端静态，无后端/迁移）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| Web 前端（管理端 + 用户端 SPA） | 新增 `frontend/src/shared/PageHead.vue`；改 `style.css`、`themes/{bento,neon,terminal}.web.css`、`generated/themes.css`、40 个页面、`layout/menus.js`、13+1 个测试 | 无 | Vite（`--base=/ocap/`） | 仅前端静态目录 `web/ocap`（原子交换，无需重启后端） |
| 后端 | 无改动 | 无 | 无 | 不重启、不重新部署 |
| nginx 配置 | 无改动 | — | — | 不 reload（配置未变） |

## 目标环境与策略

- 环境：**测试环境 `192.168.31.51:8090`**（画像 P7 唯一环境），用户 `yangyang`，本机 SSH 免密；外网 `https://ai-freeark.xin/ocap/`。
- 策略：**recreate（单实例静态替换）**。理由：单实例、无冗余、无流量切换能力；静态站点替换为原子目录交换，停机窗口≈0（秒级），符合 recreate 适用条件。
- 预计停机：≈0（静态文件 `try_files` 回退 `index.html`，交换瞬间完成）。
- 授权：**部署需用户确认=是**，本计划不执行任何部署命令；E2 前须取得当轮授权。

## 预检清单

| 检查项 | 命令 / 方法 | 通过标准 |
|---|---|---|
| 待部署提交已在远端 | 本地 `git rev-parse HEAD` 与 `git ls-remote origin main` 比对 | 哈希一致（push 由用户/CI 按画像 P9 执行） |
| 本地工作树干净 | `git status --porcelain` | 无未提交改动（除本次项目文档） |
| 本地前端构建通过 | `$env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run build -- --base=/ocap/` | 退出码 0 |
| 产物正确性 | 在 `frontend/dist` 产物中 grep 统一标题文案（如「我的认证与申诉」「AI 服务配置」） | 关键文案命中（M-DE-047） |
| 目标机磁盘/内存 | `ssh yangyang@192.168.31.51 'df -h /home; free -m'` | 磁盘 ≥2G、内存 ≥500M |
| 目标机本地状态不触碰 | 仅改 `web/ocap`；不动 `backend/.env`、`backend/**`、Freeark | 预检确认仅写 `web/` 与 `snapshots/` |
| Freeark 基线 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/`（目标机） | 200 |
| 回滚锚点记录 | 见 DEPLOY-001 | 生成 `web-$TS.tar.gz` 并记录 `$TS` |
| E2 通道可用性 | 直接 SSH 内网实测（非沙箱代理） | 免密 SSH 成功；若走沙箱外网代理返回隧道不可达则判 BLOCKED，改内网机器代执行（M-DE-052） |

## 部署步骤

> 仅前端静态改动，省略后端打包/依赖/迁移/重启与 nginx 变更（配置未变）。组件依赖顺序：基础设施（无）→ 数据层（无）→ 服务层（无）→ 前端。

### DEPLOY-001: 生成回滚快照（目标机）
- 组件：Web 前端静态（architecture_design 部署视图）
- 位置：目标机
- 命令：
  ```bash
  ssh yangyang@192.168.31.51 'mkdir -p /home/yangyang/ocap/snapshots && TS=$(date +%Y%m%d%H%M%S) && sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web && echo ANCHOR_TS=$TS'
  ```
- 预期：生成 `web-$TS.tar.gz`，输出 `ANCHOR_TS=<时间戳>`（记录为回滚锚点）。
- 回滚：ROLLBACK-001（快照保留 ≥7 天，无需回滚本身）。

### DEPLOY-002: 本地构建并上传前端产物（开发机 → 目标机）
- 组件：Web 前端构建产物
- 位置：开发机（构建）→ 目标机（上传）
- 命令（PowerShell，仓库根）：
  ```powershell
  $env:VITE_API_BASE='/ocap/api/v1'
  npm --prefix frontend run build -- --base=/ocap/
  tar -czf frontend_dist.tar.gz -C frontend\dist .
  scp frontend_dist.tar.gz yangyang@192.168.31.51:/tmp/
  ```
- 预期：`built in …s`，产物含统一标题文案；`/tmp/frontend_dist.tar.gz` 上传成功。
- 回滚：ROLLBACK-002（删除 `/tmp/frontend_dist.tar.gz`，目标机静态目录此时尚未变更）。

### DEPLOY-003: 目标机静态目录原子替换
- 组件：`/home/yangyang/ocap/web/ocap`
- 位置：目标机
- 命令（用 DEPLOY-001 的 `$TS`，注意远端变量需就地展开，先 echo 核对）：
  ```bash
  ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/web && sudo mv ocap ocap.old_'"$TS"' && sudo mkdir -p ocap && sudo tar xzf /tmp/frontend_dist.tar.gz -C ocap && ls ocap/index.html'
  ```
- 预期：`ocap/index.html` 存在；旧目录保留为 `ocap.old_$TS`（M-DE-046）。
- 回滚：ROLLBACK-003。

### DEPLOY-004: 部署后验证与冒烟
- 组件：整体
- 位置：开发机 / 目标机
- 命令：见「部署后验证」清单逐项执行。
- 预期：全部通过；若关键项失败 → 执行 ROLLBACK-003 回滚。
- 回滚：ROLLBACK-004（即触发 ROLLBACK-003）。

## 回滚步骤（逆序）

### ROLLBACK-004: 验证失败时回滚（= 触发 ROLLBACK-003）
- 类型：正式回滚
- 命令：执行 ROLLBACK-003。
- 预期：回到上一版本静态。

### ROLLBACK-003: 回滚 DEPLOY-003（静态目录换回）
- 类型：正式回滚
- 命令（`$TS` 用 DEPLOY-001 锚点，先 `echo` 出完整命令核对再执行）：
  ```bash
  ssh yangyang@192.168.31.51 'cd /home/yangyang/ocap/web && sudo rm -rf ocap && sudo mv ocap.old_'"$TS"' ocap && ls ocap/index.html'
  ```
- 变量取值与核验：`$TS` 取自 DEPLOY-001 输出的 `ANCHOR_TS`；执行后 `ls web/ocap/index.html` 且旧 asset 恢复。
- 预期：旧静态恢复，站点回到部署前。新增文件（如 `PageHead.vue` 相关产物）在旧版本中不存在、不被引用，随 `ocap` 目录一并移除，无残留风险。
- 禁止：不得用 `git reset --hard` / `git clean` / `git stash`（目标机无 git，且会破坏本地状态）——只用 tar 快照/旧目录恢复（通用经验）。

### ROLLBACK-002: 回滚 DEPLOY-002（清理上传临时包）
- 类型：紧急止血（清理）
- 命令：`ssh yangyang@192.168.31.51 'rm -f /tmp/frontend_dist.tar.gz'`
- 预期：临时包删除；不影响线上（DEPLOY-003 未执行时）。

### ROLLBACK-001: 快照处理
- 类型：无需操作
- 命令：保留 `web-$TS.tar.gz` ≥7 天。
- 预期：回滚锚点可追溯。

## 不可逆步骤汇总

无。本次为纯前端静态替换，无数据库迁移、无外部系统调用、无通知发送，所有步骤可逆（快照/旧目录恢复）。

## 部署后验证

| 检查项 | 命令 / URL | 成功标准 |
|---|---|---|
| 内网前端可达 | `GET http://192.168.31.51:8090/ocap/` | 200, text/html |
| SPA 回退 | `GET http://192.168.31.51:8090/ocap/admin/login` | 200，返回 index.html |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | 200 |
| 外网静态资源 | `GET https://ai-freeark.xin/ocap/assets/<hash>.js` | 200 |
| 统一标题文案 | 在产物 `assets/*.js` 中 grep「我的认证与申诉」「AI 服务配置」 | 命中（M-DE-047） |
| 后端未受影响 | `systemctl is-active ocap-backend` | active（本次未重启，仍 active） |
| Freeark 未受影响 | `GET https://ai-freeark.xin/`；`systemctl --state=failed` | 200；无 `freeark-*` 失败 |
| 视觉人工复核 M-01 | 三主题（bento/neon/terminal）同一中文标题宽度对比 | 宽度误差 ≤2px，terminal 标题非大写（AC-366-03） |
| 视觉人工复核 M-02 | 375px 视口打开长标题页 | 长标题换行、无横向滚动条（AC-369-02） |

> 等待部署授权：本计划仅为 PHASE_11a 产物，未连接任何目标环境、未执行任何部署命令。E2 需用户当轮明确授权（画像 P7 部署需确认=是）。
