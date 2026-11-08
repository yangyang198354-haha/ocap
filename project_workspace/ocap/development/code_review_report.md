<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-08T13:44:45+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告（PHASE_06 CODE_REVIEW）

## 1. 结论

- CRITICAL：0
- MAJOR：3（原有遗留，均有明确原因与后续动作，见 §4）
- MINOR：7
- 缺陷回流：GR-D-001 的 4 个 MAJOR（DEF-001~004）已全部 FIXED，见 §7。
- 自验证：编译、系统检查、冒烟测试、迁移检查、三层全量测试全部通过。
- 评审结论：**可重新进入 GROUP_D 复跑**（无 CRITICAL；遗留 MAJOR 3 条未超过门控上限）。

## 2. 自验证证据

### 2.1 编译

```
> python -m compileall -q backend
COMPILE_EXIT=0
```

### 2.2 系统检查

```
> python manage.py check --settings=config.test_settings
System check identified no issues (0 silenced).
CHECK_EXIT=0
```

### 2.3 冒烟测试

```
> python manage.py test tests.smoke --settings=config.test_settings
...... 
Ran 6 tests in 0.096s
OK
Destroying test database for alias 'default'...
```

### 2.4 迁移检查

```
> python manage.py makemigrations --check --dry-run
No changes detected
MIGRATION_CHECK_EXIT=0
```

前序 `migrate --check` 输出 `No migrations to apply`。

## 3. 五维评分（5 分制）

| 维度 | 分数 | 依据 |
|---|---|---|
| 正确性 | 4.0 | 6 项端到端冒烟流程真实通过；统一错误体与状态码一致；金额两位小数；决议/投票/审批状态机有约束兜底。扣分：前端与小程序未经运行验证；结算复用 EXPENSE 为假设。 |
| 可维护性 | 4.0 | 按 app 分层（models/services/views/serializers/urls），业务规则集中在 services；权限与附件策略独立；命名与错误码统一。扣分：部分管理端页面为紧凑实现，交互简化。 |
| 安全性 | 4.0 | 全部业务端点默认登录；角色与房屋关系校验；防自批；验证码限流与锁定；审计白名单；密码规则与防枚举；外部凭据只读环境变量。扣分：未做渗透测试；并发与越权矩阵依赖后续 D 组用例。 |
| 性能 | 3.5 | 列表分页、批量导入上限、数据库索引与唯一约束；审计写入不阻塞主流程。扣分：未做压测；xlsx 全量解析在内存中完成。 |
| 测试完备性 | 3.0 | 后端有 6 个真实执行的冒烟用例覆盖主链路。扣分：单元/集成/E2E 三层测试由 GROUP_D 负责；前端与小程序无自动化测试。 |
| **综合** | **3.7** | 满足进入测试阶段的条件。 |

## 4. 问题清单

### MAJOR

| ID | 位置 | 问题 | 原因与后续动作 |
|---|---|---|---|
| CR-001 | `frontend/`、`miniprogram/` | 前端与小程序未安装依赖、未构建、无组件测试，运行时行为未经真实执行验证。 | 用户约束“不安装依赖、不改全局环境”；已做路由/接口静态核对，交付前需在允许安装的环境执行 `npm install && npm run build` 并补组件测试。 |
| CR-002 | `backend/apps/*/migrations/0001_initial.py` | 迁移为 `makemigrations` 自动生成，不完全符合画像 P6“手写最小化、按 app 分范围”的约定。 | 为在有限时间内完成 14 个 app 的可运行基线；已人工核对字段、索引与唯一约束，并通过 `makemigrations --check` 与 `migrate`。后续若上线前要求手写迁移，可按 app 拆分复核。 |
| CR-003 | `backend/config/settings.py` | 实际运行 Django 6.0.6 / DRF 3.17.1，高于画像目标的 Django 5.2。 | 本机既有环境，用户要求不降级；代码未使用 6.0 专属 API。需在 CI/部署环境固定到画像版本后复跑。 |

### MINOR

| ID | 位置 | 问题 | 处理 |
|---|---|---|---|
| CR-004 | `miniprogram/pages/profile-setup/index.vue` | 小程序端未上传头像，仅保存昵称。 | 已收敛为只保存昵称；头像上传依赖附件接口，后续在 Web 端或补 `uni.uploadFile`。 |
| CR-005 | `frontend/src/admin/AdminSeats.vue` | “变更职位”在 MEMBER/CHAIR 间切换，未提供完整职位下拉。 | 记录为交互简化，后续补 VICE_CHAIR 选项与生效日期。 |
| CR-006 | `backend/apps/registry/services.py`、`apps/integrations/aliyun_sms.py` | openpyxl 与阿里云 SDK 缺失时降级（503 / `SDK_MISSING`）。 | 符合 P11 外部依赖不可用时的失败可见原则；部署前安装依赖即可。 |
| CR-007 | `backend/apps/jobs/` | 定时任务仅提供 `run_due_jobs` 命令，未接入系统调度。 | 由 E1 部署计划配置 cron/计划任务。 |
| CR-008 | `backend/apps/approval/services.py` | 并发决定同一审批实例未做压力测试。 | 依赖 `pending_slot` 唯一约束与事务；由 D 组补并发用例。 |
| CR-009 | `frontend/src/shared/http.js` | 错误提示直接使用后端 `message`，未做本地化兜底。 | 后端错误体统一中文；保留 `details.retry_after` 拼接。 |
| CR-010 | `backend/apps/claims/views.py` | 结算（SETTLEMENT）复用 EXPENSE 审批作用域。 | 架构未单列结算流程，标 `[ASSUMPTION] A-01`，需求确认后可拆分。 |

## 5. 逐项自检（对照 §J GROUP_C）

| 条件 | 结果 | 证据 |
|---|---|---|
| MOD 全部实现 | 满足 | MOD-001~022 对应 app、Web 与管理端路由、小程序页面均已落盘 |
| 无未解决 CRITICAL | 满足 | §4 CRITICAL=0 |
| MAJOR 遗留 ≤3 且逐条原因 | 满足 | CR-001~003 均给出原因与后续动作 |
| PM 复跑无新增失败 | 待 PM 核验 | §2 命令与输出可供复跑 |
| 迁移符合 P6 | 部分（见 CR-002） | 自动生成但通过 `--check`，字段与约束已核对 |
| 改动范围与 implementation_plan 一致 | 满足 | 改动集中在 `backend/`、`frontend/`、`miniprogram/`、`development/` |
| 未使用无出处的闭源 API/寄存器 | 满足 | 外部调用仅微信/短信/邮件公开接口，均有 `# [P11: ...]` 出处注释 |

