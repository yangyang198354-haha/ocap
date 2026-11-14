<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-13T23:05:58+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap/requirements/user_stories.md</file>
    <file>project_workspace/ocap_ui_theme/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_ui_theme/requirements/user_stories.md</file>
    <file>project_workspace/ocap_registry_import/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_registry_import/requirements/user_stories.md</file>
    <file>project_workspace/ocap_content_publish/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_content_publish/requirements/user_stories.md</file>
    <file>project_workspace/ocap_admin_polish/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_admin_polish/requirements/user_stories.md</file>
    <file>project_workspace/ocap_user_directory/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_user_directory/requirements/user_stories.md</file>
    <file>project_workspace/ocap_product_review/phase_status.md</file>
  </input_files>
  <phase>PHASE_01</phase>
  <status>APPROVED</status>
</file_header>

# ocap 产品评审：需求 / 用户故事 / 代码三者一致性与用户视角易用性（评审基线 HEAD afa1fe8）

> 本文只做评审，不改任何代码与其他批次文档。所有"修正候选"待用户逐条勾选（用户答复 Q5=A）后，才会另行写正式需求与用户故事。
> 路径缩写：`B/` = `backend/apps/`，`W/` = `frontend/src/`，`M/` = `miniprogram/`。凡写成 `文件:行` 的位置均为本次亲自打开或 grep 命中核对过的行。
> 手机号、姓名等清册内容一律不写入本文。

## 0. 评审方法与核对深度（必读）

| 项 | 说明 |
|---|---|
| 范围 | 6 个已交付批次（ocap、ocap_ui_theme、ocap_registry_import、ocap_content_publish、ocap_admin_polish、ocap_user_directory）共 149 个用户故事，其中 Must Have 133 个 |
| 判断依据 | 以代码为准（先 grep 路由/类名/组件，再读代码），不以设计文档为准 |
| 核对深度（矩阵"深度"列） | **读码** = 打开了与 AC 直接相关的函数体并逐点对照；**定位** = 找到了实现类/页面/路由，并核对了入口可达性与明显的 AC 关键点，**未逐条 AC 对照函数体**。"定位"级的 CONSISTENT 只表示"有实现、有入口、未发现矛盾"，不等于 AC 全部通过，需由后续 E2E 用例逐条验证 |
| 契约抽查 | 写了只读脚本 `/tmp/claude-0/-root-myproject-ocap/0130fd24-0fdc-48ac-9199-c3a574e51a0e/scratchpad/contract.py`（在会话临时目录，不入仓库），解析 `W/shared/api.js`、`M/utils/api.js` 与各 `B/*/urls.py` |
| 未做的事 | 未运行任何测试、未连接测试机或外网；视觉类 AC（对比度、动效、首屏闪烁、三套风格逐页观感）无法凭读码判定，一律只做"定位" |

## 1. 执行摘要

### 1.1 各批次故事数

| 批次 | 故事总数 | Must Have | Should Have | 备注 |
|---|---|---|---|---|
| ocap（批次 1+2+架构回写） | 73（US-001 ~ 073） | 69 | 4（US-032、033、034、064） | 基线 |
| ocap_ui_theme | 18（US-074 ~ 091） | 12 | 6 | |
| ocap_registry_import | 13（US-092 ~ 104） | 11 | 2 | |
| ocap_content_publish | 27（US-105 ~ 131） | 24 | 3 | |
| ocap_admin_polish | 13（US-132 ~ 144） | 12 | 1 | 与 user_directory 编号冲突 |
| ocap_user_directory | 5（US-132 ~ 136） | 5 | 0 | 与 admin_polish 编号冲突 |
| 合计 | 149 | 133 | 16 | |

### 1.2 一致性统计（对象：133 个 Must Have 故事，每个一行，见第 2 节）

| 结论 | 数量 | 说明 |
|---|---|---|
| CONSISTENT | 118 | 其中"读码"41、"定位"77（定位级含义见第 0 节） |
| INCONSISTENT | 7 | US-007、008、024、031、041、049、069 |
| MISSING | 3 | US-026（申诉状态不可见）、US-029（移除/退出同住人无入口）、US-112（自定义版式模板无入口） |
| DOC_CONFLICT | 5 | US-004、019、082、098、UD 的 US-135；另有"文档冲突项"D-1 ~ D-8（第 2.3 节，主要是编号冲突）不占矩阵行 |
| UNDOCUMENTED | 12 项 | 代码有而需求/故事没有的用户可见规则，单列第 2.2 节，不占矩阵行 |

Should/Could 抽查范围：ocap 的 US-032、033、034、064；ui_theme 的 US-085、086；content_publish 的 US-118、122、129；admin_polish 的 US-143；其余 Should 故事未核对（registry_import 的 US-100/101、ui_theme 的 US-087 ~ 090、user_directory 无 Should 故事）。

### 1.3 易用性与修正候选

| 项 | 数量 |
|---|---|
| 易用性问题（第 4 节 UX-01 ~ UX-29） | 29 |
| 修正候选 CORR（第 5 节） | 28：CRITICAL 1 / MAJOR 10 / MINOR 17 |
| 待用户确认的问题（第 7 节） | 10 |
| 契约抽查（第 3 节） | Web 142 处 + 小程序 33 处调用，全部能对应到后端路由与方法，无法对应数 = 0；另有 11 条后端路由无前端调用（其中 7 条为定时任务入口） |

### 1.4 最重要的发现（建议优先处理）

1. **同住人链路在用户端实际不可用**（CORR-001，CRITICAL）：申请同住人要手输"专有部分 ID"，产权业主没有任何"有新申请"的提示，申请人看不到申请状态，移除/退出同住人没有入口。
2. **报销/备用金发起接口对所有注册用户开放**（CORR-002，MAJOR）：与 AC-049-05 相反，且页面也对所有人展示"新建申请"。
3. **小程序用手机号验证码/密码登录后只保持 30 分钟闲置会话**（CORR-003，MAJOR），与"小程序默认保持 7 天"不一致。
4. **用户看不到自己的认证申诉结果、自己的房屋/身份展示不准确**（CORR-004、005）。
5. **管理端：无确认的破坏性操作、手输用户 ID、列表只能看到前 20 条**（CORR-006、007、008）。
6. **文档编号冲突**（CORR-019）：user_directory 与 admin_polish 的 REQ/US/AC/约束编号整段重复。
7. 基线失败 TC-INT-311 是**测试过时**，模板与需求一致（第 6 节，CORR-023）。

## 2. 三者一致性矩阵

### 2.1 Must Have 故事逐个核对（133 行）

列说明：后端位置、Web 前端位置、小程序位置均为 `文件:行`（M 列"—"表示该故事不涉及或端上无此功能；"无入口"表示后端有而前端没有）。

