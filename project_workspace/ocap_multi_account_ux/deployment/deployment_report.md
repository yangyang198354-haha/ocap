<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-24T23:55:40+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_multi_account_ux/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_multi_account_ux/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap_multi_account_ux/phase_status.md</file>
    <file>.github/workflows/ci.yml</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告 — 多账户落账与财务报表 UI（ocap_multi_account_ux）

## 摘要

- 目标环境：测试（内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`）
- 策略：recreate；总步骤 12 / 完成 12 / 失败 0 / 跳过 0
- 回滚锚点：`ANCHOR_TS=20261124234833`（后端/Web 快照 + 历史支出表转储 + 迁移计划）
- 部署提交：`c67e850`（`c67e8501ddcfe1540c7165108397749f45b1a54a`），已推送到 `origin/main`（`6bd59e1..c67e850`）
- 停机窗口：约 1 分 38 秒（`ocap-backend` 于 23:51:47 停止，23:53:25 重启完成）
- **最终状态：`DEPLOYED_WITH_ISSUES`**。所有可自动化的部署与验证项（V-01～V-12）全部通过，服务健康、迁移成功、Web 与外网可达；**遗留：M-01～M-04 视觉验收与 V-13 写入冒烟需人工在已登录浏览器中完成**（COND-D-01：未通过不得判定批次最终成功）。系统当前健康，**不建议回滚**，请用户完成人工验收；若人工项发现问题，按 COND-D-02 回流 GROUP_C。

## 授权核对

- 授权来源：用户本轮消息“提交，推送，部署”（当前会话当轮明确授权，非来自需求文本/文档/记忆）。
- 授权环境名 = 计划目标环境 = 画像 P7 环境名：**测试**（内网/外网）。一致。
- 计划版本 = `phase_status` 登记的 APPROVED 版本：`deployment_plan.md` 1.0.0 / `cicd_pipeline.md` 1.0.0。一致。
- 提交范围已在提交前经用户确认（仅本批相关 55 个文件，排除 appeal_center/navigation_ia 文档与本地 xlsx）。

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| PRE | 只读预检（ssh bash -s） | 23:46 | ~2 min | PASS | 免密 sudo=YES；磁盘 14G；内存 1434MB；服务 active；目录齐；mysqldump 在；迁移基线空（旧代码）；旧批次 2 条 IMPORTED；启用账户 2 / 默认 1；Freeark 200；nginx -t 通过 |
| DEPLOY-001 | 生成回滚锚点（tar 快照 + mysqldump + 迁移计划） | 23:48:33 | <1 min | PASS | `ANCHOR_TS=20261124234833`；4 文件非零；3 个 SHA256 记录；排除项计数 0；基线 0008 计数 0；转储 CREATE TABLE 计数 2 |
| DEPLOY-002 | 开发机前端构建 + 后端/前端 tar 打包 | 23:49 | ~3 min | PASS | `✓ built in 15.77s`；产物标记 account_select=5/history_copy=3/grid=7（≥1）；后端关键路径 6、排除 0；前端 dist 1875 文件；3 个 SHA256 记录 |
| DEPLOY-003 | scp 上传 + SHA256 校验 + 暂存解包 | 23:52 | <1 min | PASS | 两端 SHA256 一致（后端 33ceef04…、前端 62cabd92…）；暂存含 manage.py 与 0008；.env 计数 0；前端文件数 1875 |
| DEPLOY-004 | 停止 ocap-backend + 辅助 timer/service | 23:51:47 | <10 s | PASS | BACKEND=inactive；TIMER=inactive；SERVICE=inactive |
| DEPLOY-005 | 覆盖后端代码（cp -a，保留 .env/venv/var） | 23:53 | <10 s | PASS | COPY_OK；0008 文件 present；`.env` SHA=5a7f1eb5…（与 PRE-09 基线一致，未被覆盖） |
| DEPLOY-006 | 迁移门控 → migrate ledger 0008 → schema/数据校验 | 23:53 | ~10 s | PASS | 门控 PLAN_LINES=1、PLAN_LINE=ledger.0008；`Applying ledger.0008... OK`；showmigrations `[X] 0008`；BATCH_COLS True；BATCH_TOTAL=2（未变）、BATCH_NULL_ACCOUNT=2（未变）、状态 ['IMPORTED']（未变） |
| DEPLOY-007 | 启动后端 + 辅助 timer + 日志检查 | 23:53:25 | ~5 s | PASS | BACKEND=active（PID 1504836）；TIMER=active；日志仅正常 worker 切换；LOG_ERROR_COUNT=0 |
| DEPLOY-008 | 后端只读路由鉴权验证 | 23:53 | <5 s | PASS | 未带令牌：reports?account_id=1 → 401、historical-expenses/batches → 401、batches/1/withdraw → 401、accounts/summary → 401 |
| DEPLOY-009 | 交换式替换 Web 静态目录 | 23:54 | <10 s | PASS | WEB_SWAPPED；1875 文件；index.html SHA=a4734286…（与本地一致）；ocap.old 保留 |
| DEPLOY-010 | Web/外网验证 | 23:54 | <10 s | PASS | 内网首页 200；主 JS assets/index-DPXXyX9L.js → 200；新文案存在于 5 个产物文件；Freeark 200；外网 https://ai-freeark.xin/ocap/ → 200 |
| DEPLOY-011 | 小程序产物本地构建（不上传） | 23:55 | ~1 min | PASS | `DONE Build complete`；app.json 存在；新文案“请选择入账账户”marker=1；产物在本地临时目录，未上传微信平台 |
| DEPLOY-012 | 清理 /tmp 暂存 + 最终状态确认 | 23:55 | <5 s | PASS | /tmp 暂存已清；快照与 ocap.old 保留；FINAL_SVC=active；FINAL_TIMER=active |

## 验证结果

| 编号 | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 后端存活 | `systemctl is-active ocap-backend` = active | ✅ |
| V-02 | 日志无新错误 | 最近 3 min `Traceback/ERROR/Unknown column/no such column/FieldError` 计数 = 0 | ✅ |
| V-03 | 新字段 | `BATCH_COLS True`（account_id / approval_instance_id / decided_at 均存在） | ✅ |
| V-04 | 旧数据未被改写 | BATCH_TOTAL=2、BATCH_NULL_ACCOUNT=2、BATCH_STATUSES=['IMPORTED']，与基线一致 | ✅ |
| V-05 | 报表账户口径路由鉴权 | `GET /api/v1/ledger/reports?account_id=1` → 401 | ✅ |
| V-06 | 历史支出批次/撤回路由鉴权 | `POST .../batches/1/withdraw` → 401；`.../batches` → 401 | ✅ |
| V-07 | Web 首页 | `http://127.0.0.1:8090/ocap/` → 200 | ✅ |
| V-08 | 前端主资源 | `assets/index-DPXXyX9L.js` → 200 | ✅ |
| V-09 | 新文案在产物中 | 5 个产物文件含“暂无可用账户” | ✅ |
| V-10 | 外网入口 | `https://ai-freeark.xin/ocap/` → 200 | ✅ |
| V-11 | 小程序产物（本地） | `app.json` 存在，构建成功 | ✅ |
| V-12 | 账户数据可用 | 启用账户 2、默认账户 1（AC-416 满足） | ✅ |
| V-13 | 关键功能写入冒烟 | 未执行（需已登录会话造可辨识测试数据） | ⏳ 待人工 |
| M-01 | AC-410 管理端按钮对比度 | 未执行（需真实浏览器登录） | ⏳ 待人工（COND-D-01） |
| M-02 | AC-417 卡片横向排列/滚动 | 未执行（需真实浏览器，含 8 账户构造） | ⏳ 待人工（COND-D-01） |
| M-03 | AC-417 合计固定不滚动 | 未执行（需真实浏览器） | ⏳ 待人工（COND-D-01） |
| M-04 | AC-421 报表详情收支分色 | 未执行（需真实浏览器登录） | ⏳ 待人工（COND-D-01） |