## 6. 建议 GROUP_D 优先覆盖

1. 认证与限流：验证码错误次数/锁定、防枚举、Token 过期与续期。
2. 房屋关系：重复认证冲突、首位户主、撤销后的接任、同住人越权。
3. 审批：DESIGNATED / HALF_MAJORITY 边界、防自批、撤回/重提、并发决定。
4. 财务：金额精度、收入表导入错误率阈值、报表周期锁定、作废后台账。
5. 权限矩阵：未登录 401、非成员 403、委员/主任差异、管理员端点。
6. 前端/小程序：在允许安装依赖的环境中构建并验证登录、认证、决议、投票主链路。

## 7. 缺陷修复（ocap-GROUP_C-2）

依据 GR-D-001，带 `REWORK_AUTHORIZED` 修复 4 个 MAJOR 产品缺陷：

| DEF | 位置 | 根因 | 修改说明 | 状态 |
|---|---|---|---|---|
| DEF-001 | `apps/resolutions/views.py::ResolutionListCreateView` | GET 与 POST 共用 `IsChairOrVice`，读接口被写权限约束 | `get_permissions` 按方法分离：GET → `IsMember`，POST → `IsChairOrVice` | FIXED |
| DEF-002 | `apps/income/views.py::IncomeSheetListView/IncomeSheetDetailView`、`apps/ledger/views.py::LedgerReportListCreateView/LedgerReportDetailView` | 财务读接口误用 `IsIncomeMember`，普通登录用户 403 | 列表/明细 GET 改 `IsMember`；收入导入、提交、台账生成仍限 `IsIncomeMember` | FIXED |
| DEF-003 | `apps/ledger/services.py::LedgerService.generate` | 同周期直接抛 `LEDGER_LOCKED`，与"手动重新生成、版本 +1"冲突 | 同周期改为覆盖原行：重算金额与内容、`version += 1`、刷新 `generated_at`，审计记录版本 | FIXED |
| DEF-004 | `apps/polls/models.py`、`migrations/0002_poll_kind_scope_question_type.py`、`views.py`、`services.py` | 应答仅限业委会成员；Poll 缺 kind/scope/参与人快照，Question 缺题型 | 新增 `kind` / `survey_scope` / `participant_count` / `result_snapshot` 与 `qtype` / `required`；代表投票快照现任代表；调查按范围、代表投票按快照校验参与资格；同意-反对-弃权返回分母与通过判定 | FIXED |

### 7.1 自验证

```
> python manage.py test tests.unit tests.integration tests.e2e --settings=config.test_settings -v 1
Ran 115 tests in 0.980s

OK
```

```
> python manage.py makemigrations --check --dry-run --settings=config.test_settings
No changes detected
```

分层结果：unit 33/33 OK、integration 72/72 OK、e2e 10/10 OK；相对修复前 106 通过 + 9 失败，9 条失败全部转绿，无回退。

### 7.2 遗留 MAJOR（未超过 3 条）

CR-001、CR-002、CR-003 维持原状，原因与后续动作见 §4；本次回流未引入新的 CRITICAL/MAJOR/MINOR。

文档版本：1.0.0 → 1.1.0（MINOR）；旧版本 1.0.0 登记为 SUPERSEDED。

## 8. 完整性复核（ocap-GROUP_C-4）

版本 1.2.0 → 1.3.0（MINOR），状态 DRAFT。方式：只读静态评审，以代码为准（git grep + 读代码），不采信 implementation_plan 自述；未安装依赖、未运行测试。上文 §1~§7 的结论保留；本节发现推翻其中"前端路由/接口静态核对已完成"的判断，详见 CR-011 ~ CR-014。

### 8.1 结论

- 后端（backend/）：MOD-001 ~ 014 全部落盘，核心业务（认证、清册、房屋关系、业委会席位、审批引擎、决议、报销、收入、台账、投票）可运行，实现质量较好。
- 未完整实现。三类问题：(1) 账号合并只有服务函数，没有任何触发入口（CR-011）；(2) Web 前端与小程序对后端的接口路径、请求体、`/me` 响应结构多处对不上（CR-012 ~ CR-015、CR-019、CR-020、CR-022），按现状 UI 无法完成决议表决发起、报销、投票/调查、管理端撤销认证等 Must Have 流程；(3) 收入表单条录入缺失、重复行不跳过、备用金核销会重复计入支出、季度/年度报表未接入定时任务（CR-016 ~ CR-018）。
- REQ-FUNC 68 条：IMPLEMENTED 38 / PARTIAL 28 / MISSING 2。US 73 条：IMPLEMENTED 41 / PARTIAL 29 / MISSING 3。
- 新增 finding：CRITICAL 4（CR-011 ~ 014）/ MAJOR 9（CR-015 ~ 023）/ MINOR 3（CR-024 ~ 026）（均 OPEN，本次只读评审不修复）。
- 编译检查：`python3 -m compileall -q backend` 退出码 0（仅语法层面，不代表可运行）。

### 8.2 REQ-FUNC 追溯矩阵

缩写：I = IMPLEMENTED，P = PARTIAL，M = MISSING。后端位置均在 `backend/apps/` 下；Web 为 `frontend/src/`，小程序为 `miniprogram/pages/`。

