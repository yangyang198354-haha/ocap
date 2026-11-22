<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-22T21:36:11+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_approval_flow/phase_status.md</file>
    <file>project_workspace/ocap_approval_flow/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告 — 审批流程多步化与或/与签（ocap_approval_flow）

## 摘要

| 项 | 值 |
|---|---|
| 目标环境 | 测试（树莓派 `192.168.31.51`；内网 `http://192.168.31.51:8090/ocap/`，外网 `https://ai-freeark.xin/ocap/`） |
| 提交 | `30d9f27`（已推送 origin/main） |
| 策略 | recreate（单实例；停服 → 覆盖代码 → 迁移 → 启动） |
| 开始 / 结束 | 2026-11-22T21:30:03+08:00 / 2026-11-22T21:36:11+08:00 |
| 停机窗口 | 21:33:25 停止 → 21:34:42 启动，约 77 秒 |
| 回滚锚点 | `TS=20261122213109`（后端/Web 快照、4 表转储、迁移计划、nginx 备份） |
| 步骤统计 | 总 12 / 完成 11 / 部分完成 1（DEPLOY-012 自动项完成，人工项待用户）/ 失败 0 / 跳过 0 |
| 最终状态 | **DEPLOYED_SUCCESSFULLY** |

> 小程序仅本地构建验证，未上传微信平台。人工验证清单 MV-01~MV-06 仍待用户执行。

## 授权核对

| 核对项 | 结果 |
|---|---|
| 授权来源 | 本次 E2 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`、`TARGET_ENV=测试（树莓派 192.168.31.51）`、`USER_AUTHORIZATION=“提交并推送，然后部署测试环境”`（2026-11-22T21:30:03+08:00） |
| 授权环境 = 计划环境 = 画像 P7 环境 | 一致：测试（树莓派 192.168.31.51，内网 8090 / 外网 ai-freeark.xin） |
| 计划版本 = phase_status APPROVED 版本 | `deployment_plan.md` 1.0.0 = 登记版本 1.0.0 |
| GROUP_E1 状态 | APPROVED（GR-E1-001 PASS） |
| 待部署提交在远端 | 是：`30d9f27` 已推送 `origin/main`（`2fcb47c..30d9f27`） |

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 锚点 | `tar` 后端/Web + `showmigrations --plan` + `mysqldump` 4 表 + nginx 备份 | 21:31:09 | ~50s | SUCCESS | `ANCHOR_TS=20261122213109`；后端快照 SHA256 `c27c1921…`、Web `24861c88…`、转储 `c0afff43…`；排除项 `0`；转储 `CREATE TABLE` 4；基线 `approval.0003` 计数 0 |
| DEPLOY-002 构建打包 | `npm --prefix frontend run build -- --base=/ocap/`；`tar` 后端与 `dist` | 21:32 | ~3min | SUCCESS | `✓ built in 8.40s`；文案计数 `或签（任一通过）`=4、`审批过程`=4；后端关键文件 3、排除项 0；Web 文件 1539；后端包 `139c7a39…`、Web 包 `1850c87b…`、`index.html` `2becd17a…` |
| DEPLOY-003 上传暂存 | `scp` → `/tmp`；`sha256sum`；解包暂存 | 21:32 | ~40s | SUCCESS | 两端 SHA256 一致；`MANAGE_OK`、`MIGRATION_OK`；`ENV_FILES=0`；`WEB_STAGE_FILES=1539`。首次执行因文件名连字符/下划线笔误未找到文件，目标机无变更，修正后通过 |
| DEPLOY-004 停止服务 | `systemctl stop ocap-run-due-jobs.timer`、`stop ocap-backend` | 21:33:25 | ~5s | SUCCESS | `TIMER_STOPPED`、`BACKEND_STOPPED`；后端 `inactive` |
| DEPLOY-005 覆盖后端 | `cp -a` 暂存代码到 `backend/`（排除 `.env`/`venv`/`var`） | 21:33 | ~20s | SUCCESS | `ENV_PRESERVED`、`VENV_PRESERVED`、`VAR_PRESERVED`；`0003_approval_steps.py` 存在；`.env` SHA256 `5a7f1eb5…` 与 PRE-09 一致 |
| DEPLOY-006 迁移 | `migrate --plan` 门控 → `migrate --noinput` → `showmigrations` → schema 检查 | 21:33 | ~45s | SUCCESS | 门控 `PLAN=[approval.0003_approval_steps]`、`PLAN_COUNT=1`；`Applying approval.0003_approval_steps... OK`；schema：`TABLES_OK True`、`INSTANCE_COL True`、`ACTION_COLS True`、`STEP_COUNT 2`=`DESIGNATED_FLOWS 2`、`PENDING_DESIGNATED_NO_STATE 0`、`MULTI_STEP_FLOWS 0`、`STEP_STATE_GT1 0`、`ALL_STEPS 0` |
| DEPLOY-007 启动 | `start ocap-backend`、`start ocap-run-due-jobs.timer`、`journalctl` | 21:34:42 | ~15s | SUCCESS | 后端 `active`，`MainPID=1431764`，gunicorn 26.2.0 监听 `127.0.0.1:9000`；定时器 `active`；日志无 Traceback/ERROR |
| DEPLOY-008 后端只读验证 | `curl` 3 个端点 | 21:34 | ~3s | SUCCESS | `API_ME=401`、`API_TASKS=401`、`API_INSTANCE=401`（新路由已加载且鉴权生效） |
| DEPLOY-009 替换 Web | `ocap.new` 解包 → `ocap`→`ocap.old` → `ocap.new`→`ocap` | 21:35 | ~20s | SUCCESS | `WEB_SWAPPED`；文件 1539；`index.html` SHA256 `2becd17a…` 与本地一致 |
| DEPLOY-010 Web 入口验证 | 日志错误计数、首页、文案、主资源、外网 | 21:35 | ~10s | SUCCESS | `JOURNAL_ERRORS=0`、`WEB_INDEX=200`、文案命中 `assets/labels-DPeGsd53.js`、`ASSET_HTTP=200`、`EXTERNAL=200` |
| DEPLOY-011 小程序构建 | `UNI_INPUT_DIR=<repo>\miniprogram`、`UNI_OUTPUT_DIR=%TEMP%\ocap_mp_build_20261122213109` | 21:35 | ~40s | SUCCESS | `DONE Build complete.`、`MP_BUILD_EXIT=0`、`MP_APP_JSON=True`、`MP_LABEL_COUNT=1`、`MP_FILES=120`；构建目录已清理 |
| DEPLOY-012 部署后冒烟 | 验证表 V-01~V-11 + 人工清单 | 21:35 | ~1min | PARTIAL（自动项完成，人工项待用户） | 自动验证全部 PASS；MV-01~MV-06 未执行（需管理员/委员账号与双窗口并发操作） |

## 验证结果

| 编号 | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 后端存活 | `active`（MainPID 1431764） | 是 |
| V-02 | 日志无新错误 | `JOURNAL_ERRORS=0`（近 6 分钟，匹配 Traceback/ERROR/Unknown column/no such column） | 是 |
| V-03 | 新表/字段 | `TABLES_OK True`、`INSTANCE_COL True`、`ACTION_COLS True` | 是 |
| V-04 | 回填完整 | `STEP_COUNT 2` = `DESIGNATED_FLOWS 2`；`PENDING_DESIGNATED_NO_STATE 0` | 是 |
| V-05 | 新路由鉴权 | `/api/v1/approval/tasks` → `401` | 是 |
| V-06 | 时间线路由鉴权 | `/api/v1/approval/instances/1` → `401` | 是 |
| V-07 | Web 首页 | `http://127.0.0.1:8090/ocap/` → `200` | 是 |
| V-08 | 新文案在产物中 | `assets/labels-DPeGsd53.js` 命中 `或签（任一通过）` | 是 |
| V-09 | 外网入口 | `https://ai-freeark.xin/ocap/` → `200` | 是 |
| V-10 | 小程序产物 | `app.json` 存在；文案命中 1；120 个文件 | 是 |
| V-11 | 前端主资源 | `assets/index--UDZFWWi.js` → `200` | 是 |

