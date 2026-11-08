<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-08T13:43:16+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/code_review_report.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划（PHASE_05 SOFTWARE_DEVELOPMENT）

## 1. 范围与结论

按 `module_design.md` 实现 MOD-001 ~ MOD-022：

- 后端：14 个 Django app，覆盖核心能力、账号、业主清册、房屋关系、业委会、身份合并、审批、决议、报销/备用金、收入、台账、投票/调查、定时任务。
- Web：`frontend/`（Vue 3 + Vite + Element Plus + Pinia），含用户端 14 个路由与管理端 9 个路由。
- 小程序：`miniprogram/`（uni-app + Pinia），含登录、资料完善、首页、房屋、决议、投票、报销、我的共 10 个页面。

实现方式为全新代码（greenfield），代码写入画像 P3 的 `backend/`、`frontend/`、`miniprogram/`。未执行 npm 安装、构建与前端测试（用户约束：不安装依赖、不改全局环境），详见 §8。

## 2. 文件改动清单（按依赖拓扑）

### 2.1 工程与配置

| 文件 | 说明 |
|---|---|
| `backend/manage.py`、`backend/config/settings.py`、`config/test_settings.py`、`config/urls.py` | 项目入口、环境变量配置、SQLite 测试库与外部服务替身、`api/v1/` 路由聚合 |
| `backend/requirements.txt` | Django / DRF 运行依赖 |
| `frontend/package.json`、`vite.config.js`、`index.html`、`src/main.js`、`src/App.vue` | Web 工程骨架与开发代理 |
| `miniprogram/package.json`、`vite.config.js`、`main.js`、`App.vue`、`pages.json`、`manifest.json` | 小程序工程骨架与页面注册 |

### 2.2 core / integrations

| 文件 | 说明 |
|---|---|
| `apps/core/models.py` | AuditLog / Attachment / SystemConfig / RateLimit / Lockout / JobRun |
| `apps/core/errors.py` | 统一错误体 `{code,message,details?}` 与 DRF 异常映射（ADR-021） |
| `apps/core/audit.py`、`config.py`、`ratelimit.py`、`user_refs.py`、`attachments.py`、`permissions.py`、`masking.py`、`serializers.py`、`views.py`、`urls.py` | 审计白名单、系统配置默认值、限流与锁定、用户引用注册表与合并分发、附件策略、权限类、脱敏、附件上传下载、配置读取 |
| `apps/core/money.py` | 金额统一两位小数序列化（新增） |
| `apps/core/checks.py` | 启动检查：短信 TTL、验证码位数、审计保留期、用户引用注册 |
| `apps/integrations/wechat.py`、`sms.py`、`aliyun_sms.py`、`email.py`、`fakes.py` | 微信、短信、邮件适配器与测试替身；阿里云 SDK 缺失时返回 `SDK_MISSING` |

### 2.3 账号与组织

| 文件 | 说明 |
|---|---|
| `apps/accounts/*` | User / AdminAccount / WeChatIdentity / AuthToken / VerificationCode / WeChatLoginState / LoginTicket；注册、三类登录、微信登录与 Web 扫码、票据交换、密码、资料、头像、邮箱验证、管理员账号 |
| `apps/accounts/authentication.py` | Bearer Token 认证（IDLE / EXTENDED 过期） |
| `apps/registry/*` | RegistryUnit / RegistryPhone；选项级联、管理员 CRUD、手机号维护、xlsx/csv 导入 |
| `apps/residency/*` | Membership（HEAD/OWNER/RESIDENT，唯一 active_slot）、Appeal、ResidentApplication；认证、自动升级首位户主、撤销与接任、同住人申请与审批、退出 |
| `apps/committee/*` | CommitteeConfig、Seat；席位赋予/变更/撤销/到期、人数与任期配置、产权变化联动 |
| `apps/identity/*` | `/me` 聚合、绑定/换绑手机号、注销、房屋关系撤销、账号合并 |

### 2.4 审批与业务

