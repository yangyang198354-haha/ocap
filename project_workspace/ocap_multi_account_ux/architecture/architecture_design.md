<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-24T22:22:09+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>0.1.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/requirements/requirements_spec.md</file><file>project_workspace/ocap_multi_account_ux/requirements/user_stories.md</file><file>backend/apps/ledger/models.py</file><file>backend/apps/ledger/services.py</file><file>backend/apps/ledger/historical.py</file><file>backend/apps/ledger/views.py</file><file>backend/apps/income/views.py</file><file>backend/apps/income/services.py</file><file>backend/apps/claims/views.py</file><file>backend/apps/claims/services.py</file><file>backend/apps/approval/services.py</file><file>frontend/src/portal/Reports.vue</file><file>frontend/src/portal/ReportDetailDialog.vue</file><file>frontend/src/portal/AccountCard.vue</file><file>frontend/src/portal/Income.vue</file><file>frontend/src/portal/Claims.vue</file><file>frontend/src/portal/HistoricalExpenses.vue</file><file>frontend/src/admin/AdminAccounts.vue</file><file>frontend/src/shared/api.js</file><file>miniprogram/pages/claims/index.vue</file><file>miniprogram/utils/api.js</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

## 架构概览

本次为 INCREMENTAL 改动，在现有 Django 5.2 + DRF 单体后端、Vue 3 + Element Plus Web 前端、uni-app 小程序三端内就地扩展，不新增服务、不引入新依赖。改动集中在三类位置：

1. **读时聚合**：财务报表列表在既有 `LedgerReport` 存储之上按选中账户实时聚合收支（不新增报表存储），账户卡片选择状态提升到页面级，详情浮层改为被动接收页面账户。
2. **审批接入**：历史支出导入从"导入即入账"改为"导入生成待审批批次 → 复用既有审批引擎（收入表审批流程）→ 通过后回调入账"，批次与行新增状态机字段，旧批次保持原状（C-389）。
3. **账户选择入口**：收入逐条/批量导入、报销、备用金（Web + 小程序）、历史支出导入统一增加"入账账户"选择，前端强制必选，服务端对缺省值保持默认账户回退以兼容既有调用方与基线测试。

关键质量属性（引 REQ-NFUNC-074～078）：

| 质量属性 | 目标 | 实现要点 |
|---|---|---|
| 响应式布局 | 卡片按可用宽度均分；超宽仅卡片区横向滚动，页面无水平溢出；合计固定 | `Reports.vue` 卡片区 flex + `overflow-x:auto`，标题/合计置于滚动容器之外 |
| 可读性 | 操作文字对比度 ≥ 4.5:1，禁用态 ≥ 3:1 且可区分 | 账户管理页改用带可见底/边的按钮，禁用态使用既有 `--muted`/`--line` 组合 |
| 颜色语义一致 | 同一方向颜色全站一致，且始终保留文字标签 | 复用 `AccountCard.vue` 的 `--success`/`--danger` 与"收入/支出"文字 |
| 数据一致性 | 入账账户等于提交所选账户；未通过审批零台账、零余额变化 | 账户在提交时快照到 `IncomeSheet`/`Claim`/`HistoricalExpenseBatch`；历史支出仅在审批回调中入账 |
| 跨端一致 | Web 与小程序同一入口的默认账户、必填、仅启用账户规则相同 | 两端调用同一账户汇总接口与 claims 接口，前端各自做相同的默认与校验 |

## 部署视图

只用画像 P7 中存在的测试环境；无生产环境。

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Django 后端（含迁移与审批回调） | gunicorn `127.0.0.1:9000`，systemd `ocap-backend` | 测试（内网树莓派 192.168.31.51 / 外网 `https://ai-freeark.xin/ocap/`） |
| Web SPA 静态产物 | nginx `:8090` 下 `/ocap/` 静态目录 | 同上 |
| 微信小程序 | uni-app 构建产物（`build:mp-weixin`） | 开发者工具/小程序平台发布需用户当轮授权，本次不在 E1 计划内自动发布 |
| 数据库 | MySQL `192.168.31.98:3306/ocap`（测试库） | 同上 |

不新增进程、定时任务、容器或端口；部署方式仍为 tar 打包 + scp + 迁移 + systemd 重启。