## 回滚记录

未触发任何 ROLLBACK。回滚锚点与 `ocap.old` 均保留：

- 后端快照：`/home/yangyang/ocap/snapshots/backend-20261122213109.tar.gz`（`c27c1921…`）
- Web 快照：`/home/yangyang/ocap/snapshots/web-20261122213109.tar.gz`（`24861c88…`）
- 数据转储：`/home/yangyang/ocap/snapshots/approval-20261122213109.sql`（`c0afff43…`，4 表）
- 迁移计划基线：`/home/yangyang/ocap/snapshots/migplan-20261122213109.txt`
- 旧 Web 目录：`/home/yangyang/ocap/web/ocap.old`
- nginx 配置备份：`/etc/nginx/sites-available/ocap.bak_20261122213109`（本次未改配置）

回滚安全条件（当前实测）：`MULTI_STEP_FLOWS 0`、`STEP_STATE_GT1 0`、`ALL_STEPS 0`；部署后如用户创建多步/会签流程，反向迁移将转为 `[MANUAL_ROLLBACK_REQUIRED]`。

## 当前系统状态与人工干预建议

系统已处于新版本运行状态，无回滚。建议：

1. 用户按 `deployment_plan.md` 的人工验证清单执行 MV-01~MV-06（尤其 MV-05 双窗口并发会签）。
2. 浏览器强刷（Ctrl+F5）后再验收 Web；确认无误后可择期删除 `web/ocap.old` 与快照（建议保留 ≥ 7 天）。
3. 小程序在微信开发者工具导入 `miniprogram/` 构建产物（需先设 `UNI_INPUT_DIR`），确认后人工上传体验版。

## 遗留问题

| 编号 | 问题 | 处置 |
|---|---|---|
| R-01 | `deployment_plan.md` PRE-07 原写“`migrate --plan` 应为 1 行 approval.0003”，但目标机旧代码尚不含该迁移，预检阶段实际为 0 行 | 已将“恰为 1 行”的门控放在 DEPLOY-006（代码覆盖后）执行并通过；预检正确口径是“无待应用迁移/基线为 0001、0002 已应用”。建议后续计划修订 PRE-07 措辞 |
| R-02 | 人工验证 MV-01~MV-06 未执行 | 待用户用管理员与委员账号执行；不阻塞部署状态 |
| R-03 | CI 在 push 后异步触发，本次未等待其完成 | 本地已通过 GROUP_D 全量与构建；以 GitHub Actions 结果为准，失败则按“源头 revert 后重新部署”处理 |
| R-04 | 小程序未上传微信平台 | 按用户要求在开发者工具人工确认后上传 |
| R-05 | 部署期间一次暂存命令因文件名笔误失败（未产生目标机变更） | 已修正并重跑；无需回滚 |
