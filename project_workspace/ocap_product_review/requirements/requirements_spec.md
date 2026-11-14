<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-13T23:53:56+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_product_review/requirements/product_review.md</file>
    <file>project_workspace/ocap_product_review/phase_status.md</file>
    <file>project_workspace/ocap/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap/requirements/user_stories.md</file>
    <file>project_workspace/ocap_ui_theme/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_registry_import/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_content_publish/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_admin_polish/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_user_directory/requirements/requirements_spec.md</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# 产品评审修正 需求规格（增量）

> 本文只描述系统应当做什么，不含技术选型、类设计、字段名或新接口设计。"基线"列引用的 `文件:行` 来自 product_review.md 的评审（评审基线 HEAD afa1fe8），其中本次亲自复核过的行已核对。
> 来源标记：`[USER 2026-11-13 Qn=X]` = 用户对 product_review.md 第 7 节问题的答复（用户原话"按照推荐"，见 phase_status.md clarifications 最后一条）；`[REVIEW product_review.md §x CORR-NNN]` = 评审结论与用户"按推荐"勾选的修正候选；`[CODE: 文件:行]` = 现有系统。
> 路径缩写：`B/` = `backend/apps/`，`W/` = `frontend/src/`，`M/` = `miniprogram/`。

## CORR → REQ → US 映射表

| CORR | 严重度 | 处理 | REQ | US |
|---|---|---|---|---|
| CORR-001 | CRITICAL | 做（Q3=A Web+小程序都补；Q4=B 小程序补同住人链路） | REQ-FUNC-142、143、144、145 | US-150、151、152、153 |
| CORR-002 | MAJOR | 做（Q2=A） | REQ-FUNC-146 | US-154 |
| CORR-003 | MAJOR | 做 | REQ-FUNC-147 | US-155 |
| CORR-004 | MAJOR | 做 | REQ-FUNC-148 | US-156 |
| CORR-005 | MAJOR | 做 | REQ-FUNC-149 | US-157 |
| CORR-006 | MAJOR | 做 | REQ-FUNC-150 | US-158 |
| CORR-007 | MAJOR | 做 | REQ-FUNC-151 | US-159 |
| CORR-008 | MAJOR | 做 | REQ-FUNC-152 | US-160、161 |
| CORR-009 | MAJOR | 做（Q8=A 补管理页） | REQ-FUNC-153 | US-162 |
| CORR-010 | MAJOR | **不做代码**；Q5=B 转文档修正（Web 通过跳转微信授权页扫码登录） | REQ-NFUNC-027 | US-177 |
| CORR-011 | MINOR | 做 | REQ-FUNC-154 | US-163 |
| CORR-012 | MINOR | 做（Q10=A） | REQ-FUNC-155 | US-164 |
| CORR-013 | MINOR | 做 | REQ-FUNC-156 | US-165 |
| CORR-014 | MINOR | 做（与 CORR-002 一起） | REQ-FUNC-157（报销/备用金部分见 REQ-FUNC-146） | US-166 |
| CORR-015 | MINOR | 做 | REQ-FUNC-158 | US-167 |
| CORR-016 | MINOR | 不做（见"超出范围"） | — | — |
| CORR-017 | MINOR | 只做 Q4=B 范围：同住人链路（见 CORR-001）+ 财务报表明细 | REQ-FUNC-142 ~ 145、159 | US-150 ~ 153、168 |
| CORR-018 | MINOR | 不做 | — | — |
| CORR-019 | MAJOR | 做（Q9=A user_directory 整体重新编号） | REQ-NFUNC-026 | US-176 |
| CORR-020 | MINOR | 做（文档注记） | REQ-NFUNC-027 | US-177 |
| CORR-021 | MINOR | 做（文档修正） | REQ-NFUNC-027 | US-177 |
| CORR-022 | MINOR | 做（Q1=C、Q6=A、Q7=A） | REQ-FUNC-161、162、163、164、165 | US-170、171、172、173、174 |
| CORR-023 | MINOR | 做（仅写验收口径，测试修改由后续测试阶段完成） | REQ-FUNC-166 | US-175 |
| CORR-024、025 | MINOR | 不做 | — | — |
| CORR-026 | MINOR | 做 | REQ-FUNC-160 | US-169 |
| CORR-027、028 | MINOR | 不做 | — | — |
| —（零回归） | — | 画像 P5 baseline 判定要求 | REQ-NFUNC-028 | US-178 |

## 执行摘要