## ADR

### ADR-187: 报表列表按账户取数采用读时聚合
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-360 要求季报/年报列表随选中账户显示该账户口径的收入、支出、结余；C-388 要求不修改已生成的报表存储；现有 `LedgerReportListView`（`backend/apps/ledger/views.py:168` 附近）只返回全局存储值，`ReportSerializer`（`backend/apps/ledger/views.py:236` 附近）不含账户维度；详情接口已支持 `account_id` 并按台账重新聚合（`backend/apps/ledger/views.py:205-233`）。
- Options:
  - A. 读时聚合：列表接口接收 `account_id`，对当前页报表按账户实时汇总台账。优：不改存储、与详情口径天然一致（AC-419-01）、无数据迁移；缺：每次列表多一次台账聚合查询。
  - B. 生成报表时为每个账户物化一条 `LedgerReport`。优：列表查询快；缺：改变报表存储语义，违反 C-388，历史报表需回填，账户停用/新增后需重算。
  - C. 新增按账户缓存表并按需刷新。优：性能可控；缺：新增存储与失效逻辑，当前数据量（单小区季度/年度报表）无必要，复杂度超出需求。
- Decision: 选 A。报表仍只存全局快照；`account_id` 存在时，服务层用一次台账扫描为当前页每条报表计算收入/支出，`legacy` 返回 `false` 以与详情接口一致。
- Consequences: 正向——零迁移、口径唯一、天然满足 C-388；负向——列表每页增加一次聚合查询，报表页存在重叠周期（年报表 + 季报表）时同一笔流水会被计入多条报表（符合业务语义），聚合实现需按周期桶分配。

### ADR-188: 财务报表页账户选择状态与详情联动
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-359/360/361 要求页面默认选中默认账户、卡片可切换、列表与详情跟随同一账户，且详情浮层不再提供账户下拉（AC-420-01）。
- Options:
  - A. 页面级单一 `selectedAccountId`：卡片、列表查询参数、详情浮层入参共用。优：单一事实来源，浮层无需自选账户；缺：刷新页面回到默认账户（需求未要求持久化）。
  - B. 列表与浮层各自维护账户选择。优：实现局部；缺：违反"详情跟随页面账户"，且需删除浮层下拉后仍保留第二个状态，易不一致。
  - C. 账户写入 URL query 持久化。优：可分享/刷新保留；缺：需求未要求，新增路由参数与回退逻辑，超出范围。
- Decision: 选 A。`selectedAccountId` 由 `Reports.vue` 持有；账户加载完成后若当前值失效则回落到 `is_default` 账户（无则首个启用账户）；列表请求携带该值，浮层通过 prop 接收。
- Consequences: 正向——满足 AC-418-01/02、AC-420-01/02，状态简单可测；负向——刷新不保留非默认账户选择（需求未要求，记录为已知限制）。

### ADR-189: 历史支出导入复用既有审批引擎与收入表审批流程
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-357、C-386、C-387 要求历史支出导入改为审批通过后入账且不新建独立审批体系；Q-03 用户选择"完全复用收入表审批"；现有审批引擎为 `ApprovalEngine`，通过 `register_callbacks(subject_type, ...)` 注册审批后回调，收入表用 `subject_type="income_sheet"`、`scope="INCOME"`（`backend/apps/income/apps.py`、`backend/apps/income/services.py`）。
- Options:
  - A. 新增 `subject_type="historical_expense_batch"`，审批流程取 `scope="INCOME"` 的启用流程，审批回调在 `apps/ledger` 注册。优：完全复用流程配置/审批人/通知/审计，数据边界清晰；缺：`ApprovalEngine` 的 `subject_title` 需补一个分支。
  - B. 把历史支出包装成 `IncomeSheet` 走收入表审批。优：零引擎改动；缺：污染收入数据与报表，方向/模板语义错误。
  - C. 新建独立审批表与页面。优：无耦合；缺：违反 C-386，重复实现审批人、通知、审计。
