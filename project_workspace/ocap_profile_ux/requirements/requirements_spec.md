<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-18T22:52:50+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_batch_1118/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_identity_property/requirements/requirements_spec.md</file>
    <file>frontend/src/portal/me/MeProfile.vue</file>
    <file>frontend/src/portal/PortalUserMenu.vue</file>
    <file>frontend/src/admin/AdminSeats.vue</file>
    <file>frontend/src/admin/AdminFlows.vue</file>
    <file>frontend/src/admin/AdminMemberships.vue</file>
    <file>frontend/src/shared/api.js</file>
    <file>backend/apps/core/attachments.py</file>
    <file>backend/apps/approval/views.py</file>
    <file>backend/apps/committee/views.py</file>
    <file>backend/apps/identity/views.py</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 需求规格说明 — ocap_profile_ux

## 执行摘要

用户提出 7 项体验与功能诉求：个人资料页控件对齐、默认头像与右上角展示、头像上限由 2 MB 放宽到 5 MB、管理端业委会席位/业主代表持有人改为分列表格并支持过滤折叠、审批流程可查看细节并编辑、用户房屋关系支持按楼栋/单元/楼层过滤与按姓名/电话/专有部分搜索、新增可被他人访问的用户 profile 页（含实名显示开关与签名档）。原文见 `phase_status.md` 的 `<request>`。

- 功能需求 9 条（REQ-FUNC-255～263），非功能需求 4 条（REQ-NFUNC-051～054），约束 4 条（C-81～84）。
- `[INFERRED]` 2 条，占比 2 ÷ 13 = 15.4%（上限 20%，符合画像 P5）。
- 优先级默认规则：用户明确提到的功能为 Must Have；由推断补充的度量类非功能项为 Should Have。据此 Must Have 9 条、Should Have 4 条。

## 现有系统基线

| 现状 | 位置 |
|---|---|
| 个人资料页：昵称、性别、生日、保存按钮同处一个 flex 行，未设置垂直居中与控件等高 | `frontend/src/portal/me/MeProfile.vue:6-13` |
| 头像上传前校验 2 MB，文案"不超过 2 MB"；后端 AVATAR 上限 2 MB | `frontend/src/portal/me/MeProfile.vue:20,37,60-62`；`backend/apps/core/attachments.py:25` |
| 右上角用户菜单仅显示昵称文本与下拉箭头，无头像 | `frontend/src/portal/PortalUserMenu.vue:3-16` |
| 业委会席位页已是表格，但"持有人"列把昵称/账号/专有部分/姓名拼在一行；过滤仅支持 position、status；接口不返回手机号 | `frontend/src/admin/AdminSeats.vue:22-53`；`backend/apps/committee/views.py:25-62` |
| 审批流程页仅支持新建、启停、删除，无查看审批人明细与编辑入口；后端已有 `PUT /admin/approval/flows/{id}` 与 `admin.updateFlow` | `frontend/src/admin/AdminFlows.vue:11-58`；`backend/apps/approval/views.py:79-104`；`frontend/src/shared/api.js:184` |
| 用户房屋关系列表仅支持身份过滤与 `q`（账号/昵称/专有部分），无楼栋/单元/楼层过滤，无姓名与电话搜索 | `frontend/src/admin/AdminMemberships.vue:5-25`；`backend/apps/identity/views.py:94-109` |
| 无公开 profile 页；无签名档字段；实名（清册姓名）仅在认证/身份相关内部使用，无用户可控的展示开关 | `backend/apps/accounts/models.py:15-30`；`backend/apps/committee/services.py:65-77` |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-255 | 个人资料页的昵称输入、性别选择、生日选择与保存按钮在同一行内垂直居中，控件高度一致，生日控件不再低于其他控件；空间不足时整行换行且各控件保持同一基线 | 用户原文 1；`MeProfile.vue:6-13` | Must Have | 变更（当前未设垂直对齐） | 纯布局 |
| REQ-FUNC-256 | 未上传头像的用户展示系统内置默认头像；首页/个人中心右上角在昵称旁展示头像，与昵称、下拉箭头同一水平线 | 用户原文 2；`PortalUserMenu.vue:3-16` | Must Have | 新增 | 默认头像资源形态见待确认推断项 I-6 |
| REQ-FUNC-257 | 头像上传上限由 2 MB 调整为 5 MB，前端预校验与后端最终校验一致 | 用户原文 3；`MeProfile.vue:37,60-62`；`attachments.py:25` | Must Have | 变更（2 MB → 5 MB） | 格式仍限 jpg/png |
| REQ-FUNC-258 | 管理端业委会席位/业主代表列表以表格分列展示持有人信息：昵称、姓名、联系电话、专有部分坐落、专有部分类型各自独立成列，并保留现有列（职位、状态、任期开始、任期结束、操作）；支持按楼栋、单元、职位过滤；资格失效/已结束的席位默认折叠，可展开查看 | 用户原文 4；`AdminSeats.vue:22-53`；`committee/views.py:25-62` | Must Have | 变更（一列拼接 → 分列 + 过滤 + 折叠） | 电话展示须遵守 C-82 |
| REQ-FUNC-259 | 审批流程列表可查看单个流程的详情（名称、适用范围、审批方式、启用状态、审批人清单）；管理员可编辑流程的名称、审批方式、审批人与启用状态，保存后立即生效 | 用户原文 5；`AdminFlows.vue:11-58`；`approval/views.py:79-104` | Must Have | 新增（后端 PUT 已存在，缺前端入口） | 适用范围是否可改见 Q6 |
| REQ-FUNC-260 | 管理端用户房屋关系列表支持按专有部分的楼栋、单元、楼层过滤，并支持按姓名、联系电话、专有部分（坐落或编号）搜索，便于查看整体分布与按人/按房定位 | 用户原文 6；`AdminMemberships.vue:5-25`；`identity/views.py:94-109` | Must Have | 变更（仅身份过滤 → 多条件） | 电话搜索口径见 Q4 |
| REQ-FUNC-261 | 系统提供用户 profile 页，展示该用户的昵称、头像、身份与签名档；其他用户可通过点击昵称或头像进入该页 | 用户原文 7 | Must Have | 新增 | 入口范围见 Q2 |
| REQ-FUNC-262 | 已验证身份的产权业主可自行选择是否在 profile 页展示实名；默认不展示，关闭后仅展示昵称 | 用户原文 7 | Must Have | 新增 | 实名取值见 Q3 |
| REQ-FUNC-263 | 用户可编辑自己的签名档，并在自己的与他人看到的 profile 页展示；签名档为空时展示空状态文案 | 用户原文 7 | Must Have | 新增 | 长度见 I-4 |

