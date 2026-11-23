<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T22:48:59.9533029+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.1</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_finance_ux/requirements/user_stories.md</file>
    <file>project_workspace/ocap_finance_ux/phase_status.md</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — ocap_finance_ux

## 架构概览

本次为 **INCREMENTAL** 改动，位于现有 Django + DRF 后端与 Vue 3 门户/管理端之内，不新增服务、不新增第三方依赖、不改微信小程序（C-374）。

改动由三条主线组成：

1. **账户维度**：在 `apps/ledger` 内新增账户实体，让台账流水归属账户；收入表与报销单增加账户外键，审批入账时传递账户；存量流水通过幂等迁移归入默认账户「第四届业主委员会基本账户」（REQ-FUNC-336～339、REQ-FUNC-338、C-370）。
2. **报表链式口径**：`LedgerReport` 增加期初/期末字段与旧口径标记，生成时按累计发生额计算期初期末；作废后把覆盖期间及之后的报表标记过期，重算时级联刷新后续报表（REQ-FUNC-335、REQ-NFUNC-068）。
3. **门户与管理端展示**：财务报表页改为「筛选 + 账户卡片 + 报表列表 + 动效浮层详情」，主页新增账户余额卡片，管理端新增账户管理（REQ-FUNC-333、334、340、341、REQ-NFUNC-066/067/072）。

关键质量属性：数据一致性（REQ-NFUNC-068 差额 0.00）、权限最小化（REQ-NFUNC-069）、首屏性能 P95 ≤ 2 s 与详情 ≤ 500 ms（REQ-NFUNC-070）、可追溯审计（REQ-NFUNC-071）。

## 部署视图

| 组件 | 运行单元 | 环境（画像 P7 中存在的） | 本次变化 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn `127.0.0.1:9000`） | 测试（内网 192.168.31.51 / 外网 frp） | 新增模型与迁移、账户 API、报表链式计算；需重启服务并执行迁移 |
| Web 前端 | nginx `:8090` 下的静态产物 | 同上 | 财务报表页、主页卡片、管理端账户管理；需重新构建并替换静态产物 |
| 数据库 | MySQL `192.168.31.98:3306` 库 `ocap` | 同上 | 新增账户表、流水账户列、报表期初期末列；迁移前需快照 |
| 定时任务 | 现有 `generate_due` 触发路径（不变） | 同上 | 生成逻辑内部改为链式口径，无新增进程 |
| 微信小程序 | — | — | 不涉及（C-374） |

未引入生产环境（画像 P7 中不存在生产环境），未引入容器化或新的部署方式（P8 禁用 Docker）。

## ADR

### ADR-178: 账户实体放在 ledger 应用内
- Status: Proposed
- Type: decision
- Context: 需要新增账户实体并让 `LedgerEntry` 归属账户（REQ-FUNC-336、REQ-FUNC-338）。现有 `apps/accounts` 表示登录主体与凭据（`backend/apps/accounts/models.py:7-63`），语义不同；台账模型集中在 `backend/apps/ledger/models.py:5-53`。
- Options:
  - A. 放在 `apps/ledger`：同应用内已有流水与报表服务，迁移与事务边界一致，改动最小；缺点是 ledger 应用职责变宽。
  - B. 新建 `apps/funds` 应用：职责更纯；缺点是新增应用注册、跨应用迁移依赖与额外路由，超出本次范围。
  - C. 放在 `apps/accounts`：复用现有应用；缺点是与登录/凭据语义冲突，权限与迁移耦合。
- Decision: 选择 A，因为本次账户只服务于台账与报表（REQ-FUNC-336/337/341），与 `LedgerEntry` 强一致（C-370）。
- Consequences: 正向——迁移与业务写入在同一事务域，便于保证总额不变；负向——ledger 应用后续若继续扩张需要再拆分。

