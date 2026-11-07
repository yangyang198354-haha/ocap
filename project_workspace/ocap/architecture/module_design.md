<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-07T21:01:49+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md (5.0.0 APPROVED)</file><file>requirements/user_stories.md (3.0.0 APPROVED)</file><file>architecture/architecture_design.md (0.2.0)</file><file>architecture/module_design.md (0.1.0)</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：业主委员会 Web 应用 + 微信小程序（ocap）

> 只设计到接口签名与数据结构为止，无函数体。ocap 是**新建独立仓库**，下列"新建"文件均尚不存在，本次**不创建**任何代码目录。
> 类型用 Python 3.12 类型注解 / TypeScript 表达。HTTP 约定见 ADR-021：前缀 `/api/v1`，错误体 `{code, message, details?}`，分页 `{count, page, page_size, results}`，金额为十进制字符串，时间为带时区 ISO 8601。
> 鉴权记号：`PUB` 无需鉴权；`M` 已登录普通用户（MEMBER 令牌）；`A` 管理员（ADMIN 令牌）；`M:委员+` 业委会成员（委员/主任/副主任）；`M:主任+` 主任或副主任；`M:代表` 业主代表。
>
> **0.2.0 修订说明（0.1.0 → 0.2.0）**：(1) 落实用户 2026-11-07 对架构开放问题的答复（OQ-01~16 已决、建议值表已确认），并与 requirements_spec 5.0.0 的 REQ-FUNC-064~068、C-15~C-19 对齐，覆盖表扩为 REQ-FUNC-001~068；(2) 阿里云短信：IFC-011 去掉 `ttl_minutes`，新增 `AliyunSmsGateway` 与错误映射（ADR-022）；(3) 会话：令牌两种期限（IFC-038 `authenticate_token`）；(4) 限流：新增 `core_lockout` 与 `RateLimiter.register_failure`；(5) 配置：新增 IFC-009（审计保留期限，下限 6 个月）；(6) 附件：新增"附件规格表"（C-12/C-18），申诉改为按 id 关联附件；(7) 合并：新增"合并引用登记表"（REQ-FUNC-067）；(8) 审批：REQ-FUNC-066 规则落到 IFC-082/083；(9) 收入表导入改为可带 `flow_id` 直接待审批（AC-059-01）；(10) 依赖：说明 core 端点与附件策略的注册式装配，避免 core 反向依赖。GR-B-001-F01：本次已完整读完需求与故事全文（spec 至 564 行、stories 至 1028 行）。

## 代码布局建议（画像 P3，已确认 OQ-15）

```
ocap/                                 仓库根（git，独立仓库）
├── backend/                          Django 项目
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                       settings.py  test_settings.py  urls.py  wsgi.py
│   ├── apps/                         （不命名为 platform，避免与标准库同名）
│   │   ├── core/ integrations/ accounts/ registry/ residency/ committee/ identity/
│   │   └── approval/ resolutions/ claims/ income/ ledger/ polls/ jobs/
│   │       每个 app：models.py  services.py  api/{views,serializers,permissions,urls}.py  migrations/  tests/
│   └── tests/integration/            跨 app 集成测试
├── frontend/                         Vue 3 + Vite（src/portal  src/admin  src/shared），测试 frontend/tests/
├── miniprogram/                      uni-app，测试 miniprogram/tests/
├── deploy/systemd/                   systemd unit 模板（不含任何凭据）
└── project_workspace/                SDLC 文档（已有）
```
- 测试位置约定：后端 `backend/apps/<app>/tests/test_*.py`，运行 `python manage.py test --settings=config.test_settings`（Django test runner，与 Freeark 一致 [CODE: /root/myproject/Freeark/CLAUDE.md "测试运行器：Django test runner"]）；前端 `frontend/tests/**/*.spec.js`（vitest）；小程序 `miniprogram/tests/*.spec.js`（vitest，沿用 Freeark 布局 [CODE: /root/myproject/Freeark/miniprogram/tests/setup.js]）。
- 迁移（P6）：每个 app 的 `migrations/` 手写、单 app 范围；允许用 `makemigrations --dry-run <app>` 辅助对照，但**不提交其产物**（用户已确认，OQ-15，GR-B-001-F02 关闭）。
- 画像需 PM 同步（本角色不能改画像）：P3 代码目录与测试位置按上述布局；P11-3 短信=阿里云短信、邮件=事务邮件服务（SMTP）、测试替身=`integrations/fakes.py`。

## 共享类型（core）

```python
UserId = int
Money = Decimal                      # 两位小数；JSON 传输为字符串，如 "1234.50"
class ErrorBody(TypedDict):          # 所有非 2xx 响应
    code: str                        # UPPER_SNAKE，如 CODE_EXPIRED
    message: str
    details: NotRequired[dict[str, list[str]]]
class Page(TypedDict, Generic[T]):
    count: int; page: int; page_size: int; results: list[T]   # page_size ≤ 100，默认 20

class CodePurpose(StrEnum):  REGISTER="REGISTER"; LOGIN="LOGIN"; EMAIL_LOGIN="EMAIL_LOGIN"; BIND_PHONE="BIND_PHONE"; CHANGE_PHONE="CHANGE_PHONE"; CANCEL="CANCEL"; EMAIL_VERIFY="EMAIL_VERIFY"
class UnitRole(StrEnum):     HEAD="HEAD"; OWNER="OWNER"; RESIDENT="RESIDENT"            # 户主/产权业主/同住人；游客=无有效记录（派生）
class SeatPosition(StrEnum): CHAIR="CHAIR"; VICE_CHAIR="VICE_CHAIR"; MEMBER="MEMBER"; REPRESENTATIVE="REPRESENTATIVE"
SEAT_RANK = {CHAIR: 4, VICE_CHAIR: 3, MEMBER: 2, REPRESENTATIVE: 1}                  # 合并取高（REQ-FUNC-061）
UNIT_ROLE_RANK = {HEAD: 3, OWNER: 2, RESIDENT: 1}                                    # 合并取高（REQ-FUNC-030）
class ApprovalStatus(StrEnum): PENDING; APPROVED; REJECTED; WITHDRAWN
class Channel(StrEnum):      MINIAPP="MINIAPP"; WEB="WEB"                              # 微信身份来源
class SessionKind(StrEnum):  IDLE="IDLE"; EXTENDED="EXTENDED"                          # 会话期限（REQ-FUNC-064，ADR-004）
class AuthResult(TypedDict):                                                           # 所有登录/注册成功响应
    token: str; user: UserBrief; is_new: bool                                          # is_new：本次请求新建了账号；小程序据此进入头像昵称设置页（REQ-FUNC-065）
```

## 模块总览

| MOD | 名称 | 文件（均新建，路径相对仓库根） | 职责（一句话） | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-001 | core 平台基础 | `backend/apps/core/`（models、audit.py、attachments.py、masking.py、ratelimit.py、config.py、user_refs.py） | 审计日志、附件存取、手机号脱敏、限流与锁定、系统配置、用户引用注册表等横切能力 | REQ-NFUNC-001（限流侧）/002/003/004、C-06/07/12/18；US-032/033/034/064 | 无（HTTP 端点与附件策略采用注册式装配，不 import 其他模块） |
| MOD-002 | integrations 外部服务适配 | `backend/apps/integrations/{wechat.py,sms.py,aliyun_sms.py,email.py,fakes.py}` | 微信、阿里云短信、邮件三类外部服务的统一适配接口与测试替身 | REQ-FUNC-002/003/004/008、REQ-NFUNC-001（发送侧）；C-15/C-16 | MOD-001 |
| MOD-003 | accounts 账号与登录 | `backend/apps/accounts/` | 用户/管理员主体、令牌与会话期限、验证码、各种登录方式、密码、个人资料、邮箱归属、管理员账号管理 | REQ-FUNC-001~008、016、023~025、031、064、065（服务端侧）、068；REQ-NFUNC-001；US-001~011、017、030、032、069、070、073 | MOD-001、MOD-002 |
| MOD-004 | registry 业主清册 | `backend/apps/registry/` | 专有部分与登记手机号的存储、维护、批量导入，逐级选择的选项查询 | REQ-FUNC-009、010（选项部分）、018、033（清册侧）；US-018/019/020/035 | MOD-001 |
| MOD-005 | residency 房屋关系与认证 | `backend/apps/residency/` | 产权业主/户主/同住人关系，清册认证，申诉，同住人申请与移除，户主接任 | REQ-FUNC-010~015、019、020、022、032、033、034（关系侧）；US-020~029、035、036 | MOD-001、003、004 |
| MOD-006 | committee 业委会与业主代表 | `backend/apps/committee/` | 业委会/业主代表席位、人数与任期配置、到期与资格失效 | REQ-FUNC-035、036（数据侧）、052、053、056、057、061（席位侧）、063（席位侧）；US-037~042、066、068 | MOD-001、003、005 |
| MOD-007 | identity 身份生命周期与聚合 | `backend/apps/identity/` | 编排：账号合并（含在途事项）、手机号绑定/更换、账号注销、撤销认证级联、`/me` 身份聚合 | REQ-FUNC-017、021、026~030、034、036、053、061、067；US-012~016、027、028、031、036、066、072 | MOD-001~006 |
| MOD-008 | approval 审批引擎 | `backend/apps/approval/` | 审批流程配置、提交时快照、审批动作、撤回、多审批人任一通过、不得自审等通用规则 | REQ-FUNC-038（指定负责人）、042、054、055、062、066；US-043、048、067、071 | MOD-001、003、006 |
| MOD-009 | resolutions 业委会决议 | `backend/apps/resolutions/` | 决议的发起、审批/半数同意表决、截止判定、公开 | REQ-FUNC-037~039、060；US-044~047、065 | MOD-001、006、008 |
| MOD-010 | claims 报销与备用金 | `backend/apps/claims/` | 报销单、备用金预借单、核销单及其审批 | REQ-FUNC-040~042、058、062；US-049~051、067 | MOD-001、006、008、012 |
| MOD-011 | income 收入表 | `backend/apps/income/` | 收入表录入（单条/导入）、审批生效、作废 | REQ-FUNC-048、049、059；US-058~060 | MOD-001、006、008、012 |
| MOD-012 | ledger 台账与财务报表 | `backend/apps/ledger/` | 追加式台账、季度/年度报表的生成与查询 | REQ-FUNC-041（口径）、050、051、058（口径）；US-061~063 | MOD-001、006 |
| MOD-013 | polls 投票与调查 | `backend/apps/polls/` | 业主代表投票与调查的发起、作答、截止汇总与公开 | REQ-FUNC-043~047；US-052~057 | MOD-001、005、006 |
| MOD-014 | jobs 定时任务 | `backend/apps/jobs/`（management commands） | 周期性幂等任务的统一入口 | REQ-FUNC-050、053（任期）、060；REQ-NFUNC-001/003/004（清理） | MOD-001、003、006、009、012、013 |
| MOD-020 | web-portal 用户端 | `frontend/src/portal/` | 注册登录、认证、个人中心、决议/投票/调查/报表/申请（Web） | 全部用户侧 REQ（见覆盖表）；US-001~008 等 | 后端 API |
| MOD-021 | web-admin 管理后台 | `frontend/src/admin/` | 清册、申诉、撤销认证、业委会与代表、审批流程、配置（含审计保留期限）、管理员账号与密码重置、审计 | REQ-FUNC-018、019、025、034、035、052、054、056、057、064（管理员会话）、068；US-011、019、026、036~043、064、069、073 | 后端 API |
| MOD-022 | miniprogram 小程序 | `miniprogram/` | 用户端功能的小程序形态（含微信一键登录、首次登录头像昵称设置、提交意见） | REQ-FUNC-003、004、045、064（小程序 7 天会话）、065 及其余用户侧功能 | 后端 API |

## 模块详情

### MOD-001 core

**职责**：横切基础能力，被所有后端模块依赖，自身不依赖任何业务模块。
**数据表**（业务无关）：
- `core_audit_log(id, occurred_at idx, actor_type{MEMBER,ADMIN,SYSTEM}, actor_id int null, actor_label varchar(64), action varchar(64), object_type varchar(48), object_id varchar(64), result{SUCCESS,FAILURE,DENIED}, detail JSON, ip varchar(45) null)`；索引 `(action, occurred_at)`、`(object_type, object_id)`。不设外键，actor_label 为脱敏快照。
- `core_attachment(id uuid pk, owner_type{MEMBER,ADMIN}, owner_id int, purpose varchar(32), original_name varchar(255), content_type varchar(100), size int, sha256 char(64), storage_path varchar(255), status{TEMP,LINKED}, linked_type varchar(48) null, linked_id varchar(64) null, created_at)`。TEMP 超过 24 小时由 MOD-014 清理。
- `core_system_config(key varchar(64) pk, value JSON, updated_at, updated_by_admin_id int null)`。
- `core_rate_limit(key varchar(128), window_start datetime, count int)`，唯一 `(key, window_start)`。用于"发送频率"类固定窗口计数。
- `core_lockout(key varchar(128) pk, fail_count smallint, window_start datetime, locked_until datetime null)`。用于"累计/连续失败后锁定"：验证码目标 30 分钟内累计错 10 次锁 30 分钟（key=`codefail:<target>`）；密码连续错 5 次锁 15 分钟（key=`pwfail:<规范化标识>`，标识不存在时同样计数，使响应与存在时无差别）。成功登录清零该 key。
- `core_job_run(job_name pk, last_run_at, last_status, last_error text)`。

**接口**：

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-001 | `AuditService.record(*, actor: AuditActor, action: str, object_type: str, object_id: str, result: Literal["SUCCESS","FAILURE","DENIED"], detail: dict[str, JSONValue] \| None = None) -> None`（在调用方事务内写入；detail 中禁止出现明文手机号、验证码、令牌，写入前经 `scrub()` 过滤并对形如手机号的值脱敏） | 内部 | `action` 必须在枚举 `AuditAction` 内（见下"审计动作清单"），否则抛 `ValueError`（开发期失败） |
| IFC-002 | `GET /api/v1/admin/audit-logs?action=&object_type=&object_id=&actor_id=&from=&to=&page=&page_size=` → `Page[AuditLogItem]` | `A` | `from/to` ISO 8601，区间 ≤ 366 天；`page_size ≤ 100`；非法 → 400 `INVALID_QUERY`；手机号字段已脱敏（US-019 AC-019-07） |
| IFC-003 | `AttachmentService.store(*, file: UploadedFile, purpose: AttachmentPurpose, owner: Principal) -> AttachmentRef`；`.link(attachment_ids: list[UUID], linked_type: str, linked_id: str, purpose: AttachmentPurpose, owner: Principal) -> None`（校验归属人，以及"附件规格表"中该用途的数量上限与合计上限；`link` 在调用方事务内执行）；`.open(attachment_id: UUID, principal: Principal) -> FileResponse`（权限由 `AttachmentAccessPolicy` 按 linked_type 分派）；`register_attachment_policy(linked_type: str, policy: AttachmentPolicy) -> None`（由各业务模块在 app 启动时注册自己的下载策略，core 不 import 业务模块）；`class AttachmentPolicy(Protocol): def can_open(self, linked_id: str, principal: Principal) -> bool` | 内部 | 校验见 IFC-004；`link` 超过数量/合计上限 → 抛 `AttachmentLimitExceeded`（API 层转 400 `ATTACHMENT_LIMIT`） |
| IFC-004 | `POST /api/v1/attachments`（multipart：`file`，`purpose`）→ 201 `AttachmentRef{id: UUID, name: str, size: int, content_type: str}` | `M`（purpose=`APPEAL_PROOF/RESOLUTION/INVOICE/INCOME_VOUCHER/AVATAR`）；`A` 无上传需求 | `purpose` ∈ 枚举；按"附件规格表"校验：扩展名白名单且**文件头魔数与扩展名一致（类型以实际内容为准）**、单文件大小；超限 → 413 `FILE_TOO_LARGE`，类型不符（含扩展名与内容不一致，如 .pdf 实为 html/可执行文件）→ 400 `FILE_TYPE_NOT_ALLOWED`；每次只接收一个文件（反向代理请求体上限按 12 MB 配置）；上传限流 60 次/小时/用户 → 429 |
| IFC-005 | `GET /api/v1/attachments/{id}/download` → 文件流 | `M` 或 `A`，按 `AttachmentAccessPolicy` | 无权或不存在统一 404 `NOT_FOUND`；响应头 `X-Content-Type-Options: nosniff`、`Content-Disposition: attachment` |
| IFC-009 | `GET /api/v1/admin/system-config` → `dict[str, JSONValue]`（仅返回可编辑键）；`PUT /api/v1/admin/system-config/{key}` `{value: JSONValue}` → 200 | `A` | 可编辑键白名单 `EDITABLE_KEYS = {"audit.retention_months"}`，其他键 → 404 `CONFIG_KEY_NOT_EDITABLE`（其余配置只经环境变量或运维直接改库）；`audit.retention_months` 须为整数且 **≥ 6**、≤ 120，低于 6 → 400 `RETENTION_TOO_SHORT`（message：保留期限不得低于 6 个月，AC-034-04）；写审计 `SYSTEM_CONFIG_CHANGED`（含变更前后值） |
| IFC-006 | `mask_phone(phone: str) -> str`（`"13800000000"→"138****0000"`）；DRF 字段 `MaskedPhoneField`（只读）；`PlainPhoneField`（仅 `/admin/registry/**` 序列化器可用，用测试断言限定） | 内部 | 非 11 位输入原样返回 `"****"` |
| IFC-007 | `SystemConfig.get(key: str, default: T) -> T`；`.set(key: str, value: JSONValue, admin_id: int) -> None`；`RateLimiter.hit(key: str, *, limit: int, window_seconds: int) -> RateDecision{allowed: bool, retry_after: int}`（`UPDATE … SET count=count+1` 原子累加）；`RateLimiter.is_locked(key: str) -> RateDecision`；`RateLimiter.register_failure(key: str, *, limit: int, window_seconds: int, lock_seconds: int) -> RateDecision`（在 `window_seconds` 内累计失败达 `limit` 次即写 `core_lockout.locked_until`；已锁定时不累加）；`RateLimiter.reset(key: str) -> None`（成功后清零）；`client_ip(request) -> str`（仅当直连地址 ∈ `TRUSTED_PROXY_ADDRS` 时采信 `X-Forwarded-For` 最右一跳，否则用直连地址） | 内部 | 配置键白名单见"配置项清单"；锁定期内连正确的验证码/密码也拒绝（AC-032-03/05） |
| IFC-008 | `register_user_reference(model: type[Model], field: str, *, on_conflict: Literal["keep_primary","move_all","delete_secondary","custom"], handler: Callable \| None = None) -> None`；`assert_all_user_fks_registered() -> None`（Django `check` 框架中执行，未登记的指向 User 的外键使启动检查失败） | 内部 | — |