- 业务背景：用户原话 `"全面评审需求，用户故事，代码实现，三者是否一致。补充端到端测试用例并且在测试环境上测试。以用户的角度思考产品设计是否合理、易用。并且做出设计修正，并再次迭代开发"`（phase_status.md request，2026-11-13）。评审结论见 product_review.md（1.0.0）；用户勾选修正候选时的原话为 `"按照推荐"`（2026-11-13，phase_status.md clarifications 最后一条）。本批把被勾选的修正候选落成可验收的需求与用户故事。
- 数量：功能需求 25 条（REQ-FUNC-142 ~ 166）/ 非功能需求 3 条（REQ-NFUNC-026 ~ 028）；约束 C-40 ~ C-45。
- `[INFERRED]`：0 条，0 ÷ (25 + 3) = 0/28 = 0.0%，不超过画像 `inferred_max` 20%。需要确认的细节（非推断）见"开放问题"。
- 优先级规则（一次说明）：CRITICAL / MAJOR 的 CORR（001 ~ 009、019）对应的需求为 Must Have；MINOR 的 CORR（011 ~ 015、017 部分、020 ~ 023、026）对应的需求为 Should Have；REQ-NFUNC-028（零回归）依画像 P5 baseline 判定定为 Must Have。按此规则：Must Have 14 条（功能 12 + 非功能 2），Should Have 14 条（功能 13 + 非功能 1）。
- 编号：先做 CORR-019。扫描全仓 `project_workspace/*/requirements`（不含 product_review.md 自身），实际最大编号为 REQ-FUNC-135、REQ-NFUNC-23（admin_polish）、US-144、C-34、AC-144-xx；ocap_user_directory 整体重新编号为 REQ-FUNC-136 ~ 141、REQ-NFUNC-024 ~ 025、US-145 ~ 149、C-35 ~ C-39、AC-145-xx ~ 149-xx（新旧对照表见该批两个文档开头）。本批编号接续其后：REQ-FUNC 自 142、REQ-NFUNC 自 026、US 自 150、C 自 C-40。
- 用户已答复 Q1 ~ Q10（2026-11-13，全部"按推荐"）：Q1=C 报销/备用金/收入金额上限改为管理员在配置页设置，默认 100 万元；Q2=A 报销/备用金仅现任业委会成员可发起；Q3=A 同住人链路 Web + 小程序都补；Q4=B 小程序只补同住人与报表明细；Q5=B 微信登录保持跳转链接、改需求文字；Q6=A 半数分母取在任人数；Q7=A 题数 ≤ 50、选项 2 ~ 10、窗口 ≥ 60 分钟、收入导入 ≤ 5000 行写进需求；Q8=A 补自定义版式模板管理页；Q9=A user_directory 重新编号；Q10=A 注销自动关闭本人待处理的同住人申请与产权申诉。
- 端到端验证：每个 Must Have 故事至少有 1 条标 `[E2E]` 的验收标准，可经公开入口发 HTTP 请求、使用 `e2e_` 前缀测试账号验证（画像 P4-1）。纯界面行为（弹窗、文案）由前端用例验证，故事中注明。

## 现有系统基线

| 主题 | 现状 | 位置 |
|---|---|---|
| 申请同住人 | Web 要手输"专有部分 ID"；小程序无此功能；产权业主需自己点"查看待我审批"，首页/待办无提示；申请人看不到状态；移除/退出同住人没有入口（后端能力在） | `W/portal/Units.vue:41,207,216`；`W/shared/api.js`（4 个函数无调用）；`B/residency/views.py:169-195,205-281` |
| 报销/备用金发起 | 任何已登录注册用户都能发起；页面对所有人展示"新建申请" | `B/claims/views.py:84,111`（仅 `IsMember`）；`W/portal/Claims.vue:7`；`B/core/permissions.py:28`（`IsCommitteeMember` 对非成员返回 403"需要业委会成员身份"） |
| 小程序会话 | 手机号验证码/密码登录得到 30 分钟闲置会话，仅微信一键登录为 7 天 | `B/accounts/views.py:42-43,112,124,160`；`B/core/config.py:36` |
| 申诉可见性 | 用户端只能提交申诉，看不到状态与驳回原因（驳回原因已存储） | `W/shared/api.js`（`myAppeals` 无调用）；`B/residency/models.py:31-45` |
| 身份展示 | Web 个人中心无身份；"我的房屋"页只有认证表单；多户时只显示取到的第一条房屋身份；管理端目录显示最高身份 | `W/portal/Me.vue`；`W/portal/Units.vue:3-52`；`B/committee/services.py:65-77`；`B/accounts/directory.py:19-47` |
| 破坏性操作 | 撤销认证、撤销席位、删除专有部分、删除审批流程、收入表作废、撤回、注销均无二次确认 | `W/admin/AdminMemberships.vue:49-57`；`AdminSeats.vue:130-138`；`AdminRegistry.vue:253-260`；`AdminFlows.vue:88`；`W/portal/Income.vue:180`；`Claims.vue:303`；`ResolutionDetail.vue:95`；`Me.vue:235` |
| 手输用户 ID | 赋予席位、配置审批人要手输用户数字 ID | `W/admin/AdminSeats.vue:40`；`AdminFlows.vue:36` |
| 列表分页 | 多个列表只取第一页（默认每页 20 条，上限 100）且无翻页、无总数 | `B/core/serializers.py:7`；`W/admin/AdminUsers.vue:71-81`；`AdminMemberships.vue:42`；`AdminAppeals.vue:45`；`AdminFinance.vue:43` |
| 版式模板 | 管理端只能选择已有模板，无新建/改名/编辑/删除入口（后端能力在） | `W/admin/AdminContentEditor.vue:16,181`；`W/shared/api.js`（3 个函数无调用）；`B/content/views_admin.py:112-132` |
| 登录页提示 | 密码框占位符"手机号 / 邮箱 / 账号"，但邮箱 + 密码永远失败 | `W/portal/Login.vue:16`；`B/accounts/services.py:202-203` |
| 注销与待处理项 | 注销结束房屋关系、使席位失效、清空资料，未处理待审同住人申请与待审申诉 | `B/identity/services.py:105-127`；基线 AC-031-05 |
| 个人资料 | 无生日项；更换头像后不显示当前头像；上传前无格式/大小提示 | `W/portal/Me.vue:134,143-144` |
| 菜单与入口 | "待办""报销/备用金"对所有用户展示；非委员点开才报错 | `W/portal/PortalLayout.vue:38,41`；`W/portal/Home.vue:36-46`；`B/approval/views.py:116,131` |
| 内部值显示 | 认证成功提示含角色英文代码；投票列表显示英文状态与原始时间戳；管理端显示 ACTIVE/true | `W/portal/Units.vue:175`；`W/portal/Polls.vue:15`；`W/admin/AdminSeats.vue:22`；`AdminUsers.vue:11,28` |
| 小程序报表 | 只显示总额，无明细（Web 有报表详情） | `M/pages/me/index.vue:31`；`W/portal/Reports.vue:52,61` |
| 信息详情 | 内容下线/不存在时页面空白 | `W/portal/InfoDetail.vue:28-33` |
| 自拟规则（代码有、需求无） | 金额上限 100 万元硬编码（配置项无人读取）；题数 ≤ 50（配置）；选项 2 ~ 10；表决窗口 ≥ 60 分钟（配置）；收入批量导入 ≤ 5000 行；逐条录入一次 ≤ 500 条；任期开始日不得早于今天；报销发生日期不得晚于今日；备用金预计核销日期须晚于今日；核销一次最多关联 50 张报销单；半数分母默认取在任人数（配置）；同一专有部分已有待审申诉、同一人已有待审同住人申请时拒绝重复提交 | `B/claims/views.py:24,50-51,96,124,151`；`B/income/views.py:28,48,80,219`；`B/core/config.py:37-40`；`B/polls/views.py:51,97-98,109`；`B/resolutions/views.py:219`；`B/committee/views.py:67`；`B/committee/services.py:80-87`；`B/residency/views.py:79,186` |
| 导入模板 | 示例行为 6 行（含 `1栋负1层924号`、`10栋1层1号`）；既有用例 TC-INT-311 仍按旧 4 行断言，当前基线唯一失败 | `B/registry/import_spec.py:42-49`；`B/registry/import_template.py:24-58`；`backend/tests/integration/test_registry_import_xlsx_defects.py:118`；画像 P4 已知既有失败 |
| 文档编号 | user_directory 与 admin_polish 的 REQ/US/AC/C 编号整段重复；ui_theme 与 registry_import 的 C-21 ~ C-24 重复，registry_import 与 content_publish 的 C-25/26 重复 | product_review.md §2.3 D-1 |

