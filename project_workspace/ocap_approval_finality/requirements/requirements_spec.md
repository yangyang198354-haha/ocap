<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-21T13:30:00+08:00</timestamp>
  <project_name>ocap_approval_finality</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>backend/apps/resolutions/views.py</file>
    <file>backend/apps/resolutions/services.py</file>
    <file>backend/apps/claims/views.py</file>
    <file>backend/apps/income/views.py</file>
    <file>backend/apps/approval/services.py</file>
    <file>frontend/src/portal/ResolutionDetail.vue</file>
    <file>frontend/src/portal/Income.vue</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格：审批失败终局与重新发起留痕

## 执行摘要

用户原始诉求：“如果一个投票已经审批，已经投票失败了，那么结束之后……就不应该再重新发起了，除非我新起一个表决”；随后明确：“失败即终级，不可重级……适用于报销、备用金、收入表”；“失败的表决或者审批，这个记录得保留、得留痕，可以重新提交（= 新建一张新单），再次通过”；“撤回是允许重启的”；“新旧单需要互相关联，便于留痕”。

结论：4 类单据（决议、报销、备用金、收入表）审批结果为“未通过”后，**不得在原单上重新提交**，只能新建新单再次办理；原单永久保留并与新单互相关联。

功能需求 7 条 / 非功能需求 0 条；`[INFERRED]` 0 条；7 条全部 Must Have。

## 现有系统基线

| 位置 | 现状 |
|---|---|
| `backend/apps/resolutions/views.py:194-222` | 决议重提允许 `REJECTED`、`WITHDRAWN`；半数同意决议到点失败后仍可重提 |
| `backend/apps/claims/views.py:258-285` | 报销/备用金重提允许 `REJECTED`、`WITHDRAWN`（核销 `SETTLEMENT` 已禁止） |
| `backend/apps/income/views.py:329-350` | 收入表重提允许 `REJECTED`、`WITHDRAWN` |
| `backend/apps/resolutions/services.py:66-96` | 定时判定只把决议置为 `REJECTED`，**不关闭审批实例**，产生“决议已失败、实例仍审批中”的分叉 |
| `backend/apps/approval/services.py:75-83` | 重提前检查最新审批实例状态，实例仍 `PENDING` 时返回 `NOT_RESUBMITTABLE` |
| `frontend/src/portal/ResolutionDetail.vue:31-34` | 状态为 `REJECTED` 或 `WITHDRAWN` 时显示“修改后重新提交” |
| `frontend/src/portal/Income.vue:34-35` | 状态为 `DRAFT`、`REJECTED`、`WITHDRAWN` 时显示“提交/重新提交” |
| 小程序 `pages/resolutions`、`pages/claims` | 未提供重提入口，只做列表/详情展示 |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-269 | 决议、报销、备用金、收入表四类单据在审批结果为“未通过”后，不得在原单据上重新提交；Web 端不展示重提入口，后端接口对原单重提一律拒绝 | 用户原文“失败即终级，不可重级……适用于报销、备用金、收入表”“不是就旧的重新再次提交” | Must Have | 变更 | 覆盖旧规则 AC-048-04（被拒可重提） |
| REQ-FUNC-270 | 发起人撤回的单据仍可在原单修改后重新提交 | 用户原文“撤回是允许重启的” | Must Have | 保持不变 | 仅 `WITHDRAWN` 保留原单重提 |
| REQ-FUNC-271 | 审批失败后，发起人可新建一张同类型单据重新发起；新单独立走审批，通过后正常生效 | 用户原文“需要重新提个新的”“可以重新提交，再次通过” | Must Have | 新增 | 新单不与原单共享审批实例或表决记录 |
| REQ-FUNC-272 | 失败单据必须永久保留，至少保留失败原因、表决票数与分母或拒绝人与时间、原金额/明细、发起人 | 用户原文“这个记录得保留、得留痕” | Must Have | 新增 | 不得删除或覆盖原单 |
| REQ-FUNC-273 | 新建单据与原失败单据必须互相显示关联（原单显示“已由 #新单 重新发起”，新单显示“重新发起自 #原单”） | 用户确认“需要这个，便于留痕” | Must Have | 新增 | 关联仅展示，不改变权限与可见性 |
| REQ-FUNC-274 | 半数同意决议到表决截止自动判为失败时，同步结束对应审批实例，失败单据不得残留在任何人的待办中 | 用户反馈的重提报错根因；用户原文“结束之后” | Must Have | 修复 | 消除“决议终态、实例审批中”的数据分叉 |
| REQ-FUNC-275 | “未通过”单据的列表与详情须显示失败原因（表决未过半 / 审批人拒绝），并提示“该单据已结束，如需再次办理请新建” | 用户原文“标记为失败”“我看得更清楚一点” | Must Have | 变更 | 数据库状态值不变，只改文案 |

## 非功能需求

无。

## 约束

| ID | 约束 | 来源 |
|---|---|---|
| C-90 | 不新增或修改数据库状态枚举值（`PENDING`/`APPROVED`/`REJECTED`/`WITHDRAWN`；收入表另有 `DRAFT`/`EFFECTIVE`/`VOID`） | `resolutions/models.py:6`、`labels.js:38-40` |
| C-91 | 已通过/已生效单据不可修改；收入表生效后只能作废 | 基线 US-048 AC-048-05、US-060 |
| C-92 | 不改变审批通过门槛、投票分母规则、投票权限与审批流程配置 | 基线 REQ-FUNC-045/046、`approval/services.py` |
| C-93 | 失败单据不得删除、覆盖或就地改写；留痕为强制要求 | 用户原文“记录得保留、得留痕” |
| C-94 | 新建单据不继承原单的表决记录与审批实例，必须重新走完整审批 | 用户原文“新起一个表决” |
| C-95 | 关联信息不改变原有权限与可见性（决议公开范围、财务单据可见范围保持不变） | 基线 IFC-358、财务权限 |

## 决策记录

| 编号 | 决策值 | 日期 | 来源 | 受影响位置 |
|---|---|---|---|---|
| D-01 | “重新提交”= 新建一张新单，不在旧单上修改 | 2026-11-21 | 用户答复（“第一个，对”） | REQ-FUNC-271 |
| D-02 | 新旧单据互相显示关联 | 2026-11-21 | 用户答复（“我需要这个，便于留痕”） | REQ-FUNC-273 |
| D-03 | 指定负责人拒绝与投票失败同样处理（终局、需新建） | 2026-11-21 | 用户答复（“这个也同样适用”） | REQ-FUNC-269 |
| D-04 | 撤回仍允许在原单修改后重提 | 2026-11-21 | 用户答复（“撤回是允许重启的”） | REQ-FUNC-270 |

## 超出范围

- 已失败单据的“复活”或撤销终局状态。
- 审批流程配置错误（如半数同意流程误加审批人）的历史数据清理。
- 报销/备用金/收入表的金额计算规则与作废规则调整。
- 小程序新增重提或新建入口（当前小程序未提供此类入口）。

## 待确认推断项

无。

## 开放问题

| ID | 问题 | 影响 |
|---|---|---|
| Q1 | 关联文案的具体位置与样式（原单详情的关联行、新单详情的来源行）由设计阶段定稿 | 仅展示层，不影响功能 |
| Q2 | 失败单据在新单创建后是否需要在列表中默认折叠或标记“已重新发起” | 列表展示细节，设计阶段确认 |