## 非功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-NFUNC-051 | 头像上传类型仍限 jpg/jpeg/png；超过 5 MB 时前端阻止上传并提示文案含"5 MB"，后端返回 413 与错误码 `FILE_TOO_LARGE` | 用户原文 3；`attachments.py:95`；`test_batch1118_appeal.py:120-124` | Must Have | 变更（阈值 2 MB → 5 MB） | 阈值须两端一致 |
| REQ-NFUNC-052 | profile 页不得展示手机号、邮箱、生日、证件等敏感信息；实名仅在本人开启后展示；管理端列表中的联系电话沿用现行脱敏规则，不因本次改动放开 | 用户原文 7；`committee/views.py:34-40`（手机号脱敏）；协议 §L-2 | Must Have | 新增 | 隐私边界 |
| REQ-NFUNC-053 | 席位列表与房屋关系列表在 5000 条记录规模下，带过滤/搜索的查询响应时间 ≤ 2 秒 [INFERRED] | 推断（用户要求"容易地看到整体信息"） | Should Have | 新增 | 需架构/测试确认口径 |
| REQ-NFUNC-054 | 默认头像为内置资源，单个文件 ≤ 100 KB，不依赖外网 CDN；深浅两种主题下均可见 [INFERRED] | 用户原文 2 + 推断 | Should Have | 新增 | 资源规格待确认 |

## 约束

- C-81：席位表格"现有的列都保留"——职位、状态、任期开始、任期结束、操作列不得删减（用户原文 4）。
- C-82：管理端联系电话沿用现行脱敏展示（当前席位接口返回脱敏手机号），不得因新增电话搜索而全量返回明文号码 [CODE: backend/apps/committee/views.py:34-40]。
- C-83：实名展示必须由产权业主本人显式开启，默认关闭；他人不可代为开启（用户原文 7）。
- C-84：头像格式仍限 jpg/jpeg/png，沿用现有魔数与扩展名校验 [CODE: backend/apps/core/attachments.py:25-35]。

## 超出范围

- 用户未明确排除任何功能；本批次不包含：头像裁剪/滤镜、profile 页关注/私信/动态流、实名认证流程改造、微信小程序端同步（后者见开放问题 Q1，若用户确认纳入再单列需求）。

## 待确认推断项

| ID | 推断内容 | 推断依据 | 需谁确认 |
|---|---|---|---|
| I-1 | [INFERRED] 本轮以 Web 端（frontend/）为主实现；微信小程序端是否同步默认头像、右上角头像与 profile 页未说明 | 用户原文未提平台，历史需求多为双端 | 用户（Q1） |
| I-2 | [INFERRED] 实名展示开关默认关闭，开启后展示清册业主姓名 | 用户原文"自己可以选择是否显示实名"；隐私默认最小披露 | 用户（Q3） |
| I-3 | [INFERRED] "资格失效折叠"按所有非 ACTIVE 状态（REVOKED/EXPIRED/INVALIDATED/REPLACED/MERGED）归入折叠区 | 用户原文"资格失效"；现有状态枚举 `committee/models.py:28-29` | 用户（Q5） |
| I-4 | [INFERRED] 签名档为纯文本，长度上限 100 字，不支持富文本 | 用户原文未给限制；与昵称 64 字量级一致 | 用户 |
| I-5 | [INFERRED] 楼层过滤选项按楼层数值升序排列 | 项目既有约定（楼层选项须数值排序） | 用户 |
| I-6 | [INFERRED] 默认头像采用系统内置图片（非昵称首字母生成） | 用户原文"默认头像"未指定形态 | 用户 |
| I-7 | [INFERRED] 房屋关系列表默认仅显示有效关系（现状 `ended_at` 为空），不新增"已结束关系"展示 | 现状接口已按 `ended_at__isnull=True` 过滤 | 用户 |

## 开放问题

- Q1：默认头像、右上角头像、profile 页是否需要同步到微信小程序端？若需要，profile 页在小程序内的入口位置为何？
- Q2："点击昵称/头像查看 profile"的入口覆盖哪些页面？建议首期覆盖：决议参与人列表、投票人列表、房屋关系列表、本人用户菜单（点击进入自己的 profile）。
- Q3：实名展示取哪个姓名？同一用户多套房产对应不同清册姓名时如何取值与提示？
- Q4：房屋关系"按电话找人"支持完整号码还是后 4 位模糊匹配？管理员是否可见完整号码（与 C-82 的脱敏规则如何协调）？
- Q5："资格失效折叠"是否等同于所有非 ACTIVE 状态？是否需要显示各状态计数？
- Q6：审批流程编辑是否允许修改"适用范围（决议/支出/收入）"与审批方式？已有待审批实例时，编辑是否需要二次确认？
