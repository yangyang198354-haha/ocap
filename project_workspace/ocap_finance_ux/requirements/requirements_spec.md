<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-23T22:41:49+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/phase_status.md</file>
    <file>frontend/src/portal/Reports.vue</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/layout/menus.js</file>
    <file>backend/apps/ledger/models.py</file>
    <file>backend/apps/ledger/views.py</file>
    <file>backend/apps/ledger/services.py</file>
    <file>backend/apps/ledger/urls.py</file>
    <file>backend/apps/income/models.py</file>
    <file>backend/apps/income/services.py</file>
    <file>backend/apps/income/views.py</file>
    <file>backend/apps/claims/models.py</file>
    <file>backend/apps/claims/services.py</file>
    <file>backend/apps/claims/views.py</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格说明 — ocap_finance_ux

## 执行摘要

用户要求提升财务报表页体验并引入多账户盈余管理：报表可按年报/季报筛选，点击报表以带动效的独立层查看详情，季度与年度报表的期初、期末结余必须连续；后台可创建多个账户，每个账户按历史收入支出计算余额，现有全部流水迁移到默认账户“第四届业主委员会基本账户”，账户号可编辑；主页新增账户余额卡片，财务报表页展示多账户卡片、每个账户余额及最近 10 笔收支明细。原文见 `phase_status.md` 的 `<request>`。

- 功能需求 9 条（REQ-FUNC-333～341），非功能需求 7 条（REQ-NFUNC-066～072），约束 7 条（C-370～376）。
- `[INFERRED]` 3 条，占比 3 ÷ 16 = 18.8%（上限 20%，符合画像 P5）。
- 优先级默认规则：用户明确提到的功能为 Must Have；据此功能需求 9 条均为 Must Have，非功能需求为 Should Have。
- 尚存的业务口径问题（报表与账户关系、初始结存、最近 10 笔排序、停用/删除、权限等）列在“开放问题”，每条给出推荐选项，等待用户确认后再进入架构。

## 现有系统基线

