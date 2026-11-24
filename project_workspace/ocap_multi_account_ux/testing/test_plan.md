<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-24T22:58:21+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/requirements/user_stories.md</file><file>project_workspace/ocap_multi_account_ux/requirements/requirements_spec.md</file><file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file><file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file><file>project_workspace/ocap_multi_account_ux/development/code_review_report.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

## 测试策略

- 被测改动：多账户落账（收入逐条/批量导入、报销、备用金、历史支出导入审批）与财务报表多账户 UI（卡片布局、默认选中、按账户取数、详情去下拉与收支分色）；含 Web、管理后台与微信小程序三端。
- 范围 in scope：US-339～US-353 的 37 条 AC（AC-410-01～AC-424-02）；前后端契约（Web api.js、小程序 utils/api.js → Django 路由）；三端账户字段一致性。
- 范围 out of scope：小程序报表/核销（Q-10 用户确认不改）；生产环境任何调用；小程序真机渲染与微信开放接口（画像 P11-3，测试用 fake，不真实调用）。
- 环境：后端 `backend/`，`python manage.py test --settings=config.test_settings`（SQLite 内存库，模型直建表、不执行迁移）；Web 前端 `frontend/`，`npx vitest run --passWithNoTests`；小程序 `miniprogram/`，`npm test`。不安装依赖、不使用容器（画像 P8）。
- 判定模式：INCREMENTAL / baseline（画像 P5），该层相对基线零新增失败且新写用例全部通过才进入下一层；已知基线失败：无。
- 分层：后端目录 `tests/unit`、`tests/integration`、`tests/e2e` 即分层标记；前端/小程序测试统一在客户端测试目录，按 `describe` 标注层级（契约/组件/页面）。
- critical path 口径：本批无浏览器 E2E 框架可驱动真实微信/管理后台登录，采用多步 API 旅程 + 客户端组件测试；e2e 报告首行声明“替代（多步 API 旅程 + 页面组件挂载）”。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-410-01 | TC-WEB-2001 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::账户管理按钮 | 管理员列表含默认/非默认账户 | 挂载 AdminAccounts 并渲染操作列 | 操作列为 `el-button`（非 `el-link`），"编辑"/"设为默认"/"停用"均可见 | 1 默认 + 1 非默认账户 |
| AC-410-02 | TC-WEB-2001 | 组件 | sim | 新写 | 同上 | 默认账户行 | 查看"设为默认"按钮 | `disabled` 为 true，且无 `is-link` 类（可用态样式不同） | 默认账户 |
| AC-411-01 | TC-WEB-2002 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::收入逐条录入 | 账户 A(默认)/B 均启用 | 打开"逐条录入"对话框 | 显示 AccountSelect，`createAccountId` 自动为 A；请求 `/ledger/accounts/summary` 带 `status=ENABLED` | A=1 默认、B=2 |
| AC-411-02 | TC-WEB-2002、TC-INT-2001 | 组件/集成 | sim | 新写 | 同上；backend/tests/integration/test_multi_account_ux_api.py::收入导入按账户 | 选择 B 并填写 1 条 | 保存为草稿 / 导入 | POST 载荷 `account_id=2`；收入表列表 `account_id=2`、`account_name=B` | CSV 1 行 |
| AC-411-03 | TC-WEB-2003 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::无可用账户 | 账户摘要返回空 | 打开逐条录入 | 显示"暂无可用账户"，保存按钮 disabled，无 POST | `{accounts:[]}` |
| AC-412-01 | TC-WEB-2004、TC-INT-2001、TC-E2E-2001 | 组件/集成/E2E | sim | 新写 | 同上；backend/tests/e2e/test_multi_account_ux_journey.py | 选择 B 上传 3 行 | 导入并审批通过 | 草稿 3 行归属 B；审批后 B 余额按 3 行增加，A 不变 | 3 行 CSV |
| AC-412-02 | TC-WEB-2004 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::导入未选账户 | 未选账户 | 调用批量导入 | 提示"请先选择入账账户"，无 post | 无 |
| AC-413-01 | TC-WEB-2005 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::报销表单 | A 默认、B 启用 | 打开报销表单 | AccountSelect 默认 A，可选启用账户 | A/B |
| AC-413-02 | TC-WEB-2005、TC-INT-2002、TC-E2E-2001 | 组件/集成/E2E | sim | 新写 | 同上；test_multi_account_ux_api.py::报销账户 | 选择 B 提交 | 审批通过 | 报销 `account_id=B`；B 余额减少、A 不变 | 300.50 |
| AC-414-01 | TC-WEB-2005 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::备用金表单 | A 默认 | 切换类型为备用金 | 账户选择项仍在且默认 A | A/B |
| AC-414-02 | TC-WEB-2006、TC-INT-1416（现有） | 组件/集成 | sim | 新写+现有 | frontend/tests/multi_account_ux.spec.js::未选账户；test_finance_accounts_api.py::test_advance_uses_selected_account | 未选账户 / 选 C | 提交 | 前端提示"请选择入账账户"且无 POST；后端审批后支出归属 C | 50.00 |
| AC-415-01 | TC-WEB-2007 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::历史支出页 | A 默认 | 挂载页面 | 显示 AccountSelect，`accountId` 默认 A；加载 INCOME 流程 | A/B |
| AC-415-02 | TC-INT-2003、TC-E2E-2001 | 集成/E2E | sim | 新写 | test_multi_account_ux_api.py::历史导入按账户 | 选择 B 导入并审批 | 查询台账 | 批次内成功行 `account_id=B`；批次视图 `account_name=B` | 2 行 |
| AC-415-03 | TC-WEB-2007 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::历史支出页 | 未选账户 | 提交导入 | 提示"请选择入账账户"，无 post，不创建批次 | 无 |
| AC-416-01 | TC-UNIT-2002、TC-INT-2003 | 单元/集成 | sim | 新写 | backend/tests/unit/test_multi_account_ux_rules.py；test_multi_account_ux_api.py | 合法文件 | 提交导入 | 批次 PENDING，行 PENDING，台账 0 条，余额不变 | 2 行 |
| AC-416-02 | TC-INT-2003、TC-E2E-2001 | 集成/E2E | sim | 新写 | test_multi_account_ux_api.py::历史导入按账户 | 审批通过 | 查询台账/账户 | 成功行入账且账户正确；重复行保持 DUPLICATE 不入账 | 2 行含 1 重复 |
| AC-416-03 | TC-UNIT-2003、TC-INT-2004、TC-INT-2005 | 单元/集成 | sim | 新写 | test_multi_account_ux_rules.py::_finish；test_multi_account_ux_api.py | 驳回 / 撤回 | 查询台账余额与批次状态 | 无台账记录、余额不变、状态 REJECTED/WITHDRAWN 可查 | 1 行 |
| AC-416-04 | TC-INT-2004、TC-WEB-2008 | 集成/组件 | sim | 新写 | 同上；frontend/tests/multi_account_ux.spec.js::历史支出状态 | 已驳回批次 | 查看列表 | 状态显示"已驳回"，`posted_rows=0` | REJECTED 批次 |
| AC-417-01 | TC-WEB-2009 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::报表卡片布局 | 3 个启用账户 | 挂载报表页 | 卡片容器 `.reports-account-grid` 存在且含 3 张卡片；样式规则 `flex: 1 1 0`、`min-width:280px` | 3 账户 |
| AC-417-02 | TC-WEB-2009 | 组件 | sim | 新写 | 同上 | 8 个启用账户 | 挂载报表页 | 容器样式含 `overflow-x:auto`，8 张卡片全部渲染 | 8 账户 |
| AC-417-03 | TC-WEB-2009 | 组件 | sim | 新写 | 同上 | 账户区可滚动 | 检查 DOM | 合计标题/金额在 `.reports-account-grid` 之外（同级），不随卡片滚动 | 8 账户 |
| AC-418-01 | TC-WEB-2009 | 组件 | sim | 新写 | 同上 | A 为默认 | 挂载报表页 | A 卡片 `aria-pressed=true` 且 `is-selected`，其余 false | A/B/C |
| AC-418-02 | TC-WEB-2009 | 组件 | sim | 新写 | 同上 | 当前选中 A | 点击 B 卡片 | B 唯一选中，列表请求带 `account_id=B` | A/B |
| AC-418-03 | TC-WEB-2009、TC-INT-1408（现有） | 组件/集成 | sim | 新写+现有 | 同上；test_finance_accounts_api.py::test_summary_enabled_filter_and_recent_zero | 存在停用账户 | 挂载报表页 | 请求 `status=ENABLED`；停用账户不渲染、不可选 | 停用账户 |
| AC-419-01 | TC-UNIT-2001、TC-INT-2006、TC-E2E-2001 | 单元/集成/E2E | sim | 新写 | test_multi_account_ux_rules.py::_totals_by_period；test_multi_account_ux_api.py::报表列表按账户 | Q1 有 A/B 流水 | 请求 `/ledger/reports?account_id=A` | 列表收入/支出/结余等于 A 口径，与详情 `account_id=A` 一致 | A 收入100/支出20；B 收入200 |
| AC-419-02 | TC-WEB-2009 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::切换账户保留筛选 | 筛选"仅季报"、选中 A | 点击 B 卡片 | 新请求 `period_type=QUARTER&account_id=B`，页码回 1 | 2 页数据 |
| AC-420-01 | TC-WEB-2010 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::报表明细 | 选中 B 打开详情 | 渲染浮层 | 浮层内无 `el-select`、无"全部账户"文案 | 明细 1 行 |
| AC-420-02 | TC-WEB-2010、TC-INT-2006 | 组件/集成 | sim | 新写 | 同上；test_multi_account_ux_api.py::报表详情账户口径 | 选中 B | 加载详情 | 请求 `/ledger/reports/{id}` params `{account_id:B}`；金额与 B 口径一致 | B 支出 80 |
| AC-421-01 | TC-WEB-2010 | 组件 | sim | 新写 | frontend/tests/multi_account_ux.spec.js::报表明细分色 | 明细含收入/支出行 | 渲染 | 收入行文字/金额类 `is-income`，支出行 `is-expense`；两者 CSS 变量不同 | 1 收 1 支 |
| AC-421-02 | TC-WEB-2010 | 组件 | sim | 新写 | 同上 | 仅支出行 | 渲染 | 全部行 `is-expense`，方向列显示"支出"；空明细显示"本期暂无收支明细" | 仅支出 + 空明细 |
| AC-421-03 | TC-WEB-2010 | 组件 | sim | 新写 | 同上 | 详情已加载 | 查看指标卡 | 本期收入 `is-income`、本期支出 `is-expense` | 1 收 1 支 |
| AC-422-01 | TC-INT-2004、TC-WEB-2008 | 集成/组件 | sim | 新写 | 同上 | 驳回批次 | 查看列表 | 状态"已驳回"，台账 0 条、余额不变 | 1 行 |
| AC-422-02 | TC-INT-2004 | 集成 | sim | 新写 | test_multi_account_ux_api.py::驳回后重导 | 已驳回批次 | 同文件重新导入并审批 | 新批次 id 不同；仅新批次入账；原批次保持 REJECTED | 同文件 1 行 |
| AC-423-01 | TC-MP-2001 | 页面 | sim | 新写 | miniprogram/tests/multi_account_ux.spec.js::小程序报销账户 | A 默认、B 启用 | 打开报销页 | account picker 默认 A，候选仅启用账户 | A/B |
| AC-423-02 | TC-MP-2002、TC-MP-018（现有） | 页面 | sim | 新写+现有 | 同上；miniprogram/tests/pages.spec.js::TC-MP-018 | 未选/选 B | 提交 | 未选提示"请选择入账账户"且无 POST；选 B 时载荷 `account_id=B` | B |
| AC-424-01 | TC-MP-2001 | 页面 | sim | 新写 | miniprogram/tests/multi_account_ux.spec.js::小程序备用金账户 | A 默认 | 切换备用金类型 | picker 仍默认 A | A/B |
| AC-424-02 | TC-MP-2002、TC-MP-020（现有） | 页面 | sim | 新写+现有 | 同上；miniprogram/tests/pages.spec.js::TC-MP-020 | 选 C/未选 | 提交 | 载荷 `account_id=C`；未选不发请求 | C |

