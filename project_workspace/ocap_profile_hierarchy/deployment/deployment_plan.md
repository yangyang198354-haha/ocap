<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-21T12:17:20+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/architecture/module_design.md</file>
    <file>project_workspace/ocap_profile_hierarchy/testing/e2e_test_report.md</file>
    <file>project_workspace/ocap_profile_ux/deployment/deployment_plan.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 部署计划：个人主页信息层级与实名认证徽章

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布 |
|---|---|---|---|---|
| Web 前端 | `frontend/src/portal/UserProfile.vue` | 无 | `npm run build`（frontend） | 替换目标机静态目录 `/home/yangyang/ocap/web/dist` |
| 小程序 | `miniprogram/pages/me/index.vue` | 无 | `uni build -p mp-weixin`（UNI_INPUT_DIR/UNI_OUTPUT_DIR） | 仅生成产物；上传由微信开发者工具人工完成，不在自动部署内 |
| 后端 | 无 | 无 | 无 | 不重启 |

## 目标环境与策略

- 环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`，画像 P7）。
- 策略：recreate（单实例、静态产物整体替换），预计停机 0（nginx 直接读静态目录，替换窗口 < 5s）。
- 生产不存在；不使用 Docker/容器；不新增 nginx 配置。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| 测试已通过 | 本计划前置：GROUP_D APPROVED；CI 全绿 | 报告与 CI 一致 |
| 远端可达、磁盘充足 | `ssh yangyang@192.168.31.51 "df -h /home \| tail -1"` | 可用空间 > 500MB |
| 后端/定时任务状态 | `systemctl is-active ocap-backend ocap-run-due-jobs.timer` | 均 active |
| 现有静态目录存在 | `test -f /home/yangyang/ocap/web/dist/index.html && echo OK` | 输出 OK |
| 当前版本锚点 | 记录 `sha256sum /home/yangyang/ocap/web/dist/index.html` | 输出 SHA256 非空 |
| nginx 配置未变 | `sudo -n nginx -t` | syntax is ok |

## 部署步骤

### DEPLOY-001: 生成回滚锚点（目标机）
- 组件：Web 静态产物 + nginx 备份
- 位置：目标机
- 命令：`TS=$(date +%Y%m%d%H%M%S); sudo tar czf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap web && sudo cp /etc/nginx/sites-available/ocap /etc/nginx/sites-available/ocap.bak_$TS && sha256sum /home/yangyang/ocap/snapshots/web-$TS.tar.gz`
- 预期：快照存在且 SHA256 非空；记录 `TS` 到部署报告
- 回滚：ROLLBACK-001

### DEPLOY-002: 本地构建 Web 并打包（开发机）
- 组件：Web 前端
- 位置：开发机
- 命令：`cd frontend && npm run build && cd .. && tar czf "$env:TEMP\web_dist_<sha>_<TS>.tar.gz" -C frontend dist`
- 预期：构建退出码 0，`dist/assets/index-*.js` 更新；tar 生成
- 回滚：ROLLBACK-002

### DEPLOY-003: 上传制品（开发机 → 目标机）
- 组件：Web 制品
- 位置：开发机/目标机
- 命令：`scp "$env:TEMP\web_dist_<sha>_<TS>.tar.gz" yangyang@192.168.31.51:/tmp/`
- 预期：远端 `/tmp/web_dist_<sha>_<TS>.tar.gz` 存在且大小一致
- 回滚：ROLLBACK-003

### DEPLOY-004: 替换静态目录（目标机）
- 组件：Web 静态产物
- 位置：目标机
- 命令：`cd /home/yangyang/ocap/web && rm -rf dist.new && mkdir dist.new && tar xzf /tmp/web_dist_<sha>_<TS>.tar.gz -C dist.new --strip-components=1 && rm -rf dist && mv dist.new dist`
- 预期：`dist/index.html` 存在，资源哈希为新版本
- 回滚：ROLLBACK-004

### DEPLOY-005: 构建小程序产物（开发机，不部署）
- 组件：微信小程序
- 位置：开发机
- 命令：`cd miniprogram; $env:UNI_INPUT_DIR='<repo>\miniprogram'; $env:UNI_OUTPUT_DIR='<repo>\miniprogram\dist\build\mp-weixin'; npm run build:mp-weixin`
- 预期：`dist/build/mp-weixin/app.json` 存在；构建 DONE
- 回滚：ROLLBACK-005

### DEPLOY-006: 部署后验证（只读）
- 组件：Web + 后端（只读）
- 位置：目标机
- 命令：见“部署后验证”表
- 预期：全部 PASS
- 回滚：ROLLBACK-006

### DEPLOY-007: 后端发布（跳过）
- 说明：后端零改动，不重启 `ocap-backend`，不执行迁移，避免无谓中断。
- 回滚：ROLLBACK-007（无操作）

### DEPLOY-008: nginx 重载（跳过）
- 说明：配置无改动，不 reload。
- 回滚：ROLLBACK-008（无操作）

## 回滚步骤（逆序）

### ROLLBACK-008: 反向回滚 DEPLOY-008
- 类型：正式回滚（无操作）
- 命令：无（未执行变更）
- 预期：nginx 配置与运行状态不变

### ROLLBACK-007: 反向回滚 DEPLOY-007
- 类型：正式回滚（无操作）
- 命令：无（未重启后端）
- 预期：后端持续 active

### ROLLBACK-006: 反向回滚 DEPLOY-006
- 类型：正式回滚（无操作）
- 说明：只读验证，无状态变更；若验证失败，执行 ROLLBACK-004

### ROLLBACK-005: 反向回滚 DEPLOY-005
- 类型：正式回滚
- 命令：`Remove-Item -Recurse -Force <repo>\miniprogram\dist\build\mp-weixin`
- 变量取值与核验：仅本地构建产物，可随时重新构建
- 预期：产物目录不存在

### ROLLBACK-004: 恢复旧静态产物（目标机）
- 类型：正式回滚
- 命令：`TS=<部署报告记录的锚点>; rm -rf /home/yangyang/ocap/web/dist && tar xzf /home/yangyang/ocap/snapshots/web-$TS.tar.gz -C /home/yangyang/ocap/web --strip-components=1 web/dist`（如 tar 路径为 `web/dist`，使用 `--strip-components=2` 前先 `tar tzf` 核对）
- 变量取值与核验：`TS` 取自部署报告 DEPLOY-001；执行前 `tar tzf` 确认包含 `web/dist/index.html`
- 预期：`dist/index.html` 的 SHA256 与锚点记录一致

### ROLLBACK-003: 删除远端临时制品
- 类型：正式回滚
- 命令：`rm -f /tmp/web_dist_<sha>_<TS>.tar.gz`
- 预期：文件不存在

### ROLLBACK-002: 清理本地制品
- 类型：正式回滚
- 命令：`Remove-Item "$env:TEMP\web_dist_<sha>_<TS>.tar.gz"`
- 预期：文件不存在

### ROLLBACK-001: 锚点处置
- 类型：正式回滚（无操作）
- 说明：锚点保留用于追溯；部署成功且稳定 24h 后可按运维惯例清理 `web-$TS.tar.gz`

## 不可逆步骤汇总

| 步骤 | 不可逆点 | 处置 |
|---|---|---|
| DEPLOY-004 | 用户浏览器可能缓存旧 `index.html` 引用 | 发布后提示用户强刷（Ctrl+F5）；资源哈希变化不影响旧缓存短期可用 |
| 小程序上传（不在本计划） | 微信平台版本上传后不可撤回 | 由用户在微信开发者工具确认后再上传；本计划只构建产物 |
| nginx 备份清理 | 删除 `ocap.bak_TS` 后无法回到旧配置 | 本次不修改配置，不清理备份 |

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| Web 首页 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/` | 200 |
| 新产物包含徽章文案 | `grep -rl "已实名认证" /home/yangyang/ocap/web/dist/assets | head -1` | 输出非空 |
| 主资源可达 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ocap/<index.html 中引用的 js>` | 200 |
| 未登录访问他人主页接口 | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9000/api/v1/users/1/profile` | 401 |
| 后端与定时任务 | `systemctl is-active ocap-backend ocap-run-due-jobs.timer` | 均 active |
| 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | 200 |
| 小程序产物 | `Test-Path <repo>\miniprogram\dist\build\mp-weixin\app.json` | True |
| 人工渲染（MV-01/MV-02） | 浏览器 / 微信开发者工具 | 昵称 → 实名+徽章 → 身份；颜色与字体可区分 |