| REQ | 判定 | 实现位置（后端 文件:行 / 前端页面） | 说明 |
|---|---|---|---|
| 001 | I | accounts/views.py:85、services.py:148 / portal/Register.vue | 注册页未提供选填邮箱输入（后端支持） |
| 002 | I | accounts/views.py:156-190 / portal/Login.vue、WechatCallback.vue | |
| 003 | P | accounts/views.py:99,108 / miniprogram login/index.vue | 小程序只有验证码登录，无密码登录（CR-020） |
| 004 | I | accounts/views.py:139 / miniprogram login/index.vue | |
| 005 | I | accounts/services.py:176 / portal/Login.vue | 统一失败文案已落实 |
| 006 | I | accounts/services.py:167,176 / portal/Login.vue | |
| 007 | I | accounts/services.py:199,354 / portal/Login.vue、Me.vue | |
| 008 | I | accounts/views.py:156（`fast_login:1`）/ portal/Login.vue | 条件性可实现，见需求备注 |
| 009 | I | registry/models.py、registry/views.py | |
| 010 | I | registry/views.py:9 / portal/Units.vue、miniprogram units | |
| 011 | P | residency/views.py:35 | 仅微信登录、无手机号的用户在 Web 和小程序里都没有绑定手机号入口，认证返回 PHONE_REQUIRED（CR-019） |
| 012 | I | residency/views.py:35-55、AdminAppealDecision | |
| 013 | I | residency/services.py:14-43 | |
| 014 | I | residency/views.py:170-240 / portal/Units.vue | 小程序无同住人申请入口（需求未要求小程序） |
| 015 | I | identity/services.py:me（is_guest） | |
| 016 | P | accounts/services.py:308 / portal/Me.vue | Web 扫码首次登录未取微信昵称（回调未调用 web_userinfo，`get_or_create_wechat_user` 的 nickname 参数无人传入）（CR-026） |
| 017 | P | identity/services.py:81 / portal/Me.vue:126-135 | Web 注销请求不带 `phone`，后端校验失败；无手机号用户无法注销（CR-019） |
| 018 | I | registry/views.py:10-13 / admin/AdminRegistry.vue | |
| 019 | I | residency/views.py:63-92 / portal/Units.vue、admin/AdminAppeals.vue | 小程序申诉未带证明文件，必失败（CR-020） |
| 020 | I | residency/services.py:51 | |
| 021 | P | identity/views.py:31 | 后端有；Web、小程序无换绑入口；新号属他人账号时报 409 而非合并（CR-011、CR-019） |
| 022 | I | residency/views.py:250-281 / portal/Units.vue | |
| 023 | I | accounts/services.py:43,292 / portal/Me.vue | |
| 024 | P | accounts/services.py:143；identity/services.py:47 | 手机号唯一，但微信账号绑定已有手机号时不合并（CR-011） |
| 025 | I | accounts/views.py:269-330、jobs/management/commands/create_admin.py / admin/AdminLogin.vue | |
| 026 | M | identity/services.py:47-60 | `bind_phone` 遇已注册手机号直接 409，不合并（CR-011） |
| 027 | I | accounts/services.py:374 | |
| 028 | M | identity/services.py:62-79 | `change_phone` 同上（CR-011） |
| 029 | P | accounts/services.py:392、identity/services.py:124 | 规则函数已写，全仓库无调用方（CR-011） |
| 030 | P | residency/services.py:107 | 同上 |
| 031 | I | accounts/services.py:199-220,354 | |
| 032 | I | residency/views.py:181 | |
| 033 | I | registry 修改不触碰 Membership | |
| 034 | P | identity/services.py:105、identity/views.py:84 / admin/AdminMemberships.vue | 管理端调用 `/admin/memberships/{id}/revoke`，后端路由为 `/admin/memberships/revoke`（CR-015） |
| 035 | I | committee/views.py:51-61、committee/services.py:92 / admin/AdminSeats.vue | |
| 036 | P | identity/services.py:16-45 / portal/Home.vue、miniprogram index、me | 后端返回结构与前端读取不一致（CR-012） |
| 037 | P | resolutions/views.py:67-85 / portal/Resolutions.vue | Web 表单无附件上传、无截止时间（CR-022） |
| 038 | P | approval/services.py:25-120、resolutions/views.py:164-190 / portal/ResolutionDetail.vue | 半数同意模式在 Web 无法发起（缺 `vote_deadline` 输入）（CR-022） |
| 039 | I | resolutions/views.py:60-62,100-110 / portal/Resolutions.vue | |
| 040 | P | claims/views.py:83,110 / portal/Claims.vue、miniprogram claims | 前端调用 `POST /claims` 不存在（CR-013） |
| 041 | P | claims/services.py:10-25、ledger/services.py:33 | 核销关联的报销单重复计入支出（CR-017） |
| 042 | I | approval/views.py、approval/services.py:27 / admin/AdminFlows.vue | 修改流程请求方法不一致，见 CR-015 |
| 043 | P | polls/views.py:38-86 / portal/Polls.vue | 创建请求缺 `kind`，必失败；无 UI 可赋予业主代表（CR-014、CR-015） |
| 044 | P | polls/views.py:56-66 / portal/Polls.vue | 同上，无调查范围选择 |
| 045 | P | polls/views.py:154-226 / portal/PollDetail.vue、miniprogram polls/detail.vue | 前端 POST `/polls/{id}/response` 且字段为 `option_key`，后端为 `/responses` 与 `value`（CR-014） |
| 046 | P | polls/views.py:94-118,204-210 | 打分范围写成 0~100，需求为 1~5（CR-021）；前端不支持多题型 |
| 047 | P | polls/views.py:228-243、polls/services.py:21 | 发起人可在截止前看结果（CR-021） |
| 048 | P | income/views.py:104-137 / portal/Income.vue | 无单条录入接口；凭证附件未实现（CR-016） |
| 049 | I | income/views.py:200-300、income/services.py:13-66 | |
| 050 | P | ledger/services.py:69-121、jobs/views.py:56 | `run_due_jobs` 不含报表生成，仓库无定时配置（CR-018） |
| 051 | I | ledger/views.py:14,54 / portal/Reports.vue、miniprogram me | |
| 052 | I | committee/views.py:83-142 / admin/AdminSeats.vue | |
| 053 | I | committee/services.py:92-175（active_slot 约束、失效联动） | |
| 054 | I | approval/views.py:34-42 / admin/AdminFlows.vue | |
| 055 | P | approval/services.py:58-84、resolutions/views.py:101-140、claims/views.py:228-276、income/views.py | 后端齐全；Web 决议无撤回/重提按钮（CR-022） |
| 056 | P | committee/views.py:51（REPRESENTATIVE） | 管理端席位表单无"业主代表"选项（CR-015） |
| 057 | I | committee/views.py:AdminCommitteeConfigView / admin/AdminSeats.vue:68,113 | |
| 058 | P | claims/views.py:137-180 | 不支持"多退"（报销总额低于预借额时拒绝）；见 CR-017 |
| 059 | P | income/views.py:60-95 | 无重复行判定；错误率超 2% 整体拒绝而非跳过（CR-016） |
| 060 | I | resolutions/services.py:38-70、jobs/management/commands/run_due_jobs.py:21 | |
| 061 | P | committee/services.py:176、residency/services.py:107 | 合并未接线（CR-011） |
| 062 | I | approval/services.py:27-40,108 | |
| 063 | I | approval/services.py:105（审批人现任校验） | |
| 064 | I | accounts/services.py:239-282、accounts/views.py:36 | |
| 065 | P | miniprogram login/index.vue:45、profile-setup/index.vue | 触发条件读 `profile_completed`，后端从不返回（CR-020） |
| 066 | I | approval/services.py:36-40,108 | |
| 067 | P | core/user_refs.py、polls/apps.py:14-15、resolutions/apps.py | 登记了冲突策略，但合并未接线；未写 `MERGE_ANSWER_DISCARDED` 审计（CR-011） |
| 068 | I | accounts/views.py:331 / admin/AdminUsers.vue:99 | |