| 现状 | 位置 |
|---|---|
| 财务报表页由“报表列表卡片 + 页面底部内联详情卡片”组成，详情无独立容器与过渡动效 | `frontend/src/portal/Reports.vue:19-45` |
| 报表列表已有“全部”混合展示，但没有周期类型筛选控件 | `frontend/src/portal/Reports.vue:4-26` |
| 报表默认按年、周期类型、季度倒序 | `backend/apps/ledger/models.py:53` |
| 报表列表接口已支持按 `period_type`、`year` 过滤，前端未使用 | `backend/apps/ledger/views.py:18-26` |
| 报表以（周期类型, 年, 季度）唯一，详情为生成时快照 | `backend/apps/ledger/models.py:48-52` |
| 报表按所选期间独立汇总，余额=本期间收入-本期间支出，没有期初/期末字段 | `backend/apps/ledger/services.py:73-100` |
| 台账流水没有账户维度 | `backend/apps/ledger/models.py:5-29` |
| 收入生效后写入台账，来源类型为 `income_record` | `backend/apps/income/services.py:22-24` |
| 报销/备用金/核销通过后写入台账，来源类型为 `claim` | `backend/apps/claims/services.py:20-21`、`backend/apps/claims/services.py:39-41` |
| 流水作废保留记录并标记受影响报表过期 | `backend/apps/ledger/services.py:50-67` |
| 财务报表查看对所有登录用户开放，生成仅业委会成员 | `backend/apps/ledger/views.py:15-16`、`backend/apps/ledger/views.py:29-31` |
| 首页当前为身份卡、待办、统计卡、快捷入口、投票与最新决议，没有账户余额卡片 | `frontend/src/portal/Home.vue:3-78` |
| 门户导航“财务报表”对所有角色可见；后台“财务”分组现有报销记录与金额上限 | `frontend/src/layout/menus.js:32`、`frontend/src/layout/menus.js:53-59` |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-333 | 在财务报表页提供周期类型筛选（全部 / 仅年报 / 仅季报），默认“全部”；列表按年份倒序，同年内按年度优先、季度从 Q4 到 Q1 的稳定顺序展示；切换筛选回到第 1 页 | [USER]“除了当前按照时间倒排季报和年报外。可以看过滤出年报和所有季度报”；[CODE: frontend/src/portal/Reports.vue:19-26] | Must Have | 变更（无筛选 → 三档筛选） | 排序沿用现有倒序规则 |
| REQ-FUNC-334 | 点击某份报表后，以带进入/退出过渡动效的独立浮层展示报表详情，不再在页面底部内联展示；关闭后保留原筛选与页码 | [USER]“点击指定报告后，有动效可以看到详细。不要显示在底部”；[CODE: frontend/src/portal/Reports.vue:28-45] | Must Have | 变更（底部内联 → 独立浮层） | 浮层形态由设计阶段决定 |
| REQ-FUNC-335 | 报表必须展示期初结余、本期收入、本期支出、期末结余，并保证期间连续：季度期初=上一季度期末（上年 Q4 → 本年 Q1）；年度期初=当年 Q1 期初，年度期末=当年 Q4 期末；年度收入/支出等于四个季度之和 | [USER]“季度报，年报的期初期末结算要连起来。不要每个季度单独计算”；[CODE: backend/apps/ledger/services.py:73-100] | Must Have | 变更（单期收支 → 连续期初期末） | 最早期间期初口径见开放问题 |
| REQ-FUNC-336 | 在管理后台提供账户管理：可创建多个账户，账户至少包含名称与账户号；账户号可编辑且全局唯一；名称与账户号必填 | [USER]“后台可以创建多个账户…账户号可以编辑”；[CODE: frontend/src/layout/menus.js:53-59] | Must Have | 新增 | 停用/删除策略见开放问题 |
| REQ-FUNC-337 | 每个账户的余额等于该账户历史有效收入合计减去有效支出合计（作废流水不计）；无流水账户余额显示 0.00；账户名称或账户号变更不影响余额 | [USER]“对每个账户进行计算”“增加一个账户盈余，能够基于历史收入支出表，计算出当前…盈余”；[CODE: backend/apps/ledger/services.py:76-97] | Must Have | 新增 | “账户盈余”按账户余额口径 |
| REQ-FUNC-338 | 系统应把现有全部收入与支出流水迁移到默认账户“第四届业主委员会基本账户”；迁移后不得存在未归属账户的流水，且迁移前后有效流水总额不变 | [USER]“当前导入的所有收入和支出，迁移到默认的第四届业主委员会基本账户” | Must Have | 新增 | 默认账户账户号初始值见开放问题 |
| REQ-FUNC-339 | 新产生的收入与支出流水必须归属某个账户；未指定时归属默认账户 | [USER]“迁移到默认的…基本账户”（默认账户作为归属落点）；[CODE: backend/apps/income/services.py:22-24]；[INFERRED] | Must Have | 新增 | 录入时是否可选其他账户见开放问题 |
| REQ-FUNC-340 | 主页新增一张账户余额卡片，展示各账户名称与余额，并提供进入财务报表页的入口 | [USER]“主页有个卡片可以显示”；[CODE: frontend/src/portal/Home.vue:3-78]；[INFERRED] | Must Have | 新增 | 卡片展示粒度见开放问题 |
| REQ-FUNC-341 | 财务报表页顶部展示全部账户卡片（名称、账户号、余额），每张卡片展示该账户最近 10 笔收入/支出明细（日期、方向、金额、类型或摘要），随后是原有报表列表 | [USER]“导航栏，财务报表进入可以看到多个卡片，就有所有账户的余额，还有最近10笔收入支出的详细” | Must Have | 新增 | 排序与作废口径见开放问题 |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-066 | 报表详情浮层的进入/退出过渡时长为 240–320 ms；支持 Esc 关闭；关闭后焦点回到触发的报表条目；操作系统开启“减少动态效果”时不播放位移动画 | [USER]“有动效”；[CODE: 现有前端交互基线] | Should Have | 新增 | 可访问性与动效可用性 |
| REQ-NFUNC-067 | 财务报表页、账户卡片与详情浮层在 360×640 及 1440×900 视口下可完整操作，不出现横向滚动；支持主流浏览器最近两个大版本 | [USER]“用户体验需要提升，UI 需要极具视觉冲击力”；[CODE: 现有响应式布局基线] | Should Have | 新增 | 具体浏览器清单在架构阶段固定 |
| REQ-NFUNC-068 | 数据一致性：任一账户余额 = 该账户有效收入合计 − 有效支出合计；季度/年度链式等式（期末 = 期初 + 收入 − 支出）误差为 0.00；迁移前后全部有效收入、支出合计差额均为 0.00 | [USER]“每个账户进行计算”“期初期末结算要连起来”；[CODE: backend/apps/ledger/services.py:76-97] | Should Have | 新增 | 金额以人民币分位精度比较 |
| REQ-NFUNC-069 | 权限：账户创建与编辑仅管理后台已登录管理员可操作；账户余额与流水明细的查看沿用现有财务报表权限（登录用户可查看）；未登录返回未授权，越权返回禁止 | [CODE: backend/apps/ledger/views.py:15-16、29-31] | Should Have | 新增 | 业委会成员是否可管理账户见开放问题 |
| REQ-NFUNC-070 | 性能：在测试环境局域网内，财务报表页首屏（账户卡片 + 最近 10 笔 + 报表列表）P95 ≤ 2 s；点击报表到详情内容可见 ≤ 500 ms | [INFERRED]（无既有指标，见开放问题 Q-FA-09） | Should Have | 新增 | 待确认 |
| REQ-NFUNC-071 | 可追溯：账户的创建、编辑（含账户号变更）记录操作人、时间与变更前后值，可在后台审计日志中查询 | [CODE: backend/apps/ledger/services.py:101-106（现有报表生成审计）] | Should Have | 新增 | 沿用现有审计能力 |
| REQ-NFUNC-072 | 视觉与信息层级：在 1440×900 视口首屏内同时可见账户卡片区与至少 5 条报表；账户余额数字为页面最大字号层级（不小于相邻正文的 1.5 倍）；卡片、按钮与浮层的颜色、圆角、阴影、间距遵循现有视觉规范 | [USER]“UI 需要极具视觉冲击力”“看到多个卡片…还有最近10笔”；[CODE: frontend/src/portal/Reports.vue:1-47] | Should Have | 新增 | 以设计走查清单验收 |

