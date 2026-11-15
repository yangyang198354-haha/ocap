<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-14T17:29:30+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/phase_status.md</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/stores/auth.js</file>
    <file>frontend/src/portal/Units.vue</file>
    <file>backend/apps/identity/services.py</file>
    <file>backend/apps/committee/services.py</file>
    <file>backend/apps/residency/models.py</file>
    <file>backend/apps/residency/services.py</file>
    <file>backend/apps/accounts/directory.py</file>
    <file>backend/apps/registry/models.py</file>
    <file>miniprogram/pages/index/index.vue</file>
    <file>miniprogram/pages/me/index.vue</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格：用户端身份显示与认证房屋信息展示（INCREMENTAL）

## 执行摘要

- 业务背景（用户原话）：“没有认证的业主身份的是游客，认证了业主身份（和清册业主手机号一致、或者通过申诉上传了产权证明的），是产权业主，被产权业主认可拉进来的事同住人。这个信息应当在主页的当前身份的模块正确显示。认证房屋模块除了显示数量，还要显示专有部分的名称以及类型，还要有面积信息。”
- 功能需求 6 条（REQ-FUNC-136 ~ 141）；非功能需求 3 条（REQ-NFUNC-024 ~ 026）。
- `[INFERRED]` 1 条（面积显示格式），占比 1 ÷ (6 + 3) = 11.1%，不超过画像 20%。
- 优先级规则：用户明确提到的身份显示、认证房屋明细与两端一致为 Must Have；加载态与排序稳定性为 Should Have。
- 用户已确认：Q-ID-01 职务优先直接显示；Q-ID-02 Web 与小程序都改；Q-ID-03 包含同住人房屋并标注；Q-ID-04 主页卡片内展开；Q-ID-05 全部展示；Q-ID-06 用户端不出现“户主”。决策见“决策记录”。
- 本轮只做需求与用户故事；用户确认后进入架构与开发。

## 现有系统基线

| 现有能力 | 位置 | 现状 |
|---|---|---|
| 主页当前身份显示 | `frontend/src/portal/Home.vue:9` | 显示 `auth.identities.join('、')`，无身份时显示“游客” |
| 用户端身份数据来源 | `frontend/src/stores/auth.js:10` | 取 `/me` 的 `identities.labels` |
| 身份文案生成 | `backend/apps/committee/services.py:65-77` | 先放业委会职务，再放第一条有效房屋关系的中文角色名；无身份时“游客” |
| 房屋关系角色 | `backend/apps/residency/models.py:8` | HEAD=户主、OWNER=产权业主、RESIDENT=同住人 |
| 首位认证规则 | `backend/apps/residency/services.py:30` | 首位认证者为 HEAD（户主），后续产权人为 OWNER |
| 认证房屋统计卡 | `frontend/src/portal/Home.vue:107-108` | 只显示已绑定房屋数量，note 为“已绑定的房屋数” |
| 用户端房屋明细 | `frontend/src/portal/Units.vue` | 只有清册认证、申诉、同住人表单，没有已绑定房屋列表 |
| 用户端返回的房屋信息 | `backend/apps/identity/services.py:20-23` | 仅 `unit_id`、`specific_part`、`role`，无类型与面积 |
| 房屋类型与面积 | `backend/apps/registry/models.py` | 清册已有专有部分类型（住宅/公寓/商铺/车位/其他）与面积 |
| 小程序主页 | `miniprogram/pages/index/index.vue:8、80-85` | 同样显示 labels 与“认证房屋”数量；无房屋明细 |

## 当前实现对照（差距）