- Decision: 选 A。批次提交时用 `ApprovalEngine.submit(scope="INCOME", subject_type="historical_expense_batch", subject_id=batch.id, flow_id=..., submitter=user)`；`on_approved` 写台账，`on_rejected` 置"已驳回"，`on_withdrawn` 置"已撤回"。
- Consequences: 正向——审批规则与收入表完全一致，满足 Q-03；负向——`ApprovalEngine` 审批列表标题需新增"历史支出导入#id"分支，否则显示原始 subject_type。

### ADR-190: 历史支出导入批次与行采用扩展状态机并兼容旧批次
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-357/363、C-389；现有 `HistoricalExpenseBatch` 只有 `IMPORTED/VOIDED` 状态且导入即写台账（`backend/apps/ledger/models.py`、`backend/apps/ledger/historical.py`），行状态为 `IMPORTED/DUPLICATE/ERROR`；既有批次不得回溯补审批。
- Options:
  - A. 在原模型上扩展：`account`（可空 FK）、`approval_instance_id`、`decided_at`，批次状态增加 `PENDING/REJECTED/WITHDRAWN`，行增加 `PENDING`。优：旧数据零迁移、列表/明细页面与既有查询复用；缺：状态语义增多，查询必须显式区分"待入账"和"已入账"。
  - B. 新建"审批批次 + 行"平行表，旧表只读。优：新旧隔离彻底；缺：两套查询/页面/作废逻辑，长期维护成本高，且旧表仍需展示。
- Decision: 选 A。旧批次保持 `IMPORTED` 且 `account` 为空；新导入批次默认 `PENDING`，行先落 `PENDING`，审批通过后转为 `IMPORTED` 并写入 `ledger_entry`；去重键把 `PENDING` 批次也纳入，避免多个待审批批次重复入账。
- Consequences: 正向——C-389 零回溯，迁移可逆；负向——任一按状态统计的旧查询必须确认是否要包含 `PENDING`；被驳回批次的 `PENDING` 行会长期保留（作为历史证据），去重查询需按批次状态排除。

### ADR-191: 账户选择采用共享前端组件
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-352～356、364/365 需要 Web 四处（收入对话框、收入导入工具栏、报销/备用金表单、历史支出导入）与小程序一处选择"仅启用账户 + 默认默认账户"；账户汇总接口已存在（`GET /ledger/accounts/summary?status=ENABLED`），详情见 module_design IFC-420。
- Options:
  - A. 新建自加载的 `AccountSelect.vue`：挂载时拉取启用账户，自动回填默认账户，空列表时显示"暂无可用账户"。优：默认值/过滤/空态一次实现，四处行为一致（REQ-NFUNC-078）；缺：每实例一次轻量请求，页面可能重复请求。
  - B. 各页面自行加载与渲染 `el-select`。优：无新文件；缺：四处重复默认与空态逻辑，易出现两端不一致。
  - C. 引入 Pinia 全局账户 store。优：只请求一次；缺：为 5 处选择引入全局状态与失效处理，超出需求。
- Decision: 选 A。组件只负责"取启用账户 + 渲染选择 + 默认选中 + 空态"，校验与提交由各页面负责；小程序因技术栈不同单独实现等价 picker（MOD-214）。
- Consequences: 正向——Web 端一致且可单测；负向——打开收入页会同时有工具栏与对话框两个实例（各一次请求），数据量小可接受。

### ADR-192: 服务端 account_id 保持缺省回退默认账户
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-352～356 要求用户必须选择账户；但现有收入、报销/备用金接口已接受可选 `account_id` 并回退默认账户（`backend/apps/income/views.py:287-288`、`backend/apps/claims/views.py:128/167/202`），既有集成/E2E 测试大量在不传 `account_id` 的情况下调用；画像 P4 要求测试基线零新增失败。
- 被排除的方案与约束来源：
  - 服务端强制 `account_id` 必填（400）：会破坏既有测试与旧版小程序调用；需求的可测验收（AC-411-03、AC-412-02、AC-423-02、AC-424-02）均以"页面不发出请求"为准，不需要服务端拒绝。
  - 仅服务端校验、前端不加控件：违反 REQ-FUNC-352～356 的可见选择要求。