### 8.3 US 追溯矩阵

Must Have 故事均已逐条对照 AC（Given/When/Then）；`US-032/033/034/064` 为 Should Have。

| US | 判定 | 对应 REQ | 未满足的 AC 或缺口 |
|---|---|---|---|
| 001 | I | 001 | |
| 002 | I | 002 | |
| 003 | P | 003 | AC-003-02：小程序无密码登录入口 |
| 004 | I | 004 | |
| 005 | I | 005 | |
| 006 | I | 006 | |
| 007 | I | 007 | |
| 008 | I | 008 | |
| 009 | I | 023 | |
| 010 | P | 024 | 三入口同一账号的合并路径缺失 |
| 011 | I | 025 | AC-011-05 管理端入口齐全（8 个导航项） |
| 012 | M | 026 | AC-012-01、AC-012-04：绑定已属他人的手机号时不合并，返回 409 |
| 013 | I | 027 | |
| 014 | M | 028 | 同 US-012 |
| 015 | P | 029 | 规则已写，未触发 |
| 016 | P | 030、061 | AC-016-05~07 同上 |
| 017 | I | 031 | |
| 018 | I | 009 | |
| 019 | I | 018 | |
| 020 | I | 010 | |
| 021 | P | 011 | 微信用户无绑定手机号入口 |
| 022 | I | 012 | |
| 023 | I | 013 | |
| 024 | I | 014、032 | |
| 025 | I | 015 | |
| 026 | I | 019、013 | 小程序申诉不带证明（需求不要求小程序） |
| 027 | I | 020 | |
| 028 | P | 021 | 无 UI；新号属他人账号不合并 |
| 029 | I | 022 | |
| 030 | P | 016 | Web 扫码首次登录不取微信昵称（AC-030-03） |
| 031 | P | 017 | Web 注销请求缺 `phone`；无手机号用户无法注销 |
| 032 | I | NFUNC-001 | |
| 033 | I | NFUNC-002 | |
| 034 | I | NFUNC-003 | |
| 035 | I | 033 | |
| 036 | P | 034 | 管理端撤销请求路径与后端不一致（CR-015） |
| 037 | I | 035 | |
| 038 | I | 052 | |
| 039 | I | 053 | |
| 040 | I | 057 | |
| 041 | P | 036 | `/me` 结构不一致（CR-012） |
| 042 | P | 056 | 管理端无业主代表选项 |
| 043 | I | 054、042 | |
| 044 | P | 037 | Web 无附件、无截止时间输入 |
| 045 | I | 038 | |
| 046 | P | 038、060 | Web 无法设置表决截止时间 |
| 047 | I | 039 | |
| 048 | P | 055 | 决议侧无撤回/重提 UI |
| 049 | P | 040 | 前端接口不通，且无导航入口（CR-013） |
| 050 | P | 041、062 | 接口不通；备用金/报销重复计入（CR-017） |
| 051 | P | 058 | 无核销 UI；多退场景被拒；重复计入 |
| 052 | P | 043 | 创建请求缺 `kind`；无业主代表可选 |
| 053 | P | 043、046 | 后端判定正确（polls/services.py:60）；UI 链路不通 |
| 054 | P | 044 | 同 US-052 |
| 055 | P | 046 | AC-055-02：打分 0~100 而非 1~5；前端无多题型 |
| 056 | P | 045 | 提交路径与字段不一致 |
| 057 | P | 047 | 截止前发起人可见结果；前端字段不一致 |
| 058 | M | 048 | AC-058-01、AC-058-08：无单条录入接口；凭证附件（AC-058-07）无实现 |
| 059 | P | 048、059 | AC-059-02 重复行不跳过；AC-059-03/05 错误率 >2% 整体拒绝 |
| 060 | I | 049 | |
| 061 | P | 050 | 未接入定时任务 |
| 062 | P | 050 | 后端 `POST /ledger/reports/generate` 可用；Web 用户端无入口，管理端按钮调用不存在的 `/admin/ledger/reports` |
| 063 | I | 051 | |
| 064 | I | NFUNC-004 | |
| 065 | I | 060 | |
| 066 | P | 061 | 同 US-016 |
| 067 | I | 062 | |
| 068 | I | 063 | |
| 069 | I | 064 | |
| 070 | P | 065 | AC-070-01：触发条件永不成立 |
| 071 | I | 066 | |
| 072 | P | 067 | 同 US-012 |
| 073 | I | 068 | |

### 8.4 前端可达性

| 功能 | Web 入口 | 小程序入口 | 判定 |
|---|---|---|---|
| 登录/注册 | `/login` ↔ `/register` 互链 | pages/login | 小程序缺密码登录 |
| 房屋认证/申诉/同住人 | PortalLayout"我的房屋" | index、me 按钮 → units | 小程序申诉缺证明文件 |
| 决议 | 导航"决议" | tabBar"决议" | 可达 |
| 投票/调查 | 导航"投票/调查" | tabBar"投票" | 可达但接口不通（CR-014） |
| 报销/备用金 | **无**：路由 `/claims` 已注册，PortalLayout、Home 均无链接 | index、me 按钮 → claims | Web 不可达（CR-013）；小程序可达 |
| 收入表 | **无**：路由 `/income` 已注册，无任何链接 | 需求未要求 | Web 不可达（CR-016） |
| 财务报表 | 导航"财务报表" | me 页内嵌 | 可达；手动重新生成报表无用户端入口 |
| 审批待办 | 导航"待办" | index 内嵌 | 可达 |
| 个人资料/密码/邮箱/注销 | 导航"个人中心" | profile-setup（仅昵称） | 手机号绑定、换绑 Web 和小程序都没有入口（CR-019） |
| 管理端 | AdminLayout 8 项导航全部可达 | — | 页面可达；"业主代表"赋予选项缺失、合并按钮路径不存在（CR-015） |
| 业主代表赋予 | 无选项 | — | Web 管理端缺 |

需求要求小程序具备的功能（REQ-FUNC-003/004/045/065）：004 可用；003 缺密码登录；045 页面可达但接口不通；065 页面不会被触发。

### 8.5 MOD / IFC 对齐

