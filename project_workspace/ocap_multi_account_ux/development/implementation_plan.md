<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-24T22:45:00+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>0.1.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/requirements/requirements_spec.md</file><file>project_workspace/ocap_multi_account_ux/requirements/user_stories.md</file><file>project_workspace/ocap_multi_account_ux/architecture/architecture_design.md</file><file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file><file>project_workspace/ocap_multi_account_ux/architecture/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>DRAFT</status>
</file_header>

## 实现概览

- 模块数：13（MOD-202～MOD-214）；改动文件：后端 10（含新建迁移 1）、前端 10（含新建 1）、小程序 2、测试调整 7。
- 实现顺序按 module_design 依赖图：MOD-207（模型/迁移）→ MOD-208（历史支出服务与回调）→ MOD-209（后端接口）→ MOD-202/203（报表聚合与序列化）→ MOD-211/212（收入/报销后端）→ MOD-204（AccountSelect）→ MOD-205/206（报表 UI）→ MOD-210（历史支出 UI）→ MOD-213（账户管理按钮）→ MOD-214（小程序）。
- 无新增依赖；遵守 ADR-187～194。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-207 | backend/apps/ledger/models.py | 修改 | - | M | 批次新增 account/approval_instance_id/decided_at；状态机 PENDING/IMPORTED/REJECTED/WITHDRAWN/VOIDED；行状态增加 PENDING | DONE |
| 2 | MOD-207 | backend/apps/ledger/migrations/0008_historical_expense_approval.py | 新建 | MOD-207 | L | AddField×3、AlterField×2，依赖 0007 | DONE |
| 3 | MOD-208 | backend/apps/core/audit.py | 修改 | - | L | 新增 SUBMITTED/REJECTED/WITHDRAWN 审计动作 | DONE |
| 4 | MOD-208 | backend/apps/ledger/historical.py | 修改 | MOD-207 | H | create_pending_batch 提交审批；on_approved/rejected/withdrawn；withdraw_batch；作废仅限 IMPORTED；重复判定按账户隔离 | DONE |
| 5 | MOD-208 | backend/apps/ledger/apps.py | 修改 | MOD-208 | L | ready() 注册 historical_expense_batch 回调 | DONE |
| 6 | MOD-208 | backend/apps/approval/services.py | 修改 | - | L | subject_title 支持历史支出批次 | DONE |
| 7 | MOD-209 | backend/apps/ledger/views.py | 修改 | MOD-208 | H | 导入接 account_id/approval_flow_id；批次视图新增字段；列表 annotate posted_rows；撤回端点；报表列表 account_id | DONE |
| 8 | MOD-209 | backend/apps/ledger/urls.py | 修改 | MOD-209 | L | 批次撤回路由 | DONE |
| 9 | MOD-202 | backend/apps/ledger/services.py | 修改 | - | M | _totals_by_period 单次台账扫描分桶 | DONE |
| 10 | MOD-203 | backend/apps/ledger/views.py | 修改 | MOD-202 | M | ReportSerializer 按 account 覆盖金额并 legacy=False；报告详情沿用既有 account_id | DONE |
| 11 | MOD-211 | backend/apps/income/views.py | 修改 | MOD-202 | M | 导入解析 account_id 写入收入表；重复判定按账户；sheet_view 返回 account；列表 select_related | DONE |
| 12 | MOD-212 | backend/apps/claims/views.py | 修改 | - | L | claim_view 返回 account_id/account_name；列表/详情 select_related | DONE |
| 13 | MOD-204 | frontend/src/shared/AccountSelect.vue | 新建 | - | M | 自加载启用账户、默认选中、loaded 事件、空态 | DONE |
| 14 | MOD-205 | frontend/src/portal/Reports.vue、AccountCard.vue | 修改 | MOD-203/204 | H | 卡片 flex 均分+横向滚动；selectedAccountId 默认并传 account_id；可点击/键盘/aria-pressed；收支分色 | DONE |
| 15 | MOD-206 | frontend/src/portal/ReportDetailDialog.vue | 修改 | MOD-205 | M | 删除账户下拉；接收 accountId；指标与明细收支分色 | DONE |
| 16 | MOD-211 | frontend/src/portal/Income.vue、shared/api.js | 修改 | MOD-204 | M | 导入账户选择、创建弹窗账户选择与校验、列表展示账户；importFile 带 account_id | DONE |
| 17 | MOD-212 | frontend/src/portal/Claims.vue | 修改 | MOD-204 | M | 报销/备用金表单账户选择、校验、提交 account_id；列表展示账户 | DONE |
| 18 | MOD-209/210 | frontend/src/shared/api.js | 修改 | MOD-209 | L | historicalExpenseApi.importFile({accountId,flowId})、withdrawBatch | DONE |
| 19 | MOD-210 | frontend/src/portal/HistoricalExpenses.vue、shared/confirm.js | 修改 | MOD-209 | H | 账户/流程选择与校验；状态与行状态映射；撤回/作废；说明文案 | DONE |
| 20 | MOD-213 | frontend/src/admin/AdminAccounts.vue | 修改 | - | L | 操作列改高对比度按钮，禁用态可辨 | DONE |
| 21 | MOD-214 | miniprogram/utils/api.js、pages/claims/index.vue | 修改 | MOD-211/212 | M | accounts 接口；报销/备用金账户 picker 默认与校验；提交 account_id | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件，含调用方客户端） | 状态 | 说明 |
|---|---|---|---|---|
| US-339 | AC-410-01 | frontend/src/admin/AdminAccounts.vue:操作列 el-button | DONE | 链接按钮改带边框按钮（默认主题文字/边框对比度达标） |
| US-339 | AC-410-02 | 同上 `:disabled="row.is_default"` + `plain` | DONE | 禁用态透明度与可用态不同 |
| US-340 | AC-411-01 | frontend/src/portal/Income.vue:创建弹窗 AccountSelect | DONE | 默认账户由 AccountSelect loaded 事件回填 |
| US-340 | AC-411-02 | Income.vue:create() account_id；backend/apps/income/views.py IncomeSheetCreateView | DONE | 后端既有逐条创建已接收 account_id |
| US-340 | AC-411-03 | Income.vue:noAccounts + 保存按钮 :disabled | DONE | 提示"暂无可用账户"，按钮不可用，无请求 |
| US-341 | AC-412-01 | Income.vue 工具栏 AccountSelect + importFile；income/views.py IncomeImportView | DONE | 草稿写 account；审批通过后按账户可查 |
| US-341 | AC-412-02 | Income.vue:importFile 前置校验 | DONE | "请先选择入账账户"，不发请求 |
| US-342 | AC-413-01 | frontend/src/portal/Claims.vue:报销表单 AccountSelect | DONE | 默认 A，仅启用账户 |
| US-342 | AC-413-02 | Claims.vue:create() + claims/views.py ClaimCreateView | DONE | 提交 account_id，入账扣减对应账户 |
| US-343 | AC-414-01 | Claims.vue:备用金表单 AccountSelect | DONE | 与报销共用表单项 |
| US-343 | AC-414-02 | Claims.vue:create() 校验；claims/views.py | DONE | 未选账户提示"请选择入账账户" |
| US-344 | AC-415-01 | frontend/src/portal/HistoricalExpenses.vue 工具栏 | DONE | 账户默认选中，仅启用账户 |
| US-344 | AC-415-02 | historical.py on_approved 逐行 account=batch.account | DONE | 批次行写到所选账户 |
| US-344 | AC-415-03 | HistoricalExpenses.vue:uploadFile 校验 | DONE | 未选账户/流程分别提示，不创建批次 |
| US-345 | AC-416-01 | historical.py create_pending_batch；ledger/views.py import | DONE | 批次 PENDING，台账 0 条 |
| US-345 | AC-416-02 | historical.py on_approved | DONE | 仅 PENDING 批次入账，重复/错误行不入账 |
| US-345 | AC-416-03 | historical.py on_rejected/on_withdrawn/withdraw_batch | DONE | 不写台账、余额不变，状态可查 |
| US-345 | AC-416-04 | HistoricalExpenses.vue STATUS_TEXT；ledger/views.py _batch_view | DONE | "已驳回"展示并可查看 |
| US-346 | AC-417-01 | Reports.vue `.reports-account-grid` flex:1 1 0 + min-width 280px | DONE | 3 卡等宽铺满，无页面级横向滚动 |
| US-346 | AC-417-02 | 同上 overflow-x:auto | DONE | 卡片区内横向滚动，宽度不压缩 |
| US-346 | AC-417-03 | 合计行位于滚动容器外 | DONE | 仅卡片区横向移动 |
| US-347 | AC-418-01 | Reports.vue selectedAccountId + AccountCard is-selected/aria-pressed | DONE | 默认账户唯一选中 |
| US-347 | AC-418-02 | Reports.vue selectAccount → resetAndLoad | DONE | 点选切换唯一选中 |
| US-347 | AC-418-03 | Reports.vue loadAccounts status=ENABLED | DONE | 停用账户不出现 |
| US-348 | AC-419-01 | Reports.vue filters account_id；ledger/views.py ReportSerializer | DONE | 列表按选中账户实时聚合 |
| US-348 | AC-419-02 | Reports.vue selectAccount 保持 periodFilter 并 resetAndLoad | DONE | 回到第 1 页，筛选保留 |
| US-349 | AC-420-01 | ReportDetailDialog.vue 移除 el-select | DONE | 无账户下拉/全部账户 |
| US-349 | AC-420-02 | Reports.vue :account-id；ReportDetailDialog load(accountId) | DONE | 指标与明细同账户口径 |
| US-350 | AC-421-01 | ReportDetailDialog 明细方向/金额 is-income/is-expense | DONE | 与账户卡片使用同一 CSS 变量 |
| US-350 | AC-421-02 | 明细空态提示 + 方向文字 | DONE | 无明细空态既有实现保留 |
| US-350 | AC-421-03 | ReportDetailDialog 指标卡 is-income/is-expense | DONE | 收入/支出分色 |
| US-351 | AC-422-01 | HistoricalExpenses.vue 状态列 + 明细 | DONE | 已驳回可查看，台账不变 |
| US-351 | AC-422-02 | historical.py 去重仅 PENDING/IMPORTED 批次；新批次 id 不同 | DONE | 驳回批次不阻止重新导入 |
| US-352 | AC-423-01 | miniprogram/pages/claims/index.vue account picker + loadAccounts | DONE | 默认 A，仅启用账户 |
| US-352 | AC-423-02 | 同上 chosenAccountId + create | DONE | 未选提示"请选择入账账户"且不发请求 |
| US-353 | AC-424-01 | miniprogram claims picker（备用金分支共用） | DONE | 默认 A |
| US-353 | AC-424-02 | miniprogram chosenAccountId + create | DONE | 未选拦截；提交 account_id |

## 迁移

- `backend/apps/ledger/migrations/0008_historical_expense_approval.py`：新增 account、approval_instance_id、decided_at；调整批次与行状态枚举。可逆（Reverse 删除字段并恢复原枚举），已在 test_settings 下通过 `makemigrations --check`。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 无 | - | - | - |

## 开放问题

- [ASSUMPTION] 历史支出与收入导入的"重复"判定按账户隔离，并把 account 为空的历史旧数据视为默认账户范围；否则不同账户同日同额同类同说明的合法记录会被误跳过。
- [ASSUMPTION] 报表列表按账户覆盖 total_income/total_expense/balance，期初/期末沿用报表详情按账户计算；列表仅展示前三个金额。
- [ASSUMPTION] 历史支出导入的审批流程 scope 复用 INCOME（ADR-189），前端只列出 INCOME 流程。
- 小程序构建需 `UNI_INPUT_DIR` 指向仓库根（原 `build:mp-weixin` 默认找 `src/manifest.json` 会失败），属仓库既有布局问题，未修改构建配置。