**附件规格表**（C-12、C-18；"图片"= jpg/jpeg/png，见 OQ-18；类型以文件实际内容为准）：
| purpose | 允许格式 | 单个上限 | 数量上限 | 合计上限 | 关联对象 |
|---|---|---|---|---|---|
| `RESOLUTION` | pdf、jpg、jpeg、png、docx、xlsx | 10 MB | 10 | 50 MB | 决议 |
| `APPEAL_PROOF` | jpg、jpeg、png、pdf | 10 MB | 5 | 不另设（5 × 10 MB） | 申诉 |
| `INVOICE` | jpg、jpeg、png、pdf | 10 MB | 10 | 不另设（10 × 10 MB） | 报销单 |
| `INCOME_VOUCHER` | jpg、jpeg、png、pdf | 10 MB | 10（每条收入记录） | 不另设 | 收入记录 |
| `AVATAR` | jpg、jpeg、png（需求写 jpg/png，jpeg 是同一格式的另一扩展名） | 2 MB | 1 | 2 MB | 用户 |
边界：数量与大小"恰为上限"通过，超过一个/一字节即拒绝（AC-044-08、026-07、049-08、058-07、030-07/08）。附件逐个上传、按 id 关联；决议的合计上限在 `link` 时校验。

**AttachmentAccessPolicy**（谁能下载）：
| linked_type | 可下载者 |
|---|---|
| `appeal` | 申诉人本人、`A` |
| `resolution` | 决议 `APPROVED/REJECTED`（已公开）：全体已登录用户；`PENDING`：发起人、业委会成员、`A`；`WITHDRAWN`：发起人、`A` |
| `claim_invoice` | 发起人、流程快照中的审批人、`A`（REQ-FUNC-041/Q59） |
| `income_voucher` | 业委会成员、`A` `[ASSUMPTION]`（需求未规定收入凭证的可见范围） |
| `avatar` | 全体已登录用户 |
| 未关联（TEMP） | 仅上传者 |

**审计动作清单 `AuditAction`**（覆盖 REQ-NFUNC-003/004）：`ADMIN_LOGIN`、`ADMIN_LOGIN_FAILED`、`REGISTER`、`CERTIFY_BY_REGISTRY`、`HEAD_ASSIGNED`、`HEAD_SUCCEEDED`、`APPEAL_SUBMITTED`、`APPEAL_DECIDED`、`RESIDENT_APPLICATION_DECIDED`、`RESIDENT_REMOVED`、`RESIDENT_LEFT`、`CERTIFICATION_REVOKED`、`ACCOUNT_CANCELLED`、`ACCOUNTS_MERGED`、`PHONE_CHANGED`、`PHONE_BOUND`、`EMAIL_OWNERSHIP_CHANGED`、`REGISTRY_IMPORTED`、`REGISTRY_UNIT_CHANGED`、`SEAT_GRANTED`、`SEAT_CHANGED`、`SEAT_REVOKED`、`SEAT_EXPIRED`、`SEAT_INVALIDATED`、`COMMITTEE_CONFIG_CHANGED`、`APPROVAL_FLOW_CHANGED`、`RESOLUTION_SUBMITTED/WITHDRAWN/DECIDED`、`CLAIM_SUBMITTED/WITHDRAWN/DECIDED`、`INCOME_SUBMITTED/WITHDRAWN/DECIDED/VOIDED`、`INCOME_IMPORTED`、`POLL_CREATED`、`POLL_CLOSED`、`REPORT_GENERATED`、`AUDIT_PURGED`、`ADMIN_CREATED`、`ADMIN_PASSWORD_RESET`（OQ-23）、`SYSTEM_CONFIG_CHANGED`、`MERGE_ANSWER_DISCARDED`（REQ-FUNC-067）。
全部审计动作与需求范围对应：REQ-NFUNC-003（认证/户主/同住人审批/注销/申诉/清册/合并/邮箱归属/管理员登录/撤销认证）、REQ-NFUNC-004（身份与配置变更、决议/财务/收入表发起与审批、投票调查发起、报表生成；半数同意判定与合并致身份失效由 `RESOLUTION_DECIDED`、`SEAT_INVALIDATED` 覆盖，操作人为 SYSTEM，AC-064-08）。

**配置项清单**（`SystemConfig` 键与默认值；数值均已由用户确认，括号为需求来源编号；未括号者为技术配置）：`code.sms.length=6`、`code.sms.ttl_seconds=300`、`code.email.ttl_seconds=600`、`code.resend_interval_seconds=60`、`code.target_per_hour=5`、`code.target_per_day=10`、`code.ip_per_hour=30`、`code.max_wrong_per_code=5`、`code.target_lock_after_wrong=10`、`code.target_lock_seconds=1800`（C-06）；`login.password_fail_limit=5`、`login.password_lock_seconds=900`；`password.min_len=8`、`password.max_len=64`（C-08）；`audit.retention_months=24`（C-07，下限 6，经 IFC-009 修改）；`attachment.max_count.resolution=10`、`attachment.max_bytes=10485760`、`attachment.max_total_bytes.resolution=52428800`（C-12）、`attachment.max_count.appeal=5`、`attachment.max_count.invoice=10`、`attachment.max_count.voucher=10`、`attachment.avatar_max_bytes=2097152`（C-18）；`session.idle_seconds=1800`、`session.extended_seconds=604800`、`session.admin_idle_seconds=1800`、`session.miniapp_extended=true`（REQ-FUNC-064）；`claim.amount_max=null`（Q96）；`poll.max_questions=50`（Q97 技术防线）；`vote.min_window_minutes=60`（Q110）；`vote.denominator_mode="ACTIVE"`（Q99）；`report.show_expense_reason=false`（OQ-08）；`wechat.phone_quick_verify_enabled=false`。凭据类（AppSecret、阿里云 AccessKey、SMTP 口令、`SECRET_KEY`、数据库口令）**不进 SystemConfig**，只读环境变量。启动检查（Django `check` 框架）：①`ALIYUN_SMS_TEMPLATE_TTL_MINUTES * 60 == code.sms.ttl_seconds`；②`code.sms.length` ∈ 4..6（阿里云验证码模板单变量限制，ADR-022）；③`audit.retention_months >= 6`；④`assert_all_user_fks_registered()`（IFC-008）。

### MOD-002 integrations

**职责**：把微信、短信、邮件封装为窄接口；业务模块只依赖接口，不接触 HTTP 细节与服务商字段。外部调用统一超时 5 秒（沿用 Freeark [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/views_miniapp.py:156]），失败映射为下列异常，由 API 层转 502/503。
**文件**：`wechat.py`（真实实现）、`sms.py`（`SmsGateway` 协议 + `ConsoleSmsGateway` 开发替身 + `get_sms_gateway()` 工厂）、`aliyun_sms.py`（`AliyunSmsGateway`，唯一使用阿里云 SDK 的文件，延迟导入，ADR-022）、`email.py`（`EmailGateway` + 基于 Django SMTP 后端的实现）、`fakes.py`（供测试注入的内存替身，记录发送内容、可编程失败）。