- MOD-001 ~ 014、021 的目录与职责均存在，MOD-020、022 存在但与后端契约不一致（见 CR-012 ~ CR-014）。MOD-014 只有 `run_due_jobs` 与 `create_admin`，缺报表生成任务（CR-018）。
- 路由与签名偏离（CR-025）：
  - IFC-120：`/reports`、`/reports/{id}`、`/reports/generate` 实际为 `/ledger/reports...`。
  - IFC-110：`POST /income/sheets`（JSON 单条/多条录入）不存在；IFC-111/112 实际挂在 `/admin/income/sheets...`，且这些端点用的是业委会成员权限而非管理员权限；`ImportReport` 结构、`dry_run` 与设计不符。
  - IFC-090/100/101/102：流程字段设计为 `flow_id`，实现为 `approval_flow_id`；核销入参为 `advance_id` + `reimbursement_ids`，与设计的 `settles_advance_id` 模型不同。
  - IFC-132：答案结构为 `{question_id, value}`，打分范围偏离；IFC-133 截止前设计为一律 403 `RESULT_NOT_PUBLIC`，实现为 409 `NOT_CLOSED` 且发起人例外。
  - IFC-140：缺 `--now`、`--only`，缺 `generate_reports`、`purge_temp_attachments` 任务；另增 `jobs/*` HTTP 触发端点（管理员权限），设计未列。
  - IFC-027 响应以 `is_new` 触发头像昵称页，设计如此，但小程序实现读的是 `profile_completed`。

### 8.6 约定检查

- 迁移：全部 14 个 app 的 `0001_initial.py` 由 `makemigrations` 生成（CR-002 已记）。commit c275c46 新增的 3 个 0003 迁移（claims、income、ledger）文件头为 `# Generated by Django 6.0.6 on 2026-11-08 04:39`，包含 `RenameIndex` 的 Django 哈希索引名（如 `claims_clai_status_2fd679_idx`）和 `AlterModelOptions`，判定为 makemigrations 自动生成，不是手写。每个文件只涉及单个 app，满足"按 app 划分"，但违反"手写、禁止 makemigrations 产物"（CR-023）。
- 凭据：未发现硬编码凭据；外部凭据均从环境变量读取。`config/settings.py:7` 的 `SECRET_KEY` 有弱默认值、`ALLOWED_HOSTS` 默认 `*`（CR-024）。
- 外部服务：`git grep` 未在 `apps/integrations` 之外发现 requests/urllib/smtplib/阿里云 SDK 调用，符合约束。
- 仓库中没有 `deploy/systemd/`（画像 P3 列出），定时任务无调度配置（CR-018）。

### 8.7 五维评分（0–10）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 4/10 | 7/10 | 7/10 | 6/10 | 4/10 |

依据：后端服务层逻辑扎实，但账号合并未接线、核销重复计入，前端与后端契约多处不符，正确性评 4；权限、限流、凭据、审计较好，评 7；列表分页与唯一约束尚可，无明显 N+1，评 7；分层清晰但路由命名偏离设计，评 6；前端无自动化测试，且前后端契约问题没有被测试发现，评 4（低于 6，对应 CR-026）。综合约 5.6。