### ADR-179: 报表仍保持全组织唯一期间，账户筛选作用于报表详情
- Status: Proposed
- Type: constraint-driven
- Context: 用户确认口径 Q-FA-01=A：报表仍为全组织统一口径，另提供账户筛选。现有唯一约束为 (period_type, year, quarter)（`backend/apps/ledger/models.py:48-52`），需求要求期初期末连续（REQ-FUNC-335）。
- 被排除方案与约束来源: 按账户分别生成报表会改变唯一键并需要重算全部历史报表，与 Q-FA-01=A 及 Q-FA-08=A 冲突；统一报表且不提供账户筛选不满足“另提供账户筛选”。
- Decision: 报表列表与快照保持全组织口径与现有唯一键；报表详情接口接受 `account_id`，在该视角下按账户实时计算收入、支出、期初、期末与明细。
- Consequences: 正向——历史报表无需按账户拆分，改动可控；负向——账户视角的详情为实时计算，与组织快照可能存在“同一期间、不同口径”的两组数字，需在 UI 标注「全部账户 / 指定账户」。

### ADR-180: 期初期末采用“累计额快照 + 重算级联”
- Status: Proposed
- Type: decision
- Context: 季度期初=上季期末、年度期初=当年 Q1 期初（REQ-FUNC-335、AC-403-01/02/03/05）；现有报表只保存本期收支与结余（`backend/apps/ledger/services.py:73-100`）。最早期间期初为 0（Q-FA-02=A）。
- Options:
  - A. 生成时按期间起点前的有效流水累计计算期初，期末=期初+收入−支出；作废时把覆盖期间及之后的报表标记过期，重算目标期间后级联刷新既有后续报表。优点：与现有快照模型一致、读取零计算；缺点：需要级联逻辑。
  - B. 读取时每次实时累计计算期初期末。优点：永远一致；缺点：与“报表快照”语义冲突，详情读取成本随数据量增长。
  - C. 只保存本期收支，期末由前端串联。优点：改动最小；缺点：无法满足 AC-403-05 的同步更新与 AC-403-06 的非空要求。
- Decision: 选择 A，因为报表本身就是生成时快照（Q-FA-08=A），且数据量有限（按年/季），级联范围可控。
- Consequences: 正向——历史报表仍可追溯，链式关系在库中可直接核对；负向——重算涉及后续报表，需要在同一事务中按时间升序处理，并写入审计。

### ADR-181: 存量流水迁移采用三段手写迁移
- Status: Proposed
- Type: constraint-driven
- Context: 需把全部存量收支迁入默认账户（REQ-FUNC-338、C-370），迁移必须幂等、总额不变；画像 P6 要求手写 scoped 迁移、禁用 makemigrations 全量产物（P8）。
- 被排除方案与约束来源: 一次性 `RunPython` 同时建表、加列并改非空在 MySQL 上不可回退且难以分段验证；使用 `makemigrations` 生成全量产物被 P8 禁止。
- Decision: 拆为：①建账户表、给流水加可空外键、给报表加期初/期末与旧口径字段；②`RunPython` 幂等创建默认账户并回填所有空账户流水；③把流水账户列改为非空（`on_delete=PROTECT`）。迁移反向操作只回退结构，不回滚已归属数据，需数据库快照兜底（C-375）。
- Consequences: 正向——每一步可单独验证，重跑回填不产生重复账户或重复归属；负向——迁移不可完全逆转，部署计划必须包含备份与人工回滚说明。

### ADR-182: 账户余额实时聚合，不设缓存列
- Status: Proposed
- Type: decision
- Context: 余额=有效收入合计−有效支出合计（REQ-FUNC-337、REQ-NFUNC-068）；账户数量少、流水按 `occurred_on` 已有索引（`backend/apps/ledger/models.py:26-29`）。
- Options:
  - A. 每次按账户聚合有效流水。优点：不会漂移，作废/补录即时生效；缺点：每次请求产生聚合查询（账户数×1）。
  - B. 在账户上保存 `balance` 字段并在入账/作废时增减。优点：读取快；缺点：并发与异常路径易漂移，需要校准任务。
  - C. 定时物化余额。优点：读取快；缺点：新增定时任务与延迟，超出本次范围。
- Decision: 选择 A，因为账户数量有限且已有 `(status, occurred_on)` 索引，聚合成本低，一致性优先（REQ-NFUNC-068）。
- Consequences: 正向——余额永远等于流水合计，便于测试直接核对；负向——账户很多且流水很大时需要再引入优化（记为风险）。