| 文件 | 说明 |
|---|---|
| `apps/approval/*` | ApprovalFlow / FlowApprover / ApprovalInstance / ApprovalAction；DESIGNATED 与 HALF_MAJORITY、提交校验、撤回/重提、防自批、回调注册 |
| `apps/resolutions/*` | Resolution / Vote；发起（主任/副主任）、详情权限、公开/我的/待表决、表决与到期判定 |
| `apps/claims/*` | Claim（报销/备用金/核销）、附件策略、提交/撤回/重提、管理员列表 |
| `apps/income/*` | IncomeSheet / IncomeRecord；CSV/xlsx 导入（≤5MB、≤5000 行、错误率 >2% 拒绝）、记录编辑、提交/重提/撤回/作废、合计重算 |
| `apps/ledger/*` | LedgerEntry / LedgerReport；收入与支出快照、周期唯一锁定、报表生成审计 `REPORT_GENERATED`、金额两位小数 |
| `apps/polls/*` | Poll / Question / Participant / PollResponse / PollAnswer；创建、投票、结果汇总、到期关闭 |
| `apps/jobs/*` | `run_due_jobs`（投票截止、决议判定、席位到期、令牌/验证码/state/ticket 清理、审计保留）、`create_admin` |

### 2.5 迁移

`backend/apps/*/migrations/0001_initial.py`：14 个 app 各一份初始迁移，使用自动生成（`makemigrations`），已通过 `makemigrations --check --dry-run`。回流修复新增手写迁移 `backend/apps/polls/migrations/0002_poll_kind_scope_question_type.py`（DEF-004）。

### 2.6 前端

| 区域 | 文件 |
|---|---|
| 共享层 | `src/shared/{http,api,format}.js`、`src/shared/style.css`、`src/stores/auth.js`、`src/router/index.js` |
| 用户端 | `src/portal/{PortalLayout,Login,Register,WechatCallback,Home,Me,Units,Resolutions,ResolutionDetail,Tasks,Claims,Income,Polls,PollDetail,Reports}.vue` |
| 管理端 | `src/admin/{AdminLogin,AdminLayout,AdminRegistry,AdminAppeals,AdminMemberships,AdminSeats,AdminFlows,AdminFinance,AdminUsers,AdminAudit}.vue` |

### 2.7 小程序

`miniprogram/utils/{http,api}.js`、`miniprogram/store/auth.js`、`miniprogram/tests/setup.js`、`miniprogram/pages/{login,profile-setup,index,units,resolutions,polls,claims,me}/…`。

## 3. 关键实现约定

- 认证：`Authorization: Bearer <token>`；管理员与成员令牌分存储键，Web 端 `ocap_token` / `ocap_admin_token`。
- 错误体：所有异常统一为扁平 `{code, message, details?}`；前端只读 `message` / `details.retry_after`。
- 金额：数据库 `Decimal(12,2)`，序列化统一 `money()`，输出字符串（如 `"300.50"`），前端不做浮点运算。
- 附件：先上传得到临时附件 ID，业务提交时携带附件 ID，由各 app 的附件策略校验归属与用途并转为 LINKED。
- 审计：动作必须命中 `core/audit.py` 白名单；越权与失败结果分别记 `DENIED` / `FAILURE`。
- 限流与锁定：验证码按手机号/邮箱/IP 多维限流；连续失败进入锁定并返回 `CODE_RATE_LIMITED` 与 `retry_after`。
- 外部服务：全部经 `apps/integrations`，测试注入 `fakes.Fake*`，生产缺失 SDK 时明确降级而非静默成功。
- 幂等：定时任务按 `JobRun` 记录；前端重复提交由后端唯一约束与状态机拦截。

## 4. 数据库迁移说明

- 迁移范围：仅本项目新增表，未引入第三方 app 迁移。
- 约束：`Membership.active_slot`、`Seat.active_slot`、`ApprovalInstance.pending_slot`、`Vote(resolution,revision,voter)`、`LedgerReport.period` 等唯一约束在迁移中落库。
- 回滚：`migrate <app> zero` 可回滚初始迁移；生产执行前需备份（由 E1 部署计划负责）。
- 偏差：画像 P6 要求手写最小化迁移，本次使用 `makemigrations` 自动生成后再核对字段与约束；见 §7 `[DEVIATION] D-03`。