### 8.8 新增 finding

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-011 | CRITICAL | `identity/services.py:47-79,124`；`accounts/services.py:143` | 账号合并只有 `merge_accounts` 等函数，全仓库没有调用方。`bind_phone`、`change_phone` 遇已注册手机号直接 409。REQ-FUNC-026/028 缺失，029/030/061/067 无法触发；US-012、014 缺失，US-015、016、066、072 部分。管理端 `mergeUsers` 调用的 `/admin/users/merge` 路由也不存在。 | FIXED（§9.1） |
| CR-012 | CRITICAL | `identity/services.py:16-45` 对比 `frontend/src/portal/Home.vue:5`、`Polls.vue:48`、`Resolutions.vue:46`、`stores/auth.js:9-10`、`miniprogram/pages/index/index.vue`、`me/index.vue` | `/me` 实际返回 `{profile, identities:{is_guest, units, committee, labels}}`，前端按"中文标签数组"读取 `identities`，`.join`/`.some` 会在渲染时抛 TypeError，首页和业委会身份判断失效（发起决议/调查的控件不显示）。小程序同样。 | FIXED（§9.1） |
| CR-013 | CRITICAL | `frontend/src/shared/api.js:60-62`、`miniprogram/utils/api.js:21-22`、`portal/Claims.vue`、`PortalLayout.vue:7-12` | 报销/备用金链路不通：前端 `POST /claims`（后端仅有 `/claims/reimbursements`、`/claims/advances`，`/claims` 只支持 GET）、`GET /claims/mine`（后端用 `scope=mine`）、`/settlements`（后端 `/claims/settlements`）。请求缺 `occurred_on`、`invoice_ids`、`expected_usage`、`expected_settle_on` 等必填字段，无核销界面；Web 用户端没有 `/claims` 入口。US-049、050、051 不可用。 | FIXED（§9.1） |
| CR-014 | CRITICAL | `portal/Polls.vue:66-74`、`PollDetail.vue:50-60`、`miniprogram/utils/api.js:20`、`miniprogram/pages/polls/detail.vue` 对比 `polls/views.py:38-86,154-226` | 投票/调查链路不通：创建请求缺必填的 `kind`，题目用 `text`/`{key,label}` 而后端要 `title`/`qtype`/字符串选项，无调查范围、题型、必答设置；作答请求 `POST /polls/{id}/response` 对比后端 `/responses`，字段 `option_key` 对比后端 `value`。US-052 ~ 056 经 UI 不可用。 | FIXED（§9.1） |
| CR-015 | MAJOR | `frontend/src/shared/api.js:116,128-132`、`admin/AdminSeats.vue:28-31`、`AdminFinance.vue:53-66` | 管理端：撤销认证调用 `/admin/memberships/{id}/revoke`（后端为 `/admin/memberships/revoke`，体为 user_id+unit_id）；修改审批流程用 PATCH（后端 PUT）；生成报表调用不存在的 `/admin/ledger/reports`（且后端生成接口要求业委会成员而非管理员）；收入表列表用管理员令牌访问成员权限的 `/admin/income/sheets` 会被拒；席位表单无"业主代表"选项，US-042 不可用。 | FIXED（§9.1） |
| CR-016 | MAJOR | `income/urls.py`、`income/views.py:60-95,104-137`、`portal/Income.vue`、`PortalLayout.vue` | 收入表：无单条录入接口（US-058，AC-058-01/-08）；凭证附件未链接（REQ-FUNC-048）；导入不判重复行（AC-059-02），错误率超 2% 整体拒绝而非跳过错误行（AC-059-03/-05）；Web 无 `/income` 导航入口。 | FIXED（§9.1） |
| CR-017 | MAJOR | `claims/services.py:10-25`、`claims/views.py:137-180`、`ledger/services.py:33` | 备用金核销：预借审批通过即入账，报销单各自审批通过也入账，核销单再入账差额，关联报销单未作废，支出被重复计入（预借 1000、报销 1200 时合计 2400，应为 1200）；报销总额低于预借额时直接拒绝，未实现"多退"登记。违反 REQ-FUNC-041、058，影响财务报表。 | FIXED（§9.1） |
| CR-018 | MAJOR | `jobs/management/commands/run_due_jobs.py`、`jobs/views.py:56`、仓库无 `deploy/systemd/` | 季度/年度报表自动生成（REQ-FUNC-050，US-061）：`run_due_jobs` 不调用 `LedgerService.generate_due`，只有需管理员手动触发的 HTTP 端点；IFC-140 的 `--now`/`--only` 与 `generate_reports`、`purge_temp_attachments` 任务缺失；仓库中没有 systemd 定时器模板。 | FIXED（代码侧，§9.1）；systemd 定时器模板交 devops-engineer（`deploy/systemd/` 无写权限） |
| CR-019 | MAJOR | `portal/Me.vue`（无换绑/绑定）、`Me.vue:126-135`、`identity/views.py:42-50`、`residency/views.py:45` | 手机号绑定/换绑在 Web 和小程序都没有入口：仅微信登录的用户无法完成清册认证（PHONE_REQUIRED），也无法注销；Web 注销请求不带 `phone`，后端校验失败。US-021、028、031 部分实现。 | FIXED（§9.1） |
| CR-020 | MAJOR | `miniprogram/pages/login/index.vue`、`units/index.vue:93-95`、`login/index.vue:45` | 小程序：无密码登录（AC-003-02）；登录页提示"未注册手机号将自动创建账号"与后端 404 行为矛盾（AC-003-05）；头像昵称设置页以 `me.profile_completed === false` 触发，后端不返回该字段（登录响应是 `is_new`），页面不可达（AC-070-01）；申诉不带证明文件会 400。 | FIXED（§9.1） |
| CR-021 | MAJOR | `polls/views.py:204-210,236-240` | 打分题范围写成 0~100，需求为 1~5（AC-055-02）；发起人可在截止前读取结果，需求与设计均要求截止后才公开（REQ-FUNC-047，IFC-133）。 | FIXED（§9.1） |
| CR-022 | MAJOR | `portal/Resolutions.vue:27-64`、`ResolutionDetail.vue`、`api.js:45-52` | 决议 Web 界面：创建表单无 `vote_deadline`，选"半数同意"流程必然 400，无附件上传；无撤回、重新提交按钮（`resubmit` 只传流程 id，后端需要标题和正文）。US-044、046、048 部分。 | FIXED（§9.1） |
| CR-023 | MAJOR | `claims/migrations/0003_*.py`、`income/migrations/0003_*.py`、`ledger/migrations/0003_*.py` | 三个 0003 迁移由 makemigrations 生成（文件头 `Generated by Django 6.0.6 on 2026-11-08 04:39`，哈希索引名），违反画像 P6/P8"手写、禁用 makemigrations 产物"。内容仅为索引重命名与字段选项，建议改为手写等价迁移并保持依赖链。与 CR-002 同类，合并处理。 | FIXED（§9.1；CR-002 的 0001/0002 仍遗留） |
| CR-024 | MINOR | `config/settings.py:7,9` | `DJANGO_SECRET_KEY` 缺省回退为固定弱值，`ALLOWED_HOSTS` 缺省为 `*`；缺少非 DEBUG 时拒绝启动的检查。非凭据硬编码，但部署环境漏配时有风险。 | FIXED（§9.1） |
| CR-025 | MINOR | 见 §8.5 | 路由与签名偏离设计（IFC-110/111/112/120/132/133/140）；应在 module_design 回写或代码对齐。 | OPEN（未改：属架构决定，原因见 §9.1） |
| CR-026 | MINOR | `frontend/tests` 不存在，`miniprogram/tests/` 仅有 `setup.js`；`accounts/views.py:166-181` | 前端无测试，因此上述契约问题未被发现；Web 微信扫码首次登录未取微信昵称（REQ-FUNC-016）。 | 昵称已修（§9.1）；前端测试留给 test-engineer，头像转存未做；状态 OPEN（部分） |

### 8.9 对前述结论的影响

- §1 的"可重新进入 GROUP_D"结论只适用于后端接口层。Web 与小程序的 Must Have 流程（CR-011 ~ CR-014）不能视为完成；CR-001 的"已做路由/接口静态核对"表述应更正为"路由已注册，接口契约未核对"。
- 新增 CRITICAL 4 条，按 §J 标准，MOD 全部实现但存在未解决 CRITICAL，建议回流 GROUP_C 修复后再复跑 GROUP_D。
- 遗留 MAJOR 现为 3 条旧的（CR-001 ~ 003）+ 9 条新的（CR-015 ~ CR-023，其中 CR-023 与 CR-002 同类），超过 3 条，须逐条在修复计划中写明处理时机；本次为只读评审，未修复。

本次评审未修改任何产品代码、测试代码或其他文档。

## 9. 缺陷修复（ocap-GROUP_C-5，版本 1.3.0 → 1.4.0）

依据用户决定（2026-11-08，上报处理 Q1=A）与 `REWORK_AUTHORIZED`，修复 §8.8 中 CRITICAL 4 条（CR-011 ~ 014）、MAJOR 9 条（CR-015 ~ 023）及可改的 MINOR。计划见 implementation_plan 1.3.0 §11。旧版本 1.3.0 请 PM 登记为 SUPERSEDED。

### 9.1 逐条修复记录