#### 2.1.1 批次 ocap（69 行）

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| ocap | US-001 | FUNC-001 | B/accounts/services.py:68-113,116-160,168-184 | W/portal/Register.vue:36,51 | —（注册仅 Web，符合 REQ） | CONSISTENT / 读码 | 验证码 6 位、间隔/时/日/IP 限流、错 5 次作废、30 分钟累计 10 次锁定、邮箱 UNVERIFIED_REG 均与 AC-001-01 ~ 06 对得上（数值见 B/core/config.py:10-43） |
| ocap | US-002 | FUNC-002 | B/accounts/views.py:164-171,174-208 | W/portal/Login.vue:113-119；WechatCallback.vue:30 | — | CONSISTENT / 定位 | 回调与票据交换存在；二维码展示问题见 US-008 |
| ocap | US-003 | FUNC-003 | B/accounts/services.py:187-216 | — | M/pages/login/index.vue:7,19 | CONSISTENT / 读码 | 统一失败文案在 services.py:213；未注册手机号验证码登录返回 404"该手机号尚未注册"（services.py:191）与 AC-003-05 一致；会话时长问题见 US-069 |
| ocap | US-004 | FUNC-004、065 | B/accounts/views.py:147-161 | — | M/pages.json:4（profile-setup 页） | DOC_CONFLICT / 定位 | AC-004-01/002"昵称取用微信昵称"已被 REQ-FUNC-065/US-070（小程序改为首次登录后设置头像昵称）改写，US-004 未注明；代码按 US-070 实现 |
| ocap | US-005 | FUNC-005 | B/accounts/services.py:196-216 | W/portal/Login.vue:108 | — | CONSISTENT / 读码 | 三种失败同一文案，连续 5 次错误锁定 15 分钟 |
| ocap | US-006 | FUNC-006 | B/accounts/services.py:187,196 | W/portal/Login.vue:107-108 | M/pages/login/index.vue:7 | CONSISTENT / 读码 | |
| ocap | US-007 | FUNC-007 | B/accounts/services.py:219-239（邮箱只验证码，规则同 OQ-11） | W/portal/Login.vue:16（密码框占位符"手机号 / 邮箱 / 账号"） | — | INCONSISTENT / 读码 | AC-007-02：邮箱登录"不提供邮箱 + 密码入口"。后端按账号/手机号查用户（services.py:202-203），邮箱 + 密码必然失败；但页面占位符却写"邮箱"，诱导用户这样输入 |
| ocap | US-008 | FUNC-008 | B/accounts/views.py:170-171（返回 fast_login:1） | W/portal/Login.vue:113-119、32（只拼一个 qrconnect 跳转链接，fast_login 未使用） | — | INCONSISTENT / 读码 | AC-008-01/02：登录页"展示微信登录组件/二维码"。实际只有文字链接"微信扫码登录"，点击整页跳转；未配置 appid 时入口静默消失（Login.vue:119-122）。快速登录是否可达取决于跳转后的微信页面，页面本身没有二维码 |
| ocap | US-009 | FUNC-023 | B/accounts/services.py:46-63,317；views.py:209 | W/portal/Me.vue:204 | — | CONSISTENT / 定位 | |
| ocap | US-010 | FUNC-024 | B/accounts/services.py:163-165 | — | — | CONSISTENT / 读码 | 手机号唯一由注册检查保证 |
| ocap | US-011 | FUNC-025 | B/accounts/views.py:315-345 | W/admin/AdminLogin.vue:30；AdminLayout.vue:79-93 | — | CONSISTENT / 定位 | |
| ocap | US-012 | FUNC-026 | B/identity/services.py:88-103,148-181；identity/views.py:36-50 | W/portal/Me.vue:170-185,184 | M/pages/phone/index.vue:68 | CONSISTENT / 读码 | 合并以手机号原账号为主，写审计 ACCOUNTS_MERGED |
| ocap | US-013 | FUNC-027 | B/accounts/services.py:417-433 | — | — | CONSISTENT / 定位 | 注销置空手机号，可再注册 |
| ocap | US-014 | FUNC-028 | B/identity/services.py:66-86 | W/portal/Me.vue:193 | M/pages/phone/index.vue | CONSISTENT / 读码 | |
| ocap | US-015 | FUNC-029 | B/accounts/services.py:435 | — | — | CONSISTENT / 定位 | |
| ocap | US-016 | FUNC-030、061 | B/residency/apps.py:16（Membership 自定义合并）；committee/services.py:176 | — | — | CONSISTENT / 定位 | |
| ocap | US-017 | FUNC-031 | B/accounts/services.py:219-239,397 | W/portal/Me.vue:214,225 | — | CONSISTENT / 读码 | |
| ocap | US-018 | FUNC-009 | B/registry/models.py:82-104 | — | — | CONSISTENT / 定位 | |
| ocap | US-019 | FUNC-018 | B/registry/views.py:284-321；registry/import_spec.py:42-49 | W/admin/RegistryImportDialog.vue:161 | — | DOC_CONFLICT / 定位 | AC-019-08 写的是 5 列（楼栋…手机号）、缺列拒绝；registry_import 批次已改为 8 列并整体拒绝旧 5 列文件，但 US-019 未注明被替代。代码按 8 列 |
| ocap | US-020 | FUNC-010 | B/registry/views.py:57 | W/portal/Units.vue:82,115-140 | M/pages/units/index.vue（pages.json:5） | CONSISTENT / 读码 | 已含 registry_import 的"跳过空层级" |
| ocap | US-021 | FUNC-011 | B/residency/views.py:29-52；residency/services.py:15-54 | W/portal/Units.vue:174 | M/pages/units/index.vue:155 | CONSISTENT / 读码 | |
| ocap | US-022 | FUNC-012 | B/residency/views.py:55-103,134-166 | W/portal/Units.vue:187-198 | M/pages/units/index.vue:181 | CONSISTENT / 定位 | |
| ocap | US-023 | FUNC-013 | B/residency/services.py:15-54 | — | — | CONSISTENT / 读码 | 先到先得为户主，写 HEAD_ASSIGNED 审计 |
| ocap | US-024 | FUNC-014、032 | B/residency/views.py:169-195（UNIT_HAS_NO_OWNER 在 :181，重复申请在 :186）；:205-250 | W/portal/Units.vue:41（手输"专有部分 ID"）、207、216、225 | 无入口 | INCONSISTENT / 读码 | 后端规则齐全，但 AC-024-01"注册用户选择专有部分 X 并提交申请 / 通知产权业主可见"在 Web 上：①申请人要手输内部数字 ID，而页面其他位置不展示该 ID；②产权业主没有任何提示，必须自己点"查看待我审批"；小程序没有此功能。→ CORR-001 |
| ocap | US-025 | FUNC-015 | B/identity/services.py:17-46 | W/portal/Home.vue:9 | M/pages/me/index.vue:23 | CONSISTENT / 定位 | |
| ocap | US-026 | FUNC-019 | B/residency/views.py:55-103,104-166；core/attachments.py:22-23 | W/portal/Units.vue:187-198（提交）；W/shared/api.js `myAppeals` 无调用 | M/pages/units/index.vue:23-26,181（仅提交） | MISSING / 读码 | 提交与管理员审核均已实现；AC-026-01/03"用户可见申诉状态/驳回结果"无任何入口（`unitApi.myAppeals` 未被任何页面使用）。→ CORR-004 |
| ocap | US-027 | FUNC-020 | B/identity/services.py:105-127；residency/services.py:54-70 | — | — | CONSISTENT / 读码 | |
| ocap | US-028 | FUNC-021 | B/identity/services.py:66-86 | W/portal/Me.vue:193 | M/pages/phone/index.vue | CONSISTENT / 读码 | |
| ocap | US-029 | FUNC-022 | B/residency/views.py:251-281（移除、退出） | W/shared/api.js `removeResident`、`leaveUnit` 无调用 | 无入口 | MISSING / 读码 | AC-029-02/03：产权业主移除同住人、同住人主动退出——后端有接口，Web 与小程序均无按钮。→ CORR-001 |
| ocap | US-031 | FUNC-017 | B/identity/services.py:105-127；accounts/services.py:417-433 | W/portal/Me.vue:235（无二次确认弹窗，靠验证码） | — | INCONSISTENT / 读码 | AC-031-05"待审批的同住人申请或待审核的申诉……一并关闭"：注销代码只结束房屋关系、使席位失效、清空资料（identity/services.py:105-127），未见对 Appeal/ResidentApplication 的 PENDING 状态做任何处理，申请会残留在审批/审核队列。→ CORR-012 |
| ocap | US-035 | FUNC-033 | B/registry/views.py:186（owners 覆盖更新不动 Membership） | W/admin/AdminRegistry.vue:244 | — | CONSISTENT / 定位 | |
| ocap | US-036 | FUNC-034 | B/identity/services.py:129-146；committee/services.py:158 | W/admin/AdminMemberships.vue:49-57 | — | CONSISTENT / 读码 | 功能一致；撤销无二次确认见 CORR-006 |
| ocap | US-037 | FUNC-035 | B/committee/services.py:92-123；committee/views.py:35-71 | W/admin/AdminSeats.vue:40（手输用户 ID）、111 | — | CONSISTENT / 读码 | CAP_NOT_CONFIGURED/TERM_NOT_CONFIGURED：未先配置人数与任期时赋予会报错（services.py:98,103），AC 未提；"任期开始日不得早于今天"见 UNDOCUMENTED U-4 |
| ocap | US-038 | FUNC-052 | B/committee/services.py:125-157；views.py:73-96 | W/admin/AdminSeats.vue:122,132 | — | CONSISTENT / 定位 | |
| ocap | US-039 | FUNC-053 | B/committee/services.py:158-175,206；jobs/management/commands/run_due_jobs.py:26 | — | — | CONSISTENT / 定位 | 到期失效依赖 `run_due_jobs`（deploy/systemd/ocap-run-due-jobs.timer 存在；部署报告记录已启用） |
| ocap | US-040 | FUNC-057 | B/committee/views.py:98-142 | W/admin/AdminSeats.vue:99,144 | — | CONSISTENT / 定位 | |
| ocap | US-041 | FUNC-036 | B/committee/services.py:65-77（身份标签取**第一条**房屋关系后 break，无排序）；identity/services.py:17-46；accounts/directory.py:19-47（管理端按最高身份） | W/portal/Home.vue:9；W/portal/Me.vue（整页无身份展示） | M/pages/me/index.vue:23 | INCONSISTENT / 读码 | AC-041-01"个人信息页显示身份"：Web 个人中心没有身份展示，只有首页英雄区；AC-041-02"多个专有部分有不同身份时分别显示"：只显示一个标签，且取哪条由数据库顺序决定（可能显示"同住人"而此人在另一户是户主），与管理端目录显示的"最高身份"互相矛盾。→ CORR-005 |
| ocap | US-042 | FUNC-056 | B/committee/services.py:92-123（REPRESENTATIVE 同一路径） | W/admin/AdminSeats.vue:111 | — | CONSISTENT / 定位 | |
| ocap | US-043 | FUNC-054、042 | B/approval/views.py:28-71（审批人须现任成员 :41） | W/admin/AdminFlows.vue:36（手输审批人用户 ID）、68-88 | — | CONSISTENT / 读码 | 审批人输入方式见 CORR-007 |
| ocap | US-044 | FUNC-037 | B/resolutions/views.py:46-86,199-233；core/attachments.py:15-17,56-76 | W/portal/Resolutions.vue:113,125,139 | 无（仅查看） | CONSISTENT / 读码 | 附件数量/大小/合计/类型/魔数校验齐全 |
| ocap | US-045 | FUNC-038 | B/approval/services.py:86-118；resolutions/views.py:111-136 | W/portal/Tasks.vue:49；ResolutionDetail.vue:85 | — | CONSISTENT / 读码 | |
| ocap | US-046 | FUNC-038、060 | B/resolutions/services.py:60-96；resolutions/views.py:172-196 | W/portal/ResolutionDetail.vue:85 | M/pages/resolutions/detail.vue（pages.json:7） | CONSISTENT / 读码 | 严格过半 `agree*2 > denominator`（services.py:76）；分母取在任人数（"ACTIVE"，见 UNDOCUMENTED U-6，Q99 用户未答复） |
| ocap | US-047 | FUNC-039 | B/resolutions/views.py:55-66（public = 已通过/未通过）、111-122 | W/portal/Resolutions.vue:104；Home.vue:132 | M/pages/resolutions/index.vue（pages.json:6） | CONSISTENT / 读码 | 已撤回、审批中不公开 |
| ocap | US-048 | FUNC-055 | B/resolutions/views.py:124-170；approval/services.py:58-84；claims/views.py:229-280；income/views.py:321-360 | W/portal/ResolutionDetail.vue:95,118；Claims.vue:303；Income.vue:162,172 | — | CONSISTENT / 读码 | 撤回/作废无确认弹窗见 CORR-006 |
| ocap | US-049 | FUNC-040、042 | B/claims/views.py:83-108（`permission_classes = [IsMember]` :84，:111 同；函数体无业委会成员校验）；approval/views.py:116（流程列表限成员） | W/portal/Claims.vue:7（"新建申请"对所有人可见）、225 | M/pages/claims/index.vue | INCONSISTENT / 读码 | AC-049-05"业主代表、普通产权业主、户主、同住人或游客尝试发起 → 被拒绝"：任何已登录用户只要知道一个有效 flow_id 就能创建报销/备用金；UI 上非成员只会在取流程列表时得到 403 提示。→ CORR-002。另：金额上限 100 万为代码自拟（U-2） |
| ocap | US-050 | FUNC-041、062 | B/approval/services.py:86-118（自审拒绝 :102）；claims/services.py | W/portal/Tasks.vue:49；Claims.vue:216 | M/pages/claims/index.vue | CONSISTENT / 读码 | |
| ocap | US-051 | FUNC-058 | B/claims/views.py:137-181（IsIncomeMember、:157-166 校验） | W/portal/Claims.vue:292 | M/pages/claims/index.vue | CONSISTENT / 定位 | |
| ocap | US-052 | FUNC-043 | B/polls/views.py:30-69（NO_REPRESENTATIVES :69） | W/portal/Polls.vue:107 | — | CONSISTENT / 读码 | 最短投票窗口 60 分钟（U-3）AC 未提 |
| ocap | US-053 | FUNC-043、046 | B/polls/services.py:48-100 | W/portal/PollDetail.vue:103 | M/pages/polls/detail.vue（pages.json:9） | CONSISTENT / 定位 | |
| ocap | US-054 | FUNC-044 | B/polls/views.py:154-226（资格校验 :166-172） | W/portal/PollDetail.vue:93 | M/pages/polls/detail.vue | CONSISTENT / 读码 | |
| ocap | US-055 | FUNC-046 | B/polls/views.py:96-120,176-226 | W/portal/Polls.vue:33-46,107 | — | CONSISTENT / 读码 | 题数上限 50、选项 2~10 为自拟（U-3） |
| ocap | US-056 | FUNC-045 | B/polls/views.py:154-226 | W/portal/PollDetail.vue:93 | M/pages/polls/detail.vue | CONSISTENT / 定位 | |
| ocap | US-057 | FUNC-047 | B/polls/views.py:228-242；polls/services.py:59 | W/portal/PollDetail.vue:103；Polls.vue:8 | M/pages/polls/detail.vue | CONSISTENT / 定位 | |
| ocap | US-058 | FUNC-048 | B/income/views.py:203-260（IsIncomeMember） | W/portal/Income.vue:126 | — | CONSISTENT / 定位 | |
| ocap | US-059 | FUNC-048、059 | B/income/views.py:62-200 | W/portal/Income.vue:138 | — | CONSISTENT / 定位 | 导入行数上限 5000（:80）为自拟（U-1） |
| ocap | US-060 | FUNC-049、062 | B/income/views.py:297-368；approval/services.py:120（原审批人） | W/portal/Income.vue:161,182 | — | CONSISTENT / 定位 | 作废无确认见 CORR-006 |
| ocap | US-061 | FUNC-050 | B/ledger/services.py:70-128；jobs/management/commands/run_due_jobs.py:27 | — | — | CONSISTENT / 定位 | |
| ocap | US-062 | FUNC-050 | B/ledger/views.py:28-52（IsCommitteeMember） | W/portal/Reports.vue:71 | — | CONSISTENT / 定位 | |
| ocap | US-063 | FUNC-051 | B/ledger/views.py:14-78 | W/portal/Reports.vue:52,61 | M/pages/me/index.vue:31（仅总额） | CONSISTENT / 定位 | |
| ocap | US-065 | FUNC-060 | B/resolutions/services.py:60-96,92-96；jobs 每分钟调用 | W/portal/ResolutionDetail.vue | M/pages/resolutions/detail.vue | CONSISTENT / 读码 | |
| ocap | US-066 | FUNC-061 | B/committee/services.py:176-205 | — | — | CONSISTENT / 定位 | |
| ocap | US-067 | FUNC-062 | B/approval/services.py:42,100-102 | — | — | CONSISTENT / 读码 | |
| ocap | US-068 | FUNC-063 | B/approval/services.py:100（APPROVER_NO_LONGER_ELIGIBLE） | — | — | CONSISTENT / 定位 | |
| ocap | US-069 | FUNC-064 | B/accounts/views.py:42-43,112,124,135,160,205（仅勾选 remember_me 或微信小程序登录才 EXTENDED）；accounts/services.py:275-296；core/config.py:36（`session.miniapp_extended` 全仓库无读取点） | W/portal/Login.vue:12,18 | M/utils/api.js:4-6（手机号登录不带 remember_me） | INCONSISTENT / 读码 | AC-069-04"微信小程序端登录 → 7 天内再次打开仍登录"：小程序用手机号验证码/密码登录得到的是 30 分钟闲置会话，只有微信一键登录（views.py:160）是 7 天。→ CORR-003 |
| ocap | US-070 | FUNC-065 | B/accounts/views.py:147-161 | — | M/pages.json:4；pages/me/index.vue（"修改头像昵称"入口） | CONSISTENT / 定位 | |
| ocap | US-071 | FUNC-066 | B/approval/services.py:42,93,100-108 | — | — | CONSISTENT / 读码 | |
| ocap | US-072 | FUNC-067 | B/polls/apps.py:16-17；resolutions/apps.py:19-20；approval/apps.py:13-16；core/user_refs.py:20-43 | — | — | CONSISTENT / 定位 | 所有指向用户的外键必须登记合并策略（有启动检查） |
| ocap | US-073 | FUNC-068 | B/accounts/views.py:377-400（含"不能重置自己的密码" :378，U-12） | W/admin/AdminUsers.vue:102 | — | CONSISTENT / 读码 | |