## 回滚记录

未触发回滚。所有 12 步成功；回滚锚点（`snapshots/{backend,web,ledger-history,migplan}-20261124234833.*`）与 `web/ocap.old` 均保留，可按 `deployment_plan.md` 的 ROLLBACK-012→001 逆序执行。

**若需回滚**（人工验收发现阻断问题）：
1. 先 `ROLLBACK-006` 前置判定：统计 `NEW_STATUS_BATCHES` / `PENDING_ROWS` / `ACCOUNT_LINKED_BATCHES`；若部署后产生了 PENDING/REJECTED/WITHDRAWN 批次，标 `[MANUAL_ROLLBACK_REQUIRED]`，不得自动反向迁移。
2. 逆序执行 ROLLBACK-005（恢复后端快照）→ ROLLBACK-004（启动）→ ROLLBACK-009（恢复 `ocap.old`）。
3. 本次部署期间无写入冒烟数据，理论上 `NEW_STATUS_BATCHES=0`，反向迁移可安全执行；但仍以现场统计为准。

## 当前系统状态与人工干预建议

- 系统当前状态：**健康**。后端 active、迁移 0008 已应用、旧数据未被改写、Web 已更新且内外网可达、Freeark 未受影响、辅助 timer 已恢复。
- 需用户完成的人工项（COND-D-01，未完成前批次不算最终成功）：
  - **V-13**：登录测试环境，用含 `SMOKE-<时间戳>` 的可辨识数据走一遍“收入录入选账户 → 报销选账户 → 历史支出导入选账户”，确认台账只入所选账户、历史批次为“审批中”未入账。
  - **M-01～M-04**：在 Chrome/Edge 打开 `192.168.31.51:8090/ocap/`，按 `deployment_plan.md` 人工清单逐项核对按钮对比度、卡片横向滚动、合计固定、收支分色。M-02/M-03 需 8 个账户时，可临时停用部分账户或在本地开发环境构造（不得在他人 Freeark 环境造数），验证后恢复。
  - 任一不通过 → 不要回滚，先按 COND-D-02 回流 GROUP_C 修复并重跑 GROUP_D；确认无法快速修复时再执行回滚。
