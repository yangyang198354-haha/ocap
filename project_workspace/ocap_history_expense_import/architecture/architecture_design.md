<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T17:25:22+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/requirements/requirements_spec.md</file><file>project_workspace/ocap_history_expense_import/requirements/user_stories.md</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 架构设计（增量）

## 架构概览

本次改动位于现有 Django 单体后端与 Vue 3 前端内，**不新建服务、不新建平行台账**。核心做法：

- 历史支出导入使用新增的“导入批次 + 行明细”模型承载原始行与处理结果；
- 成功行通过现有 `LedgerService.post` 写入 `LedgerEntry`（`direction=EXPENSE`，`source_type="historical_expense"`，`source_id=batch.id`，`seq=line_no`）；
- 不创建报销/备用金/核销申请，不创建审批实例，不进入审批待办（REQ-FUNC-337、C-371）；
- 作废批次调用现有 `LedgerService.void_by_source`，自动把覆盖日期的已生成报表标记为过期（REQ-FUNC-341）；
- 报表生成与展示复用现有 `LedgerService.generate` 与报表页面（REQ-FUNC-339）。

关键质量属性：导入失败不得留下半批数据（C-375）；批次可追溯与可作废（REQ-FUNC-338/341）；仅业委会成员可操作（REQ-FUNC-340）。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 画像 P7 测试环境（树莓派） |
| Web 前端 | nginx 8090 静态站点 `/home/yangyang/ocap/web/ocap` | 画像 P7 测试环境 |
| 数据库 | MySQL 库 `ocap`（测试）/ SQLite 内存库（测试） | 画像 P7 |
| 定时任务 | 无新增；现有 `ocap-run-due-jobs.timer` 不涉及本功能 | 画像 P7 |

## ADR

### ADR-178: 历史支出不进入报销审批流
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-337、C-370、C-371。现有支出只能通过报销/备用金审批后写台账（`backend/apps/claims/services.py:10-27`），历史支出若逐笔补审批会产生大量历史单据与待办。
- Options:
  - A 新建历史报销单并自动审批：保留单据形态，但污染报销列表/待办，且需要伪审批人；缺点明显。
  - B 直接写台账并单独标记“历史导入”：不产生报销/审批实例，符合“只补历史数据”的边界；纠错靠批次作废。
- Decision: 选 B。
- Consequences: 正向：审批待办与报销列表干净；报表可直接复用。负向：历史支出在报销列表不可见，必须通过批次页追溯；需新增批次管理能力。

### ADR-179: 使用“批次 + 行明细”承载导入
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-334~338、C-375。需要展示每个输入行的成功/重复/错误结果与金额合计，并支持整批作废。
- Options:
  - A 仅用 `LedgerEntry`：只能保留成功行，无法回看错误行与原始文件信息。
  - B 批次表 + 错误 JSON：实现少一张表，但 5000 行明细查询/核对不便。
  - C 批次表 + 行明细表：每行保存原始字段与处理结果，成功行关联台账；查询与作废清晰。
- Decision: 选 C。
- Consequences: 正向：可逐行核对、统计准确、作废可定位台账。负向：多一张表与一次迁移，导入时写入行数增加。

### ADR-180: 台账来源标识与作废策略
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-337、341；现有台账唯一约束 `(source_type, source_id, seq)`（`backend/apps/ledger/models.py:21-29`），报表按 `status=ACTIVE` 汇总（`backend/apps/ledger/services.py:76-79`）。
- 被排除方案与约束来源：
  - 物理删除台账行：会破坏报表历史与审计，排除；
  - 复用 `source_type="claim"`：会与报销单 id 冲突并混淆来源，排除。
- Decision: 使用 `source_type="historical_expense"`、`source_id=batch.id`、`seq=line_no`；作废通过现有 `LedgerService.void_by_source` 置 `VOIDED` 并标记报表过期，不物理删除。
- Consequences: 正向：复用现有唯一约束、幂等写入与报表过期机制。负向：`source_id` 与 `claim` 共用数值空间，查询时必须同时按 `source_type` 过滤。

### ADR-181: 权限与入口沿用业委会成员范围
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-340、C-376；现有 `IsIncomeMember` 只允许现任主任/副主任/委员（`backend/apps/core/permissions.py:93-102`），收入表页面使用同一权限。
- 被排除方案与约束来源：
  - 允许管理员：画像与现有财务页面明确收入/报表属业委会成员权限，管理员财务页只含报销；
  - 允许业主代表：现有 `CommitteeQuery.is_member` 不含代表席位。
- Decision: 后端统一 `IsIncomeMember`；前端菜单 `audience: 'committee'`，新增独立页面。
- Consequences: 正向：与收入表权限一致，无新权限模型。负向：无业委会账号时无法导入，需要先授予委员席位并绑定账号。

### ADR-182: 前端入口为独立页面
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-333~338；现有「收入表」是独立页面（`frontend/src/portal/Income.vue`），「财务报表」是只读页（`frontend/src/portal/Reports.vue`）。
- Options:
  - A 嵌入财务报表页：入口少，但导入/批次管理与只读报表混杂；
  - B 嵌入收入表页：语义不符；
  - C 新增「历史支出导入」独立页面并加入业委会菜单：职责清晰，便于后续批次管理。
- Decision: 选 C。
- Consequences: 正向：导入、批次、作废同页，权限入口明确。负向：新增一个前端页面与路由/菜单项。

## 开放问题 / ASSUMPTION

- [ASSUMPTION] 凭证附件本期不做（Q-HE-01）；如需要，后续在批次行与台账之外增加附件关联。
- [ASSUMPTION] 支出类别为自由文本（Q-HE-02），导入后写入台账 `entry_type`（为空时用“历史支出”）。
- [ASSUMPTION] 作废保留批次与行明细，状态置“已作废”（Q-HE-04）。
- [ASSUMPTION] 本期不做批次筛选/导出（Q-HE-05），列表按时间倒序分页。
- 待用户确认：REQ-FUNC-338 批次页与 REQ-FUNC-341 整批作废为推断项，用户确认前保留为本期 Should Have。