## 5. 自验证（PHASE_06 证据）

| 命令 | 结果 |
|---|---|
| `python -m compileall -q backend` | 退出码 0 |
| `python manage.py check --settings=config.test_settings` | `System check identified no issues (0 silenced).` |
| `python manage.py test tests.smoke --settings=config.test_settings` | `Ran 6 tests in 0.096s` / `OK` |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| `python manage.py migrate --check`（前序执行） | `No migrations to apply` |

冒烟测试文件 `backend/tests/smoke/test_flows_smoke.py` 覆盖：手机号注册与资料更新、重复注册 409、业主清册认证成功、清册不一致 422、指定审批决议通过、收入表导入→提交→审批、未登录 401 与无权限 403、金额两位小数。该文件由开发工程师在 FULL_FLOW 且原有测试为零的前提下编写，test-engineer 可接管或替换（§A 例外条款）。

## 6. 前端与小程序静态核对

- 路由与模块设计页面清单逐项对应；所有 API 调用集中在 `src/shared/api.js`、`miniprogram/utils/api.js`。
- 401 统一清理令牌并跳转登录；错误提示读取统一错误体。
- 金额仅做字符串展示；未做四则运算。
- 未执行构建、类型检查或组件测试（依赖未安装），见 §8。

## 7. 假设与偏差

- `[ASSUMPTION] A-01`：结算（SETTLEMENT）复用 `EXPENSE` 审批作用域与流程配置；依据 module_design 未单列结算流程。
- `[ASSUMPTION] A-02`：收入分类为自由文本，不做字典约束（需求仅要求分类字段）。
- `[ASSUMPTION] A-03`：`IsIncomeMember` 定义为“现任业委会成员”，与收入表录入权限一致。
- `[ASSUMPTION] A-04`：半数同意分母取 `CommitteeQuery.denominator_for_half_majority`，票数分母模式来自 `SystemConfig`。
- `[DEVIATION] D-01`：实际运行环境 Django 6.0.6 / DRF 3.17.1，目标画像为 Django 5.2；未降级，代码未使用 6.0 专属 API。
- `[DEVIATION] D-02`：`openpyxl` 与阿里云短信 SDK 未安装，xlsx 导入返回 `IMPORT_UNAVAILABLE`（503），阿里云网关返回 `SDK_MISSING`；csv 导入与 console 短信网关可用。
- `[DEVIATION] D-03`：0001/0002 迁移由 `makemigrations` 自动生成，未按 P6 手写；字段与约束已人工核对并通过 `--check`。1.3.0 起三个 `0003_*` 已改为手写（见 §11.3），0001 仍属 CR-002，留待后续。
- `[DEVIATION] D-04`：前端与小程序依赖未安装，未执行 `npm install` / 构建 / 组件测试，相关产物仅做静态实现与路由覆盖核对。

## 8. 未验证项与风险

- 前端/小程序运行时行为、响应式布局、微信端 `uni.login` 与头像选择未在真实环境验证。
- 微信开放平台 / 小程序凭据未配置，扫码与一键登录仅完成代码路径与错误映射。
- 生产 MySQL 未连接验证（测试使用 SQLite 内存库）。
- 并发场景（同一房号同时认证、同一审批实例并发决定）依赖数据库唯一约束，未做压力测试。
- 定时任务未接入系统 cron/计划任务，仅提供命令。

## 9. 开放问题（沿用需求/架构登记）

- OQ-17：微信 Web 扫码登录是否强制绑定手机号（当前实现：扫码成功即建号/登录，手机号可为空，后续可绑定）。
- OQ-25：收入表导入文件的列顺序与中文表头别名集合（当前支持中英文常见表头并给出逐行错误）。
- C-19：审计日志保留到期后的归档方式（当前按配置月数删除过期记录并写 JobRun）。
- Q110：业委会人数上限变更时对既有超编席位的处理（当前允许超编提示，不自动撤销）。