## 功能需求

| ID | 描述（系统应当…） | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|
| REQ-FUNC-142 | 在 Web 用户端与微信小程序，让注册用户申请成为某专有部分的同住人时，用与产权认证相同的"逐级选择楼栋、单元、楼层、户号"方式选择房屋；选择过程中不要求用户知道或手输任何内部编号；选定后的提交结果沿用既有规则（该专有部分暂无产权业主时拒绝并提示先做产权认证；同一人对同一专有部分已有待审申请时拒绝重复提交） | [REVIEW product_review.md §5 CORR-001]；[USER 2026-11-13 Q3=A、Q4=B]；基线 REQ-FUNC-014、032 | Must Have | 变更 | 变更前：Web 手输"专有部分 ID"、小程序无入口 → 变更后：Web 与小程序均逐级选房屋。基线 `W/portal/Units.vue:41,207` |
| REQ-FUNC-143 | 当某专有部分有待审批的同住人申请时，系统应当在该专有部分的产权业主（含户主）打开 Web 用户端或小程序的首页时，以及进入"我的房屋"时，显示"待审批同住人申请"的数量，并可从该提示直接进入审批列表（该提示不依赖"待办"页，因为"待办"只对业委会成员显示，见 REQ-FUNC-157）；审批通过或拒绝后数量随之减少；无待审批申请时不显示该提示。审批规则沿用既有（任一产权业主可审批；已处理的申请再次处理被拒绝） | [REVIEW CORR-001]；[USER Q3=A、Q4=B]；基线 REQ-FUNC-014、US-024 AC-024-01、AC-024-04 | Must Have | 新增 | 变更前：产权业主须自己点"查看待我审批"，无任何提示 → 变更后：首页与"我的房屋"有数量提示。本需求不含短信/微信主动推送（基线"超出范围"），见开放问题 Q-PR-03 |
| REQ-FUNC-144 | 系统应当让申请人在 Web 用户端与小程序的"我的房屋"中查看自己提交的全部同住人申请：房屋（显示专有部分名称）、提交时间、状态（待审批 / 已通过 / 已拒绝）、处理时间；已拒绝的申请可再次提交新申请 | [REVIEW CORR-001]；[USER Q3=A、Q4=B]；基线 REQ-FUNC-022、US-029 AC-029-01 | Must Have | 新增 | 变更前：申请人看不到申请状态 → 变更后：可查看 |
| REQ-FUNC-145 | 系统应当在 Web 用户端与小程序提供：（1）专有部分的任一产权业主（含户主）查看该专有部分当前同住人名单并移除某位同住人；（2）同住人主动退出自己所在的专有部分；移除或退出前须二次确认（见 REQ-FUNC-150）；操作后该用户在该专有部分不再是同住人，在其他专有部分的身份不变，若无其他身份回到游客；非该专有部分的产权业主（含管理员）不能移除 | [REVIEW CORR-001]；[USER Q3=A、Q4=B]；基线 REQ-FUNC-022、US-029 AC-029-02 ~ 05 | Must Have | 新增 | 变更前：后端能力在，Web 与小程序均无入口 → 变更后：两端有入口。管理员移除为"已评估未采纳"（Q14=C），不变 |
| REQ-FUNC-146 | 只有现任业委会成员（委员、主任、副主任）才能发起报销申请与备用金申请：非成员（含业主代表、普通产权业主、户主、同住人、游客）直接调用发起时被拒绝（HTTP 403，提示"需要业委会成员身份"），且 Web 用户端与小程序不向非成员显示"报销/备用金"入口与"新建申请"按钮；成员的现有发起、审批、核销行为不变 | [USER 2026-11-13 Q2=A]；[REVIEW CORR-002、CORR-014]；基线 REQ-FUNC-040、US-049 AC-049-05；`B/claims/views.py:84,111`（现仅限已登录用户）、`B/core/permissions.py:46-55` | Must Have | 变更 | 变更前：任何已登录用户可创建；页面对所有人展示入口 → 变更后：仅现任业委会成员。落实基线 AC-049-05 的原意 |
| REQ-FUNC-147 | 无论用户在微信小程序用何种方式登录（微信一键登录、手机号验证码登录、账号/手机号 + 密码登录），登录会话都应当保持 7 天：7 天内再次打开仍处于登录状态，满 7 天后要求重新登录；Web 用户端与管理后台的会话规则不变 | [REVIEW CORR-003]；基线 REQ-FUNC-064(2)、US-069 AC-069-04；`B/accounts/views.py:42-43,112,124,160` | Must Have | 变更 | 变更前：小程序手机号验证码/密码登录只有 30 分钟闲置会话 → 变更后：均为 7 天 |
| REQ-FUNC-148 | 系统应当在 Web 用户端与小程序的"我的房屋"中，让用户查看自己提交的全部产权申诉：房屋（专有部分名称）、提交时间、状态（待审核 / 已通过 / 已驳回）、处理时间；已驳回的显示驳回原因；管理员审核结果变化后，用户刷新即可看到新状态 | [REVIEW CORR-004]；基线 REQ-FUNC-019、US-026 AC-026-01、AC-026-03 | Must Have | 新增 | 变更前：后端能力在，用户端无入口 → 变更后：两端可见 |
| REQ-FUNC-149 | 系统应当在 Web 用户端个人中心、"我的房屋"以及小程序"我的"页，列出该用户已认证的每一套房屋及其在该房屋的身份（户主 / 产权业主 / 同住人），并给出一个汇总身份：取值优先级为业委会职务（主任 > 副主任 > 委员 > 业主代表）> 户主 > 产权业主 > 同住人 > 游客，同一用户只给出一个汇总身份，与管理端注册用户目录（REQ-FUNC-136）口径一致；用户没有任何认证房屋时显示"游客"与"暂无已认证房屋"；身份只读 | [REVIEW CORR-005]；基线 REQ-FUNC-036、US-041 AC-041-01/02；REQ-FUNC-136（user_directory，重新编号后）；`B/committee/services.py:65-77`、`B/accounts/directory.py:19-47` | Must Have | 变更 | 变更前：个人中心无身份，多户时只显示取到的第一条房屋身份（顺序不定） → 变更后：逐房屋列出 + 汇总取最高。基线 AC-041-02"分别显示各专有部分身份"得以落实 |
| REQ-FUNC-150 | 系统应当在以下不可逆或影响面大的操作执行前，弹出"将产生的后果 + 确认 / 取消"的确认步骤，取消则不执行任何变更：管理端的撤销产权认证、撤销业委会席位、删除专有部分、删除审批流程；用户端的收入表作废、决议/报销/收入表撤回、移除同住人、退出同住人、账号注销。账号注销前的确认须列出后果：户主身份将由他人接任、业委会席位失效、待处理的申请与申诉被关闭、账号不可恢复 | [REVIEW CORR-006]；`W/admin/AdminMemberships.vue:49-57`、`AdminSeats.vue:130-138`、`AdminRegistry.vue:253-260`、`AdminFlows.vue:88`、`W/portal/Income.vue:180`、`Claims.vue:303`、`ResolutionDetail.vue:95`、`Me.vue:235`；基线 REQ-FUNC-017、034、052 | Must Have | 新增 | 仅 Web；小程序本批无注销与收入表（Q4=B），小程序的移除/退出同住人同样遵守本条 |
| REQ-FUNC-151 | 管理端赋予业委会席位、配置审批流程的审批人时，系统应当让管理员按姓名（清册实名）、手机号后四位或账号搜索并选择注册用户，不再手输用户数字 ID；候选项显示昵称、清册实名（有则显示）、账号、脱敏手机号与当前最高身份，选中后再次显示所选用户信息供确认；搜索结果超过一页时可翻页；选中不符合既有规则的用户（如席位须为产权业主、审批人须为现任业委会成员）时，沿用既有拒绝与错误信息 | [REVIEW CORR-007]；基线 REQ-FUNC-035、042、054；REQ-FUNC-136、141（user_directory）；`W/admin/AdminSeats.vue:40`、`AdminFlows.vue:36` | Must Have | 变更 | 变更前：手输用户 ID（审批人为逗号分隔的 ID） → 变更后：搜索并选择。手机号仍按 REQ-NFUNC-002 脱敏 |
| REQ-FUNC-152 | 系统应当让以下列表支持翻页并显示总条数：管理端的账号、房屋关系、申诉、业委会席位、审批流程、财务；用户端（Web 与小程序）的决议、投票/调查、报销/备用金、收入表、财务报表、待办。每页默认 20 条（沿用现状）；总条数大于每页条数时可到达每一页的全部记录；翻页或加载更多后，列表筛选条件与搜索关键词保持不变 | [REVIEW CORR-008]；`B/core/serializers.py:7`（现默认每页 20、上限 100，无翻页入口）；`W/admin/AdminUsers.vue:71-81`、`AdminMemberships.vue:42`、`AdminAppeals.vue:45`、`AdminFinance.vue:43` | Must Have | 变更 | 变更前：只显示前 20 条 → 变更后：可浏览全部。Web 用翻页控件，小程序用"加载更多"，见开放问题 Q-PR-08 |
| REQ-FUNC-153 | 管理端应当提供"我的版式模板"管理页：管理员可新建自定义版式模板（填写名称与样式）、改名、编辑样式、删除；保存后该模板出现在内容编辑器的模板选择列表中，选用后预览与自定义时一致；名称不能为空；内置模板不可修改、不可删除；已被内容引用的自定义模板禁止删除，并提示被引用的内容数量 | [USER 2026-11-13 Q8=A]；[REVIEW CORR-009]；基线 REQ-FUNC-104、US-112 AC-112-02、AC-112-04；`W/admin/AdminContentEditor.vue:16,181`、`B/content/views_admin.py:112-132` | Must Have | 新增 | 变更前：后端能力在，管理端无入口 → 变更后：有管理页。"内置模板不可改删""被引用时禁止删除"为管理页的边界处理（沿用素材库"引用中禁止删除"的已确认做法 Q-CP-14），见开放问题 Q-PR-07 |
| REQ-FUNC-154 | Web 用户端登录页的密码登录输入提示应当写为"账号或手机号"，不再出现"邮箱"；邮箱不能用密码登录的既有规则不变 | [REVIEW CORR-011]；基线 REQ-FUNC-007、US-007 AC-007-02；`W/portal/Login.vue:16` | Should Have | 变更 | 变更前：提示"手机号 / 邮箱 / 账号" → 变更后："账号或手机号" |
| REQ-FUNC-155 | 账号注销时，系统应当自动关闭该用户本人提交的、仍待处理的同住人申请与产权申诉：关闭后它们不再出现在产权业主的审批列表和管理员的申诉审核列表中，也不能再被通过；关闭动作写入审计日志；注销本身不受这些待处理项阻碍 | [USER 2026-11-13 Q10=A]；[REVIEW CORR-012]；基线 REQ-FUNC-017、US-031 AC-031-05；`B/identity/services.py:105-127` | Should Have | 变更 | 变更前：待处理项残留在队列 → 变更后：随注销一并关闭。已处理的历史记录不变 |
| REQ-FUNC-156 | Web 用户端个人中心的资料卡应当：显示并允许修改生日；更换头像后显示当前头像；选择头像文件时提前提示"jpg/png，不超过 2 MB"，并限定可选文件类型 | [REVIEW CORR-013]；基线 REQ-FUNC-016、C-18（头像 jpg/png、≤ 2 MB）；`W/portal/Me.vue:134,143-144` | Should Have | 新增 | 小程序不在本条范围（评审标注"小程序另议"，Q4=B 未涉及资料项） |
| REQ-FUNC-157 | 系统应当只向有权限的用户展示入口：Web 用户端的导航与首页快捷入口、小程序入口，"待办"只对现任业委会成员显示；非成员看不到"待办"，也不会因点击而得到错误提示；报销/备用金入口见 REQ-FUNC-146；其余入口按既有权限规则显示；入口显示与接口权限一致 | [REVIEW CORR-014]；`W/portal/PortalLayout.vue:38,41`、`W/portal/Home.vue:36-46`、`B/approval/views.py:131`（待办仅成员可访问） | Should Have | 变更 | 变更前：所有用户可见"待办" → 变更后：仅成员。非成员的产权业主进入同住人审批的入口按 REQ-FUNC-143 显示（首页与"我的房屋"），不经"待办" |
| REQ-FUNC-158 | Web 用户端与管理端不得向用户展示内部值：角色、状态一律显示中文名称（如"户主""产权业主""进行中""已结束""启用""停用"），布尔值显示"是 / 否"，时间统一显示为"年-月-日 时:分"（Asia/Shanghai）；产权认证成功提示显示中文身份名称而不是英文代码 | [REVIEW CORR-015]；`W/portal/Units.vue:175`、`W/portal/Polls.vue:15`、`W/admin/AdminSeats.vue:22`、`AdminUsers.vue:11,28`；格式沿用 REQ-FUNC-139（user_directory，登录时间格式） | Should Have | 变更 | 变更前：显示 HEAD/OWNER、OPEN/CLOSED、true、原始时间戳 → 变更后：中文与统一格式 |
| REQ-FUNC-159 | 微信小程序的"财务报表"应当提供与 Web 用户端报表详情同口径的明细：点击某期报表可查看该期的收入与支出明细及合计；报表仍只对已登录注册用户可见，明细字段与可见范围不超出 Web 报表详情 | [USER 2026-11-13 Q4=B]；[REVIEW CORR-017]；基线 REQ-FUNC-051、US-063；`M/pages/me/index.vue:31`、`W/portal/Reports.vue:52,61` | Should Have | 新增 | 变更前：小程序只显示总额 → 变更后：可看明细。设密码、注销、收入表不在小程序补（Q4=B） |
| REQ-FUNC-160 | Web 用户端信息公开详情页打开已下线、已删除或不存在的内容时，应当显示"内容不存在或已下线"并提供返回列表的链接，不得空白 | [REVIEW CORR-026]；基线 REQ-FUNC-100；`W/portal/InfoDetail.vue:28-33` | Should Have | 变更 | 变更前：页面空白 → 变更后：错误态 |
| REQ-FUNC-161 | 报销、备用金与收入表的单笔金额上限应当由管理员在管理后台的配置页面设置：默认值为 1,000,000.00 元（沿用现状）；修改后对此后的新提交立即生效，已提交的记录不受影响；金额超过当前上限时提交被拒绝并提示当前上限；配置变更写入审计日志。报销/备用金与收入表可共用同一个上限 | [USER 2026-11-13 Q1=C]（默认值沿用 100 万元，phase_status.md）；[REVIEW CORR-022、§2.2 U-2]；`B/claims/views.py:24,50-51`、`B/income/views.py:28,48`（硬编码；`B/core/config.py:37` 的配置项现无人读取） | Should Have | 变更 | 变更前：硬编码 100 万，与基线 C-14"不自拟数值"相抵 → 变更后：管理员可设，默认 100 万。是否分设两个上限、取值校验见 Q-PR-01 |
| REQ-FUNC-162 | 采用"半数同意通过"方式的业委会决议，判定通过所用的分母应当是表决截止时的现任（在任）业委会成员人数，同意数须严格超过分母的一半，弃权不计为同意；发起人不回避的既有规则不变 | [USER 2026-11-13 Q6=A]；[REVIEW §2.2 U-6、CORR-022]；基线 REQ-FUNC-038、060、C-13；`B/core/config.py:40`、`B/committee/services.py:80-87`、`B/resolutions/services.py:76` | Should Have | 变更 | 变更前：基线 Q99（分母取在任人数还是人数上限之和）未答复 → 变更后：取在任人数，Q99 关闭。基线"9 人、至少 5 票"仅在 9 个席位全部在任时成立 |
| REQ-FUNC-163 | 发起投票/调查时，系统应当执行并在发起界面提示以下限制：一份投票/调查最多 50 道题；单选题与多选题的选项数为 2 ~ 10 个；表决窗口（发起到截止）不得少于 60 分钟，该最短窗口同样适用于"半数同意通过"决议的表决截止时间；违反时提交失败并提示具体限制 | [USER 2026-11-13 Q7=A]；[REVIEW CORR-022、§2.2 U-3、UX-20]；`B/polls/views.py:51,97-98,109`、`B/resolutions/views.py:219`、`B/core/config.py:38-39` | Should Have | 新增 | 变更前：基线 C-14 称"题数上限待补"，AC-055-04 未决 → 变更后：50 / 2 ~ 10 / 60 分钟。发起界面须事先显示这三项限制（原先只在失败后才知道） |
| REQ-FUNC-164 | 收入表批量导入的文件数据行（不含表头）上限为 5000 行，超出时整份文件被拒绝并提示"文件行数超过 5000"；逐条录入一次提交最多 500 条记录，超出被拒绝并提示"records 须为 1~500 条"一类的具体上限 | [USER 2026-11-13 Q7=A]（5000 行）；[REVIEW CORR-022、§2.2 U-1]；`B/income/views.py:80,219`（500 条为现状，Q7 未单独提及，见 Q-PR-02） | Should Have | 新增 | 变更前：基线 C-14 称导入细节待补 → 变更后：5000 行写入需求 |
| REQ-FUNC-165 | 以下现行校验规则应当写入需求并保持不变：（1）赋予业委会席位时，任期开始日不得早于今天；（2）报销的发生日期不得晚于今日；（3）备用金的预计核销日期须晚于今日；（4）备用金一次核销最多关联 50 张报销单；（5）同一专有部分已有待审申诉时，同一用户不得对其重复提交申诉；同一用户对同一专有部分已有待审同住人申请时，不得重复提交 | [REVIEW CORR-022、§2.2 U-4、U-5、U-7]；`B/committee/views.py:67`、`B/claims/views.py:96,124,151`、`B/residency/views.py:79,186` | Should Have | 新增 | 以代码现状为准，Q7 的答复未逐项涵盖这些规则，见 Q-PR-02 |
| REQ-FUNC-166 | 管理端下载的清册导入模板，其示例行应当为 6 行，包含 4 个专有部分（`1栋1单元3层301号`、`车库A-088`、`1栋负1层924号`、`10栋1层1号`）：把该模板原样预检与导入时，总行数为 6、失败行数为 0、新增专有部分数为 4 | [REVIEW CORR-023、§6]；基线 REQ-FUNC-129、US-138 AC-138-02/03；`B/registry/import_spec.py:42-49`、`B/registry/import_template.py:24-58` | Should Have | 变更 | 变更前：registry_import AC-093-01 未规定示例行数，测试 TC-INT-311 按旧 4 行断言 → 变更后：验收口径为 6 行 / 4 个专有部分；仅为验收口径澄清，测试修改由后续测试阶段完成 |

