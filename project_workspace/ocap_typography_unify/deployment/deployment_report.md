<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-27T07:20:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/deployment/deployment_plan.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告 — Web 端字体与标题统一（测试环境）

## 摘要

- 目标环境：测试环境 `192.168.31.51:8090`（raspberrypi），外网 `https://ai-freeark.xin/ocap/`。
- 策略：recreate（单实例静态原子交换）。
- 回滚锚点：`ANCHOR_TS=20261127071708`（`web-20261127071708.tar.gz`，49.9MB）。
- 开始/结束：2026-11-27 07:17 ~ 07:20（本地时间戳）。
- 总步骤 4 / 完成 4 / 失败 0 / 跳过 0。
- **最终状态：DEPLOYED_SUCCESSFULLY**。

## 授权核对

- 授权来源：用户当轮明确授权（原话：「授权部署到测试环境，执行部署并做验证」）。
- 授权环境名 = 计划环境名 = 画像 P7 环境名 = **测试环境**，一致。
- 计划版本 = APPROVED 版本 = **deployment_plan.md v1.0.0**，一致。
- 偏差记录：本次部署自**工作区构建**（改动尚未 commit/push），用于测试环境预览；提交与推送待用户视觉确认后另行处理。已在执行前向用户明示。

## 分步执行

| DEPLOY | 命令（摘要） | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 快照 | `tar czf snapshots/web-$TS.tar.gz -C ocap web` | 07:17 | ~5s | SUCCESS | ANCHOR_TS=20261127071708，快照 49928657 字节 |
| DEPLOY-002 构建上传 | `npm run build --base=/ocap/` + `tar` + `scp` | 07:16~07:17 | ~16s | SUCCESS | built in 8.98s；tar 1951950 字节，两端一致 |
| DEPLOY-003 静态交换 | `mv ocap ocap.old_$TS && mkdir ocap && tar xzf … -C ocap` | 07:17 | ~3s | SUCCESS | ocap/index.html 1132B，90 个文件 |
| DEPLOY-004 验证 | 见「验证结果」 | 07:18~07:20 | ~2min | SUCCESS | 全部通过 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 内网前端 `GET :8090/ocap/` | 200, text/html | ✅ |
| SPA 回退 `GET :8090/ocap/admin/login` | 200, index.html | ✅ |
| 内网静态资源 `GET :8090/ocap/assets/<hash>.js` | 200 | ✅ |
| 外网前端 `GET https://ai-freeark.xin/ocap/` | 200 | ✅ |
| 外网 Freeark `GET https://ai-freeark.xin/` | 200 | ✅ |
| 后端存活 `systemctl is-active ocap-backend` | active（未重启，符合预期） | ✅ |
| Freeark 服务 | `systemctl --state=failed` 中 freeark 数 = 0 | ✅ |
| 产物文案 | dist 中「我的认证与申诉」「AI 服务配置」「信息公开」均命中 | ✅ |
| 浏览器渲染 | 登录页正常挂载，品牌「赛博@红枫岭」完整，无布局错乱/文字重叠，控制台无错误（仅微信参数接口 503，登录页可忽略） | ✅ |

浏览器截图：`c:\Users\胖子熊\AppData\Local\Temp\trae\screenshots\ocap_login_page.jpg`。

## 回滚记录

未执行回滚（部署成功）。回滚锚点 `web-20261127071708.tar.gz` 与旧目录 `web/ocap.old_20261127071708` 均已保留，可随时按 deployment_plan ROLLBACK-003 逆序恢复。

## 遗留问题

- **M-01 / M-02（视觉人工复核）**：三主题中文标题宽度对比（AC-366-03）、375px 换行无横向滚动（AC-369-02）需登录后在真实浏览器复核——登录页渲染已确认无异常，但这两项需登录态 + 主题切换 + DevTools 测量，留待用户/人工执行。
- **改动未提交**：本次部署为工作区构建预览，字体/标题改动尚未 commit/push，待用户视觉确认后处理。
- **预存失败**：`product_review_ui.spec.js` TC-UNIT-577（委员导航过滤）为基线既有问题（CR-404），与本次无关，留待后续单独修复。