- Decision: 必选约束由 Web 表单与小程序表单强制执行（未选不提交）；服务端继续"显式传入则按传入账户，缺省回退默认账户"。历史支出导入的 `approval_flow_id` 为新增业务前提，服务端必填；`account_id` 缺省同样回退默认账户。
- Consequences: 正向——兼容旧客户端与基线测试，不引入回归；负向——绕过前端的 API 调用仍可能落到默认账户，需在测试与评审中明确该兼容口径。

### ADR-193: 账户管理页操作改用高对比度按钮
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-351、REQ-NFUNC-075 / AC-410-01/02；现状"编辑""设为默认"使用 `el-button link` 文字链（`frontend/src/admin/AdminAccounts.vue` 操作列），默认账户行的"设为默认"为禁用链接态，与白底几乎同色（截图 1）。
- Options:
  - A. 保留 `link` 文字链，仅覆盖文字颜色。优：改动最小；缺：禁用态仍缺底色/边框，可辨识度依赖单色，难以稳定达到 3:1 且与可用态区分。
  - B. 改为带可见边框/浅底的 `el-button`（小尺寸），禁用态使用 `--muted` 文字 + `--line` 边框。优：默认/禁用态天然分层，满足对比度与可区分；缺：操作列占用宽度略增。
  - C. 图标按钮 + tooltip。优：紧凑；缺：引入新图标语义，需求未要求。
- Decision: 选 B。操作列使用标准按钮形态；"设为默认"在已是默认账户时保持禁用，并保留"默认"标记列；颜色取自现有主题变量，不新增主题。
- Consequences: 正向——可读性与状态区分稳定，满足 WCAG AA 正文口径；负向——表格操作列变宽，窄屏需允许表格横向滚动（Element Plus 表格默认行为）。

### ADR-194: 小程序账户选择复用现有账户汇总与 claims 接口
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-364/365、REQ-NFUNC-078；小程序 `miniprogram/utils/api.js` 当前没有账户相关方法，`pages/claims/index.vue` 提交报销/备用金时不带 `account_id`；后端 claims 接口已接受可选 `account_id` 并支持小程序登录态。
- 被排除的方案与约束来源：
  - 新增小程序专用账户接口：重复实现，违反"两端同一规则"的目标（画像 P1/P3 共用后端）。
  - 在小程序内嵌账户管理：超出范围（REQ 明确只要求报销/备用金选择）。
  - 小程序报表页按账户切换、核销选账户：Q-10 默认本次不改。
- Decision: 在 `miniprogram/utils/api.js` 增加 `accounts` 方法调用既有 `GET /ledger/accounts/summary`（`status=ENABLED`），报销/备用金表单以 picker 展示并默认选默认账户，提交时在既有 payload 中增加 `account_id`；不新增后端端点。
- Consequences: 正向——零后端新增、与 Web 同源同规则；负向——小程序需自行处理 picker 空态与默认值，测试需覆盖两端一致性（AC-423/424）。

## 开放问题 / ASSUMPTION

| 编号 | 内容 | 处理 |
|---|---|---|
| OQ-B-01 | 历史支出导入在一个请求内同时"创建批次 + 提交审批"；若审批提交失败，批次是否保留为草稿？ | `[ASSUMPTION]`：同一数据库事务内创建批次与提交审批，任一步失败整体回滚，接口返回错误，不留下无审批批次。 |
| OQ-B-02 | 批次提交后、审批前账户被停用，审批通过时如何处理？ | `[ASSUMPTION]`：沿用现有报销/收入的既定行为——审批回调按批次快照账户入账，若账户已停用，`LedgerService.post` 抛 `ACCOUNT_UNAVAILABLE`（409），与 claims 现状一致；不新增特殊状态，测试只覆盖正常路径。 |
| OQ-B-03 | 历史支出导入模板说明文字是否同步更新？ | 是。模板说明增加"导入后提交审批，通过后才入账"，属于既有文本更新，不改变列结构。 |
| OQ-B-04 | 收入批量导入的去重是否要按账户隔离？ | 本次不改变现有去重口径（全库四字段），需求未要求；如后续需要按账户隔离，另立需求。 |
| OQ-B-05 | 报表列表默认 page_size 下读时聚合的查询次数？ | `[ESTIMATE]`：每页 1 次台账范围扫描 + Python 分桶，不随报表条数线性增长；数据量按单小区季度/年度报表评估为低风险。 |