## 非功能需求

| ID | 描述（系统应当…） | 度量指标 | 来源 | 优先级 | 增量类型 | 备注 |
|---|---|---|---|---|---|---|
| REQ-NFUNC-026 | 需求文档集的编号应当全局唯一、可追溯：ocap_user_directory 整体重新编号，且两个文档开头给出"新旧编号对照表"；其余批次重复的约束编号（ui_theme 与 registry_import 的 C-21 ~ C-24；registry_import 与 content_publish 的 C-25/26）加批次前缀注记，不改原编号 | 扫描全仓各批 `requirements/` 的 REQ-FUNC / REQ-NFUNC / US / AC 定义：重复定义数 = 0；user_directory 新旧编号对照表覆盖其全部 6 条功能需求、2 条非功能需求、5 个用户故事、5 条约束；有批次前缀注记的重复约束组 = 2（C-21 ~ C-24 一组、C-25/26 一组；user_directory 与 admin_polish、content_publish 的重复已由重新编号消除） | [REVIEW CORR-019、§2.3 D-1]；[USER 2026-11-13 Q9=A] | Must Have | 新增 | 实际起点以全仓扫描为准（执行摘要）。引用旧编号的测试用例（如 TC 中的 AC-135-01）由后续阶段按对照表更新 |
| REQ-NFUNC-027 | 前批文档中被后批替代或与代码事实不符的条目，应当有"已被 xxx 替代 / 已修正"的注记，原文保留不删：（1）ui_theme REQ-FUNC-076、US-082、C-23 被 admin_polish REQ-FUNC-135 替代；（2）registry_import AC-098-01/05/06 的旧标识示例被 admin_polish REQ-FUNC-123 替代；（3）ocap US-019 AC-019-08 的 5 列规则被 registry_import 的 8 列规则替代；（4）ocap US-004 AC-004-01/02 的"昵称取用微信昵称"被 REQ-FUNC-065 / US-070 替代；（5）ocap REQ-FUNC-008 / US-008 的"微信登录组件承载快速登录"改为"Web 端通过跳转微信授权页扫码登录，页面不内嵌二维码，快速登录提示是否出现取决于微信授权页"（Q5=B）；（6）user_directory REQ-FUNC-127（重新编号后为 REQ-FUNC-140）改为"账号、手机号、昵称搜索行为保持不变，另增实名搜索"；（7）ocap C-14、AC-049-06、AC-055-04 注明金额上限、题数上限已由本批 REQ-FUNC-161、163 落实 | 上述 7 类条目各有 1 行注记，注记中写明替代者编号；被替代条目的原文保留（原文行数不减少）；各被改文档版本 MINOR + 1、状态 DRAFT，文末有修订记录（日期、CORR 编号、改了什么） | [REVIEW CORR-020、CORR-021、CORR-010、§2.3 D-2 ~ D-5]；[USER 2026-11-13 Q5=B] | Should Have | 新增 | CORR-010 的代码改动不做（Q5=B）。注记内容不改变被注记条目其他部分的含义 |
| REQ-NFUNC-028 | 零回归与前后端一致：除本批列出的变更外，现有业务功能与权限行为不变；后端、前端、小程序现有自动化测试相对改动前基线零新增失败（基线含既有失败 TC-INT-311，待 REQ-FUNC-166 的口径落地后随测试更新，不算新增）；前后端契约（前端调用的路径、方法、字段）与后端一致 | 后端 561 条中除已知 TC-INT-311 外零新增失败；前端 vitest 181、小程序 75 零新增失败；契约测试中无法对应到后端路由的调用 = 0（含本批新增入口）；新写用例全部通过 | 画像 P4、P5（`gate_mode: baseline`）；基线 REQ-NFUNC-009；画像 P4 已知既有失败（2026-11-13 实测，HEAD afa1fe8） | Must Have | 继承 | 继承 ui_theme / admin_polish 的零回归口径 |

