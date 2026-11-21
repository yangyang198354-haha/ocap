<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-21T11:38:05+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/phase_status.md</file>
    <file>frontend/src/portal/UserProfile.vue</file>
    <file>miniprogram/pages/me/index.vue</file>
    <file>miniprogram/pages/profile-setup/index.vue</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格：个人主页信息层级与实名认证徽章

## 执行摘要

用户要求：“个人主页应该先显示昵称或者实名，然后才是身份标记。 如果是实名。可以追加一个实名认证徽章， 身份的颜色和字体可以和实名不一样。 web 端和小程序都应该做这样的改动”。

功能需求 5 条 / 非功能需求 0 条；`[INFERRED]` 0 条（原 1 条经用户 2026-11-21 确认后转为确定需求，0 ÷ 5 = 0%）。优先级规则：用户明确提到的为主路径 Must Have，本次 5 条全部 Must Have。

## 现有系统基线

| 位置 | 现状 |
|---|---|
| `frontend/src/portal/UserProfile.vue:8-16` | 头像后依次是：昵称 `h3` → 身份 `el-tag`（`profile.identity.label`）→ “实名：{real_name}”文本；实名排在身份之后，且无认证徽章 |
| `frontend/src/portal/UserProfile.vue:10-14` | 主标题固定为昵称，未给实名单独的主信息位 |
| `backend/apps/identity/services.py:99-104` | 公开 profile 的 `real_name` 仅在 `real_name_visible` 为真且存在有效产权实名时返回，白名单不变 |
| `backend/apps/accounts/views.py:280-287` | `/me/profile` 返回 `real_name`、`real_name_visible`、`can_show_real_name`，可供本人侧展示 |
| `miniprogram/pages/me/index.vue:21-27` | “我的”卡片：标题为昵称，下一行固定文案“身份：{identitySummary.label}”，没有实名与认证徽章 |
| `miniprogram/pages/profile-setup/index.vue:1-14` | 仅编辑头像昵称，不涉及展示层级 |
| 小程序路由/接口检索 | 未发现他人个人主页页面或 `/users/{id}/profile` 调用；小程序当前只有本人“我的”页 |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-264 | 个人主页主信息区按“昵称/实名 → 身份标记”的顺序展示：先显示昵称；实名可见时，实名与昵称处于同一主信息区域，且两者都排在身份标记之前 | 用户原文“先显示昵称或者实名，然后才是身份标记”；`frontend/src/portal/UserProfile.vue:10-14`、`miniprogram/pages/me/index.vue:21-27` | Must Have | 变更（实名排在身份之后 → 实名与昵称在前、身份在后） | — |
| REQ-FUNC-265 | 当实名被展示时，在实名文本旁追加一个实名认证徽章，徽章文案含“实名”字样并与实名文本紧邻；未展示实名时不出现该徽章 | 用户原文“如果是实名。可以追加一个实名认证徽章” | Must Have | 新增 | 具体文案与图标见开放问题 Q3 |
| REQ-FUNC-266 | 身份标记的视觉样式与昵称/实名不同：身份标记与实名文本/认证徽章在文字颜色、字体（字重或字号）上至少各有一项可见差异，且身份标记不套用昵称主标题样式 | 用户原文“身份的颜色和字体可以和实名不一样” | Must Have | 变更 | 具体色值/字号由设计令牌决定 |
| REQ-FUNC-267 | Web 他人个人主页按 REQ-FUNC-264～266 渲染，并保持实名可见性规则：仅当本人开启实名且存在有效实名时展示实名与徽章 | 用户原文“web 端…做这样的改动”；`frontend/src/portal/UserProfile.vue:10-14`、`backend/apps/identity/services.py:99-104` | Must Have | 变更 | — |
| REQ-FUNC-268 | 小程序在现有“我的”页按 REQ-FUNC-264～266 渲染同样层级与徽章；已开启实名的用户在该页能看到实名与认证徽章，未开启或无实名的用户只看到昵称与身份 | 用户原文“小程序都应该做这样的改动”；`miniprogram/pages/me/index.vue:21-27`（用户 2026-11-21 确认：只改现有“我的”页） | Must Have | 变更（“身份：{label}”单行 → 昵称/实名在前、身份徽章在后） | 不新增他人个人主页页面，见“超出范围” |

## 非功能需求

无。

## 约束

| ID | 约束 | 来源 |
|---|---|---|
| C-87 | 实名仅在用户开启（`real_name_visible`）且存在有效实名时展示；不得为此新增公开字段或扩大公开白名单 | `backend/apps/identity/services.py:99-104`、`backend/apps/accounts/views.py:280-287` |
| C-88 | 身份文案沿用现有汇总口径（`identity.label` / `identitySummary.label`），不新增身份枚举或改写身份名称 | `backend/apps/accounts/directory.py:21-34`、`miniprogram/pages/me/index.vue:23` |
| C-89 | Web 与小程序的主信息区调整不得改变头像、签名档、编辑资料入口的现有功能与权限 | `frontend/src/portal/UserProfile.vue:8-22`、`miniprogram/pages/me/index.vue:21-44` |

## 决策记录

| 编号 | 决策值 | 日期 | 来源 | 受影响位置 |
|---|---|---|---|---|
| D-01 | 小程序范围 = 只改现有“我的”页，不新增他人个人主页 | 2026-11-21 | 用户答复（经 PM 转述） | REQ-FUNC-268、I-1、Q1 |
| D-02 | 实名可见时主标题 = 昵称主、实名紧随其后（不替换昵称） | 2026-11-21 | 用户答复（经 PM 转述） | REQ-FUNC-264、REQ-FUNC-268、Q2 |

## 超出范围

- 小程序新增“他人个人主页”页面及其入口（当前小程序没有该页面；如需要应另立需求）。
- 后端接口、字段或数据迁移变更。
- 头像、签名档、编辑资料、身份计算规则的改动。
- 管理端任何页面的展示规则。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| I-1 | 小程序语境下的“个人主页”指现有“我的”页；本次只改该页展示，不新增他人主页 | 小程序无公开 profile 页面/接口调用，用户要求“小程序做这样的改动”且未提出新增页面 | 用户（已确认，2026-11-21） |

## 开放问题

| ID | 问题 | 影响 |
|---|---|---|
| Q1 | 小程序是否需要“他人个人主页”页面（点击他人昵称/头像进入）？当前无此页面，新增属于独立范围 | **结论（2026-11-21）：不需要，本次只改现有“我的”页**；新增他人主页另行立项 |
| Q2 | 实名可见时，主标题采用“昵称为主、实名紧随其后”，还是“实名替换昵称作为主标题”？ | **结论（2026-11-21）：昵称为主，实名紧随其后**；AC 按此断言 |
| Q3 | 认证徽章的具体文案与图标（如“已实名认证”+对勾图标）？ | 影响文案类 AC |
| Q4 | 身份与实名的具体颜色/字号令牌？ | 只影响视觉实现，不影响“存在差异”的验收 |