### ADR-183: 账户号可空且唯一，空值存 NULL
- Status: Proposed
- Type: decision
- Context: 账户号可编辑且全局唯一（REQ-FUNC-336、C-372），默认账户号初始为空（Q-FA-10=A）。
- Options:
  - A. `null=True, unique=True`，接口把空串归一化为 NULL。优点：SQLite 与 MySQL 都允许多个 NULL，无需部分索引；缺点：展示层需把 NULL 显示为空。
  - B. 非空 + 唯一，空值用占位符。优点：列简单；缺点：违背“初始为空”，且占位符会参与唯一冲突。
  - C. 部分唯一索引（`condition`）。优点：语义最准确；缺点：MySQL 不支持条件唯一索引，测试库与目标库行为不一致。
- Decision: 选择 A，因为目标库为 MySQL（画像 P7），必须避免部分索引。
- Consequences: 正向——迁移不被空账户号阻塞（AC-406-04）；负向——需要在服务层统一归一化与冲突校验。

### ADR-184: 报表详情改为 Element Plus 对话框 + 自定义过渡
- Status: Proposed
- Type: decision
- Context: 点击报表后用带进入/退出动效的独立浮层展示（REQ-FUNC-334、REQ-NFUNC-066），当前详情内联在页面底部（`frontend/src/portal/Reports.vue:28-45`）。
- Options:
  - A. `el-dialog` + 自定义过渡 CSS 与焦点还原。优点：自带 Esc 关闭、遮罩与焦点陷阱；缺点：过渡时长需覆盖默认值。
  - B. 自研 `Transition` + Teleport。优点：动效完全可控；缺点：需自行实现焦点陷阱与可访问性，风险高。
  - C. 独立路由页。优点：无遮罩复杂度；缺点：不满足“不离开列表位置”的体验目标（REQ-FUNC-334）。
- Decision: 选择 A，因为项目已统一使用 Element Plus，且“减少动态效果”可通过媒体查询关闭动画（REQ-NFUNC-066）。
- Consequences: 正向——可访问性与交互成本最低；负向——需确保关闭后焦点回到触发的报表条目并保留筛选与页码。

### ADR-185: 账户管理入口放在管理端“财务”分组
- Status: Proposed
- Type: constraint-driven
- Context: 账户创建与编辑仅管理后台管理员（REQ-FUNC-336、REQ-NFUNC-069、Q-FA-06=A）；管理端已有“财务”分组（`frontend/src/layout/menus.js:53-59`）。
- 被排除方案与约束来源: 放在用户端会违反“仅管理员”的权限口径；新建顶级菜单与现有信息架构不一致。
- Decision: 在管理端“财务”分组新增“账户管理”，路由 `/admin/finance/accounts`，沿用 `IsAdmin` 权限。
- Consequences: 正向——权限与导航一致；负向——“财务”分组项数增加，需要在窄屏菜单下验证可读性。

### ADR-186: 账户归属挂在单据上，入账时解析
- Status: Proposed
- Type: decision
- Context: 收入按表生效入账（`backend/apps/income/services.py:13-28`），报销/备用金/核销审批通过入账（`backend/apps/claims/services.py:10-43`）；新流水需归属账户（REQ-FUNC-339）。
- Options:
  - A. 在 `IncomeSheet` 与 `Claim` 上增加可空账户外键，入账时传给 `LedgerService.post`，未指定则解析默认账户。优点：一次提交整批归属一致，UI 只需一个选择器；缺点：同一单据内不能分账户。
  - B. 在每条 `IncomeRecord` 上增加账户。优点：粒度细；缺点：录入界面复杂，超出需求。
  - C. 全部强制默认账户、不提供选择。优点：最简单；缺点：不满足 Q-FA-05=A 的“可改选其他可用账户”。
- Decision: 选择 A，因为需求按“批”描述（AC-407-01/02），且改动集中。
- Consequences: 正向——归属规则清晰、测试可按单据断言；负向——未来若需要单据内分账户需再演进。