| CR | 状态 | 修复位置（文件:行） | 根因与修复说明 |
|---|---|---|---|
| CR-011 | FIXED | `identity/services.py:48-110`（`bind_phone`、`change_phone`、`_merge_by_phone`）、`identity/services.py:148`（`merge_accounts` 增 actor/trigger）、`identity/views.py:16`（`_merge_response`，合并后签发主账号新令牌）、`polls/services.py:8,31` + `polls/apps.py`、`resolutions/services.py:36` + `resolutions/apps.py`（作答/表决/参与人合并策略）、`accounts/services.py`（`fill_empty_profile_from` 先释放 `verified_email` 唯一列）、`accounts/services.py`（`session_kind_of`） | 合并函数无调用方，绑定/换绑遇到已注册手机号直接 409。现改为：验证码通过后若手机号属于其他账号，则在一个事务内按 id 升序加锁，主账号=手机号原账号，调用既有注册表合并（身份取高、席位取高、微信身份并入、待办并入）；两账号均已作答同一投票/调查/表决 → 保留主账号、丢弃副账号并写 `MERGE_ANSWER_DISCARDED`，仅副账号作答 → 并入（原注册策略 `delete_secondary` 会误删无冲突作答，已改为自定义处理）；响应 `{merged, phone, token, user}`，旧令牌失效。管理端 `mergeUsers` 入口无需求依据，删除。REQ-FUNC-026/028 现可达，029/030/061/067 随之可触发。 |
| CR-012 | FIXED | `frontend/src/stores/auth.js:9-14`、`portal/Home.vue:3-5`、`portal/PortalLayout.vue`、`portal/Resolutions.vue`、`Polls.vue`、`Claims.vue`、`Income.vue`、`Reports.vue`；`miniprogram/pages/index/index.vue:3-5`、`pages/me/index.vue:3-5` | module_design IFC-070 规定 `identities` 为对象 `{is_guest, units, committee, labels}`，后端符合设计，故只改前端读取：标签读 `identities.labels`，委员/主任判断读 `identities.committee.position`（`CHAIR/VICE_CHAIR/MEMBER`），昵称/手机号读 `profile`。后端未改。 |
| CR-013 | FIXED | `frontend/src/shared/api.js:62-75`、`portal/Claims.vue`（全文重写）、`portal/PortalLayout.vue:10`、`portal/Home.vue`；`miniprogram/utils/api.js:30-38`、`pages/claims/index.vue` | 前端改调 `POST /claims/reimbursements`、`/claims/advances`、`/claims/settlements`、`GET /claims?scope=mine\|todo`，补 `occurred_on`、`invoice_ids`（先上传 INVOICE 附件）、`expected_usage`、`expected_settle_on`、`approval_flow_id`；新增核销 UI（选已通过未核销备用金与报销单、显示差额与多退/少补）；Web 导航与首页增加"报销/备用金"入口；小程序同样处理（含 `uni.uploadFile` 上传发票）。 |
| CR-014 | FIXED | `frontend/src/shared/api.js:109`、`portal/Polls.vue`、`portal/PollDetail.vue`；`miniprogram/utils/api.js:29`、`pages/polls/detail.vue` | 创建请求带 `kind`、`survey_scope`、题目 `title/qtype/required/options`（字符串选项）、ISO 截止时间；作答改 `POST /polls/{id}/responses`，体为 `[{question_id, value}]`（多选为数组）；详情页按题型渲染、截止后展示后端汇总结果结构。 |
| CR-015 | FIXED | `frontend/src/shared/api.js:143,152`、`admin/AdminMemberships.vue`、`admin/AdminSeats.vue`、`admin/AdminFinance.vue`、`approval/views.py:90`（后端流程 PUT 支持 `is_active`） | 撤销认证改 `POST /admin/memberships/revoke {user_id, unit_id}`（并修正表格列读取 `row.user.id`/`unit_id`）；流程更新改 PUT；席位表单增"业主代表"并支持任意职位变更，配置字段改为后端的 `cap_*`/`term_months_*`；管理端财务页去掉不存在的 `/admin/ledger/reports` 与成员权限的 `/admin/income/sheets`（收入表与报表生成属业委会成员权限，在用户端使用）。另顺手修复 `identity/views.py:8` 缺失的 `mask_phone` 导入（管理端房屋关系列表原会 500）。 |
| CR-016 | FIXED | `income/views.py:214`（`AdminSheetListView.post` 逐条录入）、`:245`（`_voucher_ids`）、`:78-120`（导入跳过重复/错误行）、`portal/Income.vue`、`PortalLayout.vue:11` | 新增 `POST /admin/income/sheets`（`records` 英文字段、`voucher_ids` 凭证附件、创建 DRAFT 收入表）；PATCH 支持 `voucher_ids`；导入不再因错误率 >2% 整体拒绝，改为按 AC-059-02/03/05 跳过重复行（文件内及与已有 PENDING/EFFECTIVE 记录）与错误行并返回行号，全部跳过时 200 且不建表；Web 增收入表导航（仅业委会成员显示）。 |
| CR-017 | FIXED | `claims/services.py:30-45`（`_approve_settlement`）、`claims/services.py:64-72`（核销被拒/撤回释放关联）、`claims/views.py`（取消"报销总额不得低于预借"，核销不可重提）、`ledger/services.py:34-40`（`allow_negative`） | 核销审批通过时作废关联凭票报销单的台账，只记差额（实际花费合计 − 预借额），多退为负值冲减支出：预借 1000/报销 1200 → 支出合计 1200（原 2400），预借 1000/报销 800 → 800。核销被拒/撤回时释放预借与报销单的 `settlement_id`，可重新核销。已用临时脚本验证（不入仓库）。 |
| CR-018 | FIXED（代码侧） | `jobs/management/commands/run_due_jobs.py:27`、`ledger/services.py:110`（`generate_due` 重写） | `run_due_jobs` 现在调用 `LedgerService.generate_due`，生成已结束的上一季度和上一年度报表（原实现用"每月 28 日"近似季末，实际不会命中）；幂等。`--now/--only`、`generate_reports`/`purge_temp_attachments` 属 CR-025 偏离，未改。**systemd 定时器模板：`deploy/systemd/` 不在 software-developer 写权限内，交 devops-engineer**（见 implementation_plan §11.5）。 |
| CR-019 | FIXED | `frontend/src/portal/Me.vue`（绑定/换绑手机号、注销带 `phone`、密码 `password_confirm`、性别 0/1/2、邮箱验证）、`frontend/src/shared/api.js:24-31`；`miniprogram/pages/phone/index.vue`（新增）、`pages.json`、`pages/me/index.vue` | 增加绑定与换绑手机号 UI，合并成功后换用返回的新令牌；注销请求带 `phone`+`code`；顺带修复同页的契约错误：改密 `PUT /me/password` 且字段为 `password_confirm`、邮箱验证不再需要脱敏邮箱（后端 `accounts/views.py:276` 缺省取本人邮箱）。 |
| CR-020 | FIXED | `miniprogram/pages/login/index.vue:56-60`（`is_new` 触发资料页）、`:73`（密码登录）、`pages/units/index.vue:101-118`（申诉带证明）、`pages/me/index.vue`（资料页入口）、`utils/http.js`（`upload`） | 小程序补密码登录；去掉与后端 404 行为矛盾的"自动创建账号"文案；资料页触发条件改为登录响应的 `is_new === true`（后端从不返回 `profile_completed`），并在"我的"页提供入口；申诉先 `uni.chooseImage` + `uni.uploadFile` 上传证明，再以 `proof_ids` 提交（原 `reason` 字段后端不接受）。同时修正清册选项响应结构（`options[]`）与 tabBar 页面跳转（`switchTab`）。Web 申诉同样改为 `proof_ids`（`portal/Units.vue`、`api.js:38`），Web 清册选项结构一并修正。 |
| CR-021 | FIXED | `polls/views.py:209`（打分 1~5）、`polls/views.py:237`（截止前一律不可见） | 打分范围 0~100 → 1~5；结果接口去掉发起人/管理员的截止前例外。错误码保持 409 `NOT_CLOSED`（IFC-133 为 403，见 CR-025）。 |
| CR-022 | FIXED | `portal/Resolutions.vue`（`vote_deadline` 日期选择、附件上传、半数同意流程提示）、`portal/ResolutionDetail.vue`（撤回、重新提交，附件名读 `name`）、`api.js:50-58` | 创建表单按所选流程模式显示并提交 `vote_deadline`（ISO），支持上传 RESOLUTION 附件；详情页发起人可撤回，被拒/已撤回可修改后重新提交（带标题、正文、流程、截止时间）；仅主任/副主任看到发起按钮。 |
| CR-023 | FIXED | `claims/migrations/0003_*.py`、`income/migrations/0003_*.py`、`ledger/migrations/0003_*.py` | 去掉 `Generated by Django 6.0.6` 文件头，手写；**文件名、迁移名、依赖、operations 未变**（脚本比对 AST 与原文件完全一致，仅 docstring 差异），对数据库的效果与已应用版本相同；未新增迁移。`makemigrations --check --dry-run`（Django 5.2.19）→ `No changes detected`。 |
| CR-024 | FIXED | `config/settings.py:7-20`、`config/test_settings.py:1-6` | `DJANGO_SECRET_KEY` 缺失时不再回退固定值：DEBUG 或显式 `DJANGO_ALLOW_EPHEMERAL_SECRET=1`（仅测试设置）下用进程内随机值，否则抛 `ImproperlyConfigured` 拒绝启动；`ALLOWED_HOSTS` 默认改为 `localhost,127.0.0.1`。**部署注意**：测试机 `.env` 必须有非空的 `DJANGO_SECRET_KEY`（P7 列有该键，值未核验）。 |
| CR-025 | OPEN | — | 路由/签名偏离 module_design（IFC-110/111/112/120/132/133/140）。属架构层契约，需 system-architect 回写 module_design 或另立变更；本次未改，以免与现有测试和前端契约形成新的不一致。 |
| CR-026 | OPEN（部分） | `accounts/views.py:178-190`（Web 扫码首次登录取昵称，`[CODE: integrations/wechat.py:133]`） | 昵称已修；头像转存需要新增外部下载调用，P11 无出处，未做（`TODO(IFC-027): [UNSOURCED]`）；前端自动化测试按约束留给 test-engineer。 |