| 需求点 | 当前实现 | 差距 | 结论 |
|---|---|---|---|
| 当前身份显示 | 首位认证者显示“户主”，其余产权人显示“产权业主”；业委会职务并列在前 | 用户要求单一最高身份：有效职务直接显示职务，其余统一显示“产权业主”，不再出现“户主” | **不一致，需变更** |
| 游客判定 | 无任何有效房屋关系且无业委会职务时显示“游客” | 与需求一致 | 一致 |
| 同住人判定 | 有效 RESIDENT 关系显示“同住人” | 与需求一致 | 一致 |
| 多身份优先级 | 只取第一条有效房屋关系的角色，且职务与角色并列显示 | 需改为：主任/副主任/委员/业主代表 > 产权业主 > 同住人 > 游客，且只显示一个 | **不一致，需变更** |
| 认证房屋模块 | 只显示数量 | 需同时显示每套专有部分名称、类型、面积，全部展示并标注关系 | **不一致，需变更** |
| 房屋类型/面积数据 | 用户端房屋信息不含类型与面积 | 需在用户端展示类型与面积 | **不一致，需变更** |
| 已绑定房屋明细 | 用户端无任何明细列表 | 需在认证房屋模块内展示 | **不一致，需变更** |
| 撤销/结束关系 | `/me` 只返回未结束关系 | 与需求“当前有效”一致 | 一致 |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-136 | 在用户端主页“当前身份”模块只显示一个身份，优先级为：有效业委会职务或业主代表（主任 / 副主任 / 委员 / 业主代表）> 产权业主 > 同住人 > 游客；担任职务者直接显示职务，不再并列或重复显示“产权业主” | 用户原话；`Home.vue:9`；`committee/services.py:65-77`；`committee/models.py:27`；`residency/models.py:8`；用户 Q-ID-01 答复 | Must Have | 变更 | 变更前：职务与“户主/产权业主”并列，首位认证者显示“户主”；变更后：单一最高身份，职务优先，“户主”不再对用户显示 |
| REQ-FUNC-137 | 产权业主身份覆盖两类认证来源：清册登记手机号与当前手机号一致完成认证，或产权申诉审核通过；两者均显示“产权业主” | 用户原话；`residency/services.py:16-32`；`residency/views.py:47、72` | Must Have | 继承 | 现有角色内部仍区分首位认证者，但用户可见文案统一 |
| REQ-FUNC-138 | 同住人身份覆盖经有效产权业主审批通过的同住人申请；无任何有效房屋关系且无有效职务时显示“游客” | 用户原话；`residency/models.py:47-58`；`committee/services.py:75-76` | Must Have | 继承 | — |
| REQ-FUNC-139 | 在用户端主页“认证房屋”卡片内，除已认证专有部分数量外，逐套显示专有部分名称、类型与面积；全部有效关系都显示（产权业主与同住人均包含），并标注该套关系；仅显示当前有效关系；无已认证房屋时显示数量 0 与空状态文案 | 用户原话；Q-ID-03/04/05 答复；`Home.vue:107-108`；`identity/services.py:20-23`；`registry/models.py` | Must Have | 变更 | 变更前：仅数量；变更后：数量 + 明细列表（同住人标注“同住人”，产权业主标注“产权业主”） |
| REQ-FUNC-140 | 专有部分名称使用清册中的当前显示名称（如“1栋1单元9层902号”）；类型显示为住宅、公寓、商铺、车位、其他之一；面积保留两位小数并带“㎡”；类型或面积未登记时显示“未登记” | 用户原话；Q-ID-03 答复；`registry/models.py` | Must Have | 新增 | 面积格式为 `[INFERRED]` |
| REQ-FUNC-141 | Web 用户端与小程序用户端的“当前身份”和“认证房屋”信息保持一致（同源、同口径、同空值文案） | 用户原话；Q-ID-02 答复；现有两端页面 | Must Have | 新增 | 用户确认两端都改 |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-024 | 身份与认证房屋信息在主页首次加载完成后一次呈现，不出现先显示“游客/0 套”再跳变为真实身份与数量的情况 | `[INFERRED]` 现有 Home 先渲染后请求 /me；用户原话“正确显示” | Should Have | 新增 | 可在加载中显示占位，不显示错误身份 |
| REQ-NFUNC-025 | 认证房屋明细按专有部分名称稳定排序；同一专有部分只出现一次 | `[INFERRED]` 列表类展示的通用要求 | Should Have | 新增 | — |
| REQ-NFUNC-026 | 身份与房屋信息只展示当前有效关系；已撤销、已结束、已合并的关系不出现，且不因历史关系改变当前身份 | `residency/models.py:18-19`；`identity/services.py:20` | Must Have | 继承 | — |

## 约束

- C-34：用户可见身份为单一最高身份：主任 / 副主任 / 委员 / 业主代表 / 产权业主 / 同住人 / 游客；有效职务直接显示职务，不再并列“产权业主”；内部“户主/首位认证者”仅用于业务规则，不再作为用户身份文案（用户原话 + Q-ID-01/06 答复）。
- C-35：房屋类型取值沿用清册现有枚举：住宅、公寓、商铺、车位、其他（`registry/models.py:UNIT_TYPE_CHOICES`）。
- C-36：面积来自清册登记值；用户端不自行计算或改写（`registry/models.py:area`）。
- C-37：本期只改用户端展示与 `/me` 返回的身份/房屋信息，不改管理端用户目录的身份口径与列（管理端现状见 `accounts/directory.py:19-31`）。
- C-38：本期 Web 用户端与小程序用户端同时改动，两端信息同源（Q-ID-02 答复）。

## 超出范围

- 管理端“账号/注册用户”页面的身份显示与列调整（除非用户另行提出）。
- 修改首位认证者、产权申诉、同住人审批的业务规则。
- 房屋类型/面积的编辑入口（仍在清册导入与管理端维护）。
- 业委会职务的业务规则调整（是否在“当前身份”并列显示作为开放问题，不改变职务本身）。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| INF-01 | 面积保留两位小数并带“㎡”；缺失显示“未登记” | 现有面积字段为两位小数；用户要求“面积信息” | 用户 |

## 决策记录

| ID | 问题 | 决策 | 回复来源 | 受影响位置 |
|---|---|---|---|---|
| Q-ID-01 | 业委会职务如何显示 | 担任业委会职务或业主代表的，直接显示职务（主任/副主任/委员/业主代表）；职务失效后回落到产权业主/同住人/游客。理由：职务持有者必然已是产权业主 | 用户原话：“业主委员会委员，副主任，主任本来就是业主，如果担任业委会职务，直接显示职务。因为必然是产权业主，业主代表也一样” | REQ-FUNC-136、C-34、US-145 |
| Q-ID-02 | 是否同时改小程序 | Web + 小程序都改，两端同源同口径 | 用户选择 A | REQ-FUNC-141、C-38、US-148 |
| Q-ID-03 | 认证房屋是否含同住人房屋 | 包含，并标注该套关系（产权业主/同住人） | 用户选择 A | REQ-FUNC-139、US-146 |
| Q-ID-04 | 明细展示位置 | 主页“认证房屋”卡片内展开 | 用户选择 A | REQ-FUNC-139、US-146 |
| Q-ID-05 | 多套是否全部展示 | 全部展示并按名称排序 | 用户选择 A | REQ-FUNC-139、REQ-NFUNC-025、US-146 |
| Q-ID-06 | “户主”是否在用户端彻底不出现 | 用户端一律不显示“户主”，首位认证者同样显示“产权业主” | 用户选择 A | C-34、US-145 |

## 开放问题

无遗留开放问题（Q-ID-01 ~ 06 已由用户全部决策，见“决策记录”）。
