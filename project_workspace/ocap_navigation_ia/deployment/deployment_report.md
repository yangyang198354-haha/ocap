<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T13:26:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_navigation_ia/phase_status.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：导航信息架构整合（Web 静态增量，测试环境）

## 摘要

- 目标环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`，同一主机）。
- 部署策略：静态目录原子交换（recreate 变体，无停机）。
- 部署版本：commit `9fd5e3e`（61 files changed, 3114 insertions(+), 475 deletions(-)；本地已提交，**未 push**）。
- 开始：2026-11-22 13:20:27（回滚锚点 TS）；结束：2026-11-22 13:26（UTC+8，近似）。
- 回滚锚点：`ANCHOR_TS=20261122132027`（`backend-20261122132027.tar.gz` 30.6 MB、`web-20261122132027.tar.gz` 28.4 MB，另含 nginx 配置备份）。
- 总步骤 4 / 完成 4 / 失败 0 / 跳过 0。
- **最终状态：DEPLOYED_SUCCESSFULLY**

## 授权核对

| 项 | 值 | 结论 |
|---|---|---|
| 授权来源 | 用户最新消息原文“好的，提交并部署到测试环境”；PM 在 invocation `ocap_navigation_ia-GROUP_E2-1` 的 `special_instructions` 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与目标环境名“测试” | 一致 |
| 授权环境名 | 测试（内网 + 外网） | 一致 |
| 计划环境名 | 测试（内网 + 外网，deployment_plan.md 1.0.0） | 一致 |
| 画像 P7 环境名 | 测试（内网 192.168.31.51 / 外网 ai-freeark.xin） | 一致 |
| 计划版本 | deployment_plan.md 1.0.0（phase_status 登记 GROUP_E1=APPROVED） | 一致 |

## 预检结果

| 检查项 | 实际 | 结论 |
|---|---|---|
| P-01 待部署提交已在远端 | 本地 `9fd5e3e`；`git push` 失败（本地代理 `socks5h://127.0.0.1:10808` 未监听，直连 `Connection was reset`），远端无该提交 | **未满足（偏差，见遗留问题 1）** |
| P-02 免密 SSH | `SSH_OK` | 通过 |
| P-03 磁盘/内存 | `/home` 可用 15G；内存 available 1530 MB | 通过 |
| P-04 端口归属 | 8090/9000 属 ocap；80/8000/8080 属 Freeark，未被占用 | 通过 |
| P-05 后端 env 存在 | `ENV_OK`（未读取内容） | 通过 |
| P-06 后端健康基线 | `ocap-backend=active` | 通过 |
| P-07 nginx 语法基线 | `nginx -t` syntax is ok / test is successful | 通过 |
| P-08 Freeark 基线 | 内网 8080 返回 `200` | 通过 |
| P-09 前端目录事实 | `/home/yangyang/ocap/web/ocap` 存在 | 通过 |
| P-10 制品正确性 | 构建产物命中“我的认证与申述” | 通过 |
| P-11 快照锚点 | `ANCHOR_TS=20261122132027`，两个快照文件已生成 | 通过 |

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 001 锚点与快照 | `mkdir snapshots`；`tar czf backend-$TS.tar.gz`、`web-$TS.tar.gz`；备份 ocap/freeark nginx 配置 | 13:20:27 | ≈20s | SUCCESS | `ANCHOR_TS=20261122132027`；backend 30.6 MB、web 28.4 MB |
| 002 构建前端 | `$env:VITE_API_BASE='/ocap/api/v1'`；`npm run build -- --base=/ocap/`；文案核验 | 13:2x | 8.65s | SUCCESS | 构建成功；新产物 `index-DztR3PGZ.js`、`index-9rOhKTYD.js`；“我的认证与申述”命中 |
| 003 打包上传暂存 | `tar czf frontend_dist_$TS.tar.gz -C frontend\dist .`；`scp`；解包到 `web/ocap.new.<TS>` | 13:2x | ≈15s | SUCCESS | `STAGED`；暂存目录含 `index.html` 与 `assets/` |
| 004 原子交换 | `mv ocap ocap.old.<TS>`；`mv ocap.new.<TS> ocap`；`chown` | 13:2x | ≈2s | SUCCESS | `SWAPPED`；新目录含 `index-DztR3PGZ.js`，旧目录不含，内容已切换 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| V-01 内网前端 | `INT=200` | 是 |
| V-02 外网前端 | `EXT=200` | 是 |
| V-03 静态资源 | `ASSET=200`（内网 IP 直连 `INT_IP=200`） | 是 |
| V-04 SPA 回退 | `SPA=200` | 是 |
| V-05 产物含新文案 | 构建产物 grep 命中；目标机新目录含本次 `index-DztR3PGZ.js` 且 `ocap.old.<TS>` 不含（文件清单比对） | 是 |
| V-06 后端未受影响 | `BACKEND=active`；`TRACEBACK=0` | 是 |
| V-07 Freeark 未受影响 | `FREEARK=200`；`FREEFAIL=0` | 是 |
| V-08 关键功能冒烟（人工） | 未执行，转人工验证 MV-01~MV-04；不阻断本次自动验证结论 | 待人工 |

## 回滚记录

无。部署与自动验证全部通过，未触发任何 ROLLBACK。

## 当前系统状态与人工干预建议

不适用（未发生失败与回滚）。

## 遗留问题

1. **代码未 push（偏差）**：`git push origin main` 因本地 `http.proxy=socks5h://127.0.0.1:10808` 未监听失败；直连返回 `Connection was reset`；探测 10808/10809/7890/7897/1080/8080 均不可用。远端仓库当前无 `9fd5e3e`。需用户启动代理后执行 `git push origin main`；本次部署以本地提交构建，目标机运行不受影响，回滚依赖 tar 快照而非远端提交。
2. **P-01 偏差说明**：工作区仍有 3 个本批次前既有的无关文件未提交（`project_workspace/ocap_appeal_center/phase_status.md`、`project_workspace/ocap_appeal_center/deployment/deployment_report.md`、`registry_import_投票权清单.xlsx`），本次未触碰、未纳入提交。
3. **待人工验证**：MV-01 悬停 180ms 时序、MV-02 系统减少动效降级、MV-03 小程序真机三 Tab、MV-04 真机主题切换。
4. **小程序未构建、未发布**（RU-4 范围外）；如需发布需另行执行小程序发布流程。
5. 目标机保留 `ocap.old.20261122132027` 与快照，建议下个版本稳定后再清理；快照保留 ≥ 7 天。