## 约束

| ID | 约束 | 来源 |
|---|---|---|
| C-370 | 存量流水迁移不得丢失、重复或改变金额；迁移必须可重复执行且结果一致 | [USER] 迁移要求；[CODE: backend/apps/ledger/services.py:41-45（按来源覆盖写入）] |
| C-371 | 金额一律以人民币 2 位小数展示与比较，汇总不得出现分位误差 | [CODE: backend/apps/ledger/views.py:6（money）、backend/apps/ledger/services.py:79-90] |
| C-372 | 账户号可编辑但必须唯一；名称与账户号不得为空 | [USER]“账户号可以编辑” |
| C-373 | 报表期间沿用自然季度（1–3、4–6、7–9、10–12 月）与自然年 | [CODE: backend/apps/ledger/services.py:15-27] |
| C-374 | 本次只改 Web 门户与管理后台，不涉及微信小程序；部署沿用现有测试环境与方式，不新增环境 | [USER] 需求范围；画像 P7 |
| C-375 | 迁移属于不可逆数据操作，必须在部署窗口执行，执行前具备可回滚快照 | 画像 P7；部署计划约定 |
| C-376 | 本批次新增约束编号在全仓唯一，需求与故事编号接续现有最大值 | 项目经验 P-PM-006 |

## 超出范围

- 银行真实账户对接、自动对账、余额同步（用户未提出）。
- 多币种与汇率换算。
- 账户之间的转账、调拨、内部结算。
- 历史报表的批量重算工具（是否需要重算见开放问题）。
- 微信小程序端财务报表与账户余额展示。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| REQ-FUNC-339 | 新产生的流水默认归属默认账户 | 用户只明确了存量迁移落点；若无默认归属，新流水将无法计入任一账户余额 | 用户 |
| REQ-FUNC-340 | 主页卡片展示“各账户名称与余额” | 用户原文“主页有个卡片可以显示”承接上文账户余额 | 用户 |

## 开放问题

| ID | 问题 | 选项 | 推荐 |
|---|---|---|---|
| Q-FA-01 | 报表与账户的关系 | A. 报表仍为全组织统一口径，另提供账户筛选；B. 每个账户分别生成季报/年报；C. 统一报表，不提供账户筛选 | A（兼容历史报表与现有生成规则，改动最小） |
| Q-FA-02 | 账户是否需要“初始结存/期初余额” | A. 不设初始结存，余额纯按历史收支累计，最早期间期初为 0；B. 可设初始结存，作为该账户最早期间期初；C. 只在迁移时录入一次期初 | A（与用户“基于历史收入支出表计算”一致） |
| Q-FA-03 | 最近 10 笔的排序与作废口径 | A. 按发生日期倒序，同日按入账先后倒序，只含有效流水；B. 按创建时间倒序；C. 显示作废流水并标注 | A |
| Q-FA-04 | 账户的停用与删除 | A. 可停用不可删除；有流水时禁止删除；B. 仅无流水账户可删除；C. 允许物理删除并连带删除流水 | A（保护历史账目） |
| Q-FA-05 | 录入新流水时能否选择账户 | A. 默认预选默认账户，可改选其他可用账户；B. 全部自动归默认账户，不提供选择；C. 每次必须手动选择 | A |
| Q-FA-06 | 谁能管理账户 | A. 仅管理后台管理员；B. 管理员 + 业委会成员；C. 仅主任/副主任 | A（“后台”按管理后台理解） |
| Q-FA-07 | 主页卡片的展示粒度 | A. 启用账户合计 + 各账户余额列表；B. 仅合计；C. 仅前 3 个账户 | A（账户通常较少，信息完整） |
| Q-FA-08 | 旧报表快照如何处理 | A. 保留原快照并标记“旧口径”，按需重新生成；B. 部署后自动全部重算；C. 不处理旧快照 | A（避免部署期间长时间批处理） |
| Q-FA-09 | 性能指标是否需要 | A. 采用本规格 REQ-NFUNC-070 的 P95 ≤ 2 s；B. 不设硬指标；C. 另给指标 | A |
| Q-FA-10 | 默认账户的账户号初始值 | A. 初始为空，由管理员后续编辑填写；B. 初始填“待定”占位；C. 迁移时必须先录入账户号才允许执行 | A（账户号可编辑，迁移不被阻塞） |
