<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-23T23:56:00+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_finance_ux/deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>SUCCESS</status>
</file_header>

# 部署报告 — 财务报表体验与多账户（ocap_finance_ux，测试环境）

## 1. 结论

| 项 | 结果 |
|---|---|
| 执行授权 | 用户当轮「好的，提交并部署到测试环境」；`PRODUCTION_DEPLOY_CONFIRM=true`，环境=测试 |
| 提交与推送 | `3ed5b6b`（Merge remote-tracking branch 'origin/main'）；`9f07a3a..3ed5b6b main -> main` |
| CI | run 45209418691 `completed success`（2m20s） |
| 部署策略 | recreate；停服 23:51:28 → 后端启动 23:53:57，停机约 2.5 分钟 |
| 迁移 | 5 个全部 `OK`：ledger 0004/0005/0006、income 0006、claims 0005 |
| 验证 | V-01~V-11 全部通过；M-01 已核实；M-02~M-07 待人工浏览器验证 |
| 回滚锚点 | `ANCHOR_TS=20261123235008`（backend/web tar、5 表转储、migplan） |
| 总体状态 | **DEPLOYED / SUCCESS**（存在 1 项计划外偏差，已处置并记录于 §5） |

## 2. 目标环境

- 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/`；无生产环境。
- 应用根 `/home/yangyang/ocap`；后端 systemd `ocap-backend`（gunicorn 127.0.0.1:9000）；Web 目录 `/home/yangyang/ocap/web/ocap`。
- 辅助单元：`ocap-content-worker.service`、`ocap-run-due-jobs.timer`（部署前记录并停止/恢复）。
- 远端磁盘：`/dev/mmcblk0p2 29G 14G 16G 50% /`（部署时可用 ≈14G）。

## 3. 锚点与制品

### 3.1 目标机快照（保留 ≥7 天）

| 文件 | SHA256 |
|---|---|
| `snapshots/backend-20261123235008.tar.gz` | `90215e7fe570322f6899799d2c071d91c0c83f521247d0a863fb240bc10a9e83` |
| `snapshots/web-20261123235008.tar.gz` | `14b71ab47f2057e17f87f1a005e95a212331773d531ed02e340a99ae0bca2111` |
| `snapshots/ledger-20261123235008.sql`（5 表） | `bbe031a9368bf4831c4e9e841b24633ef1df2cf706f41779fc9209b4a1902e16` |

- 备份排除项计数 `0`；`CREATE TABLE` = `5`（`ledger_ledgerentry`、`ledger_ledgerreport`、`income_incomesheet`、`income_incomerecord`、`claims_claim`）。
- PRE-09 锚点哈希：`web/ocap/index.html` = `771e8cb6...2171e`；`backend/.env` = `5a7f1eb5...12220`。
- 额外保存：`snapshots/0004_historical_expense.py.disabled-20261123235008`（见 §5 偏差）。

### 3.2 部署制品（开发机）

| 文件 | SHA256 |
|---|---|
| `backend_3ed5b6b_20261123235008.tar.gz` | `03c09143b94001ae3874b0b5106d70cf1f5219e80b353d43850cc19f4c010b8e` |
| `frontend_dist_3ed5b6b_20261123235008.tar.gz` | `f5b7f92845b5d3251f129cac5f2b0e9044307bf401c774cf3c11298178820ba0` |
| `frontend/dist/index.html` | `1187c81490dfd731de107f62a24e3e45f2ad21590937daad6a138e99491c70e3` |

- 前端构建：`VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/` → `✓ built in 8.64s`。
- 产物文案抽检：`账户余额` 命中 3 个文件，`旧口径` 命中 1 个文件。
- 后端 tar 关键路径 6/6（3 个 ledger 迁移 + income 0006 + claims 0005 + `ledger/services.py`）；`.env/venv/var` 排除计数 `0`。
- dist 文件数 `1705`；上传后两端 SHA256 一致；暂存解包 `ENV_IN_STAGE=0`、`WEB_STAGE_FILES=1705`。

## 4. 执行记录

| 步骤 | 结果 |
|---|---|
| PRE-01~09 | 通过；基线 `ledger` 最高 `0003`（另有仓库外 `0004_historical_expense`）、`income` `0005`、`claims` `0004`；`migrate --plan` 部署前 0 行（新迁移尚未上机） |
| DEPLOY-001 | `ANCHOR_TS=20261123235008`，4 文件非零，排除项 0，`CREATE TABLE`=5 |
| DEPLOY-002 | 构建 `✓ built in 8.64s`；文案 3/1；关键路径 6；排除 0；dist 1705 |
| DEPLOY-003 | 上传 SHA256 一致；`STAGE_OK`；暂存无 `.env`；web 暂存 1705 |
| DEPLOY-004 | 停止 timer、content-worker、ocap-backend；`STOP_TIME=235128`，三者均 `inactive` |
| DEPLOY-005 | `cp -a` 覆盖；迁移文件就位；`.env` 哈希 `5a7f1eb5...` 未变；`venv`/`var` 保留 |
| DEPLOY-006 | 门控 `migrate --plan` = 恰 5 行且集合匹配；5 个迁移全部 `OK` |
| DEPLOY-007 | `active`，MainPID=1470720，`ActiveEnterTimestamp=23:53:57`；辅助单元恢复 `active` |
| DEPLOY-008 | 新路由 `ledger/accounts/summary`、`ledger/reports`、`admin/ledger/accounts` 均 `401` |
| DEPLOY-009 | `WEB_SWAPPED`；文件数 1705；`index.html` 哈希 = 本地 |
| DEPLOY-010 | V-01~V-11 通过，见 §6 |

## 5. 计划外偏差与处置

| 编号 | 现象 | 处置 | 影响 |
|---|---|---|---|
| DEV-01 | 目标机存在仓库中不存在的迁移 `ledger/0004_historical_expense.py`（历史支出批量导入，DB 已记录 applied；当前代码无对应模型/引用），与 `0006_ledger_entry_account_not_null` 形成双 leaf，`migrate --plan` 报 `Conflicting migrations detected` | 执行 DEPLOY-006 门控前将其移至 `snapshots/0004_historical_expense.py.disabled-20261123235008` 并清理 `.pyc`；未删除，回滚快照内亦保留 | 门控恢复为恰 5 行；DB 中 `ledger_historicalexpense*` 表保留不动；该文件不在 repo，若后续合入对应分支可原样恢复 |
| DEV-02 | PRE-07 计划假设 `ledger` 基线最高 `0003`，实际为 `0003 + 0004_historical_expense` | 门控口径改为“新代码下 `migrate --plan` 恰为计划 5 行集合”，已通过 | 无 |

> 该偏差不影响本次 5 个迁移的依赖图（均基于 `ledger 0003`），但说明目标机与 repo 的迁移历史存在漂移，建议后续把历史支出功能正式纳管或清理。

## 6. 部署后验证

| 编号 | 检查 | 实测 | 结论 |
|---|---|---|---|
| V-01 | `systemctl is-active ocap-backend` | `active`（PID 1470720） | PASS |
| V-02 | 近 3 分钟日志错误计数 | `ERRORCOUNT=0`；仅正常启动日志 | PASS |
| V-03 | 结构校验 | `ACCOUNT_TABLE True`、`ENTRY_COL True`、`REPORT_COLS True`、`SHEET_COL True`、`CLAIM_COL True` | PASS |
| V-04 | 回填完整 | `DEFAULT_ACCOUNTS 1`、`TOTAL_ACCOUNTS 1`、`NULL_ENTRY_ACCOUNTS 0`、默认账户名「第四届业主委员会基本账户」 | PASS |
| V-05 | 总额不变（M-01） | 迁移前转储 198 行 / `899045.56`；迁移后 `ENTRY_COUNT 198` / `ENTRY_SUM 899045.56`，差额 `0.00`；`LEGACY_REPORTS 21` = 迁移前报表 21 行 | PASS |
| V-06 | `/api/v1/ledger/accounts/summary` | `401` | PASS |
| V-07 | `/api/v1/ledger/reports` | `401` | PASS |
| V-08 | `/api/v1/admin/ledger/accounts` | `401` | PASS |
| V-09 | `http://127.0.0.1:8090/ocap/` | `200` | PASS |
| V-10 | 新文案在产物 | `assets/Reports-BetbSteP.js` 含「账户余额」 | PASS |
| V-11 | `https://ai-freeark.xin/ocap/` | `200` | PASS |