## 约束

- C-40：本批只落实用户 2026-11-13 勾选的修正候选；未勾选项（见"超出范围"）不做。来源：[USER 2026-11-13 "按照推荐"]；phase_status.md clarifications。
- C-41：除本批列出的变更外，现有规则含义不变；对前批文档的改动仅限 REQ-NFUNC-026、027 所列的编号、注记与文字修正，只写 requirements 目录。来源：special_instructions 的 REWORK_AUTHORIZED 范围。
- C-42：个人信息保护沿用既有规则：手机号脱敏为"138****0000"（REQ-NFUNC-002）；同住人申请与产权申诉的明细只对该专有部分的产权业主（含户主）、申请人本人和管理员（申诉）可见；用户搜索结果只对管理员开放。来源：基线 REQ-NFUNC-002、REQ-NFUNC-019（user_directory，重新编号后为 REQ-NFUNC-024）。
- C-43：测试只经替身，不调用真实微信、短信、邮件服务；部署后的 HTTP 端到端测试只经公开入口、只用 `e2e_` 前缀测试账号，不得修改或删除已导入的业主清册及非 `e2e_` 账号的数据。来源：画像 P4、P4-1、P8。
- C-44：小程序本批只补同住人链路与财务报表明细，设密码、注销、收入表不补。来源：[USER 2026-11-13 Q4=B]。
- C-45：本批先出需求与用户故事，经用户确认后才进入设计、开发、测试；测试环境部署须用户确认。来源：画像 P7、P9；沿用前批做法。