## 测试数据需求

- 后端：默认账户 A（`AccountService.default_account()` 自动创建）+ 自建账户 B/C；启用/停用账户各一；业委会成员（MEMBER）提交人、审批人；INCOME/EXPENSE 指定审批流程；CSV/XLSX 历史支出与收入文件（含 1 条重复行）。
- 前端：`/ledger/accounts/summary` 返回 1/3/8/0 个启用账户四种形态；报表列表分页 2 页；报表明细含收入+支出、仅支出、空明细三种形态。
- 小程序：`/ledger/accounts/summary` 返回 A(默认)/B；`/approval/flows?scope=EXPENSE` 返回 1 个流程。
- 无 `[DATA_REQUIRED]`；测试数据全部在测试内构造，不依赖外部数据。

## 不可测项

| AC | 原因 |
|---|---|
| AC-410-01、AC-410-02（对比度数值） | jsdom 不计算真实渲染颜色与对比度；已用结构化断言（`el-button`、disabled、类名）覆盖可执行部分，对比度数值列入人工验证清单 M-01。 |
| AC-417-01、AC-417-02（等宽铺满/横向滚动视觉） | jsdom 无布局引擎，无法测量卡片宽度与滚动条；已断言 DOM 结构与 SFC 样式规则，视觉结果列入人工验证清单 M-02。 |
| AC-417-03（滚动时合计固定） | 同上，滚动行为需真实浏览器；列入人工验证清单 M-03。 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-339 | TC-WEB-2001 | 组件 |
| US-340 | TC-WEB-2002、TC-WEB-2003、TC-INT-2001 | 组件/集成 |
| US-341 | TC-WEB-2004、TC-INT-2001、TC-E2E-2001 | 组件/集成/E2E |
| US-342 | TC-WEB-2005、TC-INT-2002、TC-E2E-2001 | 组件/集成/E2E |
| US-343 | TC-WEB-2005、TC-WEB-2006、TC-INT-1416 | 组件/集成 |
| US-344 | TC-WEB-2007、TC-INT-2003、TC-E2E-2001 | 组件/集成/E2E |
| US-345 | TC-UNIT-2002、TC-UNIT-2003、TC-INT-2003、TC-INT-2004、TC-INT-2005 | 单元/集成 |
| US-346 | TC-WEB-2009 | 组件 |
| US-347 | TC-WEB-2009 | 组件 |
| US-348 | TC-UNIT-2001、TC-INT-2006、TC-WEB-2009、TC-E2E-2001 | 单元/集成/组件/E2E |
| US-349 | TC-WEB-2010、TC-INT-2006 | 组件/集成 |
| US-350 | TC-WEB-2010 | 组件 |
| US-351 | TC-INT-2004、TC-WEB-2008 | 集成/组件 |
| US-352 | TC-MP-2001、TC-MP-2002、TC-MP-018 | 页面 |
| US-353 | TC-MP-2001、TC-MP-2002、TC-MP-020 | 页面 |
