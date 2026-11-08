<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-07T23:57:31+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.2.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
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
- `[DEVIATION] D-03`：迁移由 `makemigrations` 自动生成，未按 P6 手写；字段与约束已人工核对并通过 `--check`。
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