## 10. GROUP_C 回流修复（ocap-GROUP_C-2，DEF-001~004）

依据 GR-D-001 与 `REWORK_AUTHORIZED`，按最小改动修复 4 个 MAJOR 产品缺陷：

| DEF | 文件 | 改动要点 |
|---|---|---|
| DEF-001 | `backend/apps/resolutions/views.py` | `ResolutionListCreateView` 通过 `get_permissions` 分离读写：GET → `IsMember`，POST → `IsChairOrVice`。 |
| DEF-002 | `backend/apps/income/views.py`、`backend/apps/ledger/views.py` | 收入表列表 / 明细、台账列表 GET / 明细改为 `IsMember`；收入录入、提交、台账 POST 仍为 `IsIncomeMember`。 |
| DEF-003 | `backend/apps/ledger/services.py` | 同周期不再返回 409；改为覆盖原报表行、版本 +1、刷新 `generated_at` 并重写内容，审计记录带版本号。 |
| DEF-004 | `backend/apps/polls/models.py`、`migrations/0002_*.py`、`views.py`、`services.py` | Poll 新增 `kind` / `survey_scope` / `participant_count` / `result_snapshot`；Question 新增 `qtype` / `required`。创建代表投票时快照现任业主代表并拒绝无代表；应答按调查范围或参与人快照校验；代表性同意-反对-弃权题返回分母与是否通过。 |

`[ASSUMPTION] A-05`：历史客户端创建调查未传 `survey_scope` 时默认 `OWNERS_AND_RESIDENTS`，避免破坏既有调用方；新客户端应显式传值。

自验证：`python manage.py test tests.unit tests.integration tests.e2e --settings=config.test_settings -v 1` → `Ran 115 tests in 0.980s / OK`；`makemigrations --check --dry-run` → `No changes detected`。

文档版本：1.0.0 → 1.1.0（MINOR）；旧版本 1.0.0 登记为 SUPERSEDED。

## 11. 完整性复核缺陷修复（ocap-GROUP_C-5，CR-011 ~ CR-026）

依据 code_review_report §8 与用户决定（2026-11-08，上报处理 Q1=A，`REWORK_AUTHORIZED`），修复全部 CRITICAL/MAJOR（CR-011 ~ 023）及可改的 MINOR。文档版本 1.2.0 → 1.3.0（MINOR），旧 1.2.0 请 PM 登记为 SUPERSEDED。