### 9.2 自验证结果

```
> python3 -m compileall -q backend                         → 退出码 0
> (cd backend && python manage.py check --settings=config.test_settings)
System check identified no issues (0 silenced).
> (cd backend && python manage.py test --settings=config.test_settings)    # venv Django 5.2.19
Ran 120 tests ... FAILED (failures=2)       # 118 通过；2 个为预期变更（见 §9.3）
> (cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings)
No changes detected
> (cd frontend && npm run build -- --base=/ocap/)
✓ built in 29.59s
> (cd miniprogram && npx vitest run --passWithNoTests)
No test files found, exiting with code 0
```

另：用 `@vue/compiler-sfc` 对 7 个改动/新增的小程序 `.vue` 文件做模板与脚本编译检查，全部通过；小程序未做 uni-app 构建（本机无 HBuilderX/uni 构建环境），属"未验证"。临时验证脚本（8 个场景：绑定合并、绑定不合并、换绑合并及作答冲突、核销多补/多退/拒绝后重核销、`generate_due` 幂等、收入逐条录入与导入跳过）放在会话临时目录，**未入库**，全部通过（唯一一次失败为脚本自身的断言错误：草稿状态的表不参与重复比较，行为符合 OQ-12）。

### 9.3 预期变更的现有测试（未改任何测试文件，交 test-engineer）

| 测试 | 原因 |
|---|---|
| `tests/integration/test_finance_polls_api.py::IncomeTests::test_import_row_error_ratio` | 期望"错误率 >2% → 400 `IMPORT_ROW_ERRORS`"。按 REQ-FUNC-059 / AC-059-03、05 改为跳过错误行并 201 返回 `import_summary`（imported=40、failed=3）。 |
| `tests/unit/test_domain_rules.py::IncomeParseRuleTests::test_row_error_ratio_over_2_percent` | 同上，`_parse_rows` 不再抛 `IMPORT_ROW_ERRORS`，返回 `records/errors/total/row_numbers`。 |

两条均源于需求与旧实现冲突（旧阈值 2% 整体拒绝已被 Q93 取代）；其余 118 个现有用例未改且通过。若 PM 要求"现有用例零失败"，需 test-engineer 先按 AC-059-02/03/05 更新这两条再复跑 GROUP_D。建议新增用例：绑定/换绑合并（含作答冲突）、核销三种差额、`generate_due`、逐条录入、导入重复行、附件下载（管理员）、`SECRET_KEY` 缺失拒绝启动。

### 9.4 五维评分与统计（本次修复范围）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 7/10 | 8/10 | 7/10 | 6/10 | 5/10 |

- Correctness 7：后端契约与前端已对齐，主链路经脚本验证；扣分点是 Web/小程序仍无运行时（浏览器/微信）验证。
- Testability 5（<6）：前端无自动化测试，本次未能补（按约束归 test-engineer）；对应遗留 CR-026（前端测试）与上面建议用例。
- 问题统计：CRITICAL 4（CR-011 ~ 014）全部 FIXED；MAJOR 9（CR-015 ~ 023）全部 FIXED（CR-018 代码侧已修，systemd 模板交 devops-engineer）；MINOR 3：CR-024 FIXED，CR-025 OPEN，CR-026 部分 OPEN。
- 遗留 MAJOR（旧）CR-001（前端未运行时验证；现已能 `npm run build`，仍缺组件测试，建议 GROUP_D 补）、CR-002（0001 迁移为生成产物，已上线不改）、CR-003（Django 版本偏差：本次已用 5.2.19 验证，可视为关闭）。
- 新发现并顺手修复（非 §8.8 条目）：管理端房屋关系列表 `mask_phone` 缺导入；注册合并策略 `delete_secondary` 误删无冲突作答；`verified_email` 唯一列在合并时会冲突；前端改密/邮箱验证/性别/清册选项/微信回调/管理端申诉决定等多处契约不符。