| IFC | 签名 | 鉴权 / 校验 / 错误 |
|---|---|---|
| IFC-010 | `class WeChatClient(Protocol):`<br>`def miniapp_code2session(self, js_code: str) -> MiniappSession  # openid, unionid\|None, session_key（不落库、不返回前端）`<br>`def stable_access_token(self) -> str  # 进程内缓存，到期前 5 分钟更新；不使用 force_refresh`<br>`def miniapp_phone_by_code(self, code: str, openid: str \| None = None) -> str  # purePhoneNumber；仅当 wechat.phone_quick_verify_enabled`<br>`def web_exchange_code(self, code: str) -> WebAuthToken  # access_token, openid, unionid\|None`<br>`def web_userinfo(self, access_token: str, openid: str) -> WebUserInfo  # nickname, headimgurl\|None`<br>`class WeChatError(Exception): kind: Literal["INVALID_CODE","RATE_LIMITED","BLOCKED","UPSTREAM_DOWN","NOT_CONFIGURED","IP_NOT_WHITELISTED"]; errcode: int \| None` | 内部。校验：`js_code`/`code` 非空且 ≤ 128 字符；errcode 映射：40029→INVALID_CODE，45011→RATE_LIMITED，40226→BLOCKED，40164→IP_NOT_WHITELISTED，超时/5xx→UPSTREAM_DOWN，缺 AppID/Secret→NOT_CONFIGURED。凭据读自 `WECHAT_MINIAPP_APPID/SECRET`、`WECHAT_WEB_APPID/SECRET`（环境变量） |
| IFC-011 | `class SmsGateway(Protocol): def send_code(self, phone: str, code: str, purpose: CodePurpose) -> None`<br>`class SmsSendError(Exception): kind: Literal["RATE_LIMITED","INVALID_NUMBER","QUOTA_OR_BALANCE","CONFIG","UPSTREAM"]; provider_code: str \| None; retryable: bool`<br>`class AliyunSmsGateway(SmsGateway)`：配置 `ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`、`ALIYUN_SMS_SIGN_NAME`、`ALIYUN_SMS_TEMPLATE_CODE`、`ALIYUN_SMS_TEMPLATE_TTL_MINUTES`（均环境变量）；调用阿里云 `SendSms`：`PhoneNumbers`=单个手机号、`SignName`、`TemplateCode`、`TemplateParam`=`{"code": "<验证码>"}` 的 JSON 字符串；仅当响应 `Code == "OK"` 视为成功（`BizId`、`RequestId` 只写日志，不含验证码） | 内部。`phone` 已校验 `^1[3-9]\d{9}$`（C-19）；**去掉了 0.1.0 的 `ttl_minutes` 参数**：阿里云验证码模板的第二个变量不能自定义，有效期写死在模板正文，改由启动检查保证与 `code.sms.ttl_seconds` 一致；所有 `purpose` 共用一个模板；实现不得记录 `code` 明文到日志；超时 5 秒。**错误映射**（按官方错误码名称归类 [WEB: https://api.aliyun.com/document/Dysmsapi/2017-05-25/errorCode，2026-11-07，页面仅给名称，释义未取得]）：`isv.BUSINESS_LIMIT_CONTROL`、`isv.DAY_LIMIT_CONTROL`、`isv.MONTH_LIMIT_CONTROL`→`RATE_LIMITED`（API 层转 429 `CODE_RATE_LIMITED`，不重试）；`isv.MOBILE_NUMBER_ILLEGAL`→`INVALID_NUMBER`（转 400）；`isv.AMOUNT_NOT_ENOUGH`→`QUOTA_OR_BALANCE`（转 503，告警）；`isv.SMS_SIGNATURE_ILLEGAL`、`isv.SMS_TEMPLATE_ILLEGAL`、`isv.TEMPLATE_MISSING_PARAMETERS`、`isv.INVALID_PARAMETERS`、`isv.ACCOUNT_ABNORMAL`、`isp.RAM_PERMISSION_DENY`→`CONFIG`（转 503 `SMS_UNAVAILABLE`，告警）；`isv.SYSTEM_ERROR`、超时、网络错误→`UPSTREAM`（`retryable=True`，转 502 `SMS_SEND_FAILED`）；未识别的非 `OK` 码按 `UPSTREAM` 处理并记录原码 |
| IFC-012 | `class EmailGateway(Protocol): def send_code(self, email: str, code: str, purpose: CodePurpose, ttl_minutes: int) -> None`；`class EmailSendError(Exception)` | 内部。收件人 ≤ 254 字符；主题/正文模板固定，不含用户可控 HTML；使用 Django SMTP 邮件后端，配置为 Django 标准设置项（`EMAIL_HOST`、`EMAIL_PORT`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD`、`EMAIL_USE_SSL`/`EMAIL_USE_TLS`、`DEFAULT_FROM_EMAIL`），值全部来自环境变量；邮件有效期 `ttl_minutes` 写入正文，取 `code.email.ttl_seconds`（C-06，10 分钟）；SMTP 异常 → `EmailSendError`，API 层转 502 `EMAIL_SEND_FAILED` |

**外部依赖**：`requests`（微信）；官方 SDK `alibabacloud_dysmsapi20170525`（阿里云短信，ADR-022）；Django `EmailBackend`（SMTP，事务邮件服务厂商未选，C-16）。**测试替身**：`fakes.FakeWeChatClient/FakeSmsGateway/FakeEmailGateway`（画像 P11-3"测试替身"列需同步更新，见"代码布局建议"）。真实调用阿里云/微信/邮件服务的联调用例在 GROUP_D 标 NOT_TESTABLE（协议 §N-4），只在人工验证清单中执行。

### MOD-003 accounts

**职责**：主体（普通用户 `User`、管理员 `AdminAccount`）、令牌、验证码、所有登录/注册入口、密码、资料、邮箱归属。**不**处理合并/注销/换号（归 MOD-007）。
**数据表**：
- `accounts_user(id, account_no char(10) unique, phone char(11) unique null, email varchar(254) null, email_state{NONE,UNVERIFIED_REG,UNVERIFIED_CHANGED,VERIFIED}, verified_email varchar(254) unique null, password varchar(128) null, nickname varchar(30) null, avatar_attachment_id uuid null, gender smallint null{0,1,2}, birthday date null, status{ACTIVE,CANCELLED}, created_at, last_login_at null, cancelled_at null)`。`verified_email` 与 `email_state=VERIFIED` 同步，用唯一索引保证"每个邮箱至多属于一个账号"（REQ-FUNC-031）；`phone` 唯一且可空——注销后置空（REQ-FUNC-027）。
- `accounts_wechat_identity(id, user_id fk, channel{MINIAPP,WEB}, openid varchar(64), unionid varchar(64) null idx, created_at)`，唯一 `(channel, openid)`。
- `accounts_admin(id, username unique, password, is_active, created_at, created_by_admin_id null)`。
- `accounts_auth_token(id, key_hash char(64) unique, principal{MEMBER,ADMIN}, user_id fk null, admin_id fk null, session_kind{IDLE,EXTENDED}, created_at, last_active_at)`；会话期限规则见 IFC-038 `authenticate_token`；约束：user_id 与 admin_id 恰有一个非空（`CheckConstraint`，MySQL 8.0.16+ 执行；SQLite 执行）。
- `accounts_verification_code(id, target varchar(254), target_type{PHONE,EMAIL}, purpose, code_hmac char(64), expires_at, attempts smallint default 0, consumed_at null, created_at, ip null)`，索引 `(target, purpose, created_at)`。
- `accounts_wechat_login_state(state_hash char(64) pk, expires_at, consumed_at null)`（Web 扫码 CSRF `state`，10 分钟）。
- `accounts_login_ticket(ticket_hash char(64) pk, user_id fk, expires_at, consumed_at null)`（回调到前端的一次性票据，60 秒，单次使用）。

**服务接口（内部，供 MOD-007 等调用）**：

| IFC | 签名 |
|---|---|
| IFC-038 | `class AccountService:`<br>`def send_code(self, *, target: str, target_type: Literal["PHONE","EMAIL"], purpose: CodePurpose, ip: str) -> CodeSent  # 限流：间隔/时/日/IP/目标锁定；超限抛 RateLimited(retry_after)`<br>`def verify_code(self, *, target: str, purpose: CodePurpose, code: str) -> None  # 成功即 consumed；失败原子 attempts+1；抛 CodeInvalid/CodeExpired/CodeLocked`<br>`def register_by_phone(self, *, phone: str, code: str, email: str \| None) -> User`<br>`def login_by_phone_code(self, *, phone: str, code: str) -> User  # 未注册抛 PhoneNotRegistered（不创建账号）`<br>`def login_by_password(self, *, identifier: str, password: str) -> User  # identifier 为 account_no 或手机号；统一错误，不泄露账号是否存在`<br>`def login_by_email_code(self, *, email: str, code: str) -> User  # 见 OQ-11 规则`<br>`def get_or_create_wechat_user(self, *, channel: Channel, openid: str, unionid: str \| None, nickname: str \| None, avatar_url: str \| None) -> tuple[User, bool]  # 新建为游客，不强制手机号；有 unionid 且已存在同 unionid 身份则归并到该用户`<br>`def issue_token(self, principal: User \| AdminAccount, *, session_kind: SessionKind) -> str  # 返回明文 key，库存哈希；管理员只能 IDLE；小程序登录一律 EXTENDED（session.miniapp_extended）；Web 勾选 remember_me 为 EXTENDED，否则 IDLE`<br>`def authenticate_token(self, key: str, *, now: datetime) -> Principal  # 哈希查库；IDLE：now - last_active_at ≥ session.idle_seconds（管理员 session.admin_idle_seconds）→ 失效；EXTENDED：now - created_at ≥ session.extended_seconds → 失效（绝对 7 天，不随活动延长）；失效即删除该令牌并抛 AuthenticationFailed；IDLE 的 last_active_at 写库节流 300 s；用户 status≠ACTIVE 视为失效（注销后既有会话立即失效，AC-069-06）`<br>`def revoke_tokens(self, user_id: UserId) -> int`<br>`def set_password(self, user: User, password: str, confirm: str) -> None  # 规则见 C-08`<br>`def update_profile(self, user: User, data: ProfilePatch) -> User`<br>`def set_declared_email(self, user: User, email: str \| None) -> None  # 状态置 UNVERIFIED_CHANGED，并清 verified_email`<br>`def verify_email(self, user: User, email: str, code: str) -> None  # 事务：清除他人同邮箱记录（审计 EMAIL_OWNERSHIP_CHANGED），本人置 VERIFIED`<br>`def tombstone(self, user: User) -> None  # 供注销：清空 phone/email/verified_email/nickname/avatar/password/gender/birthday/wechat_identity，status=CANCELLED，吊销全部令牌`<br>`def fill_empty_profile_from(self, primary: User, secondary: User) -> None  # 供合并（REQ-FUNC-029）` |

**HTTP 接口**：

| IFC | 方法 路径 | 鉴权 | 请求体 / 参数 | 成功响应 | 校验与错误 |
|---|---|---|---|---|---|
| IFC-020 | `POST /auth/codes` | PUB | `{target: str, target_type: "PHONE"\|"EMAIL", purpose: "REGISTER"\|"LOGIN"\|"EMAIL_LOGIN"}` | 202 `{resend_after: int, expires_in: int}` | 手机号 `^1[3-9]\d{9}$`；邮箱 ≤ 254 且格式合法；`purpose` 与 `target_type` 须匹配（EMAIL_LOGIN↔EMAIL，其余↔PHONE）；REGISTER 时手机号已注册 → 409 `PHONE_ALREADY_REGISTERED`；限流 → 429 `CODE_RATE_LIMITED` `{retry_after}`；上游失败 → 502 `SMS_SEND_FAILED`/`EMAIL_SEND_FAILED`。LOGIN 对未注册手机号**也返回 202**（不泄露注册状态；真正的"未注册"提示在 IFC-023 提交时给出，满足 AC-003-05） |
| IFC-021 | `POST /me/codes` | M | `{target, target_type, purpose: "BIND_PHONE"\|"CHANGE_PHONE"\|"CANCEL"\|"EMAIL_VERIFY"}` | 202 同上 | 同上；`CHANGE_PHONE/BIND_PHONE` 的新手机号**可以**已属他人（触发合并，REQ-FUNC-026/028）；`CANCEL` 发往本人已验证手机号，无手机号 → 409 `PHONE_REQUIRED` |
| IFC-022 | `POST /auth/register` | PUB | `{phone, code, email?: str}` | 201 `AuthResult{token, user: UserBrief, is_new: true}` | `code ^\d{6}$`；验证码错误/过期 → 400 `CODE_INVALID`/`CODE_EXPIRED`；错误达上限 → 429 `CODE_LOCKED`；手机号已注册 → 409 `PHONE_ALREADY_REGISTERED`；邮箱格式非法 → 400；注册邮箱仅存为 `UNVERIFIED_REG`（AC-001-03） |
| IFC-023 | `POST /auth/login/code` | PUB | `{phone, code, remember_me?: bool}` | 200 `AuthResult` | 未注册 → 404 `PHONE_NOT_REGISTERED`（不创建账号）；其余同 IFC-022 |
| IFC-024 | `POST /auth/login/password` | PUB | `{identifier: str, password: str, remember_me?: bool}` | 200 `AuthResult` | `identifier` ≤ 32；`password` ≤ 128；账号不存在、密码错误、未设置密码一律返回 400 `LOGIN_FAILED`，文案统一为"账号或密码错误；若从未设置过密码，请使用验证码登录"，响应体与耗时形态一致，不泄露账号是否存在或是否设置过密码（OQ-16 = A 已决，AC-003-03、005-02、006-03）；同一账号/手机号（规范化标识）连续输错 5 次 → 锁定 15 分钟，锁定期内一律 429 `LOGIN_LOCKED`（含正确密码，AC-032-05），成功登录清零；标识不存在时同样计数（`RateLimiter.register_failure`，key=`pwfail:<标识>`） |
| IFC-025 | `POST /auth/login/email` | PUB | `{email, code, remember_me?: bool}` | 200 `AuthResult` | 邮箱未关联任何账号 → 404 `EMAIL_NOT_LINKED`（AC-007-03，不创建账号）；**OQ-11 规则（已决）**：仅当 ①存在 `verified_email == E` 的账号（`VERIFIED`），或 ②恰好一个账号填写了 E 且其 `email_state == UNVERIFIED_REG`（注册时填写、从未修改）时允许登录；若 E 是注册后修改过的（`UNVERIFIED_CHANGED`），或被两个及以上账号同时填写且均未验证 → 403 `EMAIL_LOGIN_NOT_ALLOWED`（message：该邮箱须在登录后验证，AC-007-06），不进入任何账号、不改变邮箱归属；**不存在** 邮箱+密码入口，传 `password` 字段 → 400 `PASSWORD_NOT_SUPPORTED_FOR_EMAIL`（AC-007-02）；成功即把该邮箱置 VERIFIED（若满足规则）并清除他人同邮箱记录 |
| IFC-026 | `POST /auth/logout` | M 或 A | 空 | 204 | 吊销当前令牌 |
| IFC-027 | `POST /auth/wechat/miniapp` | PUB | `{code: str, remember_me?: bool}`（`wx.login` 的 code） | 200/201 `AuthResult{token, user, is_new}` | `code` 非空 ≤ 128；`WeChatError` → INVALID_CODE→400 `WECHAT_CODE_INVALID`、RATE_LIMITED→429、BLOCKED→403 `WECHAT_LOGIN_BLOCKED`、UPSTREAM_DOWN/NOT_CONFIGURED/IP_NOT_WHITELISTED→503 `WECHAT_UNAVAILABLE`。小程序一律签发 `EXTENDED` 会话（7 天，REQ-FUNC-064），`remember_me` 字段被忽略。**REQ-FUNC-065（OQ-05 = A）**：新用户昵称与头像置空、响应 `is_new=true`，客户端据此进入头像昵称设置页（头像经 IFC-033 转存、昵称经 IFC-032 保存）；`is_new=false`（含已关联微信的再次登录、手机号登录）不进入该页，服务端任何路径都不用微信信息覆盖已有昵称/头像（AC-070-02/03）。**不返回 session_key** |
| IFC-028 | `GET /auth/wechat/web/params` | PUB | — | 200 `{appid: str, scope: "snsapi_login", redirect_uri: str, state: str, fast_login: 1}` | 服务端生成随机 `state` 并存哈希（10 分钟）；`redirect_uri` 由服务端配置（`WECHAT_WEB_REDIRECT_URI`，须与开放平台审核的授权回调域一致），前端不得自带；网站应用未配置 → 503 `WECHAT_UNAVAILABLE` |
| IFC-029 | `GET /auth/wechat/web/callback?code=&state=` | PUB（浏览器重定向目标） | 查询参数 | 302 到前端 `/login/wechat?ticket=<一次性票据>`；失败 302 到 `/login/wechat?error=<code>` | `state` 必须命中未过期、未消费的记录，否则 error=`STATE_INVALID`；用户在微信中拒绝授权时微信不会回调（AC-002-03，前端提示由二维码失效/超时驱动）；交换失败 error=`WECHAT_CODE_INVALID`/`WECHAT_UNAVAILABLE`；**令牌绝不出现在 URL**，URL 中只有 60 秒单次票据 |
| IFC-030 | `POST /auth/wechat/web/exchange` | PUB | `{ticket: str, remember_me?: bool}` | 200 `AuthResult` | 票据过期/已用 → 400 `TICKET_INVALID` |
| IFC-031 | `PUT /me/password` | M | `{password: str, password_confirm: str, current_password?: str}` | 204 | 两次不一致 → 400 `PASSWORD_MISMATCH`；未填确认 → 400 `PASSWORD_CONFIRM_REQUIRED`；不符规则 → 400 `PASSWORD_RULE_VIOLATION` `{details: {password: [具体规则]}}`；已设置过密码时必须带正确 `current_password`（`[ASSUMPTION]`，需求只规定首次设置） |
| IFC-032 | `GET /me/profile`；`PATCH /me/profile` | M | PATCH：`{nickname?: str(1..30), gender?: 0\|1\|2, birthday?: date, email?: str\|null, avatar_attachment_id?: UUID}` | 200 `ProfileView{account_no, phone(脱敏), nickname, avatar_url, gender, birthday, email(脱敏), email_state}` | **请求体含 `identity/role/units/seat` 等任何身份字段 → 400 `FIELD_NOT_EDITABLE`**（AC-030-06）；昵称不查重、不做内容审核；`birthday` 不得晚于今天；改邮箱 → `UNVERIFIED_CHANGED` 并清 `verified_email`；头像须是本人上传的 `AVATAR` 附件 |
| IFC-033 | `POST /me/avatar` | M | multipart `file` | 201 `AttachmentRef` | 同 IFC-004（purpose 固定为 AVATAR）；微信头像 URL 会过期（官方说明），首次微信登录时若拿到 `headimgurl` 须服务端转存为附件，不直接保存外链 |
| IFC-034 | `POST /me/email/verify` | M | `{email, code}` | 200 `{email_state: "VERIFIED"}` | `email` 必须等于本人当前填写的邮箱；验证码校验同上；成功后他人同邮箱记录清除并审计 |
| IFC-035 | `POST /admin/auth/login` | PUB | `{username, password}` | 200 `{token, admin: {id, username}}` | 会话 `session_kind=IDLE`（无"记住我"；请求体含 `remember_me` → 400 `UNKNOWN_FIELD`，AC-069-05；闲置 `session.admin_idle_seconds`=1800 秒失效）；失败 400 `LOGIN_FAILED` 并审计 `ADMIN_LOGIN_FAILED`；连续失败限流同 IFC-024；普通用户的令牌访问 `/admin/**` → 403 `FORBIDDEN`（AC-011-02） |
| IFC-036 | `POST /admin/admins` `{username(3..32,字母数字_-), password}` → 201；`POST /admin/admins/{id}/reset-password` `{password}` → 204；`GET /admin/admins` → `Page[{id, username, is_active, created_at}]` | A | 如左 | | 密码规则同 C-08（长度 8~64、含字母和数字、非全数字、非常见弱口令、不得与用户名相同）；用户名重复 → 409 `USERNAME_TAKEN`；**重置密码（REQ-FUNC-068，US-073）**：目标须是**其他**管理员（`id` = 当前管理员 → 400 `CANNOT_RESET_SELF`，字面"重置其他管理员"，OQ-23），目标不存在 → 404；成功后目标旧密码立即失效且吊销其全部令牌（AC-073-01），写审计 `ADMIN_PASSWORD_RESET`、创建写 `ADMIN_CREATED`（审计属架构暂定，OQ-23）；普通用户令牌或未登录访问 → 403 / 401（AC-073-02/03）；**不存在公开注册入口与自助找回入口**（AC-011-03、AC-073-03）。首个管理员：`manage.py create_admin --username <u>`（口令交互输入或环境变量，不写命令行参数） |
| IFC-037 | `GET /admin/users?q=<账号/手机号后四位/昵称>&page=` → `Page[AdminUserItem{id, account_no, phone(脱敏), nickname, status}]` | A | `q` ≤ 32 | | 管理员选人（赋予业委会身份）用；`q` 为纯手机号全量时仍只返回脱敏手机号 |

**依赖模块**：MOD-001（审计、限流、附件）、MOD-002（短信/邮件/微信）。
**外部依赖**：微信（经 IFC-010）、短信、邮件。

### MOD-004 registry

**职责**：业主清册的存储与维护；为逐级选择提供选项；为认证提供"手机号是否登记在某专有部分"的判断。**任何非管理员接口都不返回清册手机号**。
**数据表**：
- `registry_unit(id, building varchar(32), unit_no varchar(32), floor varchar(16), room varchar(16), specific_part varchar(100) unique, created_at, updated_at)`，唯一 `(building, unit_no, floor, room)`；`specific_part` 按"楼-单-层-户"拼接（术语依据：requirements_spec.md 执行摘要末条，引用 Freeark `docs/requirements/v1.8.0_miniprogram_owner_account/requirements_spec.md:58-64`）。
- `registry_phone(id, unit_id fk, phone char(11), created_at)`，唯一 `(unit_id, phone)`，索引 `phone`。

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-040 | `GET /units/options?building=&unit_no=&floor=` → `{level: "building"\|"unit_no"\|"floor"\|"room", options: list[{value: str, unit_id?: int}]}` | M | 参数按层级逐个出现；缺上级参数而给下级 → 400 `INVALID_QUERY`；`room` 层返回 `unit_id`；**响应中不含任何手机号或"是否已有户主"之类可推断他人信息的字段** |
| IFC-041 | `GET /admin/registry/units?q=&page=` → `Page[RegistryUnitAdminView{id, specific_part, building, unit_no, floor, room, phones: list[str /*明文*/]}]`；`POST /admin/registry/units`；`PATCH /admin/registry/units/{id}`；`DELETE /admin/registry/units/{id}`；`PUT /admin/registry/units/{id}/phones` `{phones: list[str]}` | A | 楼栋/单元/楼层/户号各 1..32 字符、不含 `-` 与控制字符；`phones` ≤ 10 个、每个 `^1[3-9]\d{9}$`、去重；删除有有效 `UnitMembership` 的专有部分 → 409 `UNIT_IN_USE`；修改/删除手机号**不改变**既有身份（REQ-FUNC-033），只影响之后比对；全部写操作审计 `REGISTRY_UNIT_CHANGED`。这是唯一返回明文手机号的接口族（US-019 AC-019-06），其余页面一律脱敏 |
| IFC-042 | `POST /admin/registry/import`（multipart `file`；`dry_run?: bool`）→ 200 `ImportResult{imported: int, updated: int, failed: int, errors: list[{row: int, reason: str}]}` | A | 仅 `.xlsx`/`.csv`（UTF-8，含 BOM 容忍），文件 ≤ 5 MB、≤ 5000 行；列：`楼栋,单元,楼层,户号,手机号`（手机号单元格内多个用英文分号分隔，OQ-12 已决，REQ-FUNC-018）；**缺少上述任一列 → 400 `IMPORT_COLUMNS_MISSING`，`details.columns` 列出缺少的列名，清册不发生任何改变**（AC-019-08）；非 Excel/CSV 或无法解析 → 400 `IMPORT_FILE_INVALID`，**清册不发生任何改变**（AC-019-03）；列齐全但个别行无效（楼栋/单元/楼层/户号为空或超长、手机号格式非 C-19）：`dry_run=false` 时无效行跳过、有效行入库、返回逐行原因（需求对清册导入的校验规则与重复记录处理尚未给出——REQ-FUNC-018 备注，故该行为 `[ASSUMPTION]`，需求只规定收入表为"跳过并提示"）；解析 xlsx 用只读模式并限制行数以防压缩炸弹；审计 `REGISTRY_IMPORTED`（仅记条数） |
| IFC-043 | `RegistryService.phone_registered(unit_id: int, phone: str) -> bool`；`RegistryService.get_unit(unit_id: int) -> UnitInfo \| None` | 内部 | — |

**依赖**：MOD-001。**外部依赖**：`openpyxl`（xlsx 读取）。

### MOD-005 residency

**职责**：产权业主/户主/同住人关系的唯一事实来源；清册认证；申诉；同住人申请、拒绝、移除、退出；户主接任。
**数据表**：
- `residency_membership(id, user_id fk, unit_id fk, role{HEAD,OWNER,RESIDENT}, source{REGISTRY,APPEAL,APPLICATION}, certified_at, ended_at null, end_reason{REVOKED,CANCELLED,REMOVED,LEFT,MERGED,UPGRADED} null, active_slot smallint null, head_slot smallint null)`；唯一 `(user_id, unit_id, active_slot)`、唯一 `(unit_id, head_slot)`（均为"槽位列"，ADR-017）；`role=HEAD ⇒ head_slot=1`。户主接任 = 把最早的有效 OWNER 记录改为 HEAD 并置 `head_slot=1`，旧户主记录先结束。
- `residency_appeal(id, user_id fk, unit_id fk, status{PENDING,APPROVED,REJECTED}, submitted_at, decided_at null, decided_by_admin_id null, reject_reason varchar(500) null, pending_slot smallint null)`，唯一 `(user_id, unit_id, pending_slot)`；产权证明经附件 `linked_type="appeal"` 关联。Q30 时限未定：不设超时动作。
- `residency_resident_application(id, applicant_id fk, unit_id fk, status{PENDING,APPROVED,REJECTED}, decided_by_id fk null, decided_at null, created_at, pending_slot smallint null)`，唯一 `(applicant_id, unit_id, pending_slot)`。

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-050 | `POST /certifications` `{unit_id: int}` → 201 `CertificationResult{unit_id, role: "HEAD"\|"OWNER"}` | M | 用户无已验证手机号 → 409 `PHONE_REQUIRED`（AC-021-02，客户端引导 IFC-071）；`unit_id` 不存在 → 404；手机号与该专有部分清册均不一致 → 422 `PHONE_NOT_IN_REGISTRY`（响应附 `appeal_available: true`，**不泄露清册内容**，AC-021-03）；已是产权业主/户主 → 409 `ALREADY_CERTIFIED`；已是同住人则升级为产权业主（取高）。事务内锁定 `registry_unit` 行（MySQL）并依赖唯一约束，重复 `IntegrityError` 重试一次；若该专有部分无有效户主则新认证者为 `HEAD`（Q29/Q39，AC-023-01/03/04）；审计 `CERTIFY_BY_REGISTRY`、`HEAD_ASSIGNED`。限流 30 次/小时/用户 |
| IFC-051 | `POST /appeals` `{unit_id: int, proof_ids: list[UUID](1..5)}`（`proof_ids` 为先经 IFC-004 以 `purpose=APPEAL_PROOF` 逐个上传得到的附件 id）→ 201 `AppealView`；`GET /appeals/mine` → `list[AppealView{id, unit, status, submitted_at, decided_at?, reject_reason?}]` | M | 无附件（`proof_ids` 为空）→ 400 `PROOF_REQUIRED`（AC-026-04）；附件格式（jpg/jpeg/png/pdf）与单个 ≤ 10 MB 在上传时校验（IFC-004，类型不符 400、超大 413），附件超过 5 个 → 400 `ATTACHMENT_LIMIT`，不创建申诉（AC-026-07；恰 5 个且各 10 MB 成功，C-18）；附件须是本人上传的 TEMP 附件；同一用户同一专有部分已有待审申诉 → 409 `APPEAL_PENDING`；已是产权业主 → 409；审计 `APPEAL_SUBMITTED` |
| IFC-052 | `GET /admin/appeals?status=&page=` → `Page[AdminAppealView{…, applicant: {id, account_no, phone(脱敏)}, proof: list[AttachmentRef]}]`；`POST /admin/appeals/{id}/decision` `{decision: "APPROVE"\|"REJECT", reject_reason?: str(≤500)}` | A | 已处理 → 409 `ALREADY_DECIDED`；APPROVE 时与 IFC-050 同一"授予产权业主/首位成为户主"逻辑（AC-026-02、AC-023-05/06）；REJECT 要求 `reject_reason`；审计 `APPEAL_DECIDED`；申诉页手机号一律脱敏（AC-019-07） |
| IFC-053 | `POST /resident-applications` `{unit_id}` → 201；`GET /resident-applications/mine`；`GET /resident-applications/to-review`（仅返回当前用户为有效 OWNER/HEAD 的专有部分的待审申请）；`POST /resident-applications/{id}/decision` `{decision: "APPROVE"\|"REJECT"}` | M（对象级：审批人须为该专有部分的有效 OWNER/HEAD） | 专有部分当前无有效产权业主 → 409 `UNIT_HAS_NO_OWNER`，**不创建申请**（REQ-FUNC-032，AC-024-06）；重复申请待审 → 409；非该房产权业主审批 → 403；已被处理 → 409 `ALREADY_DECIDED`（以条件更新 `WHERE status='PENDING'` 判断，AC-024-04）；拒绝后申请人状态保持非同住人且可再申请（AC-029-01）；审计 `RESIDENT_APPLICATION_DECIDED` |
| IFC-054 | `DELETE /units/{unit_id}/residents/{user_id}`（产权业主移除同住人）；`POST /units/{unit_id}/leave`（同住人退出） | M（对象级） | 非该专有部分有效 OWNER/HEAD → 403（管理员也不可，AC-029-04）；目标不是该房同住人 → 404；成功 204；审计 |
| IFC-055 | 内部：`class MembershipService:`<br>`def certify_owner(self, user_id: UserId, unit_id: int, source: Literal["REGISTRY","APPEAL"]) -> UnitRole  # 返回 HEAD 或 OWNER`<br>`def end_membership(self, membership_id: int, reason: EndReason) -> None`<br>`def promote_head_if_vacant(self, unit_id: int) -> UserId \| None  # 认证时间最早的有效 OWNER 接任；无则返回 None，unit 暂无户主`<br>`def list_active(self, user_id: UserId) -> list[MembershipView]`<br>`def is_owner_of_any(self, user_id: UserId) -> bool`<br>`def is_owner_of(self, user_id: UserId, unit_id: int) -> bool  # OWNER 或 HEAD`<br>`def is_owner_or_resident_of_any(self, user_id: UserId, *, include_residents: bool) -> bool`<br>`def revoke_owner(self, user_id: UserId, unit_id: int) -> RevokeResult{was_head: bool, new_head_id: UserId \| None}  # 供 MOD-007，REQ-FUNC-034/020`<br>`def merge_memberships(self, primary_id: UserId, secondary_id: UserId) -> None  # 同房取高；跨房全保留` | 内部：所有写方法要求调用方已开启事务；户主接任审计 `HEAD_SUCCEEDED` |

**依赖**：MOD-001、MOD-003（User 外键）、MOD-004（比对）。启动时向 MOD-001 注册附件下载策略 `register_attachment_policy("appeal", …)`（申诉人本人与 `A` 可下载）。

### MOD-006 committee

**职责**：业委会席位（主任/副主任/委员）与业主代表席位；人数上限与任期配置；任期到期与资格失效；为其他模块提供"现任身份"查询。
**数据表**：
- `committee_config(id=1 单例, cap_chair int null, cap_vice int null, cap_member int null, cap_rep int null, term_months_chair int null, term_months_vice int null, term_months_member int null, term_months_rep int null, updated_at, updated_by_admin_id)`。初始数据迁移写入 `cap_chair=1, cap_vice=2, cap_member=6`（用户已确认的 9 人，Q77/Q88，C-13）；**任期与业主代表人数上限默认为空 = 未配置，未配置时不允许赋予对应身份**（`TERM_NOT_CONFIGURED`/`CAP_NOT_CONFIGURED`），因为用户未给数值，不自拟。
- `committee_seat(id, user_id fk, position, term_start date, term_end date, status{ACTIVE,REVOKED,EXPIRED,INVALIDATED,REPLACED,MERGED}, ended_at null, end_reason varchar(48) null, granted_by_admin_id, created_at, active_slot smallint null)`，唯一 `(user_id, active_slot)`（一人同一时间一个业委会/业主代表身份，REQ-FUNC-053）。变更 = 结束旧席位（`REPLACED`）并新建。

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-060 | `GET /admin/committee/seats?position=&status=&page=` → `Page[SeatView{id, user: {id, account_no, nickname, phone(脱敏)}, position, term_start, term_end, status}]`；`POST /admin/committee/seats` `{user_id: int, position: SeatPosition, term_start?: date}`；`PATCH /admin/committee/seats/{id}` `{position: SeatPosition}`（变更）；`DELETE /admin/committee/seats/{id}`（撤销） | A | 目标须是有效产权业主（含户主）：否则 422 `NOT_AN_OWNER`（同住人/游客不可，Q42）；目标已有有效席位 → 409 `ALREADY_SEATED`（变更请用 PATCH；业委会与业主代表不可兼任，Q85=B，PATCH 可在二者间变更）；该身份在任人数 ≥ 上限 → 409 `CAP_REACHED`（含"调低到低于现任后，在任人数不低于新上限时不得再赋予"，Q102=B）；任期未配置 → 409 `TERM_NOT_CONFIGURED`；`term_end = term_start + term_months`（`term_start` 缺省为今天，不得早于今天 − 1 天）；先插入后复核计数，超限则回滚（防并发超员）；审计 `SEAT_GRANTED/CHANGED/REVOKED`；撤销/变更对在途事项无自动影响（REQ-FUNC-063） |
| IFC-061 | `GET /admin/committee/config` → `CommitteeConfigView`；`PUT /admin/committee/config`（部分字段可空）`{cap_chair?: int(0..50), cap_vice?: …, cap_member?: …, cap_rep?: int(0..500), term_months_chair?: int(1..120), …}` | A | 数值越界 → 400；**允许调低到低于现任人数**（Q102=B），响应附 `over_cap: list[{position, current, cap}]` 提示；总上限不强制等于 9（用户确认 9 为配置值，非硬编码，C-13）；审计 `COMMITTEE_CONFIG_CHANGED`（含变更前后值） |
| IFC-062 | 内部：`class CommitteeQuery:`<br>`def active_seat(self, user_id: UserId) -> SeatView \| None  # 请求级缓存`<br>`def is_member(self, user_id: UserId) -> bool  # CHAIR/VICE_CHAIR/MEMBER`<br>`def is_chair_or_vice(self, user_id: UserId) -> bool`<br>`def is_representative(self, user_id: UserId) -> bool`<br>`def active_member_ids(self) -> list[UserId]`<br>`def active_representative_ids(self) -> list[UserId]`<br>`def identity_labels(self, user_id: UserId) -> list[str]  # 供公开内容"发起人身份快照"`<br>`def denominator_for_half_majority(self, mode: Literal["ACTIVE","CONFIGURED_CAP"]) -> int` | 内部：查询**同时校验任期**（`term_end >= today`），因此即使定时任务未执行，到期者也立即无权限 |
| IFC-063 | 内部：`class CommitteeCommands:`<br>`def sync_after_ownership_change(self, user_id: UserId) -> SeatInvalidation \| None  # 用户不再是任何专有部分的有效产权业主 ⇒ 席位 INVALIDATED，释放名额（REQ-FUNC-053，Q101=A）`<br>`def merge_seats(self, primary_id: UserId, secondary_id: UserId) -> None  # 取高（REQ-FUNC-061）；同级只留一个；被淘汰者 MERGED`<br>`def expire_due(self, today: date) -> int  # 到期置 EXPIRED，审计 SEAT_EXPIRED` | 内部：均幂等 |

**依赖**：MOD-001、003、005（`is_owner_of_any`）。

### MOD-007 identity

**职责**：编排跨模块的身份生命周期用例与聚合视图；不拥有业务表。所有用例在**单个数据库事务**内完成（审计同事务）。
| IFC | 签名 / 路由 | 鉴权 | 输入校验、业务规则与错误 |
|---|---|---|---|
| IFC-070 | `GET /me` → `MeView{profile: ProfileView, identities: IdentitySummary}`；`IdentitySummary{is_guest: bool, units: list[{unit_id, specific_part, role: UnitRole}], committee: {position: SeatPosition, term_end: date} \| None, labels: list[str]}`（`labels` 如 `["游客"]`、`["户主","业委会主任"]`） | M | 只读（REQ-FUNC-036）。`is_guest = len(units)==0`；业主代表以 `committee.position=REPRESENTATIVE` 返回 |
| IFC-071 | `POST /me/phone/bind` `{phone: str, code: str}` 或 `{wx_phone_code: str}`（后者仅当 `wechat.phone_quick_verify_enabled`） → 200 `{merged: bool, user: UserBrief, token?: str}` | M（用户当前无手机号） | 验证码校验同 C-06；手机号不属于任何账号 → 仅绑定（AC-012-03）；属于其他账号 B → **合并**：以 B 为主账号（REQ-FUNC-029），调用 `MergeService.merge(primary=B, secondary=当前)`，成功后当前令牌失效并返回属于主账号的新 `token`（AC-012-01）；验证失败 → 400，两账号不变（AC-012-02）；用户已有手机号 → 409 `PHONE_ALREADY_BOUND`（应走换号）；`wx_phone_code` 未启用 → 400 `FEATURE_DISABLED` |
| IFC-072 | `POST /me/phone/change` `{new_phone, code}` → 200 `{merged: bool, token?: str}` | M | 新号 = 当前号 → 400；新号未被占用 → 更换，身份保留（AC-028-01），旧号立即不能登录（AC-028-04）；新号属于其他账号 B → 合并，**主账号为 B**（规则与微信绑定一致，REQ-FUNC-028）；`CHANGE_PHONE` 验证码错误 → 400 且不变更；审计 `PHONE_CHANGED`/`ACCOUNTS_MERGED`。已知风险：令牌被盗即可换号，需求未要求二次验证旧号，见风险表 |
| IFC-073 | `POST /me/cancel` `{code}` → 204 | M | 验证码发往本人手机；无手机号 → 409 `PHONE_REQUIRED`（`[ASSUMPTION]`：需求要求验证码二次确认但纯微信用户没有可发验证码的手机号，暂定先绑定手机号，OQ-25）；用例顺序：①对每个本人 HEAD 记录 `promote_head_if_vacant` ②结束全部成员关系 ③`sync_after_ownership_change`（席位失效）④**在途事项不变**（REQ-FUNC-063，只靠 `User` 墓碑使其显示"已注销用户"）⑤删除附件头像等个人资料 ⑥`tombstone` ⑦吊销全部令牌；审计 `ACCOUNT_CANCELLED`，如有接任审计 `HEAD_SUCCEEDED`；成功后同手机号可作为全新账号注册（AC-013-01） |
| IFC-074 | `POST /admin/memberships/revoke` `{user_id: int, unit_id: int}` → 200 `{was_head: bool, new_head_id: int \| null, seat_invalidated: bool}` | A | 目标须为该专有部分有效 OWNER/HEAD，否则 404；撤销 HEAD 时按 REQ-FUNC-020 接任；之后调用 `sync_after_ownership_change`（仅当用户已不是任何专有部分产权业主才失效席位，Q101=A）；审计 `CERTIFICATION_REVOKED`（含接任与席位影响，AC-036-05）；**管理员入口仅此，普通用户无** |
| IFC-075 | 内部：`class MergeService:`<br>`def merge(self, *, primary: User, secondary: User, trigger: Literal["WECHAT_BIND","PHONE_CHANGE"]) -> MergeReport`<br>步骤（同一事务；先按 id 升序对两个用户行加锁）：①`fill_empty_profile_from`（资料：以 primary 为准，空项补充；密码与凭据保留 primary）②微信身份并入 primary ③`merge_memberships`（同房取高、跨房保留、每房仍至多一个户主）④`merge_seats`（取高，同级只留一个，名额释放）⑤按下方"合并引用登记表"把 secondary 的其余引用改指向 primary（REQ-FUNC-067：同一投票/调查两账号均已作答→保留 primary 答卷、丢弃 secondary 答卷并审计 `MERGE_ANSWER_DISCARDED`；其余待办与进行中事项归 primary）⑥吊销 secondary 全部令牌 ⑦删除 secondary 行⑧审计 `ACCOUNTS_MERGED`（只记账号编号，不记手机号明文） | 内部 | 失败整体回滚；`MergeReport{kept_roles, released_seats, moved_refs}` 写入审计 detail |

**合并引用登记表**（`register_user_reference`，IFC-008；各业务模块在自己的 app 启动时登记，MOD-007 不 import 它们；启动检查保证凡指向 `accounts.User` 的外键都已登记）：
| 表.字段 | 策略 | 说明 |
|---|---|---|
| `accounts_wechat_identity.user_id` | `move_all` | 微信登录方式并入 primary（AC-015-03）；`(channel, openid)` 唯一，不会冲突 |
| `accounts_auth_token.user_id` | `delete_secondary` | 吊销 secondary 全部令牌 |
| `residency_membership.user_id` | `custom`（`merge_memberships`） | 同房取高、跨房保留（REQ-FUNC-030） |
| `residency_appeal.user_id`、`residency_resident_application.applicant_id` | `move_all`；`(user, unit, pending_slot)` 冲突时 `keep_primary` 并关闭 secondary 的待审记录 | 待办归 primary（`[ASSUMPTION]`，OQ-21） |
| `residency_resident_application.decided_by_id` | `move_all` | 历史审批人 |
| `committee_seat.user_id` | `custom`（`merge_seats`） | REQ-FUNC-061：取高；同级只留一个；被淘汰者 `MERGED` 并释放名额；审计 `SEAT_INVALIDATED` |
| `approval_flow_approver.user_id` | `custom` | 双方都是同一流程的审批人→删除 secondary 行，否则 `move_all`（`(flow, user)` 唯一） |
| `approval_instance.submitter_id`、`.decided_by_id`、`approval_action.actor_id` | `move_all` | 历史与发起人 |
| `approval_instance.flow_snapshot.approver_ids`（JSON，非外键） | `custom` | 仅处理 `PENDING` 实例：把 secondary 的 id 替换为 primary 并去重，使待办审批任务归合并后账号（AC-072-04）；若 primary 就是申请人，仍受 REQ-FUNC-062 不得自审约束 |
| `resolutions_resolution.initiator_id` | `move_all` | `initiator_labels` 快照不变（REQ-FUNC-063） |
| `resolutions_vote.voter_id` | `move_all`；`(resolution, revision, voter)` 冲突时 `keep_primary` | `[ASSUMPTION]`，OQ-21（需求只规定投票/调查） |
| `claims_claim.applicant_id`、`income_sheet.creator_id`/`.voided_by_id`、`ledger_report.generated_by_id` | `move_all` | |
| `polls_poll.initiator_id` | `move_all` | |
| `polls_participant.user_id` | `move_all`；冲突时 `keep_primary` | `participant_count` 不变（Q103） |
| `polls_response.user_id`（含 `polls_answer`） | `custom` | 冲突（两账号都已作答）→ 保留 primary、删除 secondary 的答卷并写 `MERGE_ANSWER_DISCARDED`（AC-072-01）；仅 secondary 作答→ `move_all`（AC-072-02） |
| `core_attachment.owner_id`（`owner_type=MEMBER`） | `move_all` | |
| `core_audit_log.actor_id` | 不登记 | 审计只存快照与整数 id，不设外键（ADR-007） |

**依赖**：MOD-001~006。**不被其他业务模块依赖**（依赖图的顶层编排）。

### MOD-008 approval

**职责**：通用审批壳：流程配置、提交快照、同意/拒绝/撤回、资格与不得自审规则。决议的"半数同意"表决由 MOD-009 实现，但共用实例壳。
**数据表**：
- `approval_flow(id, scope{RESOLUTION,EXPENSE,INCOME}, name varchar(60), mode{DESIGNATED,HALF_MAJORITY}, is_active, created_at, updated_at)`；约束：`HALF_MAJORITY` 仅允许 `scope=RESOLUTION`。
- `approval_flow_approver(id, flow_id fk, user_id fk)`，唯一 `(flow_id, user_id)`；`DESIGNATED` 至少 1 人；`HALF_MAJORITY` 无审批人（由全体业委会成员表决）。
- `approval_instance(id, scope, subject_type varchar(32), subject_id bigint, flow_id int, flow_snapshot JSON{name, mode, approver_ids}, submitter_id fk, status, revision int, submitted_at, decided_at null, decided_by_id null, pending_slot smallint null)`，唯一 `(subject_type, subject_id, pending_slot)`。
- `approval_action(id, instance_id fk, actor_id fk, action{SUBMIT,APPROVE,REJECT,WITHDRAW}, comment varchar(500), acted_at)`。

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-080 | `GET /admin/approval/flows?scope=`；`POST /admin/approval/flows` `{scope, name(1..60), mode, approver_ids: list[int]}`；`PUT /admin/approval/flows/{id}`；`DELETE /admin/approval/flows/{id}`（有在途实例引用时仅停用 `is_active=false`） | A | 审批人必须是**当前业委会成员**（委员/主任/副主任），否则 422 `APPROVER_NOT_COMMITTEE_MEMBER`（Q48=A）；`mode=HALF_MAJORITY` 且 `scope≠RESOLUTION` → 400；`DESIGNATED` 无审批人 → 400；改动**不影响**已提交实例（快照）；审计 `APPROVAL_FLOW_CHANGED`（变更前后） |
| IFC-081 | `GET /approval/flows?scope=` → `list[FlowOption{id, name, mode}]`（只返回启用的；**不暴露审批人名单以外的信息**，审批人仅返回昵称） | M:委员+ | `scope` 必填 |
| IFC-082 | `GET /approval/tasks?scope=&status=PENDING&page=` → `Page[TaskView{instance_id, scope, subject_type, subject_id, subject_title, submitter_label, submitted_at}]`；`POST /approval/instances/{id}/decision` `{action: "APPROVE"\|"REJECT", comment?: str(≤500)}` → 200 `InstanceView` | M:委员+ 且 ∈ 实例快照 `approver_ids` | 非快照审批人 → 403；审批人**当前已不是业委会成员** → 403 `APPROVER_NO_LONGER_ELIGIBLE`（REQ-FUNC-063）；`scope ∈ {EXPENSE, INCOME}` 且 `actor == submitter` → 403 `SELF_APPROVAL_FORBIDDEN`（REQ-FUNC-062，AC-050-09、067-01~03）；`scope == RESOLUTION` 且方式为 `DESIGNATED` 时发起人若在快照审批人内**允许自批**（REQ-FUNC-066 c，AC-071-05），不在快照内则 403（AC-071-06）；实例非 PENDING → 409 `ALREADY_DECIDED`（条件更新 `UPDATE … WHERE status='PENDING'`）：**多名审批人任一人通过即通过，先处理者生效，其后审批人得 409**（REQ-FUNC-066 a，AC-071-01/02；任一拒绝同样先到先得，`[ASSUMPTION]`，OQ-22）；`REJECT` 建议带 comment；对 `HALF_MAJORITY` 的决议实例不能用此接口（→ 409 `USE_VOTE_ENDPOINT`） |
| IFC-083 | 内部：`class ApprovalEngine:`<br>`def submit(self, *, scope: Scope, subject_type: str, subject_id: int, flow_id: int, submitter: User) -> ApprovalInstance  # 财务类（EXPENSE/INCOME，含核销）：快照审批人去掉申请人本人后，**当前在任**（`CommitteeQuery.is_member`，任期有效）的人数为 0 → 抛 NoEligibleApprover（API 层转 422 `NO_ELIGIBLE_APPROVER`，message"审批流程中没有其他可审批的人"，不创建申请，REQ-FUNC-066 b，AC-071-03/04）；RESOLUTION 不做此检查；流程停用抛 FlowInactive`<br>`def withdraw(self, instance_id: int, actor: User) -> None  # 仅 submitter，仅 PENDING；不要求仍在任（OQ-14）`<br>`def resubmit(self, *, subject_type, subject_id, flow_id, submitter) -> ApprovalInstance  # 仅 REJECTED/WITHDRAWN 后，revision+1`<br>`def is_original_approver(self, instance_id: int, user_id: UserId) -> bool  # 供收入表作废（Q109=B）`<br>`def register_callbacks(self, subject_type: str, *, on_approved: Callable[[int], None], on_rejected: Callable[[int], None], on_withdrawn: Callable[[int], None]) -> None  # 回调在同一事务内、必须幂等` | 内部 |

**依赖**：MOD-001、003、006。

### MOD-009 resolutions

**职责**：业委会决议的发起、两种审批方式、半数同意表决与截止判定、审批结束后公开。
**数据表**：
- `resolutions_resolution(id, title varchar(200), content text(≤20000), initiator_id fk, initiator_labels JSON  /*发起时身份快照，如 ["业委会主任","户主"]*/, status{PENDING,APPROVED,REJECTED,WITHDRAWN}, approval_mode{DESIGNATED,HALF_MAJORITY}, vote_deadline datetime null, revision int default 1, decided_at null, result JSON null  /*{agree, disagree, abstain, denominator, denominator_mode, passed}*/, created_at, updated_at)`；附件经 `core_attachment(linked_type="resolution")`。
- `resolutions_vote(id, resolution_id fk, revision int, voter_id fk, choice{AGREE,DISAGREE,ABSTAIN}, voted_at)`，唯一 `(resolution_id, revision, voter_id)`。

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-090 | `POST /resolutions` `{title: str(1..200), content: str(1..20000), attachment_ids: list[UUID](≤10), flow_id: int, vote_deadline?: datetime}` → 201 `ResolutionView`；`GET /resolutions?scope=public\|mine\|todo&page=` → `Page[ResolutionListItem]`；`GET /resolutions/{id}` → `ResolutionView{… status, initiator_labels, attachments, my_vote?, result?}`；`POST /resolutions/{id}/withdraw`；`POST /resolutions/{id}/resubmit`（体同创建，仅 REJECTED/WITHDRAWN） | 发起/撤回/重提：`M:主任+`（撤回/重提另需是发起人）；查看：见可见性规则 | 标题、内容必填（缺 → 400）；附件数/大小/类型按 C-12 配置（超限 400 `ATTACHMENT_LIMIT`）；附件须是本人 TEMP 上传；`flow_id` 须启用且 scope=RESOLUTION；**`mode=HALF_MAJORITY` 时 `vote_deadline` 必填且 ≥ now + `vote.min_window_minutes`**（Q110 暂定），`DESIGNATED` 时传 `vote_deadline` 被忽略；审批中不可 PATCH 修改（无该接口，REQ-FUNC-055）；**可见性**：`APPROVED/REJECTED` → 全体已登录用户；`PENDING` → 发起人、业委会成员、`A`；`WITHDRAWN` → 发起人、`A`（OQ-14 已决：已撤回的决议不公开，AC-047-07；撤回由发起人账号有效即可，不要求仍在任，AC-068-07）；不可见一律 404。提交即审计 `RESOLUTION_SUBMITTED`，发起人身份快照写入 `initiator_labels`（REQ-FUNC-036/063） |
| IFC-091 | `POST /resolutions/{id}/votes` `{choice: "AGREE"\|"DISAGREE"\|"ABSTAIN"}` → 200 `{my_vote, tally?: null}` | `M:委员+`（含发起人，不回避，Q78=A） | 决议非 `PENDING` 或非 `HALF_MAJORITY` → 409；`now >= vote_deadline` → 409 `VOTE_CLOSED`（以服务器时间，客户端时间忽略）；已投 → 409 `ALREADY_VOTED`（一人一票，唯一约束）；投票者当前不是在任成员 → 403；进行中**不返回他人投票明细**；截止前不作出通过/未通过判定（REQ-FUNC-060） |
| IFC-092 | 内部：`ResolutionService.judge_if_due(resolution_id: int, now: datetime) -> Literal["PASSED","FAILED","NOT_DUE","ALREADY_DECIDED"]` 与 `judge_all_due(now: datetime) -> int`：`now >= vote_deadline` 时，`denominator = CommitteeQuery.denominator_for_half_majority(mode)`，`passed = agree*2 > denominator`（严格过半，弃权不计同意）；以条件更新 `status:PENDING→APPROVED/REJECTED` 保证幂等；写 `result` 与审计 `RESOLUTION_DECIDED`；在 `GET /resolutions/{id}` 与 `POST …/votes` 路径上也调用（惰性判定，ADR-013） | 内部 | `DESIGNATED`：审批通过/拒绝经 IFC-082 + 引擎回调更新状态与 `decided_at`，**不设时限**（Q52=A） |

**依赖**：MOD-001、006、008。

### MOD-010 claims

**职责**：报销单、备用金预借单、备用金核销单；审批通过后按 ADR-014 写台账。
**数据表**：`claims_claim(id, kind{REIMBURSEMENT,ADVANCE,SETTLEMENT}, applicant_id fk, applicant_labels JSON, reason varchar(500), amount decimal(14,2) /*报销=报销金额；预借=预借金额；核销=差额，计算得出且只读*/, occurred_on date null /*报销发生日期*/, expected_usage varchar(500) null, expected_settle_on date null, advance_id fk(self) null /*核销→被核销的预借；报销→声明用于核销的预借*/, settlement_id fk(self) null /*报销被哪张核销单占用*/, status, revision int, decided_at null, ledger_posted bool default false, created_at, updated_at, settle_slot smallint null)`；唯一 `(advance_id, settle_slot)` 保证一张预借至多一张有效核销（kind=SETTLEMENT 时槽位=1）；发票/凭证经附件 `linked_type="claim_invoice"`。
| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-100 | `POST /claims/reimbursements` `{reason: str(1..500), amount: Money, occurred_on: date, invoice_ids: list[UUID](1..10), flow_id: int, settles_advance_id?: int}` → 201 `ClaimView` | `M:委员+` | 发票至少 1 个（"报销须凭发票"，REQ-FUNC-040）；`amount` > 0 且 ≤ `claim.amount_max`（若配置；缺省无业务上限，Q96）且 ≤ 技术精度 9,999,999,999.99；`occurred_on` 不得晚于今天；`settles_advance_id` 须是**本人**已审批通过、尚无有效核销的预借（`[ASSUMPTION]` 同一申请人）；`flow_id` 须启用且 scope=EXPENSE |
| IFC-101 | `POST /claims/advances` `{reason, amount: Money, expected_usage: str(1..500), expected_settle_on: date, flow_id}` → 201 | `M:委员+` | `expected_settle_on` ≥ 今天；金额同上 |
| IFC-102 | `POST /claims/settlements` `{advance_id: int, reimbursement_ids: list[int](1..50), note?: str(≤500), flow_id}` → 201 `ClaimView{amount = Σ报销 − 预借额}` | `M:委员+`（须为预借申请人） | 预借须已通过且无其他有效核销（409 `ADVANCE_ALREADY_SETTLING`）；每张报销单须：已 APPROVED、申请人相同、`settles_advance_id == advance_id`、`settlement_id IS NULL`，否则 422 `REIMBURSEMENT_NOT_ELIGIBLE`（Q107=A）；提交时占用（写 `settlement_id`），核销被拒绝/撤回则释放；差额 <0 表示多退（现金退回登记未规定，REQ-FUNC-058 备注），>0 表示不足部分补报 |
| IFC-103 | `GET /claims?kind=&status=&scope=mine\|todo&page=` → `Page[ClaimListItem]`；`GET /claims/{id}` → `ClaimView`；`POST /claims/{id}/withdraw`；`POST /claims/{id}/resubmit` | 见右 | **可见性（Q59=A）**：明细仅发起人、快照审批人、`A`；其余用户只通过报表看汇总；不可见 404；撤回仅发起人且 PENDING；审批中不可修改；被拒后重提 revision+1；审批人不得审批自己的申请（引擎，REQ-FUNC-062） |
**回调**（引擎 `on_approved`）：报销且无 `settles_advance_id` → `LedgerService.post(EXPENSE, amount, occurred_on, type=REIMBURSEMENT)`；报销带 `settles_advance_id` → **不入账**；预借 → 入账 `amount`，发生日期=审批通过日；核销 → 入账调整额 `Σ关联报销 − 预借额`（可为负），发生日期=审批通过日；`ledger_posted` 保证幂等。
**依赖**：MOD-001、006、008、012。

### MOD-011 income

**职责**：收入表录入（单条/批量）、审批生效、作废。
**数据表**：
- `income_sheet(id, creator_id fk, creator_labels JSON, source{MANUAL,IMPORT}, title varchar(100) null, status{DRAFT,PENDING,EFFECTIVE,REJECTED,WITHDRAWN,VOID}, revision int, effective_at null, void_reason varchar(500) null, voided_by_id null, voided_at null, created_at, updated_at)`。
- `income_record(id, sheet_id fk, line_no int, occurred_on date, amount decimal(14,2), category varchar(50), source_note varchar(200) null, remark varchar(500) null)`，唯一 `(sheet_id, line_no)`；凭证附件 `linked_type="income_voucher"`。
| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-110 | `POST /income/sheets` `{records: list[IncomeRecordIn{occurred_on: date, amount: Money, category: str(1..50), source_note?: str(≤200), remark?: str(≤500), voucher_ids?: list[UUID]}](1..500), submit?: bool, flow_id?: int}` → 201 `IncomeSheetView` | `M:委员+` | 金额 > 0 两位小数；日期不得晚于今天；`submit=true` 时 `flow_id` 必填且 scope=INCOME；必填项/精度的业务口径用户未提供（Q98），此处按字段说明的最小约束，细化走配置 |
| IFC-111 | `POST /income/sheets/import`（multipart：`file`；`flow_id?: int`；`dry_run?: bool`）→ 200/201 `ImportReport{sheet_id?: int, imported: int, skipped: list[{row: int, reason: "DUPLICATE"\|"INVALID_FIELD", detail: str}]}` | `M:委员+` | `.xlsx`/`.csv`，≤ 5 MB、≤ 5000 行；列 `日期,金额,收入类别,来源说明,备注`，`凭证附件` 列即使存在也**不导入**（电子表格无法承载文件，OQ-26 `[ASSUMPTION]`）；金额最多两位小数（OQ-12，AC-059-08），超过两位小数、日期/金额无法解析的行按错误行跳过并提示；各字段必填项用户尚未给出（Q98 余项），按字段说明的最小约束处理，细化走配置；**重复记录与错误行跳过并给出行号提示，其余有效行正常导入**（REQ-FUNC-059，AC-059-02/03）；重复判定 = 同一文件内，或与已有 `PENDING/EFFECTIVE` 收入记录的 (日期,金额,类别,来源说明) 四项全同（OQ-12 已决；与已有记录比较时 `REJECTED/WITHDRAWN/VOID` 的不算 `[ASSUMPTION]`）；**文件格式非 Excel/CSV 或无法解析 → 400 `IMPORT_FILE_INVALID`，不导入任何记录**（AC-059-04）；**全部行均重复/错误 → 200，`imported=0`，不创建收入表**（AC-059-05）；有有效行时：带 `flow_id`（启用且 scope=INCOME，且通过 `NoEligibleApprover` 检查）→ 立即创建**一份**收入表并提交审批，状态 `PENDING`，不计入报表（AC-059-01/07/09）；不带 `flow_id` → 创建 `DRAFT`，之后经 IFC-112 补凭证并提交（草稿阶段才可编辑）；非业委会成员 → 403（AC-059-06）；审计 `INCOME_IMPORTED` |
| IFC-112 | `PATCH /income/sheets/{id}` `{records: list[IncomeRecordIn]}`（**仅 `DRAFT`** 可调用，整表替换，用于导入草稿补凭证；其他状态 → 409 `SHEET_NOT_EDITABLE`，REQ-FUNC-055/049）；`POST /income/sheets/{id}/submit` `{flow_id}`；`POST /income/sheets/{id}/withdraw`；`POST /income/sheets/{id}/resubmit`；`POST /income/sheets/{id}/void` `{reason: str(1..500)}`；`GET /income/sheets?status=&page=`；`GET /income/sheets/{id}` | `M:委员+`（作废：须为该表所用流程的**原审批人**，Q109=B） | 生效前不入台账；`EFFECTIVE` 后不可修改（无编辑接口），仅 `void`；作废者不是原审批人 → 403；作废以**整份收入表**为单位（OQ-13 已决，REQ-FUNC-049；AC-060-11）：作废后全部记录对应台账条目置 VOIDED，涉及期间的已生成报表置 `stale`；**不提供单行作废的路由**，对 `…/records/{line_no}` 的作废/删除请求由框架返回 404/405，收入表保持 `EFFECTIVE`；`申请人不得审批自己的收入表`（引擎）；可见性：业委会成员与 `A`（`[ASSUMPTION]`），公众只见汇总 |
**回调**：`on_approved` → 每条记录 `LedgerService.post(INCOME, …)`（发生日期=记录日期）；`void` → `LedgerService.void_by_source("income_sheet", id)`。
**外部依赖**：`openpyxl`。**依赖**：MOD-001、006、008、012。

### MOD-012 ledger

**职责**：追加式台账与季度/年度报表。
**数据表**：
- `ledger_entry(id, direction{INCOME,EXPENSE}, amount decimal(14,2) /*收入为正；支出可为负，仅核销调整允许负*/, occurred_on date idx, entry_type varchar(32) /*收入类别 | REIMBURSEMENT | ADVANCE | SETTLEMENT_ADJ*/, summary varchar(200) null, source_type varchar(32), source_id bigint, seq smallint default 0, status{ACTIVE,VOIDED}, created_at, voided_at null)`，唯一 `(source_type, source_id, seq)`（幂等）。
- `ledger_report(id, period_type{QUARTER,YEAR}, year smallint, quarter smallint null, total_income, total_expense, balance, detail JSON, stale bool, generated_at, generated_by_type{SYSTEM,MEMBER}, generated_by_id null)`，唯一 `(period_type, year, quarter)`（重生成覆盖同一行，历史由审计保存）。
| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-120 | `GET /reports?period_type=&year=` → `list[ReportBrief]`；`GET /reports/{id}` → `ReportView{period, total_income, total_expense, balance, detail: list[{date, direction, type, amount, summary?}], stale, generated_at}`；`POST /reports/generate` `{period_type: "QUARTER"\|"YEAR", year: int(2000..2100), quarter?: 1..4}` → 200 `ReportView` | 查看：`M`（所有已登录用户，含游客，REQ-FUNC-051）；生成：`M:委员+`（**管理员不可**，Q109=B） | 未来期间 → 400 `PERIOD_NOT_STARTED`；`quarter` 在 QUARTER 时必填；**报表与明细绝不含个人姓名、手机号**（Q75=A）；`summary` 仅在 `report.show_expense_reason=true` 时包含支出事由，收入只含类别（OQ-08 已决：默认不显示事由，AC-061-11、063-05）；仅 `ACTIVE` 条目、按 `occurred_on` 归期；生成后立即可见，无需审批（Q74=A）；审计 `REPORT_GENERATED` |
| IFC-121 | 内部：`class LedgerService:`<br>`def post(self, *, direction: Direction, amount: Money, occurred_on: date, entry_type: str, summary: str \| None, source_type: str, source_id: int, seq: int = 0) -> LedgerEntry  # 幂等于 (source_type, source_id, seq)；写入后将覆盖该日期所属季度/年度的报表置 stale`<br>`def void_by_source(self, source_type: str, source_id: int) -> int`<br>`def generate(self, *, period_type, year, quarter, by: Principal) -> LedgerReport`<br>`def generate_due(self, today: date) -> list[LedgerReport]  # 上季度/上年度已结束而尚无报表者` | 内部 |
**依赖**：MOD-001、006。

### MOD-013 polls

**职责**：业主代表投票与调查的发起、作答、截止汇总、结果公开。
**数据表**：
- `polls_poll(id, kind{REP_VOTE,SURVEY}, title varchar(200), description text(≤5000) null, initiator_id fk, initiator_labels JSON, survey_scope{OWNERS_ONLY,OWNERS_AND_RESIDENTS} null, deadline datetime /*必填，创建后不可改*/, status{OPEN,CLOSED}, participant_count int null /*REP_VOTE 发起时快照人数=分母*/, result_snapshot JSON null, closed_at null, created_at)`。
- `polls_question(id, poll_id fk, order smallint, qtype{AGREE_OPPOSE_ABSTAIN,SCORE,SINGLE,MULTI,TEXT}, title varchar(200), required bool, options JSON null /*SINGLE/MULTI：2..20 项，每项 ≤ 100 字*/)`；`SCORE` 固定 1..5。
- `polls_participant(poll_id fk, user_id fk)`，唯一 `(poll_id, user_id)`（仅 REP_VOTE，发起时快照，Q103=A）。
- `polls_response(id, poll_id fk, user_id fk, submitted_at)`，唯一 `(poll_id, user_id)`（一人一票）；`polls_answer(id, response_id fk, question_id fk, value JSON)`。
| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-130 | `POST /polls` `{kind: "REP_VOTE"\|"SURVEY", title, description?, survey_scope?: …, deadline: datetime, questions: list[QuestionIn{qtype, title(1..200), required: bool, options?: list[str]}](1..poll.max_questions)}` → 201 `PollView` | `M:主任+`（委员不可，Q60=A） | `deadline` 必填、> now + 5 分钟、**创建后无修改接口**（Q67=B）；`SURVEY` 必填 `survey_scope`（二选一，Q64=A），`REP_VOTE` 禁止传；题目数超 `poll.max_questions`（暂 50，Q97）→ 400 `TOO_MANY_QUESTIONS`；`SINGLE/MULTI` 选项 2..20；`REP_VOTE` 发起时在任业主代表数为 0 → 409 `NO_REPRESENTATIVES`（message：尚无业主代表；Q111 已决 A，AC-052-09；恰有 1 名在任业主代表时可发起）；成功则固化 `polls_participant` 与 `participant_count`；审计 `POLL_CREATED` |
| IFC-131 | `GET /polls?status=OPEN\|CLOSED&kind=&page=` → `Page[PollListItem]`；`GET /polls/{id}` → `PollView{…questions, can_respond: bool, my_response?}` | `M` | 列表只含"当前用户有资格作答"的进行中问卷 + 已截止且结果公开的问卷；`REP_VOTE` 资格 = ∈ `polls_participant`；`SURVEY` 资格 = 提交时实时判定：`OWNERS_ONLY` → 有效 OWNER/HEAD；`OWNERS_AND_RESIDENTS` → 另含 RESIDENT；游客不可（AC-054 反向路径，返回 `can_respond=false`）；无资格访问进行中详情 → 404 |
| IFC-132 | `POST /polls/{id}/responses` `{answers: list[{question_id: int, value: AnswerValue}]}` → 201 `{submitted_at}`；`AnswerValue = "AGREE"\|"DISAGREE"\|"ABSTAIN"`（AOA）、`int 1..5`（SCORE）、`int`（SINGLE 选项索引）、`list[int]`（MULTI）、`str(≤1000)`（TEXT） | `M`，资格同上 | 截止（服务器时间）后 → 409 `POLL_CLOSED`；已作答 → 409 `ALREADY_RESPONDED`；必答题缺失 → 400 `REQUIRED_ANSWER_MISSING`；值与题型不符/越界 → 400；业主代表投票的作答者须**当前仍持有业主代表身份**（身份失效者不能提交，REQ-FUNC-063），但仍计入固定分母；一次提交原子完成（"手机一键"，REQ-FUNC-045）；实名记录，明细仅 `A` 与发起人可查 `[ASSUMPTION]` |
| IFC-133 | `GET /polls/{id}/result` → `PollResultView{status, participant_count?, response_count, questions: list[{question_id, qtype, tally: dict, passed?: bool}]}` | `M` | **截止前一律 403 `RESULT_NOT_PUBLIC`**；截止后全体已登录用户可见，仅汇总、**不含个人明细**（REQ-FUNC-047）；`passed` 仅对 `REP_VOTE` 的 AOA 题给出：`agree*2 > participant_count`（Q80=A、Q108=A）；SCORE 给均值与分布，选择题给各项计数，TEXT 题只给回答条数（文本内容不公开 `[ASSUMPTION]`，避免暴露个人信息）；首次访问或定时任务时固化 `result_snapshot`（惰性 + MOD-014） |
| IFC-134 | 内部：`PollService.close_if_due(poll_id: int, now: datetime) -> bool`；`close_all_due(now: datetime) -> int`（条件更新 `OPEN→CLOSED`，写快照与审计 `POLL_CLOSED`） | 内部 | 幂等 |
**依赖**：MOD-001、005（调查资格）、006（发起资格、业主代表名单）。

### MOD-014 jobs

**职责**：统一的周期任务入口，全部幂等，可传入"当前时间"测试。
| IFC | 签名 | 说明 |
|---|---|---|
| IFC-140 | `python manage.py run_due_jobs [--now ISO8601] [--only <job>]`（systemd timer 每分钟调用）；任务表：`judge_resolutions`（IFC-092，每次）、`close_polls`（IFC-134，每次）、`expire_seats`（IFC-063，每次）、`generate_reports`（IFC-121，每次，仅在上季度/上年度已结束且尚无报表时执行）、`purge_expired_codes`（每日）、`purge_temp_attachments`（每日，>24 h 的 TEMP）、`purge_audit_logs`（每日，早于 `audit.retention_months` 个日历月；写一条 `AUDIT_PURGED` 汇总）、`purge_stale_tokens`（每日，过期令牌/票据/state）。进度记录在 `core_job_run`，单个任务异常不影响其余任务，失败写日志并返回非零退出码以便 systemd 记录 |
| IFC-141 | `python manage.py create_admin --username <u>`（首个管理员初始化，REQ-FUNC-025；口令走交互输入） | 一次性运维命令 |
**依赖**：MOD-001、003、006、009、012、013。

### MOD-020 web-portal（`frontend/src/portal/`）与 MOD-022 miniprogram

| 页面/能力 | 路由（Web）/ 页面（小程序） | 调用的 IFC |
|---|---|---|
| 手机号验证码注册 / 登录 / 密码登录 / 邮箱验证码登录 | `/register` `/login`；`pages/login` | IFC-020、022~025 |
| 微信扫码 + 快速登录 | `/login` 内嵌 `WxLogin` 组件（`fast_login` 默认开）；回调页 `/login/wechat` 用票据换令牌 | IFC-028~030 |
| 小程序微信一键登录 + 头像昵称设置（仅登录响应 `is_new=true` 时自动进入 `pages/profile-setup`，REQ-FUNC-065） | `pages/login`、`pages/profile-setup` | IFC-027、032、033 |
| 登录页"记住我"（仅 Web 用户端；小程序无此项，管理员登录页无此项） | `/login`；`pages/login`（无） | IFC-023~025、030 的 `remember_me` |
| 设置密码 / 个人资料 / 邮箱验证 / 换号 / 注销 | `/me/*`；`pages/profile*` | IFC-031~034、070~073、021 |
| 逐级选择专有部分 → 认证 / 申诉 / 申请同住人 / 审批申请 / 移除 | `/units/*`；`pages/units/*` | IFC-040、050~054 |
| 决议：发起/列表/详情/撤回/重提/投票 | `/resolutions/*` | IFC-081、090~091、004~005 |
| 报销/备用金/核销 | `/claims/*`（业委会成员） | IFC-100~103、081、082 |
| 收入表 | `/income/*`（业委会成员） | IFC-110~112 |
| 审批待办 | `/tasks` | IFC-082 |
| 投票/调查：发起、作答（一键提交）、结果 | `/polls/*`；`pages/polls/*` | IFC-130~133 |
| 财务报表 | `/reports` | IFC-120 |

前端约定：Web 令牌存 `localStorage` 键 `ocap_token`，小程序存 `uni.setStorageSync`（沿用 Freeark 模式 [CODE: /root/myproject/Freeark/miniprogram/utils/auth.js]）；HTTP 封装统一解析 `{code, message}`，401 清令牌并跳登录；金额一律用字符串并以 `decimal.js` 或后端值展示，禁止浮点运算（`decimal.js` 为前端新增依赖，见 tech_stack）；手机号只显示后端给的脱敏值。

### MOD-021 web-admin（`frontend/src/admin/`，路由前缀 `/admin`）

| 页面 | 调用的 IFC |
|---|---|
| 管理员登录（无"记住我"）、管理员账号管理与重置其他管理员密码 | IFC-035、036 |
| 系统配置：审计日志保留期限（≥ 6 个月） | IFC-009 |
| 业主清册：列表/单条维护/批量导入 | IFC-041、042 |
| 产权申诉审核 | IFC-052 |
| 撤销产权业主认证（含户主接任结果展示） | IFC-037、074 |
| 业委会/业主代表席位：赋予、变更、撤销 | IFC-037、060 |
| 人数与任期配置 | IFC-061 |
| 审批流程配置（决议/财务/收入） | IFC-080 |
| 审计日志查询 | IFC-002 |
前端约定：管理后台代码按路由懒加载拆包；路由守卫只是体验层，权限以后端为准（ADR-018）。

## 权限矩阵

✓ = 允许；○ = 有条件（见备注）；— = 不允许。"成员"= 委员/主任/副主任。

| 能力 | 访客 | 游客 | 同住人 | 产权业主 | 户主 | 委员 | 主任/副主任 | 业主代表 | 管理员 |
|---|---|---|---|---|---|---|---|---|---|
| 注册/登录 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 独立登录 |
| 清册认证/申诉/申请同住人 | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| 审批/移除本房同住人 | — | — | — | ○本房 | ○本房 | ○本房 | ○本房 | ○本房 | — |
| 查看已公开决议、调查与投票结果、财务报表 | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 发起业委会决议 | — | — | — | — | — | — | ✓ | — | — |
| 对"半数同意"决议投票 | — | — | — | — | — | ✓ | ✓ | — | — |
| 审批决议/报销/备用金/收入表 | — | — | — | — | — | ○快照审批人 | ○快照审批人 | — | — |
| 发起报销/备用金/核销；录入收入表；手动重新生成报表 | — | — | — | — | — | ✓ | ✓ | — | —（报表不可） |
| 发起业主代表投票、调查 | — | — | — | — | — | — | ✓ | — | — |
| 参与业主代表投票 | — | — | — | — | — | — | — | ○发起时快照 | — |
| 参与调查 | — | — | ○范围含同住人时 | ✓ | ✓ | ✓(若为产权业主) | ✓(同左) | ✓(同左) | — |
| 清册维护、申诉审核、撤销认证、赋予/变更/撤销席位、配置（含审计保留期限）、审批流程、审计查看、管理员账号管理与重置其他管理员密码 | — | — | — | — | — | — | — | — | ✓ |
| 报销明细、发票 | — | — | — | — | — | ○仅本人发起/被指定 | 同左 | — | ✓ |
实现：DRF 权限类 `IsMember`、`IsAdmin`、`IsCommitteeMember`、`IsChairOrVice`、`IsRepresentative`（均读 `CommitteeQuery`）与对象级 `IsOwnerOfUnit`（读 `MembershipService`）；**每条矩阵单元格对应一个后端测试**（正向与越权反向各一）。

## 跨功能规则落地对照

| 规则 | 落地位置 | 关键机制 |
|---|---|---|
| 账号合并：身份取高、资料补充（REQ-FUNC-026~030、061） | IFC-075 `MergeService` | 主账号=手机号原有账号；`fill_empty_profile_from`；`merge_memberships`/`merge_seats` 取高；用户引用注册表迁移其余外键；单事务、按 id 升序加锁 |
| 户主接任（REQ-FUNC-013、020、034、Q29、Q39） | IFC-055 `promote_head_if_vacant` | `head_slot` 唯一索引；接任=认证时间最早的有效 OWNER；无人则暂无户主，下一位认证者成为户主；注销（IFC-073）与撤销（IFC-074）共用 |
| 身份失效对在途事项的影响（REQ-FUNC-053、063、Q101、Q106） | IFC-063 `sync_after_ownership_change`；审批实例快照；`initiator_labels` 快照；引擎资格复核 | 失效者不再能执行（权限现查）；在途事项状态**不自动变更**；公开内容保留发起时身份快照；无人可审批→发起人撤回重提；业主代表投票分母固定 |
| 审批流程配置（REQ-FUNC-038、042、054、062） | MOD-008 | 管理员配置；审批人只能从业委会成员选；发起时选择并快照；财务类不得自审，决议不回避 |
| 财务记账口径（REQ-FUNC-041、058） | ADR-014、MOD-010/012 | 预借审批即入账；核销只入差额；带 `settles_advance_id` 的报销不入账；台账追加式、幂等 |
| "半数同意"决议截止判定（REQ-FUNC-038、060、Q104） | IFC-092 | 截止时判定；`agree*2 > denominator`；条件更新幂等；定时任务 + 读时惰性判定 |
| 手机号脱敏（REQ-NFUNC-002） | IFC-006 | 序列化层统一脱敏；仅 `/admin/registry/**` 明文 |
| 审计（REQ-NFUNC-003/004） | IFC-001 | 同事务写入；动作枚举覆盖全部范围；保留期限 ≥ 6 个月（IFC-009） |
| 会话有效期（REQ-FUNC-064） | IFC-038 `authenticate_token` | `IDLE` 闲置 30 分钟（Web 未勾选记住我、管理员）；`EXTENDED` 自签发绝对 7 天（Web 勾选记住我、小程序）；注销/合并/重置密码即时吊销 |
| 小程序首次头像昵称（REQ-FUNC-065） | IFC-027 `is_new` + IFC-032/033 | 仅新建账号那次登录触发；任何路径不用微信信息覆盖已有资料 |
| 多审批人与自批边界（REQ-FUNC-066） | IFC-082/083 | 任一通过即通过先到先得；财务类无他人可审批则 422 拒绝；决议指定负责人可自批 |
| 合并时在途事项（REQ-FUNC-067） | IFC-075 + 合并引用登记表 | 同一投票/调查保留 primary 答卷并审计；其余待办含审批快照归合并后账号 |
| 管理员密码重置（REQ-FUNC-068） | IFC-036 | 仅限他人；吊销目标令牌；审计 |
| 验证码/密码防暴力（REQ-NFUNC-001，C-06） | IFC-038 + IFC-007（`RateLimiter`）+ IFC-011/012 | 间隔 60 秒、5/小时、10/天、IP 30/小时、单码错 5 次作废、目标累计错 10 次锁 30 分钟、密码连错 5 次锁 15 分钟；阿里云平台流控映射 429 |

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-001 | US-001 | MOD-003、002、020、022 |
| REQ-FUNC-002 | US-002 | MOD-003、002、020 |
| REQ-FUNC-003 | US-003 | MOD-003、002、022 |
| REQ-FUNC-004 | US-004、US-070 | MOD-003、002、022 |
| REQ-FUNC-005 | US-005 | MOD-003、020 |
| REQ-FUNC-006 | US-006 | MOD-003、020、022 |
| REQ-FUNC-007 | US-007 | MOD-003、002、020 |
| REQ-FUNC-008 | US-008 | MOD-003、002、020（ADR-011） |
| REQ-FUNC-009 | US-018 | MOD-004 |
| REQ-FUNC-010 | US-020 | MOD-004、005、020、022 |
| REQ-FUNC-011 | US-021 | MOD-005、004、007 |
| REQ-FUNC-012 | US-022 | MOD-005 |
| REQ-FUNC-013 | US-023 | MOD-005 |
| REQ-FUNC-014 | US-024 | MOD-005 |
| REQ-FUNC-015 | US-025 | MOD-005、007（游客派生） |
| REQ-FUNC-016 | US-030、US-070 | MOD-003、007、022 |
| REQ-FUNC-017 | US-031 | MOD-007、003、005、006 |
| REQ-FUNC-018 | US-019 | MOD-004、021 |
| REQ-FUNC-019 | US-026 | MOD-005、021 |
| REQ-FUNC-020 | US-027、036 | MOD-005、007 |
| REQ-FUNC-021 | US-028 | MOD-007 |
| REQ-FUNC-022 | US-029 | MOD-005 |
| REQ-FUNC-023 | US-009 | MOD-003 |
| REQ-FUNC-024 | US-010 | MOD-003、007 |
| REQ-FUNC-025 | US-011 | MOD-003、021 |
| REQ-FUNC-026 | US-012 | MOD-007 |
| REQ-FUNC-027 | US-013 | MOD-007、003 |
| REQ-FUNC-028 | US-014 | MOD-007 |
| REQ-FUNC-029 | US-015 | MOD-007、003 |
| REQ-FUNC-030 | US-016 | MOD-007、005 |
| REQ-FUNC-031 | US-017 | MOD-003 |
| REQ-FUNC-032 | US-024 | MOD-005 |
| REQ-FUNC-033 | US-035 | MOD-004、005 |
| REQ-FUNC-034 | US-036 | MOD-007、005、021 |
| REQ-FUNC-035 | US-037 | MOD-006、021 |
| REQ-FUNC-036 | US-041 | MOD-007、006、009、013 |
| REQ-FUNC-037 | US-044 | MOD-009 |
| REQ-FUNC-038 | US-045、046 | MOD-009、008 |
| REQ-FUNC-039 | US-047 | MOD-009 |
| REQ-FUNC-040 | US-049、051 | MOD-010 |
| REQ-FUNC-041 | US-050 | MOD-010、012、008 |
| REQ-FUNC-042 | US-043、049、050 | MOD-008、010 |
| REQ-FUNC-043 | US-052、053 | MOD-013 |
| REQ-FUNC-044 | US-054 | MOD-013 |
| REQ-FUNC-045 | US-056 | MOD-013、020、022 |
| REQ-FUNC-046 | US-055 | MOD-013 |
| REQ-FUNC-047 | US-057 | MOD-013 |
| REQ-FUNC-048 | US-058、059 | MOD-011 |
| REQ-FUNC-049 | US-060 | MOD-011、008 |
| REQ-FUNC-050 | US-061、062 | MOD-012、014 |
| REQ-FUNC-051 | US-063 | MOD-012 |
| REQ-FUNC-052 | US-038 | MOD-006、021 |
| REQ-FUNC-053 | US-039 | MOD-006、007、014 |
| REQ-FUNC-054 | US-043 | MOD-008、021 |
| REQ-FUNC-055 | US-048 | MOD-008、009、010、011 |
| REQ-FUNC-056 | US-042 | MOD-006、021 |
| REQ-FUNC-057 | US-040 | MOD-006、021 |
| REQ-FUNC-058 | US-051 | MOD-010、012 |
| REQ-FUNC-059 | US-059 | MOD-011 |
| REQ-FUNC-060 | US-065、046 | MOD-009、014 |
| REQ-FUNC-061 | US-066 | MOD-007、006 |
| REQ-FUNC-062 | US-067 | MOD-008 |
| REQ-FUNC-063 | US-068 | MOD-006、008、009、010、011、013 |
| REQ-FUNC-064 | US-069 | MOD-003（IFC-038 `authenticate_token`）、001（配置）、020、021、022 |
| REQ-FUNC-065 | US-070（并见 US-004、US-030） | MOD-003（IFC-027、032、033）、022 |
| REQ-FUNC-066 | US-071（并见 US-043、045、067） | MOD-008（IFC-082、083）、009、010、011 |
| REQ-FUNC-067 | US-072 | MOD-007（IFC-075 + 合并引用登记表）、001（IFC-008）、013、008、009 |
| REQ-FUNC-068 | US-073（并见 US-011） | MOD-003（IFC-036）、021 |
| REQ-NFUNC-001 | US-032 | MOD-003、001 |
| REQ-NFUNC-002 | US-033 | MOD-001、004 |
| REQ-NFUNC-003 | US-034 | MOD-001 |
| REQ-NFUNC-004 | US-064 | MOD-001 |

## 依赖关系

后端依赖只能指向更低层（括号内为调用的 IFC）：

```
L0  MOD-001 core
L1  MOD-002 integrations → MOD-001 (IFC-001,007)
L2  MOD-003 accounts     → MOD-001 (IFC-001,003,007), MOD-002 (IFC-010,011,012)
    MOD-004 registry     → MOD-001 (IFC-001,006)
L3  MOD-005 residency    → MOD-001, MOD-003 (User 模型), MOD-004 (IFC-043)
    MOD-006 committee    → MOD-001, MOD-003 (User 模型), MOD-005 (IFC-055 is_owner_of_any)
L4  MOD-007 identity     → MOD-001, 002 (IFC-010), 003 (IFC-038), 004, 005 (IFC-055), 006 (IFC-063)
    MOD-008 approval     → MOD-001, MOD-003, MOD-006 (IFC-062)
    MOD-012 ledger       → MOD-001, MOD-006 (IFC-062)
    MOD-013 polls        → MOD-001, MOD-005 (IFC-055), MOD-006 (IFC-062)
L5  MOD-009 resolutions  → MOD-001, MOD-006 (IFC-062), MOD-008 (IFC-083)
    MOD-010 claims       → MOD-001, MOD-006, MOD-008 (IFC-083), MOD-012 (IFC-121)
    MOD-011 income       → MOD-001, MOD-006, MOD-008 (IFC-083), MOD-012 (IFC-121)
L6  MOD-014 jobs         → MOD-001, 003, 006 (IFC-063), 009 (IFC-092), 012 (IFC-121), 013 (IFC-134)
前端：MOD-020 / MOD-021 / MOD-022 → 后端 HTTP API（IFC-002~140）
```
**已检查：无循环依赖。** 关键避环点：(1) 合并/注销/撤销认证的"跨模块级联"集中在 MOD-007，由它向下调用 003/005/006，没有任何下层反向调用它；(2) 台账独立成 MOD-012，使 claims/income 写入、reports 读取均指向它，避免 claims↔reports；(3) 合并时 secondary 的其余外键迁移通过 `UserReferenceRegistry`（MOD-001）反向登记，合并模块不必 import 业务模块；(4) `committee→residency` 仅用于"是否产权业主"判断，residency 不依赖 committee（席位失效由 identity 编排）；(5) MOD-001 的 HTTP 端点（IFC-002/004/005/009）需要知道调用方是普通用户还是管理员，但令牌认证类由 MOD-003 实现：认证类只在 `settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` 中以字符串路径装配，MOD-001 的权限类只读取 `request.user.principal_type` / `request.user.pk`，不 import MOD-003，因此 MOD-001 无静态依赖；(6) 附件下载策略与合并引用都采用"业务模块启动时向 MOD-001 注册"（IFC-003 `register_attachment_policy`、IFC-008 `register_user_reference`），箭头方向始终是业务模块 → MOD-001；(7) MOD-002 的阿里云 SDK 只被 `integrations/aliyun_sms.py` 引用，MOD-003 通过 `get_sms_gateway()` 取实现，不 import SDK。

## 代码复用（Freeark → ocap，复制改造；ADR-003）

| ocap 去向 | Freeark 来源 | 方式 | 改造点 |
|---|---|---|---|
| `accounts/auth.py` 滑动会话认证 | `FreeArkWeb/backend/freearkweb/api/authentication.py:40-106` `[CODE]` | 复制改造 | 令牌存哈希；同用户多令牌；`principal=MEMBER/ADMIN`；去掉服务账号豁免与进程内缓存依赖（改为按 `last_active_at` 节流写库）；配置沿用 `SESSION_*`、`ACTIVITY_THROTTLE_SECONDS`（settings.py:320-332） |
| `integrations/wechat.py` `miniapp_code2session` | `…/api/views_miniapp.py:137-174` `[CODE]` | 复制改造 | 封装为 `WeChatClient` 方法；增加 40226/40164/45011 映射；返回 dataclass；不返回 session_key；补 `stable_access_token`、`miniapp_phone_by_code`、`web_*` |
| `accounts` 登录视图结构 | `…/api/views_miniapp.py:177-242`（微信登录），76-108（令牌签发、用户摘要） `[CODE]` | 参考 | 逻辑搬到 `AccountService`；新用户不再用 `wx_<openid前缀>` 作用户名（改 `account_no`） |
| `WechatIdentity` 模型 | `…/api/models.py:1087-1117` `WechatBinding` `[CODE]` | 参考改造 | 增加 `channel`；唯一键 `(channel, openid)`；`unionid` 建索引 |
| DRF 权限类写法 | `…/api/views.py:127-156` `[CODE]` | 参考 | 改为读关系表，不看 `role` 字段 |
| 测试配置 | `…/freearkweb/test_settings.py` `[CODE]` | 复制 | SQLite 内存库、MD5 哈希器、NullHandler 日志；去掉 `FREEARK_POC_MOCK` |
| 小程序 HTTP 封装 | `miniprogram/utils/http.js` `[CODE]` | 复制改造 | `BASE_URL` 换为 ocap 域名；`PUBLIC_PREFIXES` 改为 `/api/v1/auth/`；错误体解析 `{code,message}`（Freeark 为 `detail`） |
| 小程序鉴权状态 | `miniprogram/utils/auth.js`、`store/auth.js` `[CODE]` | 复制改造 | 存储键改名；增加 `identity` 摘要 |
| 小程序微信登录流程 | `miniprogram/pages/login/index.vue:230-262`（`uni.login` → code → 登录） `[CODE]` | 参考 | 仅参考流程，界面全部重做 |
| 头像昵称设置 | `miniprogram/pages/profile-setup/index.vue:32`（`open-type="chooseAvatar"`） `[CODE]` | 参考 | 头像为临时文件，需 `uni.uploadFile` 转存到 IFC-033 |
| 小程序测试脚手架 | `miniprogram/tests/setup.js`、`vitest.config.mjs` `[CODE]` | 复制 | 沿用 `uni` 全局 mock |
| systemd 服务写法 | `systemctl/freeark-backend.service` `[CODE]` | 参考 | 改 Gunicorn；去 Redis 依赖；路径与用户占位待 P7 |
| 迁移风格 | `…/api/migrations/0048_add_app_feature_config.py` `[CODE]` | 参考 | 手写/裁剪 scoped |
| **不复用** | UI 风格（赛博朋克）、设备/能耗/MQTT/聊天/RAG 相关代码、`OwnerInfo`（设备绑定语义）、`pages/bind`（MAC/二维码绑设备）、`UserRoleApiGuardMiddleware` | — | 与业委会场景无关 |

## 数据迁移

全新项目，无存量数据，所有迁移均为新建：
- **0.2.0 相对 0.1.0 的表结构变化**（0.1.0 尚无代码与迁移，故只是设计修订，无迁移成本）：新增 `core_lockout`；`accounts_auth_token.extended bool` 改为 `session_kind{IDLE,EXTENDED}`；`audit.retention_days` 配置键改为 `audit.retention_months`；申诉附件改为按 id 关联（`core_attachment.linked_type="appeal"`，无新表）；收入表 `DRAFT` 状态继续使用。
- **新表**：各 app 的 `0001_initial`（表与索引见上各模块"数据表"）。落地顺序（依赖序）：`core → integrations(无表) → accounts → registry → residency → committee → approval → ledger → resolutions → claims → income → polls`。`accounts.User` 须在首个迁移前通过 `AUTH_USER_MODEL = "accounts.User"` 声明（Django 要求在建表前确定）。
- **数据迁移（种子）**：`committee_config` 单例行（cap_chair=1、cap_vice=2、cap_member=6，其余为空）；`core_system_config` 不预置（读取时用代码默认值，避免与建议值漂移）。
- **方式（P6）**：每 app 手写 scoped 迁移；约束中的"槽位列 + 唯一索引"、`CheckConstraint` 必须在迁移里显式写出并用 SQLite 与 MySQL 各验证一次；禁止提交 `makemigrations` 全量产物。
- **可逆性**：`CreateModel`/`AddIndex` 全部可逆（反向 = 删表）；种子 `RunPython` 提供空反向函数。首次上线前无数据，回滚无损失；**上线后**任何字段删除/改类型都视为不可逆，须单独写迁移并先备份（`[MANUAL_ROLLBACK_REQUIRED]`）。
- **数据风险**：MySQL 与 SQLite 对 `CheckConstraint`、`JSONField`、唯一索引对 NULL 的处理需双库验证（见 tech_stack 风险）；字符集统一 utf8mb4。

## 受影响的运行单元 / 构建

| 变更 | 动作 |
|---|---|
| 后端代码、依赖、迁移 | 先执行迁移（人工，按 P6），再重启 RU-1 `ocap-backend.service`；RU-2 下一分钟自动使用新代码 |
| 定时任务逻辑 | 无需重启常驻进程；unit 文件改动需 `systemctl daemon-reload` 并重启 `ocap-scheduler.timer` |
| 前端（Web 用户端 + 管理后台） | 重新构建 `frontend/dist` 并替换静态目录（RU-3） |
| 小程序 | 重新构建 uni-app，微信开发者工具上传、提审、发布（RU-4）；如新增请求域名需先在小程序后台配置 |
| 配置/凭据 | 只改环境变量文件后重启 RU-1；包括 `WECHAT_MINIAPP_*`、`WECHAT_WEB_*`、`WECHAT_WEB_REDIRECT_URI`、`ALIYUN_ACCESS_KEY_ID`/`ALIYUN_ACCESS_KEY_SECRET`/`ALIYUN_SMS_SIGN_NAME`/`ALIYUN_SMS_TEMPLATE_CODE`/`ALIYUN_SMS_TEMPLATE_TTL_MINUTES`、`SMS_GATEWAY`、SMTP 设置（`EMAIL_*`）、`TRUSTED_PROXY_ADDRS`、`SECRET_KEY`、数据库连接。**凭据只写部署机环境变量文件，不入仓库、不入文档**（协议 §L-2）；`SMS_GATEWAY=aliyun` 需先完成签名与模板审核（OQ-20） |
| 后端依赖 | `requirements.txt` 增加 `alibabacloud_dysmsapi20170525`（含其传递依赖）、`requests`、`openpyxl`、`gunicorn`；安装后 `pip freeze` 固定版本；变更后重启 RU-1 |
| 反向代理 | 请求体上限 12 MB（附件逐个上传，单文件 ≤ 10 MB + 表单开销）；`/api/` 反代；静态文件；向后端传递真实客户端 IP 并配置 `TRUSTED_PROXY_ADDRS`（IP 限流依赖，ADR-008）；变更后 reload |

## 领域与外部依赖出处

| IFC / MOD | 事实（端点、字段、错误码、调用顺序、限制） | 出处 |
|---|---|---|
| IFC-010 `miniapp_code2session` / MOD-002 | `GET https://api.weixin.qq.com/sns/jscode2session?appid&secret&js_code&grant_type=authorization_code`；返回 `openid`、`session_key`、`unionid`（仅小程序已绑定开放平台账号时返回）、`errcode/errmsg`；错误码 -1、40029、40226、45011；仅服务端调用 | [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/user-login/api_code2session.md，2026-11-07，摘要]；[CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/views_miniapp.py:137-174] |
| IFC-010 `stable_access_token` | `POST https://api.weixin.qq.com/cgi-bin/stable_token`，JSON：`grant_type="client_credential"`、`appid`、`secret`、`force_refresh?`；返回 `access_token`、`expires_in`（≤ 7200）；默认模式下有效期内重复调用返回同一令牌，到期前 5 分钟刷新；强制刷新会使旧令牌失效，每日限 20 次且间隔 30 秒；错误 40164 = IP 不在白名单 | [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/mp-access-token/api_getstableaccesstoken.md，2026-11-07，摘要] |
| IFC-010 `miniapp_phone_by_code`（可选） | `POST https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token=…`，JSON：`code`（必填）、`openid`（可选，校验绑定）；返回 `errcode`、`errmsg`、`phone_info{phoneNumber, purePhoneNumber, countryCode, watermark{timestamp, appid}}`；code 5 分钟有效、单次使用；错误 -1、40013、40029、45011；仅服务端调用；**该组件仅对非个人且已认证的小程序开放，按次收费** | [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/user-info/phone-number/api_getphonenumber.md，2026-11-07，摘要]；主体与收费限制：[WEB: https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/deprecatedGetPhoneNumber，2026-11-07，搜索摘要，未取得原文]。前端 `getphonenumber` 事件字段名：[UNSOURCED]，不影响本系统契约（后端只接收 `code`），开发时对照官方页核对 |
| IFC-028~030 Web 扫码登录 | 授权页 `https://open.weixin.qq.com/connect/qrconnect`，参数 `appid`、`redirect_uri`(URL 编码)、`response_type=code`、`scope=snsapi_login`、`state`、`lang`；回调 `redirect_uri?code=&state=`；用户拒绝则不回调；code 10 分钟有效、仅能换一次 access_token；内嵌脚本 `wxLogin.js`，`WxLogin` 参数 `id、appid、scope、redirect_uri、state、style、href、stylelite、fast_login、color_scheme、self_redirect、onReady、onQRcodeReady` | [WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html，2026-11-07，页面标注最后编辑 2026-06-25] |
| IFC-030 / `web_exchange_code` | `GET https://api.weixin.qq.com/sns/oauth2/access_token?appid&secret&code&grant_type=authorization_code`；返回 `access_token`、`expires_in`、`refresh_token`、`openid`、`scope`、`unionid`；40029 = code 无效 | 同上 [WEB: …/Wechat_Login.html]；[WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Authorized_Interface_Calling_UnionID.html，2026-11-07，摘要] |
| `web_userinfo` | `GET https://api.weixin.qq.com/sns/userinfo?access_token&openid&lang`；返回 `openid、nickname、sex、province、city、country、headimgurl、privilege、unionid`；40003 = openid 无效；2021-10-20 起不再返回性别与地区；头像更换后旧 `headimgurl` 失效；限频 5 万次/分钟 | [WEB: …/Authorized_Interface_Calling_UnionID.html，2026-11-07，摘要] |
| ADR-011 快速登录 | Windows 微信 ≥ 3.9.11、Mac 微信 ≥ 4.0.0，已登录且非锁定时优先提示快速登录；`fast_login=0` 关闭 | [WEB: …/Wechat_Login.html，2026-11-07] |
| unionid 跨应用 | 同一开放平台账号下的应用（移动应用、网站应用、公众号）同一用户 unionid 相同；小程序需绑定到开放平台账号才返回 | [WEB: …/Authorized_Interface_Calling_UnionID.html，2026-11-07，摘要]；小程序侧见 code2Session 条 |
| 小程序头像昵称获取 | `getUserProfile` 已不再返回真实昵称，改用 `button open-type="chooseAvatar"` 与 `input type="nickname"`；头像为临时文件需转存 | [WEB: 微信开放社区帖子汇总，2026-11-07，**非官方原文**，开发时对照官方"获取头像昵称"页复核]；[CODE: /root/myproject/Freeark/miniprogram/pages/profile-setup/index.vue:32] |
| IFC-011 `AliyunSmsGateway` / `SendSms` 字段 | IFC-011 是**本系统自定义**的窄接口（`phone, code, purpose`），不含服务商字段；适配器内部调用 `SendSms`：请求 `PhoneNumbers`（逗号分隔，≤ 1000 个，本系统每次 1 个）、`SignName`（已审核签名）、`TemplateCode`（已审核模板）、`TemplateParam`（JSON 字符串，变量个数须与模板一致）、`OutId`（可选）；响应 `Code`（`OK` 为成功）、`Message`、`BizId`、`RequestId`；单用户 QPS 5000 | [WEB: https://help.aliyun.com/zh/sms/developer-reference/api-dysmsapi-2017-05-25-sendsms，2026-11-07] |
| IFC-011 错误码 | 错误码名称：`isv.BUSINESS_LIMIT_CONTROL`、`isv.MOBILE_NUMBER_ILLEGAL`、`isv.TEMPLATE_MISSING_PARAMETERS`、`isv.SMS_SIGNATURE_ILLEGAL`、`isv.SMS_TEMPLATE_ILLEGAL`、`isv.AMOUNT_NOT_ENOUGH`、`isv.ACCOUNT_ABNORMAL`、`isv.INVALID_PARAMETERS`、`isv.SYSTEM_ERROR`、`isv.DAY_LIMIT_CONTROL`、`isv.MONTH_LIMIT_CONTROL`、`isp.RAM_PERMISSION_DENY`；**页面只给名称、未给释义**，"BUSINESS_LIMIT_CONTROL=业务限流""MONTH_LIMIT_CONTROL=月发送限额"来自搜索摘要（第三方 SDK 错误码表），归类为本系统的 `SmsSendError.kind` 是本设计的决定 | [WEB: https://api.aliyun.com/document/Dysmsapi/2017-05-25/errorCode，2026-11-07，仅名称]；释义 [UNSOURCED]（开发时对照官方 API 错误码页，不影响契约） |
| IFC-011 平台流控 | 验证码短信（中国内地）同一签名下同一号码默认 1 条/分钟、5 条/小时、10 条/天；分钟/小时按自然时间窗口（UTC+8 整点），天为滚动 24 小时；另有同一号码跨发送方 40 条/天；请求提交成功即计数；超限提示"业务限流"，具体错误码页面未指明；企业用户可在控制台调整，个人用户不可（搜索摘要） | [WEB: https://help.aliyun.com/zh/sms/user-guide/message-rules，2026-11-07] |
| IFC-011 模板规范 | 验证码模板须含"验证码/注册码/校验码/动态码"之一，并写明平台、用途、有效期至少一项；仅支持单变量与不可自定义的双变量；单变量 4~6 位（数字/字母）；变量名以字母开头、仅字母数字下划线；不得含链接、联系方式、【】；长度 1~500 字符 | [WEB: https://help.aliyun.com/zh/sms/user-guide/verification-code-template-specifications，2026-11-07] |
| IFC-011 SDK 用法 | 包名 `alibabacloud_dysmsapi20170525`，Python ≥ 3.7；**Config、endpoint、客户端类与 `SendSms` 方法名未取得原文**（README 指向 `docs/0-Usage-EN.md`，未读到） | 包名与版本：[WEB: https://github.com/aliyun/alibabacloud-python-sdk/blob/master/dysmsapi-20170525/README.md；https://pypi.org/pypi/alibabacloud-dysmsapi20170525/json，2026-11-07]；调用方式 [UNSOURCED]，PHASE_05 开发前必须先读 `docs/0-Usage-EN.md`，不得凭记忆写 |
| IFC-011 短信资质 | 官方资质页列出企业、事业单位、个人，证件示例为社会信用代码证书/企业营业执照/事业单位法人证书；未提及"其他组织"与业主委员会 | [WEB: https://help.aliyun.com/zh/sms/user-guide/qualification-application-description，2026-11-07]；业委会能否使用：未知（OQ-20） |
| IFC-012 邮件服务 | 使用 Django SMTP 邮件后端，接口为本系统自定义；SMTP 主机/端口/凭据来自环境变量；厂商未选，厂商 API/SMTP 细节不进入契约 | 设置项名称为 Django 标准设置；厂商部分 [UNSOURCED]（C-16 只定了类别，不影响契约） |
| 微信主体与认证 | 其他组织类小程序"需认证成功后方可提交发布审核"；免费认证清单含城市居民委员会、农村村民委员会等，未列业主委员会；一般其他组织材料为《组织机构代码证》及登记/批准证明，页面各节清单不完全一致 | [WEB: https://developers.weixin.qq.com/miniprogram/product/renzheng.html，2026-11-07] |
| 微信手机号快速验证适用范围 | 仅小程序、小游戏；"其他未明确声明的账号类型，如无特殊说明，均不可调用此接口"；页面未写主体类型与收费 | [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/user-info/phone-number/api_getphonenumber.md，2026-11-07]；主体/收费说法出自搜索摘要，未证实 |
| ADR-017 数据库行为 | `Index.condition` 在 MySQL 与 MariaDB 上被忽略（不支持条件索引）；`UniqueConstraint.condition` 与之有相同限制 | [WEB: https://docs.djangoproject.com/en/5.2/ref/models/indexes/ 与 …/constraints/，2026-11-07] |
| C-06/C-08 数值依据（已由用户确认） | 带外验证 10 分钟有效；记忆口令最短 8 位、应允许 ≥ 64 位、应比对常见/泄露口令表、不宜强加组合规则；连续失败上限 100 | [WEB: https://pages.nist.gov/800-63-3/sp800-63b.html，2026-11-07，该页标明已被 SP 800-63-4 取代] |
| C-07 数值依据 | 网络日志留存不少于六个月 | [WEB: https://www.cac.gov.cn/2016-11/07/c_1119867116_2.htm 与搜索摘要，2026-11-07] |