### 11.1 改动清单（按依赖拓扑：core/accounts → 业务 app → identity/jobs → 前端 api 层 → 页面）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-001 | `backend/config/settings.py`、`config/test_settings.py` | 修改 | — | L | CR-024：去掉固定默认 SECRET_KEY（缺失且非 DEBUG 时拒绝启动，测试设置显式允许随机密钥）；`ALLOWED_HOSTS` 默认收敛为 localhost | DONE |
| 2 | MOD-001 | `apps/core/permissions.py`、`core/views.py` | 修改 | — | L | 新增 `IsMemberOrAdmin`，附件下载允许管理员（审核申诉证明所需，具体可见性仍由附件策略决定） | DONE |
| 3 | MOD-003 | `apps/accounts/services.py`、`views.py` | 修改 | 1 | M | `fill_empty_profile_from` 先释放 secondary 的唯一列 `verified_email`；新增 `session_kind_of`；Web 扫码首次登录取微信昵称（CR-026）；邮箱验证未传 email 时按本人邮箱校验 | DONE |
| 4 | MOD-013 | `apps/polls/{apps,services,views}.py` | 修改 | 3 | M | 合并时作答冲突保留 primary 并审计 `MERGE_ANSWER_DISCARDED`（CR-011）；打分 1~5、截止前结果任何人不可见（CR-021） | DONE |
| 5 | MOD-009 | `apps/resolutions/{apps,services}.py` | 修改 | 3 | L | 决议表决合并处理（同轮次冲突保留 primary） | DONE |
| 6 | MOD-012 | `apps/ledger/services.py` | 修改 | — | M | `post(allow_negative)` 支持核销多退；`generate_due` 改为生成已结束的上一季度/上一年度（幂等）（CR-017/018） | DONE |
| 7 | MOD-010 | `apps/claims/{services,views}.py` | 修改 | 6 | M | 核销通过：作废关联报销单台账、只记差额（可为负）；核销被拒/撤回释放关联；核销不可重提；取消"报销不得低于预借"限制（CR-017） | DONE |
| 8 | MOD-011 | `apps/income/views.py` | 修改 | 6 | M | 单条/多条录入 `POST /admin/income/sheets`、凭证附件 `voucher_ids`、导入跳过重复/错误行（含与已有 PENDING/EFFECTIVE 记录比较）、明细接口（CR-016） | DONE |
| 9 | MOD-014 | `apps/jobs/management/commands/run_due_jobs.py` | 修改 | 6 | L | `run_due_jobs` 调用 `LedgerService.generate_due`（CR-018） | DONE |
| 10 | MOD-007 | `apps/identity/{services,views}.py` | 修改 | 3、4、5 | H | `bind_phone`/`change_phone` 遇已注册手机号走 `_merge_by_phone`（行锁、单事务、主账号=手机号原账号），返回 `{merged, token, user}`；`merge_accounts` 增 actor/trigger 审计；补 `mask_phone` 缺失导入（管理端房屋关系列表原会 500）（CR-011） | DONE |
| 11 | MOD-008 | `apps/approval/views.py` | 修改 | — | L | 流程 PUT 支持 `is_active`（启用/停用，CR-015） | DONE |
| 12 | 迁移 | `apps/{claims,income,ledger}/migrations/0003_*.py` | 修改 | — | L | 去掉 Generated 文件头改为手写，操作与索引名不变（CR-023） | DONE |
| 13 | MOD-020 | `frontend/src/shared/api.js`、`stores/auth.js` | 修改 | 1~11 | M | 契约对齐：claims/polls/income/ledger/appeal/admin 路径与字段；`identities` 按对象读取（CR-012/013/014/015/019/022） | DONE |
| 14 | MOD-020 | `frontend/src/portal/*.vue`（Home、PortalLayout、Resolutions、ResolutionDetail、Claims、Polls、PollDetail、Income、Reports、Me、Units、WechatCallback、Login） | 修改 | 13 | H | 导航增 `/claims`、`/income`；报销/备用金/核销 UI；投票 kind/题型；决议截止时间/附件/撤回/重提；手机号绑定/换绑/注销带 phone；收入逐条录入与导入提示 | DONE |
| 15 | MOD-021 | `frontend/src/admin/{AdminSeats,AdminMemberships,AdminFinance,AdminUsers,AdminAppeals}.vue` | 修改 | 13 | M | 业主代表选项、撤销认证路径与参数、申诉决定字段与证明查看、去掉不存在的合并/生成接口入口 | DONE |
| 16 | MOD-022 | `miniprogram/utils/{http,api}.js`、`pages/{login,index,me,units,claims,polls/detail}`、新增 `pages/phone/index.vue`、`pages.json` | 修改/新建 | 1~11 | H | 密码登录、`is_new` 触发资料页、`identities` 对象、申诉带证明、报销/备用金/核销、投票 `/responses`+`value`、绑定/换绑手机号页 | DONE |

### 11.2 `/me` identities 契约裁定（CR-012）

module_design IFC-070 规定 `identities` 为对象 `{is_guest, units, committee, labels}`，后端已符合，因此只改 Web 与小程序的读取处（Home.vue、PortalLayout、各页面的委员判断、小程序 index/me），后端不动。

### 11.3 迁移