## 超出范围

以下均为用户未勾选或明确排除，不占 REQ-FUNC 编号，不写用户故事与 AC：

- CORR-010 的代码改动（Web 页内微信二维码）：用户答复 Q5=B，保持跳转链接，仅改需求文字（见 REQ-NFUNC-027）。
- CORR-016 申诉上传支持 5 份文件与 pdf、CORR-018 内容中心参数页改为中文表单、CORR-024 窄屏底部标签栏调整、CORR-025 未注册手机号登录引导、CORR-027 管理端顶栏分组、CORR-028 术语统一：用户未勾选（"按照推荐"，评审推荐为"可选"）。
- CORR-017 中小程序设密码、注销、收入表：用户答复 Q4=B 不补。
- 同住人申请的短信 / 微信主动推送：基线"超出范围"已排除，本批只做站内数量提示。
- 管理员代为移除同住人、管理员代审批同住人：基线已评估未采纳（Q14=C、Q5=C）。
- 修改前批已批准条目的业务含义（只加注记与文字修正）。

## 待确认推断项

无。本批 [INFERRED] = 0 条（0 / 28 = 0.0%）。非推断但需用户确认的细节见"开放问题"。

## 开放问题

均为非阻断；正文已按推荐项写入，用户答复后只需定向修订。

