<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T18:10:00+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/deployment/deployment_plan.md</file><file>project_workspace/ocap_history_expense_import/phase_status.md</file></input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告 — 历史支出批量导入（测试环境）

## 摘要

- 目标环境：测试（树莓派，画像 P7）；策略：recreate。
- 开始：2026-11-23 18:04:30 +08:00；结束：2026-11-23 18:10 +08:00。
- 回滚锚点：`TS=20261123180449`（`backend-20261123180449.tar.gz`、`web-20261123180449.tar.gz`、`ocap.bak_20261123180449`、`freeark.bak_20261123180449`）。
- 总步骤 6 / 完成 6 / 失败 0 / 跳过 3（DEPLOY-007/008/009：nginx 与 timer 无变更）。
- 最终状态：**DEPLOYED_SUCCESSFULLY**。
- 版本标识：本地 `HEAD=9f07a3afaf350025e525be991e915438b6a50a88`，工作树含本批次未提交改动（20 项）。

## 授权核对

- 授权来源：用户当轮问答明确选择“授权部署到测试环境（推荐）”。
- 授权环境名 = `deployment_plan.md` 目标环境名 = 画像 P7 环境名：**测试环境**。
- 计划版本 = phase_status 中 APPROVED 版本：`deployment_plan.md` 1.0.0；`cicd_pipeline.md` 1.0.0。
- 结论：授权核对通过。

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 结果 | 输出摘要 |
|---|---|---|---|---|
| 预检 | 本地 `makemigrations --check`；目标机只读检查 | 18:04 | PASS | `No changes detected`；磁盘 15G 可用、内存 1544M 可用；9000/8090 属 ocap，8000/8080/80 属 Freeark；`.env` 存在且 `SECRET_KEY_SET`；`nginx -t` 成功；Freeark 8080=200；目标机 `PENDING_COUNT=0` |
| DEPLOY-001 | 生成 tar 快照与 nginx 备份 | 18:04:49 | SUCCESS | 2 份 tar（30.6MB / 41.0MB）+ 2 份 nginx 备份 |
| DEPLOY-002 | 打包后端 → scp → 解包 | 18:05 | SUCCESS | 562K tar；目标机已见 `historical.py`、`0004_historical_expense.py` |
| DEPLOY-003 | `pip install --dry-run` + `pip install` | 18:05 | SUCCESS | 两次退出码 0，全部 already satisfied |
| DEPLOY-004 | `manage.py migrate --noinput` | 18:05 | SUCCESS | `Applying ledger.0004_historical_expense... OK` |
| DEPLOY-005 | 重启 `ocap-backend` | 18:06 | SUCCESS | `active`；gunicorn 26.2.0 监听 127.0.0.1:9000，4 worker 启动 |
| DEPLOY-006 | 前端构建 → scp → 替换静态 | 18:06 | SUCCESS（重试一次） | 构建 10.35s；首次远端命令因本地引号转义失败、未对目标机产生任何变更；重试后 `index.html` 与 `HistoricalExpenses-NIlIQoAX.js` 已就位 |
| DEPLOY-007/008/009 | — | — | SKIPPED | nginx 配置未改、timer 无变更 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 后端存活 | `active` | 是 |
| 后端日志（5 分钟） | `TRACEBACKS=0` | 是 |
| 迁移已应用 | `[X] 0004_historical_expense` | 是 |
| 新接口未登录 | `GET /api/v1/admin/ledger/historical-expenses/template` → 401 | 是 |
| 登录接口存活 | `POST /api/v1/auth/login/password`（错误口令）→ 400 | 是 |
| 内网前端 | `http://127.0.0.1:8090/ocap/` → 200 | 是 |
| 外网前端 | `https://ai-freeark.xin/ocap/` → 200 | 是 |
| 外网新静态资源 | `/ocap/assets/index-aYAUecPK.js` → 200 | 是 |
| SPA 回退 | `https://ai-freeark.xin/ocap/reports` → 200 | 是 |
| 目标机 index 引用 | `/ocap/assets/index-aYAUecPK.js`（与本地构建一致） | 是 |
| Freeark 未受影响 | 8080 → 200；`https://ai-freeark.xin/` → 200 | 是 |
| 失败单元 | 无 `ocap-*` / `freeark-*` 失败单元 | 是 |
| 端口归属 | 9000/8090 属 ocap；8000/8080 属 Freeark | 是 |
| 功能冒烟（登录后导入/作废） | 未执行：无业委会成员凭据，未在目标机创建令牌 | 待用户验证 |

## 回滚记录

无（部署全部成功，未触发回滚）。

## 当前系统状态与人工干预建议

- 系统处于新版本运行状态：后端含历史支出导入 API 与 0004 迁移，前端含历史支出页面与报表页入口。
- 建议用户在浏览器登录业委会成员账号，验证：财务报表页可见“历史支出导入” → 下载模板 → 上传 1 行测试数据 → 批次列表/明细 → 整批作废。验证数据请用唯一金额/用途，验证后整批作废，避免污染报表。
- 如需回滚：按 `deployment_plan.md` 逆序执行 ROLLBACK-006→005→004→003→002，锚点 `TS=20261123180449`；ROLLBACK-004 删表会丢失已导入历史数据，标 `[MANUAL_ROLLBACK_REQUIRED]`。

## 遗留问题

1. 目标机 `web/` 下存在旧目录 `ocap.old.20261122144909`（历史遗留，本次未触碰），后续可人工清理。
2. 功能冒烟需业委会成员账号人工完成（见上）。
3. 本次部署基于本地工作树（未提交、未推送）；如后续需按远端提交重新部署，请先提交并推送。

## 补充部署 R-01：审批人显示“—”修复（2026-11-23 21:13）

- 背景：待办“查看进度”弹窗的“审批人”显示“—”。定位为时间线接口只返回 `approver_ids`、未返回 `approvers` 昵称，前端 [ApprovalTimeline.vue:19] 取不到即回退“—”；与历史支出导入无关（该弹窗为收入表#1 审批，历史导入不生成审批）。
- 授权：用户当轮明确授权部署该修复（第二次 AskUserQuestion）。
- 变更：`backend/apps/approval/services.py` 时间线补 `approvers: [{id, nickname}]`（一次查询解析，空昵称回退“用户#N”）；`tests/integration/test_approval_flow_steps.py` 增加断言。后端全量 1218 通过。
- 锚点：`TS=20261123211247` → `snapshots/backend-20261123211247.tar.gz`（35,989,625 B，可列出 `backend/`）。
- 执行：上传并解包后端 → 重启 `ocap-backend`（无迁移、无依赖变更、无前端构建）。
- 验证：
  - `systemctl is-active ocap-backend` → `active`；近 2 分钟 `Traceback` 计数 0。
  - 只读检查待办实例：`income_sheet` 实例 8 有 1 步、审批人 2 人（数据本身完整）。
  - 运行时调用 `ApprovalEngine.timeline(8, approver)`：`step 1 approvers 2 all_named True`。
  - 外网 `https://ai-freeark.xin/ocap/` → 200。
- 结果：`DEPLOYED_SUCCESSFULLY`。用户刷新“查看进度”弹窗即可看到审批人姓名。
- 回滚：`sudo rm -rf /home/yangyang/ocap/backend && sudo tar xzf /home/yangyang/ocap/snapshots/backend-20261123211247.tar.gz -C /home/yangyang/ocap && sudo systemctl restart ocap-backend`。
- 备注：沙箱重置导致上次会话 SSH 密钥丢失；本次由用户重新授权新公钥（指纹核对一致），密钥仅存于本次会话 `/tmp`。