| 项 | 内容 | 可逆 |
|---|---|---|
| `claims/0003_rename_claims_clai_status_a1b2c3_idx_…`、`income/0003_alter_incomerecord_options_and_more`、`ledger/0003_rename_ledger_lede_occurre_c39b98_idx_…` | **文件名与迁移名不变**（已应用于测试环境 MySQL）；去掉 `# Generated by Django 6.0.6` 头，改为手写文件（带说明 docstring、双引号风格）；`operations` 与依赖逐项相同，AST 与原文件一致（已用脚本比对，仅 docstring 不同）；索引名、`line_no` 字段选项均未变 | 是（RenameIndex/AlterField/AlterModelOptions 均可反向） |
| 新增迁移 | 无。本次所有后端改动均不涉及模型字段 | — |

`makemigrations --check --dry-run`（Django 5.2.19）输出 `No changes detected`，没有生成任何文件。

### 11.4 架构偏差与假设

| 编号 | 说明 |
|---|---|
| `[ASSUMPTION] A-06` | 备用金核销按 REQ-FUNC-041/058 实现：核销通过时作废关联凭票报销单的台账，只入核销差额；差额为负（多退）时 `Claim.amount` 与台账明细均记为负数。"谁登记退回现金"需求未规定，本次只体现为负差额。 |
| `[ASSUMPTION] A-07` | `change_phone` 沿用既有"原号+新号双验证码"契约（`old_phone/new_phone/old_code/new_code`），未改为 IFC-072 的 `{new_phone, code}`，避免扩大变更面；与设计的差异归入 CR-025。 |
| `[ASSUMPTION] A-08` | 导入的"重复"判定按 IFC-111/OQ-12：同文件内或与已有 PENDING/EFFECTIVE 记录的（日期、金额、类别、来源说明）四项全同。逐条录入（`POST /admin/income/sheets`）遇错整体拒绝（便于当场更正），不跳过。 |
| `[ASSUMPTION] A-09` | `generate_due` 自动生成"上一已结束季度"与"上一已结束年度"，已有未过期报表则跳过，幂等；每日运行即可。 |
| `[DEVIATION] D-05` | 截止前投票结果：IFC-133 设计为 403 `RESULT_NOT_PUBLIC`，保留既有实现 409 `NOT_CLOSED`（仅去掉发起人/管理员例外），避免无谓改动错误码；影响 IFC-133，归入 CR-025。 |

### 11.5 开放问题 / 交接事项

1. **交 devops-engineer（CR-018）**：`deploy/systemd/` 不在 software-developer 写权限内。需要新增 systemd 定时器（建议 `ocap-run-due-jobs.timer`，每日或每小时执行 `python manage.py run_due_jobs`），并在部署计划中验证；`run_due_jobs` 现已包含季度/年度报表生成。同时确认测试机 `backend/.env` 的 `DJANGO_SECRET_KEY`、`DJANGO_ALLOWED_HOSTS` 非空（CR-024 之后缺失 SECRET_KEY 会拒绝启动；ALLOWED_HOSTS 默认不再是 `*`）。
2. **CR-025（MINOR，未处理）**：IFC-110/111/112/120/132/133/140 的路由与签名偏离设计（收入表路径带 `/admin` 前缀但权限为业委会成员、台账路径 `/ledger/reports`、`approval_flow_id` 对 `flow_id`、`--now/--only`、`generate_reports`/`purge_temp_attachments` 任务缺失等）。需 module_design 回写或另立变更，属架构决定，本次不改。
3. **CR-026（MINOR，部分处理）**：Web 扫码首次登录已取微信昵称（头像转存仍未做：需要新增下载微信头像并转存附件的外部调用，P11 无出处，`TODO(IFC-027): [UNSOURCED]`）；前端自动化测试按约束留给 test-engineer。
4. `change_phone` 与 IFC-072 契约差异（A-07）、Web/小程序资料页头像上传（CR-004）仍为遗留。
5. 0001_initial 迁移仍为 makemigrations 产物（CR-002）；因已上线，本次不动。
6. 管理端不再提供"合并账号"入口：合并只由用户绑定/换绑手机号触发（REQ-FUNC-026/028），管理员侧无对应需求。

### 11.6 预期变更的现有测试（交 test-engineer，本次未改任何测试文件）

见 code_review_report §9.3。