| 编号 | 问题 | 选项 | 推荐 | 关联 |
|---|---|---|---|---|
| Q-PR-01 | 金额上限的配置细节（Q1=C 的补充）：报销/备用金与收入表是共用一个上限还是分设；配置值须为正数且保留两位小数；是否允许管理员清空表示"不设上限" | A 共用一个上限，必须为正数，不允许清空；B 分设两个上限，必须为正数；C 允许清空（不设上限） | A（用户只说"可配置、默认 100 万"，最小改动；基线 C-14 曾要求"不假定不设上限"） | REQ-FUNC-161 |
| Q-PR-02 | Q7 的答复只涉及题数、选项、窗口、5000 行。评审 U-1 ~ U-7 中还有：逐条录入一次 ≤ 500 条、任期开始日不得早于今天、报销发生日期不得晚于今日、备用金核销日期须晚于今日、核销最多关联 50 张、重复申请限制。是否按现状写入需求 | A 按代码现状写入（本稿已按此写，优先级 Should Have）；B 逐项指定新规则；C 去掉限制 | A | REQ-FUNC-164、165 |
| Q-PR-03 | 同住人申请到达产权业主的提醒形式 | A 仅站内数量提示（首页与待办，本稿采用）；B 另加微信/短信主动推送（基线"超出范围"项，需另行评审） | A | REQ-FUNC-143 |
| Q-PR-04 | 注销自动关闭的申请/申诉，其状态名称与对他人的可见性 | A 状态记为"已关闭（申请人已注销）"，不再出现在待处理队列，历史列表中可见；B 直接从列表消失 | A（保留可追溯） | REQ-FUNC-155 |
| Q-PR-05 | 端到端测试夹具：画像 P4-1 禁止修改清册，但验证同住人、申诉、身份展示等故事需要"某专有部分已有产权业主"。夹具如何取得 | A 复用测试环境已存在、已有产权业主的专有部分，`e2e_` 账号作为申请人，经管理员（`e2e_` 管理员账号）审核申诉获得认证，测完由 E2 清理；B 在 `e2e_` 前缀的专有部分上造数据（需放宽 P4-1）；C 这些故事只在本地端到端验证 | A（不触碰清册，符合 P4-1；是否能获得可用的"已有产权业主"专有部分由测试阶段核验） | 测试阶段；US-150 ~ 153、156、157 |
| Q-PR-06 | 小程序报表明细的展示范围 | A 与 Web 报表详情完全同口径（本稿采用）；B 只显示分类合计 | A | REQ-FUNC-159 |
| Q-PR-07 | 自定义版式模板管理页的边界：可编辑的样式项（沿用内容编辑器现有项）；内置模板是否只读；被内容引用的自定义模板被删除时如何处理 | A 内置只读，自定义被引用时删除前提示影响且已发布内容保持原样；B 内置只读，被引用时禁止删除（沿用素材库"引用中禁止删除"的做法，本稿采用） | B（与素材库已确认规则 Q-CP-14 一致）；若选 A，REQ-FUNC-153 末句随之改 | REQ-FUNC-153 |
| Q-PR-08 | 小程序列表的"翻页"形式 | A 加载更多并显示总数（本稿采用）；B 与 Web 相同的页码控件 | A | REQ-FUNC-152 |
| Q-PR-09 | 用户选择器（REQ-FUNC-151）按"姓名"搜索实名时，是否把实名显示在候选项中 | A 候选项显示昵称、账号、脱敏手机号、最高身份，不显示实名（实名仍可作为搜索条件）；B 同时显示实名（本稿采用） | B（管理员需要靠实名区分重名用户；user_directory 已决定实名对管理员完整可见，REQ-NFUNC-024 / 原 Q-UD-07=A） | REQ-FUNC-151 |