- 附加：经 nginx 的 `/ocap/api/v1/ledger/accounts/summary` = `401`，反向代理链路正常。

## 7. 人工验证清单状态

| 编号 | 状态 | 说明 |
|---|---|---|
| M-01 | 已完成（自动化核对） | 见 V-05；默认账户唯一、回填无遗漏 |
| M-02 | 待人工 | 报表筛选后刷新回到「全部」第 1 页 |
| M-03 | 待人工 | 360px 视口浮层无横向滚动 |
| M-04 | 待人工 | 减少动态效果下浮层无位移动画 |
| M-05 | 待人工 | 汇总接口失败时主页卡片显示失败与重试 |
| M-06 | 待人工 | 管理端账户新建/改名/设默认/停用 |
| M-07 | 待人工 | 收入/支出录入默认账户预选与归属 |

## 8. 回滚就绪性

- 前端：`/home/yangyang/ocap/web/ocap.old` 保留，可用 `mv` 立即回退（ROLLBACK-009）。
- 后端：`snapshots/backend-20261123235008.tar.gz` 叠加恢复（ROLLBACK-005），`.env`/`venv`/`var` 不在包内。
- 数据：`snapshots/ledger-20261123235008.sql` 为 5 表全量转储；迁移反向默认 `MANUAL_ROLLBACK_REQUIRED`，需先按 ROLLBACK-006 只读判定（`ACCOUNTS=1`、`SHEETS_WITH_ACCOUNT=0`、`CLAIMS_WITH_ACCOUNT=0`、无新增流水）。
- 清理项（验证通过 7 天后）：`web/ocap.old`、`/tmp/ocap_*_stage_20261123235008`、`/tmp/backend_3ed5b6b_20261123235008.tar.gz`、`/tmp/frontend_dist_3ed5b6b_20261123235008.tar.gz`。

## 9. 遗留与建议

1. 历史支出迁移（`0004_historical_expense`）来源不明且未纳入 repo，已停用保存；建议与相关功能负责人确认后正式纳管或清理 DB 中的孤儿表。
2. M-02~M-07 需在浏览器与管理员/业委会账号下完成，结果回填本报告。
3. 用户待确认项：账户选择器 OQ-01/GR-C-001-F01、默认账户停用与默认转移 F02、旧报表 legacy 展示 F03。