- **小程序**：本地构建产物已就绪，上传微信体验版需用户在微信开发者工具中人工确认后执行（不在自动化范围）。

## 遗留问题

1. **CI 状态**：推送 `c67e850` 触发了 GitHub Actions（3 job）。本次部署基于本地全量通过（后端 1256、Web 607、小程序 154），但 GitHub 上 Django 5.2 口径的 `backend` job 结果需用户确认全绿（画像目标版本为 5.2，本地验证环境为 6.0.6）。若 CI 出现与 5.2 相关的差异，按新缺陷回流 GROUP_C。
2. **CL-004 仍 OPEN**：REQ-FUNC-356（历史支出导入强制选账户）已实现并部署；Q-10（小程序报表/核销）按确认不纳入本批，未扩大范围。
3. **工作区残留**：按用户确认的提交范围，以下 4 项未提交，仍留在工作区（不影响本次部署，部署包只取 backend/frontend/miniprogram 已提交内容）：`project_workspace/ocap_appeal_center/phase_status.md`、`project_workspace/ocap_appeal_center/deployment/deployment_report.md`（新）、`project_workspace/ocap_navigation_ia/deployment/deployment_report.md`、`registry_import_投票权清单.xlsx`（本地数据，按 C-55 不入库）。
4. **git 代理**：仓库配置了失效代理 `http.proxy=socks5h://127.0.0.1:10808`，本次推送用 `git -c http.proxy= -c https.proxy=` 临时覆盖成功；建议用户在本机修正或移除该失效代理配置，避免后续 push 失败。
