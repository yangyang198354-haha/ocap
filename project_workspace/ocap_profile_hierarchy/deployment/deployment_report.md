<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-21T12:45:00+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_profile_hierarchy/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：个人主页信息层级与实名认证徽章

## 摘要

- 目标环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`）。
- 策略：recreate（Web 静态目录整体替换，后端不重启、无迁移）。
- 开始：2026-11-21T12:38:31+08:00；结束：2026-11-21T12:44:10+08:00。
- 回滚锚点：`TS=20261121123831`，`snapshots/web-20261121123831.tar.gz`（SHA256 `71b5811560b78fb85b0f257a97ec973dea91e1db06b42aa4ceef1e3c7afff96c`）；nginx 备份 `ocap.bak_20261121123831`。
- 总步骤 8 / 完成 6 / 失败 0 / 跳过 2。
- 最终状态：DEPLOYED_SUCCESSFULLY。

## 授权核对

- 授权来源：用户本轮明确选择“提交+推送+CI 全绿后部署”；PM 在 invocation `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true`、环境=测试。
- 授权环境名 = 计划环境名 = 画像 P7 环境名：“测试（内网）/ 测试（外网）”。
- 计划版本：deployment_plan v1.0.1（APPROVED）；phase_status 登记版本一致。
- 前置 CI：run 44866876013（af1cc46）三 job 全绿（Mini program 39s / Backend 1m12s / Web frontend 1m3s）。

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 001 锚点 | `tar -czf snapshots/web-$TS.tar.gz -C …/web ocap`；`sudo cp nginx/ocap ocap.bak_$TS` | 12:38:31 | ~40s | SUCCESS | `ANCHOR_TS=20261121123831`；SHA256 `71b581…f96c`；快照含 `ocap/index.html`；旧 `index.html` SHA256 `9acfea53…608c` |
| 002 构建 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`；`tar -czf web_dist_af1cc46_20261121123831.tar.gz -C frontend/dist .` | 12:39:10 | ~45s | SUCCESS | `built in 5.20s`；本地 tar SHA256 `7D32E102…4199` |
| 003 上传 | `scp … web_dist_af1cc46_20261121123831.tar.gz → /tmp/` | 12:39:55 | ~60s | SUCCESS | 远端 SHA256 `7d32e102…4199` 与本地一致；3,440,195 字节 |
| 004 替换 | `cd …/web && mkdir ocap.new && tar -xzf … -C ocap.new && mv ocap ocap.old && mv ocap.new ocap` | 12:41:00 | ~10s | SUCCESS | `WEB_SWAPPED`；新 `ocap/index.html` SHA256 `6f8e0f26…9100` = 本地 `frontend/dist/index.html` |
| 005 小程序 | `UNI_INPUT_DIR/UNI_OUTPUT_DIR npm --prefix miniprogram run build:mp-weixin` | 12:41:20 | ~90s | SUCCESS | `DONE Build complete`；`dist/build/mp-weixin/app.json` 存在（`Test-Path` True） |
| 006 验证 | 见“验证结果” | 12:43:00 | ~60s | SUCCESS | 全部检查通过 |
| 007 后端 | 跳过（零改动） | — | — | SKIPPED | 不重启 `ocap-backend`、不执行迁移 |
| 008 nginx | 跳过（配置无改动） | — | — | SKIPPED | 未 reload |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 内网 Web 首页 | `200`，返回新 `index.html`（引用 `assets/index-iq5wZfMU.js`） | 是 |
| 内网主资源 | `/ocap/assets/index-iq5wZfMU.js` → `200` | 是 |
| 新产物含徽章文案 | `grep -rl "已实名认证" web/ocap/assets` → `UserProfile-*.js`（2 个 chunk） | 是 |
| 未登录访问他人 profile | `/api/v1/users/1/profile` → `401`（路由存在且要求登录） | 是 |
| 后端服务 | `ocap-backend` = `active` | 是 |
| nginx | `nginx` = `active`；`nginx -t` successful | 是 |
| 失败服务 | `systemctl --failed` 0 loaded units listed | 是 |
| 外网 Web | `https://ai-freeark.xin/ocap/` → `200` | 是 |
| 外网静态资源 | `/ocap/assets/index-iq5wZfMU.js` → `200` | 是 |
| SPA 回退 | `/ocap/admin/login` → 返回 `index.html`，`200` | 是 |
| Freeark 未受影响 | `https://ai-freeark.xin/` → `200`；`http://127.0.0.1:8080/` → `200` | 是 |
| 小程序产物 | `miniprogram/dist/build/mp-weixin/app.json` 存在 | 是 |
| MV-01 / MV-02 | 需用户人工验收（Web 主题下颜色/字体区分；微信开发者工具“我的”页） | 待人工 |

## 回滚记录

未触发回滚。可用的回滚路径（按逆序）：

1. `verify 失败` → `cd /home/yangyang/ocap/web && rm -rf ocap && mv ocap.old ocap`（ROLLBACK-004，旧目录仍保留）。
2. 或从 `snapshots/web-20261121123831.tar.gz` 解包恢复（SHA256 `71b581…f96c`）。
3. 小程序产物为本地构建，可直接删除后重建。
4. 后端与 nginx 未变更，无需回滚。

## 当前系统状态与人工干预建议

- 系统处于新版本运行状态；`web/ocap.old` 保留旧静态产物，`snapshots/web-20261121123831.tar.gz` 与 `ocap.bak_20261121123831` 保留用于追溯。
- 建议稳定 24h 后清理 `ocap.old` 与临时包。

## 遗留问题

- 浏览器可能缓存旧 `index.html`，验证时建议强刷（Ctrl+F5）。
- 小程序上传/提审不在本计划内，需用户在微信开发者工具确认后手动上传（RU-4）。
- MV-01（Web 主题下实名与身份颜色/字体区分）与 MV-02（小程序真机展示）待人工验收。