#### 2.1.2 批次 ocap_ui_theme（12 行）

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| ui_theme | US-074 | FUNC-069 | — | W/theme/generated/registry.js；core.js:2-13 | M/pages/me/index.vue:10-13 | CONSISTENT / 定位 | 视觉特征无法读码判定 |
| ui_theme | US-075 | FUNC-070 | B/accounts/views.py:260-270 | W/theme/store.js:4,14 | M/pages/me/index.vue | CONSISTENT / 定位 | |
| ui_theme | US-076 | FUNC-071、073 | B/accounts/views.py:260-270；accounts/services.py:333 | W/portal/Me.vue:5（ThemePicker） | — | CONSISTENT / 定位 | |
| ui_theme | US-077 | FUNC-071、077 | 同上 | — | M/pages/me/index.vue:10-13,57 | CONSISTENT / 定位 | |
| ui_theme | US-078 | FUNC-072 | B/accounts/views.py:260-270（仅作用于 request.user） | W/theme/store.js:13-55；router/index.js:65-76 | M/store/theme.js | CONSISTENT / 读码 | |
| ui_theme | US-079 | FUNC-078 | — | W/theme/apply.js；frontend/index.html:8-16 | M/store/theme.js | CONSISTENT / 定位 | |
| ui_theme | US-080 | FUNC-074 | — | W/theme/core.js:2-13；generated/registry.js | M/store/theme.js | CONSISTENT / 定位 | |
| ui_theme | US-081 | FUNC-075 | — | W/portal/*.vue（14 页） | — | CONSISTENT / 定位 | 视觉验收需浏览器 |
| ui_theme | US-082 | FUNC-076 | B/accounts/views.py:273-283 | W/theme/AdminThemeSwitcher.vue；admin/AdminLayout.vue:62 | — | DOC_CONFLICT / 读码 | 管理端"固定风格 B / 无切换入口"已被 admin_polish 的 REQ-FUNC-135 明确替代，代码已按新规则实现；但 ui_theme 的 spec/故事/C-23 未注明被替代（只有新批次单向声明） |
| ui_theme | US-083 | FUNC-077 | — | — | M/pages.json:21-28（标签栏 4 项）；M/components/ThemeRoot.vue | CONSISTENT / 定位 | 标签栏 4 项与 Q125 暂定一致 |
| ui_theme | US-084 | FUNC-079 | — | W/portal/BottomTabBar.vue:118-124（5 项）；PortalLayout.vue:6-15 | — | CONSISTENT / 读码 | 窄屏断点样式未核 |
| ui_theme | US-091 | NFUNC-009 | — | W/shared/api.js | M/utils/api.js | CONSISTENT / 定位 | 契约抽查无法对应数 = 0（第 3 节）；AC-091-01 的"后端 120/120"为历史口径，现基线 561 条含 1 条失败（第 6 节） |

#### 2.1.3 批次 ocap_registry_import（11 行）

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| registry | US-092 | FUNC-083、084 | B/registry/views.py:344；import_spec.py:13-15,73-90 | W/admin/RegistryImportDialog.vue:133 | — | CONSISTENT / 定位 | |
| registry | US-093 | FUNC-085、086、NFUNC-013 | B/registry/import_template.py:24-58；import_spec.py:42-49 | W/admin/RegistryImportDialog.vue:179 | — | CONSISTENT / 读码 | 文本列格式、两个工作表齐全；示例行现为 6 行（见第 6 节） |
| registry | US-094 | FUNC-083、086、087、090 | B/registry/views.py:284-321；import_spec.py:13-15 | W/admin/RegistryImportDialog.vue:161 | — | CONSISTENT / 定位 | 20000 行/5 MB/60 秒预算常量已核（import_spec.py:13-15） |
| registry | US-095 | FUNC-087、090、095 | B/registry/views.py:186 | W/admin/AdminRegistry.vue:244 | — | CONSISTENT / 定位 | |
| registry | US-096 | FUNC-088、089 | B/registry/import_spec.py；registry/models.py:66-67 | W/admin/RegistryImportDialog.vue | — | CONSISTENT / 定位 | |
| registry | US-097 | FUNC-088、089、095 | B/registry/views.py:74-183 | W/admin/AdminRegistry.vue:7-14,172,243 | — | CONSISTENT / 定位 | |
| registry | US-098 | FUNC-091、010 | B/registry/services.py:21；models.py:47-60 | W/portal/Units.vue:133-160 | M/pages/units/index.vue | DOC_CONFLICT / 定位 | AC-098-01/05/06 中"车库-A-088""标识不变"的旧标识示例已被 admin_polish 替代（admin_polish 声明了替代，但本批文档未注明）；代码为新格式 |
| registry | US-099 | FUNC-092、098 | B/registry/views.py:186,284 | W/admin/AdminRegistry.vue:244 | — | CONSISTENT / 定位 | |
| registry | US-102 | FUNC-096 | B/residency/auto_bind.py:27-52；accounts/views.py:103；identity/views.py:46-47 | W/portal/Register.vue:54；Me.vue:170 | M/pages/phone/index.vue:68 | CONSISTENT / 读码 | 每个专有部分独立事务，失败不影响其余；仅注册与首次绑定时触发 |
| registry | US-103 | FUNC-097 | B/registry/services.py:21-60 | W/portal/Units.vue:72-78 | M/pages/units/index.vue | CONSISTENT / 定位 | |
| registry | US-104 | FUNC-098、019、011 | B/residency/views.py:44-50 | W/portal/Units.vue:175-180 | M/pages/units/index.vue:155 | CONSISTENT / 读码 | 仅一条 toast 引导申诉，见 UX-09 |

#### 2.1.4 批次 ocap_content_publish（24 行，全部为"定位"级）

本批代码量大（B/content/ 约 3500 行），本次只定位实现与入口，未逐条 AC 对照；其行为验证需由 E2E 完成。后端路由全部在契约抽查中对应成功。

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| content | US-105 | FUNC-099 | B/content/views_admin.py:50-103；posts.py:61 | W/admin/AdminContentPosts.vue:58-79 | — | CONSISTENT / 定位 | |
| content | US-106 | FUNC-099 | B/content/views_admin.py:69-98 | W/admin/AdminContentPosts.vue:63-79（有二次确认） | — | CONSISTENT / 定位 | |
| content | US-107 | FUNC-100 | B/content/views_member.py:33-43 | W/portal/InfoDetail.vue:28；InfoList.vue:24 | — | CONSISTENT / 定位 | 详情页无错误态见 UX-23 |
| content | US-108 | FUNC-100 | 同上 | — | M/pages/info/detail.vue:6-10；index.vue:92 | CONSISTENT / 定位 | |
| content | US-109 | FUNC-101 | B/content/richtext/schema.py | W/admin/editor/Toolbar.vue；RichEditor.vue | — | CONSISTENT / 定位 | |
| content | US-110 | FUNC-102 | 同上 | W/admin/editor/Toolbar.vue | — | CONSISTENT / 定位 | |
| content | US-111 | FUNC-103 | B/content/media.py:153-166 | W/admin/editor/MediaPicker.vue；AdminContentEditor.vue:260 | — | CONSISTENT / 定位 | |
| content | US-112 | FUNC-104 | B/content/views_admin.py:112-132；styles.py:42 | W/admin/AdminContentEditor.vue:16,181（只能选择）；W/shared/api.js `createStyleTemplate`/`updateStyleTemplate`/`deleteStyleTemplate` 无调用 | — | MISSING / 读码 | AC-112-02"自定义一套样式并保存为模板"在管理端没有任何入口；后端 CRUD 已有。预览与内置模板可用。→ CORR-009 |
| content | US-113 | FUNC-104 | B/content/richtext/paginate.py | W/portal/InfoDetail.vue:5-9 | M/pages/info/detail.vue:7-10 | CONSISTENT / 定位 | |
| content | US-114 | FUNC-105 | B/content/ai_jobs.py:41-204；prompts.py:26 | W/admin/AdminContentEditor.vue:274,332 | — | CONSISTENT / 定位 | |
| content | US-115 | FUNC-108 | B/content/posts.py:61 | W/admin/AdminContentEditor.vue:194,229 | — | CONSISTENT / 定位 | |
| content | US-116 | FUNC-106 | B/content/ai_jobs.py:214-253 | W/admin/AdminContentEditor.vue:346 | — | CONSISTENT / 定位 | |
| content | US-117 | FUNC-109 | B/content/services_config.py:62-188；vault.py | W/admin/AdminAiServices.vue:68 | — | CONSISTENT / 定位 | |
| content | US-119 | FUNC-111 | B/content/media.py:153-166；conf.py:9-12 | W/admin/AdminMedia.vue:49 | — | CONSISTENT / 定位 | 视频 10 MB、仅 mp4 为暂定值，页面标"待确认"（OQ-6） |
| content | US-120 | FUNC-112 | B/content/ai_jobs.py:205-253 | W/admin/AdminContentEditor.vue:260 | — | CONSISTENT / 定位 | |
| content | US-121 | FUNC-113 | B/content/views_admin.py:134-165 | W/admin/editor/MediaPicker.vue | — | CONSISTENT / 定位 | |
| content | US-123 | FUNC-107 | B/content/media.py | W/admin/editor/extensions/Video.js | M/components/RichBlocks.vue | CONSISTENT / 定位 | |
| content | US-124 | FUNC-120 | B/content/ai_jobs.py:254-336；jobs.py；management/commands/run_content_worker.py | W/admin/AdminContentEditor.vue:309,355 | — | CONSISTENT / 定位 | 依赖 `ocap-content-worker` 单元（deploy/systemd/ocap-content-worker.service；内容批次部署报告记录已运行） |
| content | US-125 | FUNC-121 | B/content/services_config.py:62-188 | W/admin/AdminAiServices.vue:68,77 | — | CONSISTENT / 定位 | |
| content | US-126 | FUNC-115 | B/content/views_admin.py:265-286；platforms.py | W/admin/AdminPlatforms.vue:68-95 | — | CONSISTENT / 定位 | |
| content | US-127 | FUNC-116 | B/content/platforms.py；wechat_token.py | W/admin/AdminPlatforms.vue:81 | — | CONSISTENT / 定位 | |
| content | US-128 | FUNC-117 | B/content/drafts.py:46-199 | W/admin/AdminContentEditor.vue:378 | — | CONSISTENT / 定位 | |
| content | US-130 | FUNC-122 | B/content/export_pack.py:23-82 | W/admin/AdminContentEditor.vue:403,408 | — | CONSISTENT / 定位 | |
| content | US-131 | FUNC-119 | B/content/views_admin.py:46（AdminOnly） | W/router/index.js:29-51 | — | CONSISTENT / 定位 | |

#### 2.1.5 批次 ocap_admin_polish（12 行）

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| admin_polish | US-132 | FUNC-123 | B/registry/models.py:47-60,77-79（save 重算标识） | W/admin/AdminRegistry.vue:21 | M/pages/units/index.vue | CONSISTENT / 读码 | |
| admin_polish | US-133 | FUNC-124 | B/registry/models.py:35-44（楼层省略规则）、47-60 | — | — | CONSISTENT / 读码 | "户号以楼层值+层开头则省略楼层段"与 AC-133-04/08/09 一致 |
| admin_polish | US-134 | FUNC-125 | B/registry/migrations/0005_regenerate_specific_part.py | — | — | CONSISTENT / 定位 | 迁移内容未逐行核 |
| admin_polish | US-135 | FUNC-126 | B/registry/views.py:74-83 | W/admin/AdminRegistry.vue:21 | M/pages/units/index.vue | CONSISTENT / 定位 | |
| admin_polish | US-136 | FUNC-127 | B/registry/views.py:126-171 | W/admin/AdminRegistry.vue:172,243 | — | CONSISTENT / 定位 | |
| admin_polish | US-137 | FUNC-128 | B/registry/views.py:284-321 | W/admin/RegistryImportDialog.vue:161 | — | CONSISTENT / 定位 | |
| admin_polish | US-138 | FUNC-129 | B/registry/import_spec.py:42-56,73-90；import_template.py:7-14 | W/admin/RegistryImportDialog.vue:133 | — | CONSISTENT / 读码 | |
| admin_polish | US-139 | FUNC-130 | B/accounts/views.py:273-283 | W/theme/AdminThemeSwitcher.vue；admin/AdminLayout.vue:62 | — | CONSISTENT / 定位 | |
| admin_polish | US-140 | FUNC-131 | B/accounts/services.py:342 | W/theme/adminStore.js:7-9 | — | CONSISTENT / 定位 | |
| admin_polish | US-141 | FUNC-132 | B/accounts/views.py:273-283 | W/theme/adminStore.js；frontend/index.html:8-16 | — | CONSISTENT / 定位 | 首屏无闪烁需浏览器验证 |
| admin_polish | US-142 | FUNC-133 | — | W/theme/generated/themes.css；admin/*.vue | — | CONSISTENT / 定位 | 视觉类 AC，只确认入口与样式文件存在 |
| admin_polish | US-144 | FUNC-135 | — | W/router/index.js:65-76（afterEach 对管理端读管理员偏好） | — | CONSISTENT / 读码 | |

#### 2.1.6 批次 ocap_user_directory（5 行；US/AC 编号与 admin_polish 重复，见 D-1）

| 批次 | US | 对应 REQ | 后端实现位置 | Web 前端 | 小程序 | 结论 / 深度 | 说明 |
|---|---|---|---|---|---|---|---|
| user_dir | US-132 | FUNC-123、124 | B/accounts/directory.py:19-47；accounts/views.py:403-430 | W/admin/AdminUsers.vue:28-45 | — | CONSISTENT / 读码 | 最高身份、"已认证（N 套）"一致；过期席位不计入（directory.py:21-24） |
| user_dir | US-133 | FUNC-125 | B/accounts/directory.py:50-62 | W/admin/AdminUsers.vue:28-45 | — | CONSISTENT / 读码 | |
| user_dir | US-134 | FUNC-126 | B/accounts/serializers.py:20；accounts/models.py:26 | W/admin/AdminUsers.vue:28-45；shared/format.js:11-14 | — | CONSISTENT / 读码 | 时区为 Asia/Shanghai（config/settings.py:82），格式化截取到分钟 |
| user_dir | US-135 | FUNC-127、NFUNC-019 | B/accounts/directory.py:65-72；accounts/views.py:419-426 | W/admin/AdminUsers.vue:22（占位符含"实名"） | — | DOC_CONFLICT / 读码 | REQ-FUNC-127"新增信息不得改变原有搜索结果集合"与同批 Q-UD-05=B、AC-135-02"搜索支持实名"互相矛盾；代码按后者实现（搜索范围变大）。→ CORR-021 |
| user_dir | US-136 | FUNC-128 | B/accounts/directory.py:35-47（只看未结束的关系与未过期席位） | W/admin/AdminUsers.vue:28-45 | — | CONSISTENT / 读码 | |

### 2.2 UNDOCUMENTED：代码有、需求/故事没有的用户可见规则（12 项）

| 编号 | 位置 | 内容 | 与文档的关系 |
|---|---|---|---|
| U-1 | B/income/views.py:80,219 | 收入表批量导入行数上限 5000；逐条录入一次最多 500 条 | 需求/AC 均无数值（Q98 余项开放） |
| U-2 | B/claims/views.py:24,50-51；B/income/views.py:28,48 | 报销/备用金/收入金额硬编码上限 1,000,000 元；配置项 `claim.amount_max`（B/core/config.py:37）无人读取 | 与 C-14、AC-049-06 相抵：Q96 要求"不自拟数值，也不假定不设上限"，代码自拟了 |
| U-3 | B/core/config.py:38-39；polls/views.py:51,97,109；resolutions/views.py:219 | 一次投票/调查题数上限 50；单选/多选选项 2~10 个；发起投票或半数同意决议的表决窗口不得少于 60 分钟 | Q97 题数上限未答；"最短窗口"在需求中只在 Q110 备注里称"技术配置" |
| U-4 | B/committee/views.py:67 | 赋予席位时"任期开始日不得早于今天" | AC-037 未提 |
| U-5 | B/claims/views.py:96,124,151 | 报销发生日期不得晚于今日；备用金预计核销日期须晚于今日；核销一次最多关联 50 张报销单 | AC-049 未提 |
| U-6 | B/core/config.py:40；committee/services.py:80-87 | 半数同意的分母默认取"在任人数"（可配置为"人数上限之和"） | Q99 用户未答复，代码采用了分析师推荐项 A |
| U-7 | B/residency/views.py:79,186 | 同一专有部分已有待审申诉、同一人已有待审同住人申请时拒绝重复提交 | AC-029-01 明确"重复申请限制需求未规定" |
| U-8 | B/accounts/views.py:286-301 | 头像专用上传接口 `POST /me/avatar`，前端不使用（改用通用附件上传 + 资料更新） | 重复入口，无用户影响 |
| U-9 | B/accounts/views.py:378 | 管理员不能重置自己的密码 | AC-073 只写了"A 重置 B" |
| U-10 | B/accounts/views.py:419-426 | 注册用户列表搜索支持实名（含部分匹配） | 仅在 user_directory 决策记录与 AC-135-02 中有，REQ-FUNC-127 文字相反 |
| U-11 | W/portal/Home.vue:30-34,36-46 | 首页统计卡片、快捷入口、倒计时 | ui_theme 设计稿有，需求/故事未逐条写 |
| U-12 | W/admin/AdminContentSettings.vue:3-24；B/content/conf.py:9-12 | "内容中心参数"管理页（含"待确认"标记） | content_publish 以 OQ-2/OQ-6 开放，未写成功能需求 |

### 2.3 文档冲突项（DOC_CONFLICT，不占矩阵行）

| 编号 | 冲突 | 影响 |
|---|---|---|
| D-1 | **编号冲突**：user_directory 的 REQ-FUNC-123 ~ 128、REQ-NFUNC-019/020、US-132 ~ 136（含 AC-132-xx ~ AC-136-xx）、C-30 ~ C-34 与 admin_polish 的 REQ-FUNC-123 ~ 135、REQ-NFUNC-19 ~ 23、US-132 ~ 144、C-31 ~ C-34 整段重复；另 ocap_ui_theme 的 C-21 ~ C-24 与 ocap_registry_import 的 C-21 ~ C-24 重复，registry_import 的 C-25/26 与 content_publish 的 C-25/26 重复，content_publish 的 C-30 与 user_directory 的 C-30 重复。两批在同一天（admin_polish 22:10、user_directory 22:30）并行编写，user_directory 基线只看到 content_publish 的末位编号（REQ-FUNC-122 / US-131） | 追溯、测试用例命名（TC 里引用 AC-135-01 等）无法唯一指向；后续任何引用都有歧义 |
| D-2 | admin_polish 替代 ocap_ui_theme 的 REQ-FUNC-076、US-082、C-23（管理端固定 B）和 registry_import 的 AC-098-01/05/06（旧标识示例）；只在新批次单向声明，前批文档未回注 | 读前批文档的人会按旧规则理解（US-082、US-098 已记为 DOC_CONFLICT） |
| D-3 | US-004 的"昵称取用微信昵称"被 REQ-FUNC-065 / US-070 改写，US-004 未注明 | 同上 |
| D-4 | US-019 AC-019-08 的 5 列文件规则被 registry_import 的 8 列规则替代，US-019 未注明 | 同上 |
| D-5 | user_directory REQ-FUNC-127 与 Q-UD-05=B / AC-135-02 互相矛盾（见 US-135 行） | 需求文字需改 |
| D-6 | ocap_ui_theme REQ-FUNC-079"Web 窄屏底部标签栏 5 项"与小程序标签栏 4 项（Q125 非阻断暂保持）并存 | 两端导航不一致，已在 UX-25 记录 |
| D-7 | registry_import AC-093-01 未规定示例行数；admin_polish REQ-FUNC-129 要求新增 `1栋负1层924号`、`10栋1层1号` 示例，模板示例行由 4 行变 6 行，但没有同步更新引用 4 行的 TC-INT-311 | 见第 6 节 |
| D-8 | ocap 需求文件头版本（spec 5.0.0 / stories 3.0.0）与其 input_files 中引用的版本标号（"4.1.0"、"2.0.0/2.1.0"）口径不一致（文件内正文用 4.1.0/2.1.0 作"修订号"，文件头用 APPROVED 号） | 易误判基线版本，建议在头部加一行对照 |

## 3. 前后端契约抽查

方法：只读脚本解析 `W/shared/api.js`（含 `admin` 对象）与 `M/utils/api.js` 中的 `get/post/http.*/adminHttp.*` 调用（路径 + 方法），对照 `B/*/urls.py` 的 `path()` 与各视图类实际定义的 `get/post/put/patch/delete`；另扫描各 `.vue/.js` 中的直接 http 调用。字段名不在本次抽查范围。

| 项 | 结果 |
|---|---|
| Web 调用 | 142 处（`W/shared/api.js`） |
| 小程序调用 | 33 处（`M/utils/api.js`） |
| 路径无法对应 | **0**（脚本唯一报"NO-ROUTE"的是测试文件 `M/tests/api.spec.js` 里的本地文件路径 `/tmp/a.png`，不是 API 调用） |
| 方法不匹配 | **0** |
| 无调用方的后端路由（11 条） | `admin/system-config`（列表，前端只用带 key 的子路径）、`auth/wechat/web/callback`（由微信回跳，非前端调用）、`me/avatar`（见 U-8）、`jobs/*` 共 7 条（定时任务入口，由 systemd timer 调用，不需要前端）、`content/media/<uuid>/file`（签名链接，由富文本/页面 `<img>` 直接访问） |
| 定义了但没有任何页面使用的前端 API 函数 | Web：`myAppeals`、`myResidentApplications`、`removeResident`、`leaveUnit`、`createStyleTemplate`、`updateStyleTemplate`、`deleteStyleTemplate`、`contentJobs`；小程序：`profile`。**这些是第 2 节 US-026/029/112 判为 MISSING 的直接证据**：后端能力在、前端无入口 |
| 需要注意 | 契约一致 ≠ 业务可用：例如 `POST /claims/reimbursements` 契约一致，但权限与 AC 不一致（US-049） |

## 4. 用户视角易用性评审

说明：下面从用户角度逐条走主要流程。"影响"写对用户的实际后果；证据均为 `文件:行`。角色按需求中的叫法；"端"= Web 门户 / Web 管理端 / 小程序。

### 4.1 游客 / 注册用户（Web 门户、小程序）

| # | 流程 | 问题 | 证据 | 对用户的影响 | CORR |
|---|---|---|---|---|---|
| UX-01 | 注册登录 | 密码登录框占位符写"手机号 / 邮箱 / 账号"，但邮箱 + 密码永远失败 | W/portal/Login.vue:16；B/accounts/services.py:202-203 | 用户照提示输邮箱，得到"账号或密码错误；若从未设置过密码……"，既不知是邮箱不支持，也可能怀疑密码错了；连错 5 次还会被锁 15 分钟 | 011 |
| UX-02 | 注册登录 | 微信登录入口是一行小字链接，点击后整页跳转；未配置微信时入口静默消失，不告知 | W/portal/Login.vue:32,113-122 | 与需求描述的"登录页展示二维码 / 快速登录"不符；用户找不到微信登录时无任何提示 | 010 |
| UX-03 | 注册登录 | 验证码登录时未注册手机号：要先拿验证码、输入后才被告知"该手机号尚未注册"，没有引导去注册 | B/accounts/services.py:187-193；W/portal/Login.vue:70-77 | 多走两步才发现走错入口 | 025 |
| UX-04 | 认证专有部分 | "我的房屋"页只是一张认证表单，不展示用户已经认证了哪些房屋、各是什么身份；首页只显示"认证房屋 N"的数字 | W/portal/Units.vue:3-52（无列表）；W/portal/Home.vue:31 | 认证完成后没有任何地方能看到结果；页面标题与内容不符 | 005 |
| UX-05 | 认证专有部分 | 认证成功提示拼接内部角色代码（`认证成功，身份：${result.role}`），疑似显示 HEAD/OWNER 英文（待 E2E 确认） | W/portal/Units.vue:175 | 用户看到英文代码，不知道自己是"户主"还是"产权业主" | 015 |
| UX-06 | 认证专有部分 | 认证失败只弹一条"可提交产权申诉"的 toast，申诉区在同页下方但依赖刚才选中的房屋；申诉只能传 1 份、且文件选择器限定图片 | W/portal/Units.vue:175-180,29,198 | 不能传 pdf、不能传多份（C-18 允许 5 份图片或 pdf）；用户不清楚下一步 | 016 |
| UX-07 | 认证专有部分 | 提交申诉后没有任何地方查看进度与结果（待审/通过/驳回及驳回原因） | W/shared/api.js `myAppeals` 无调用；M/pages/units/index.vue:181 | 用户只能等或再次提交；与 AC-026-01/03 不符 | 004 |
| UX-08 | 同住人审批 | 申请同住人要手输"专有部分 ID"（内部数字），页面其他任何位置都不展示该 ID | W/portal/Units.vue:41,207 | 普通用户无从得知 ID，该功能事实上用不了；小程序没有该功能 | 001 |
| UX-09 | 同住人审批 | 产权业主/户主要自己点"查看待我审批"才能看到申请；首页"待办"和"待办"页只含审批流程任务，不含同住人申请；也无任何红点/数字 | W/portal/Units.vue:44,216；W/portal/Tasks.vue:40；W/portal/Home.vue:139 | 申请人等不到回复，业主不知道有人在申请 | 001 |
| UX-10 | 同住人审批 | 申请人看不到自己申请的状态；产权业主无法移除同住人；同住人无法退出（后端接口都在，页面无按钮） | W/shared/api.js `myResidentApplications`/`removeResident`/`leaveUnit` 无调用 | 一旦通过就无法撤销，需求 AC-029-02/03 无法使用 | 001 |
| UX-11 | 个人中心 | 个人中心 9 个卡片纵向堆叠，没有身份展示、没有生日（需求含生日）、头像更换后不显示当前头像、上传选择器不限 jpg/png（需求 jpg/png ≤ 2 MB，出错才提示） | W/portal/Me.vue:3-103,143-144 | 找功能要滚很长；资料项不全 | 013 |
| UX-12 | 个人中心 | 更换手机号要填 6 个输入框、发两次验证码，且说明文字中含"以新手机号原账号为主，身份取高"这类系统规则 | W/portal/Me.vue:48-62 | 操作繁琐；术语对非技术用户难懂 | 028 |
| UX-13 | 账号注销 | 注销是不可逆操作，页面只有一个红色按钮 + 验证码；无"再次确认/后果清单"弹窗 | W/portal/Me.vue:85-96,235 | 验证码起到了确认作用，但没有告知"户主将由他人接任、席位失效"等后果 | 006 |
| UX-14 | 查看决议/投票/财务 | 列表只显示前 20 条且没有翻页；投票列表直接显示英文状态与原始时间戳（`item.status`、`item.deadline`） | B/core/serializers.py:7；W/portal/Polls.vue:15 | 历史决议/投票随时间增多后看不到旧的；"OPEN/CLOSED"对用户不友好 | 008、015 |
| UX-15 | 发起报销/备用金 | 非业委会成员也看到"报销/备用金"菜单和"新建申请"，点开后取流程列表被拒，只弹"需要业委会成员身份"类提示 | W/portal/PortalLayout.vue:38；W/portal/Claims.vue:7,225；B/approval/views.py:116 | 菜单对不该用的人也展示，点击后才报错；同时 API 本身未限制发起人（US-049） | 002、014 |
| UX-16 | 待办 | "待办"出现在所有用户的导航与首页快捷入口，对非委员点开是错误提示 | W/portal/PortalLayout.vue:41；W/portal/Tasks.vue:40-43；B/approval/views.py:131 | 点击即报错 | 014 |
| UX-17 | 信息公开 | 内容被下线/删除后打开详情页，页面空白（请求失败未处理） | W/portal/InfoDetail.vue:28-33 | 用户不知道发生了什么 | 026 |

### 4.2 同住人 / 产权业主（户主）

| # | 问题 | 证据 | 影响 | CORR |
|---|---|---|---|---|
| UX-18 | 多户用户的"当前身份"只显示一个且可能不是最高身份；同一人在管理端目录看到的是最高身份，两处不一致 | B/committee/services.py:65-77；B/accounts/directory.py:19-33 | 户主可能被显示为"同住人"，引起对自己权限的疑惑 | 005 |
| UX-19 | 无任何"我是哪几户的什么身份"的列表（后端 `/me` 已返回 `units`） | B/identity/services.py:20-22,34-36；W/portal/Home.vue:9 | 同 UX-04 | 005 |

### 4.3 业委会委员 / 主任 / 副主任 / 业主代表

| # | 流程 | 问题 | 证据 | 影响 | CORR |
|---|---|---|---|---|---|
| UX-20 | 发起决议/投票 | 投票窗口最短 60 分钟、题数最多 50 在表单上没有任何提示，只在提交失败后才知道 | W/portal/Polls.vue:31；B/polls/views.py:51-53,97-98 | 提交失败后才发现规则 | 022 |
| UX-21 | 收入表 | "作废"（已生效收入表）是不可逆操作，红色按钮无确认 | W/portal/Income.vue:38,180-186 | 误点即作废，需要重走审批 | 006 |
| UX-22 | 撤回 | 决议/报销/收入表"撤回"同样无确认 | W/portal/Claims.vue:33,303；ResolutionDetail.vue:26,95 | 误撤回后需修改重提 | 006 |
| UX-23 | 移动端 | 小程序没有收入表入口，报表只显示总额不含明细 | M/pages/me/index.vue:31；M/utils/api.js | 委员在手机上无法录入收入；与 Web 能力不一致 | 017 |

### 4.4 后台管理员（Web 管理端）

| # | 流程 | 问题 | 证据 | 影响 | CORR |
|---|---|---|---|---|---|
| UX-24 | 赋予席位 / 配置审批流程 | 要手输用户数字 ID（席位）和用逗号分隔的审批人 ID（流程）；ID 只在"账号"页的表格里能看到，需要来回抄写 | W/admin/AdminSeats.vue:40；W/admin/AdminFlows.vue:36；W/admin/AdminUsers.vue:28 | 易输错；同时无法确认输入的人是谁（输错 ID 只会得到"须是有效产权业主"这类通用错误） | 007 |
| UX-25 | 破坏性操作 | 撤销产权认证、撤销席位、删除专有部分、删除审批流程均无二次确认；其中撤销户主认证会触发户主接任并可能使席位失效，删除专有部分会连带删除其业主登记 | W/admin/AdminMemberships.vue:49-57；AdminSeats.vue:130-138；AdminRegistry.vue:253-260；AdminFlows.vue:88 | 误点不可恢复 | 006 |
| UX-26 | 列表浏览 | "账号""房屋关系""申诉""席位""审批流程""财务"列表均只取第一页 20 条且没有翻页；清册、审计、信息公开有翻页，其余没有 | B/core/serializers.py:7；W/admin/AdminUsers.vue:71-81；AdminMemberships.vue:42；AdminAppeals.vue:45；AdminFinance.vue:43 | 用户目录是 user_directory 批次的核心交付，但只能看到前 20 人，其余只能靠搜索；申诉超过 20 条时看不到后面的 | 008 |
| UX-27 | 术语与显示 | 席位状态、账号状态、"启用"等直接显示 `ACTIVE`/`true`；清册列表列名叫"房号"，而需求、导入模板、用户端都叫"户号"；"专有部分"这类词没有在界面里解释 | W/admin/AdminSeats.vue:22；AdminUsers.vue:11,28；AdminRegistry.vue:25 | 对非技术管理员不友好 | 015、028 |
| UX-28 | 导航与参数页 | 管理端 13 个入口平铺在一个顶栏里；"内容中心参数"页直接展示配置项键名与 JSON 列表 | W/admin/AdminLayout.vue:79-93；AdminContentSettings.vue:3-24 | 找功能难；参数页只适合开发者 | 018、027 |

### 4.5 端间不一致（Web 与小程序）与移动端

| # | 问题 | 证据 | CORR |
|---|---|---|---|
| UX-29 | 窄屏 Web 的底部标签栏只有 首页/决议/投票/报销/我的 5 项，待办、财务报表、信息公开、我的房屋只能经首页或个人中心的快捷入口到达；小程序标签栏 4 项且无报销入口（已是 Q125 暂定） | W/portal/BottomTabBar.vue:118-124；M/pages.json:21-28 | 024 |

### 4.6 按流程的步骤数观察

| 流程 | 实际步骤 | 评价 |
|---|---|---|
| 注册 → 自动认证 | 手机号 + 验证码两步即完成；清册命中时自动认证并有提示（Register.vue:54） | 良好 |
| 手动认证 | 登录 → 我的房屋 → 逐级选 3~4 级 → 点认证；成功后无结果展示 | 步骤合理，结果不可见 |
| 同住人申请 | 需知道内部 ID，业主需主动查询 | 不可用（CRITICAL） |
| 发起决议 | 菜单 → 发起 → 填标题/内容/附件/选流程 → 提交（成员）；流程列表为空时提示可读性待验证 | 步骤合理 |
| 清册导入 | 清册页 → 批量导入 → 下载模板/看说明 → 预检 → 确认；有可读的错误清单 | 良好（RegistryImportDialog.vue:133-179） |

## 5. 修正候选清单

类别：一致性修复 / 文档修正 / 易用性改进 / 缺失功能补齐。规模：S ≤ 半天，M 1~3 天，L > 3 天（均为粗估，供排期参考）。

| ID | 类别 | 严重度 | 问题 | 证据 | 建议修正（用户可理解的描述） | 影响角色/端 | 推荐与理由 | 规模 |
|---|---|---|---|---|---|---|---|---|
| CORR-001 | 缺失功能补齐 | CRITICAL | 同住人链路不可用：申请要手输内部 ID；产权业主无提示；申请人看不到状态；移除/退出无入口 | W/portal/Units.vue:41,207,216；W/shared/api.js 4 个函数无调用；US-024、US-029 | 申请同住人时直接用"选楼栋→单元→楼层→户号"选房屋；产权业主在首页/待办里看到"有 N 个同住人申请待审批"；申请人在页面看到自己的申请状态；产权业主可移除同住人、同住人可退出；小程序同步提供 | 注册用户、同住人、产权业主/户主；Web + 小程序 | **建议做**：核心业务链路，现状等于未交付 | L |
| CORR-002 | 一致性修复 | MAJOR | 报销/备用金发起未限业委会成员（接口与页面） | B/claims/views.py:84,111；W/portal/Claims.vue:7；B/approval/views.py:116 | 只有现任业委会成员能发起报销/备用金；非成员看不到该菜单与"新建申请"；非成员直接调用被拒绝 | 全体已登录用户（权限）；Web + 小程序 | **建议做**：与 AC-049-05 相反，涉及财务；需用户确认意图（见 Q2） | S |
| CORR-003 | 一致性修复 | MAJOR | 小程序手机号验证码/密码登录只保持 30 分钟闲置，未达"小程序默认 7 天" | B/accounts/views.py:42-43,112,124；B/core/config.py:36（配置无人读取）；M/utils/api.js:4-6 | 在小程序里无论用哪种方式登录，都保持 7 天登录 | 小程序用户 | **建议做**：与已确认的 REQ-FUNC-064 不符，体验影响大（手机上反复登录） | S |
| CORR-004 | 缺失功能补齐 | MAJOR | 用户看不到自己的产权申诉状态与驳回原因 | W/shared/api.js `myAppeals` 无调用；M/pages/units/index.vue:181 | 在"我的房屋"里展示申诉列表：待审核/已通过/已驳回及驳回原因 | 注册用户；Web + 小程序 | **建议做**：AC-026-01/03 明确要求 | M |
| CORR-005 | 一致性修复 | MAJOR | 身份展示不准确且缺失：多户时只显示首条房屋身份（顺序不定）；个人中心不显示身份；"我的房屋"不列出已认证房屋；与管理端目录的"最高身份"口径不一致 | B/committee/services.py:65-77；B/identity/services.py:17-46；W/portal/Me.vue；W/portal/Units.vue:3-52 | 个人中心与"我的房屋"列出"每一套房屋 + 在该房屋的身份"，另给出一个汇总身份（取最高）；两端与管理端统一口径 | 注册用户及以上；Web + 小程序 | **建议做**：AC-041-01/02 | M |
| CORR-006 | 易用性改进 | MAJOR | 破坏性/不可逆操作无二次确认：撤销认证、撤销席位、删除专有部分、删除审批流程、收入表作废、撤回、注销 | W/admin/AdminMemberships.vue:49；AdminSeats.vue:130；AdminRegistry.vue:253；AdminFlows.vue:88；W/portal/Income.vue:180；Me.vue:235 | 以上操作点击后先弹出"将产生的后果 + 确认/取消"；注销前列出后果清单 | 管理员、业委会成员、注册用户；Web | **建议做**：改动小、防误操作 | S |
| CORR-007 | 易用性改进 | MAJOR | 赋予席位、配置审批人要手输用户 ID | W/admin/AdminSeats.vue:40；AdminFlows.vue:36 | 改成"按姓名/手机号后四位/账号搜索并选择用户"，选中后显示昵称与身份确认 | 管理员 | **建议做** | M |
| CORR-008 | 易用性改进 | MAJOR | 多处列表只显示前 20 条且无翻页：管理端（账号、房屋关系、申诉、席位、审批流程、财务）与用户端（决议、投票、报销、收入表、报表、待办） | B/core/serializers.py:7；W/admin/AdminUsers.vue:71-81；AdminMemberships.vue:42；AdminAppeals.vue:45；AdminFinance.vue:43 | 所有列表提供翻页（或"加载更多"）并显示总数 | 管理员、全体用户；Web + 小程序 | **建议做**：数据增长后会直接丢可见性；user_directory 价值依赖它 | M |
| CORR-009 | 缺失功能补齐 | MAJOR | 管理端无法新建/修改/删除自定义版式模板 | W/admin/AdminContentEditor.vue:16,181；W/shared/api.js 3 个函数无调用；US-112 AC-112-02 | 在编辑器或独立页提供"我的版式模板"管理：新建、改名、编辑样式、删除 | 管理员；Web 管理端 | **建议做**（或与用户确认降级为文档修正，见 Q8） | M |
| CORR-010 | 一致性修复 | MAJOR | Web 登录页没有微信二维码/快速登录组件，只是跳转链接 | W/portal/Login.vue:32,113-122；B/accounts/views.py:170-171 | 在登录页内直接展示微信扫码二维码（支持快速登录时由微信提示）；未配置微信时给出"微信登录暂未开通"提示 | 访客；Web | **可选**：需要已审核通过的开放平台应用才能联调，测试环境无法验证；也可改为"文档修正"（见 Q5） | M |
| CORR-011 | 易用性改进 | MINOR | 密码登录提示含"邮箱"，但邮箱不能用密码登录 | W/portal/Login.vue:16 | 把提示改成"账号或手机号" | 访客；Web | **建议做**：一行文案 | S |
| CORR-012 | 一致性修复 | MINOR | 注销账号时，该用户的待处理同住人申请/产权申诉没有被关闭 | B/identity/services.py:114-139；AC-031-05 | 注销时自动关闭其待处理的申请与申诉 | 注册用户、管理员、产权业主 | **建议做**：避免审批队列残留已注销用户 | S |
| CORR-013 | 缺失功能补齐 | MINOR | 个人资料缺生日；更换头像后不显示当前头像；头像格式/大小只在失败后提示 | W/portal/Me.vue:134,143-144；REQ-FUNC-016 | 资料卡增加生日、显示当前头像，上传前提示"jpg/png，不超过 2 MB" | 注册用户；Web（小程序另议） | **建议做** | S |
| CORR-014 | 易用性改进 | MINOR | 无权限的入口对所有人展示（待办、报销/备用金新建） | W/portal/PortalLayout.vue:38,41；W/portal/Home.vue:36-46 | 按身份显示菜单；无权限的入口不出现 | 非业委会成员；Web + 小程序 | **建议做**（与 CORR-002 一起） | S |
| CORR-015 | 易用性改进 | MINOR | 界面显示内部值：英文角色/状态代码、true/false、原始时间戳 | W/portal/Units.vue:175；W/portal/Polls.vue:15；W/admin/AdminSeats.vue:22；AdminUsers.vue:11,28 | 统一显示中文名称与"年-月-日 时:分" | 全体；Web | **建议做** | S |
| CORR-016 | 易用性改进 | MINOR | 申诉上传只能 1 份、选择器只含图片 | W/portal/Units.vue:29,198；B/core/attachments.py:22 | 支持最多 5 份、图片或 pdf，并显示已选文件 | 注册用户；Web + 小程序 | **可选** | S |
| CORR-017 | 易用性改进 | MINOR | 小程序与 Web 能力不对等：无同住人、设密码、注销、收入表、报表明细 | M/pages/me/index.vue:35-39；M/utils/api.js | 待用户决定哪些在手机上也要有（见 Q4） | 小程序用户 | **可选**：需求未要求，需用户取舍 | L |
| CORR-018 | 易用性改进 | MINOR | "内容中心参数"页暴露配置键与 JSON | W/admin/AdminContentSettings.vue:3-24 | 改为带中文说明的表单（含单位、取值范围） | 管理员；Web 管理端 | **可选** | S |
| CORR-019 | 文档修正 | MAJOR | 编号冲突：user_directory 与 admin_polish 的 REQ/US/AC/约束整段重复；其余批次约束号重复 | 第 2.3 节 D-1 | user_directory 整体重新编号（REQ-FUNC-136 起、US-145 起、C-35 起、REQ-NFUNC-24 起）并同步其文档内引用；其余重复的约束编号按批次加前缀 | 文档/测试追溯 | **建议做**：纯文档，不改代码 | S |
| CORR-020 | 文档修正 | MINOR | 前批文档未注明被后批替代的条目（REQ-FUNC-076/US-082/C-23；AC-098-01/05/06；AC-019-08；AC-004-01/02） | 第 2.3 节 D-2 ~ D-4 | 在被替代条目旁加一行"已被 xxx 替代"的注记 | 文档读者 | **建议做** | S |
| CORR-021 | 文档修正 | MINOR | user_directory REQ-FUNC-127 与"搜索支持实名"互相矛盾 | 第 2.3 节 D-5；W/admin/AdminUsers.vue:22 | 把需求文字改为"账号、手机号、昵称搜索行为保持不变，另增实名搜索" | 文档读者 | **建议做**：代码正确，改文档 | S |
| CORR-022 | 文档修正 | MINOR | 代码里的自拟规则未入需求，且与"Q96/Q97/Q99 未答复、不自拟"相抵（金额上限 100 万、题数 50、选项 2~10、最短窗口 60 分钟、收入导入 5000 行、分母取在任人数等） | 第 2.2 节 U-1 ~ U-7 | 请用户逐项确认数值后写进需求与验收标准；金额上限若不要，去掉代码中的硬编码 | 业委会成员；全体 | **建议做**（先确认，见 Q1、Q6、Q7） | S |
| CORR-023 | 文档修正（测试） | MINOR | 基线失败 TC-INT-311 期望旧模板的 4 行/2 个专有部分，模板现为 6 行/4 个专有部分 | 第 6 节 | 把该用例的期望改为"6 行、0 失败、新增 4 个专有部分"，并在用例说明里引用 REQ-FUNC-129 | 测试 | **建议做**：代码与需求一致，仅测试过时 | S |
| CORR-024 | 易用性改进 | MINOR | 窄屏底部标签栏缺待办/财务报表/信息公开/我的房屋，且与小程序 4 项不一致 | W/portal/BottomTabBar.vue:118-124；M/pages.json:21-28 | 评估把"信息公开"并入底部栏或"我的"页里增加完整入口列表；Q125 一并决定 | 手机用户 | **可选** | S |
| CORR-025 | 易用性改进 | MINOR | 未注册手机号用验证码登录要走完整一步才报错 | B/accounts/services.py:187-193 | 获取验证码时或报错时直接提供"去注册"入口 | 访客；Web + 小程序 | **可选** | S |
| CORR-026 | 易用性改进 | MINOR | 信息公开详情页对已下线/不存在的内容无错误态 | W/portal/InfoDetail.vue:28-33 | 显示"内容不存在或已下线"并给返回列表链接 | 已登录用户；Web | **建议做** | S |
| CORR-027 | 易用性改进 | MINOR | 管理端顶栏 13 个入口平铺 | W/admin/AdminLayout.vue:79-93 | 按"清册与认证 / 业委会与审批 / 财务 / 内容中心 / 系统"分组 | 管理员；Web 管理端 | **可选** | M |
| CORR-028 | 易用性改进 | MINOR | 术语不统一或太技术："房号"与"户号"、"专有部分"、"席位"、更换手机号的合并规则说明 | W/admin/AdminRegistry.vue:25；W/portal/Units.vue:41；W/portal/Me.vue:49 | 统一用词（对用户用"房屋"，括号注"专有部分"），简化说明文字 | 全体；Web + 小程序 | **可选** | S |

## 6. 已知基线失败：TC-INT-311

| 项 | 内容 |
|---|---|
| 用例 | `backend/tests/integration/test_registry_import_xlsx_defects.py:118`（`tests.integration.test_registry_import_xlsx_defects.XlsxImportTests.test_tc_int_311_downloaded_template_imports_back`） |
| 现象 | 期望 `(rows_total, failed) == (4, 0)`、`imported == 2`；实得 6 行 |
| 原因 | 模板示例行由 `ocap_registry_import` 交付时的 4 行（3 位业主同一户 + 1 个车位）扩成 6 行：admin_polish 提交（3825aac）在 `B/registry/import_spec.py:42-49` 新增了 `["1栋","","负1","924","车位",...]` 与 `["10栋","","1","1","商铺",...]` 两行，以满足 REQ-FUNC-129（示例须出现 `1栋负1层924号`、`10栋1层1号`）和 AC-138-02。模板的构建逻辑（`B/registry/import_template.py:24-58`）直接取 `EXAMPLE_ROWS`，同一份示例行也被说明页使用 |
| 结论 | **测试过时，不是代码缺陷，也不是模板与需求不一致**：6 行示例与 REQ-FUNC-129、AC-138-02、AC-138-03（示例行预检失败行数 = 0）一致；AC-093-01 没有规定示例行数。该用例本应在 admin_polish 的 AC-144-04/REQ-NFUNC-20 要求的"因旧格式失败的既有用例同步更新并单列说明"中被改掉，漏掉了 |
| 预期的新断言 | rows_total = 6；failed = 0；imported（新增专有部分数）= 4（`1栋1单元3层301号`、`车库A-088`、`1栋负1层924号`、`10栋1层1号`） |
| 处理 | 见 CORR-023；另在 D-7 记录文档侧的缺失 |

## 7. 待用户确认的问题

| 编号 | 问题 | 选项 | 推荐 |
|---|---|---|---|
| Q1 | 报销/备用金/收入金额：代码硬编码了 100 万元上限（需求 Q96 说用户未给数值、不自拟） | A 保留 100 万并写进需求；B 去掉上限；C 改成管理员可在配置页设置 | C（既不自拟、也可随时调整） |
| Q2 | 谁能发起报销/备用金：AC-049-05 写"仅业委会成员"，现状任何登录用户可调接口 | A 按需求限制为业委会成员（修代码）；B 放开给所有注册用户（改需求） | A |
| Q3 | 同住人链路（CORR-001）的补齐范围 | A Web + 小程序都补；B 仅 Web；C 暂不做 | A（"手机上"是主要使用场景） |
| Q4 | 小程序要补哪些（CORR-017）：同住人、设密码、注销、收入表、报表明细 | A 全补；B 只补同住人与报表明细；C 保持现状 | B |
| Q5 | Web 微信登录（CORR-010）：现为跳转链接，需求写的是页内二维码/快速登录 | A 改成页内二维码；B 保持跳转链接并改需求文字 | B（测试环境无法联调微信；需求文字改动最小） |
| Q6 | 半数同意决议的分母（Q99 未答，代码取在任人数） | A 取在任人数（现状，写进需求）；B 取人数上限之和（9） | A |
| Q7 | 代码自拟的投票规则：题数 ≤ 50、选项 2~10 个、最短窗口 60 分钟、收入导入 ≤ 5000 行 | A 全部写进需求；B 逐项指定新数值；C 去掉限制 | A |
| Q8 | 自定义版式模板（CORR-009）：AC-112-02 要求可自定义保存 | A 补齐管理页面；B 本期只用内置模板，改需求/故事 | A |
| Q9 | 编号冲突整改方向（CORR-019） | A user_directory 整体重新编号（推荐）；B admin_polish 重新编号 | A（user_directory 篇幅小，且晚写） |
| Q10 | 注销账号时待处理的申诉/申请（CORR-012）怎么处理 | A 自动关闭（AC-031-05 原意）；B 保留给管理员处理 | A |

## 8. 本次评审的限制与未完成项

1. 矩阵中 77 行 CONSISTENT 为"定位"级，未逐条 AC 对照函数体，其中 ocap_content_publish 批次 24 行全部如此；这些行的"通过"仅表示有实现与入口，需在后续 E2E（本地为主、部署后按 P4-1 在测试环境）逐条验证。
2. 视觉与动效类 AC（对比度、首屏闪烁、动效降级、窄屏断点、三套风格逐页观感）无法凭读码判定。
3. 未核对 Should/Could 故事中的大部分（见 1.2 的抽查范围）。
4. 字段级契约（请求/响应字段名）未逐项核对，只核对了路径与方法。
5. 未读取 `docs`、`design` 目录与 `.trae/` 内容；Freeark 两份参考需求仅读了文件开头（画像 P10 标明仅作参考，本次评审不依赖其内容）。
