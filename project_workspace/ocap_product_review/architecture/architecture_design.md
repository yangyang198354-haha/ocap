<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T00:11:53+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>requirements/product_review.md</file>
    <file>phase_status.md</file>
    <file>../ocap_user_directory/architecture/module_design.md</file>
    <file>../ocap_admin_polish/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 产品评审修正 架构设计（INCREMENTAL）

> 编号接续全仓：ADR-078 起（全仓现有最大 ADR-077）、MOD-074 起（最大 MOD-073）、IFC-261 起（最大 IFC-260）。注：基线两份 module_design 中 IFC-243 ~ 246 在 user_directory 与 admin_polish 重复，属旧文档问题，本批不改前批文档，只在 module_design 中说明引用时一律写 `批次名/IFC-NNN`。
> 路径缩写：`B/` = `backend/apps/`，`W/` = `frontend/src/`，`M/` = `miniprogram/`。引用的 `文件:行` 均经 `git grep -n` / 阅读核实（基线 HEAD afa1fe8）。
> 依据：requirements_spec.md 1.0.0（REQ-FUNC-142 ~ 166、REQ-NFUNC-026 ~ 028）、user_stories.md 1.0.0（US-150 ~ 178）、开放问题 Q-PR-01 ~ 09 按推荐项（GR-A-002 条件）。

## 架构概览

**本次改动在现有系统中的位置**：不新增 app、不新增表、不新增外部依赖。后端沿用 Django 5.2 + DRF 的"每个 app 一组 views/services/urls"形态，改动落在 `residency`、`identity`、`committee`、`claims`、`income`、`core`、`accounts`、`content`、`ledger` 现有 app 内；`jobs` app 中新增一个测试夹具命令。前端改动在 `frontend/src/{portal,admin,shared}` 与 `miniprogram/{pages,utils,components}`，沿用 Vue 3 + Element Plus / uni-app + Pinia。

**改动分三类**：

| 类别 | 内容 | 对应 REQ |
|---|---|---|
| 前端补入口（后端能力已在） | 同住人申请/审批/移除/退出、我的申诉、身份展示、二次确认、用户选择器、列表翻页、版式模板管理页、中文显示、信息详情错误态、小程序报表明细 | REQ-FUNC-142 ~ 145、148、149、150、151、152、153、154、156、157、158、159、160 |
| 后端行为修正 | 报销/备用金仅委员；小程序所有登录 7 天；注销自动关闭待处理申请/申诉；金额上限可配置；版式模板被引用时禁删；报表明细脱敏；`/me` 与房屋聚合 | REQ-FUNC-143、144、145、146、147、153、155、157、161 |
| 规则固化与验收口径 | 题数/选项/窗口/导入行数/日期/重复申请规则只补常量导出与测试；半数分母；模板示例口径 | REQ-FUNC-162 ~ 166 |

**关键质量属性（引 REQ-NFUNC）**：

- REQ-NFUNC-028 零回归与契约一致：所有新增前端调用只用 `http.`/`adminHttp.` + 字面量路径、路径不带 `?`，管理端调用只对 `IsAdmin`、用户端只对 `IsMember` 族视图（`backend/tests/integration/test_frontend_contract.py:30-97`，M-SA-007）；两份 api.js 同步修改（画像 P6）。后端既有 JSON 字段只增不删不改名；`/me` 的 `identities` 键集合因新增 `summary` 而变化，需同步更新 `test_frontend_contract.py:140`（见 module_design 受影响用例表，P-SA-013）。
- REQ-NFUNC-002 / C-42 个人信息最小化：新聚合接口不返回手机号明文；同住人名单只对该专有部分的产权业主返回；用户选择器沿用管理员专属的 `admin/users`（Q-PR-09=B：实名对管理员可见）。
- REQ-NFUNC-026 / 027 为纯文档需求，已由 GROUP_A 交付，不产生设计单元；本批只在 MOD-086 中设计一条文档扫描核验用例。
- 资源受限部署（树莓派单机，画像 P7）：不引入新进程、不引入新依赖；`GET /me/housing` 用固定查询数（预取，不随房屋数/同住人数线性增长）；夹具命令分批删除。

## 部署视图

只使用画像 P7 中存在的"测试"环境（生产无）。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000，User=yangyang，WorkingDirectory=`/home/yangyang/ocap/backend`） | 测试（树莓派） | 代码变更 + 执行 `manage.py migrate`（residency 0002，仅 choices，无 SQL 变更） → 重启 |
| 定时任务 | systemd timer `ocap-run-due-jobs`（每分钟一次性进程，调用 `run_due_jobs`） | 测试 | 无代码变更；下次触发自动用新代码 |
| 内容 worker | systemd `ocap-content-worker` | 测试 | `content/styles.py`、`views_admin.py` 有改动但 worker 不依赖其行为；随后端一并重启（建议，非必须） |
| Web 前端静态资源 | `npm run build -- --base=/ocap/` 产物，经 nginx `8090` 站点 `ocap` 与 Freeark 的 `/ocap/` 反代对外 | 测试 | 重新构建并发布 |
| 微信小程序包 | `miniprogram/` uni-app 构建产物 | 微信开发者工具 / 小程序后台（人工提交，非自动部署） | 重新构建；发布到体验版属人工步骤 |
| E2E 夹具 | `manage.py e2e_fixture`（仅 E2 在测试机执行，画像 P4-1） | 测试 | 新增命令，不常驻 |
| 数据库 | MySQL 库 `ocap` | 测试 | 迁移 `residency.0002_closed_status`（AlterField ×2，仅 choices，不触碰数据；5742 条清册不被改动） |

不触碰 Freeark 的服务、端口、目录、库（画像 P7 同机共存约束、P8）。

## ADR

### ADR-078: 房屋数据聚合：新增 `GET /me/housing`，而不是扩 `/me` 或让前端自行拼装
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-143（首页与"我的房屋"显示待审批数量）、REQ-FUNC-145（产权业主查看当前同住人名单并移除）、REQ-FUNC-149（逐房屋身份）。基线缺口：没有任何接口返回"某专有部分的现任同住人"，`B/identity/services.py:19-46` 的 `/me` 只含本人房屋与角色；`B/residency/views.py:205-219` 的 `to-review` 只含待审申请。
- Options:
  - A 扩展 `/me`：把 residents、待审数量塞进 `identities.units[]`。优：一次请求；缺：`/me` 每个页面加载都调（`W/portal/PortalLayout.vue:30-32`、`Home.vue`），非产权业主也承担查询；`test_frontend_contract.py:140` 对 `identities` 键集合有严格断言，改动面大。
  - B 新增只读 `GET /me/housing`（IsMember）：返回汇总身份、每套房屋（含产权业主可见的同住人名单与待审数量）、待审总数。优：按需调用，仅"我的房屋"页与产权业主首页使用；`/me` 只增 `summary` 与 `role_label`（见 ADR-080）；缺：多一个端点与一份契约。
  - C 前端用现有 `to-review` + `me` 自行拼装，同住人名单另加 `GET /units/<id>/residents`。优：不新建聚合；缺：N 套房屋 N 次请求，两端重复拼装逻辑，名单接口还要重复鉴权。
- Decision: 选 B。理由：REQ-NFUNC-028 要求既有字段不变（A 违反"键集合"守护）；C 在小程序端请求次数多、逻辑重复（Web + 小程序两端，REQ-FUNC-143/144/145）。非产权业主调用时 `residents` 恒为空、不额外查询。
- Consequences: 正向：契约集中，两端共用；查询数固定。负向：新增 IFC-261，两份 api.js 各加一个函数；Home 对产权业主多一次请求，须容错（首页既有测试 `frontend/tests/ui_blocks.spec.js`、`pages.spec.js` 用路由表 mock，未登记路由须不致失败，见 module_design MOD-083）。

### ADR-079: 房屋选择器复用 `GET /units/options`，抽成两端各一个共用组件
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-142（同住人申请用"逐级选择楼栋、单元、楼层、户号"，不手输内部编号）、US-150。认证区已有现成逐级选择：`W/portal/Units.vue:3-52,60-170`（Web）、`M/pages/units/index.vue:5-20`（小程序），数据来自 `B/registry/views.py:57-69` 的 `UnitOptionsView`（IsMember，返回 `{level, skipped, has_empty, options}`）。
- 约束来源与被排除方案：沿用现有接口与逐级模式（既有栈优先）。被排除：新增"按 ID 反查房屋名称"接口（仍要用户知道 ID，违背 REQ-FUNC-142）；新增"房屋搜索"接口（超出需求，且清册 5742 条，搜索接口需另做限流与脱敏评估）。
- Decision: 后端零改动；把 Units.vue 与 units/index.vue 内联的级联逻辑各抽成一个组件 `UnitCascader`（Web `W/portal/parts/UnitCascader.vue`；小程序 `M/components/UnitPicker.vue`），对外 emit 选中的 `{ unit_id, specific_part }`；认证、申诉、申请同住人三个动作共用同一个选择结果。
- Consequences: 正向：三个动作一致、未来改级联规则只改一处。负向：重构 `Units.vue`（234 行）与小程序 units 页有回归风险，需保留既有选择行为用例（MOD-086 清单中列出）。

### ADR-080: 身份汇总口径：以 `accounts/directory.identity_view` 为唯一来源，修正 `identity_labels`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-149（逐房屋身份 + 汇总身份，与管理端目录 REQ-FUNC-136 口径一致）。基线缺陷：`B/committee/services.py:65-77` 的 `identity_labels` 对房屋身份取 `list_active` 的第一条后 `break`（按 `certified_at, id` 排序，`B/residency/models.py:30`），多户时可能显示"同住人"而此人另一户是户主；管理端 `B/accounts/directory.py:19-33` 取最高身份。
- Options:
  - A 后端统一：`/me`、`/me/housing` 都调用 `directory.identity_view` 输出 `summary`；`identity_labels` 内部改为按 `ROLE_RANK` 取最高房屋身份（保持返回 `list[str]` 形态与"职务 + 房屋身份"两项结构）。优：与管理端同源，REQ-FUNC-149 的"一致"可由单测证明；缺：`identity_labels` 的结果会写入报销 `applicant_labels`、决议 `initiator_labels` 等快照（`B/claims/views.py:80`、`B/resolutions/views.py:71`），对多户用户这些新快照可能与旧快照不同。
  - B 前端按 `units` + `committee` 自行算最高身份。优：后端零改；缺：Web 与小程序两份实现，且管理端口径只存在后端，无法单测一致性。
- Decision: 选 A。快照变化只发生在"多户且角色不同"的用户上，变化方向是修正为最高身份，属 REQ-FUNC-149 的预期；新快照不回填旧记录。`labels` 仍为 `[职务?, 最高房屋身份]`，既有断言（`tests/e2e/test_gap_journeys.py:33,49,62`、`test_journeys.py:35`）仍成立。
- Consequences: 正向：口径唯一。负向：`committee.services` 需（延迟）依赖 `accounts.directory` 的排序常量，避免循环依赖的方式见 module_design IFC-274（`committee.services` 只在函数内延迟导入 `residency.services.ROLE_RANK`，不导入 `accounts`）。

### ADR-081: 报销/备用金发起权限：创建视图换用 `IsCommitteeMember`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-146（只有现任委员/主任/副主任可发起）、US-154。基线：`B/claims/views.py:84,111` 的 `ReimbursementCreateView`、`AdvanceCreateView` 用 `IsMember`；核销视图 `:138` 已用 `IsIncomeMember`。`B/core/permissions.py:28-35` 的 `IsCommitteeMember` 对非成员返回 `FORBIDDEN 403 "需要业委会成员身份"`，与 REQ-FUNC-146 要求的文案完全一致；成员判定 `CommitteeQuery.is_member`（`B/committee/services.py:37-39`）已排除业主代表并校验 `term_end >= today`（席位到期的前任成员被拒，AC-154-03）。
- Options:
  - A 视图的 `permission_classes` 换成 `IsCommitteeMember`。优：与全仓权限矩阵一致（ADR-006），契约测试把它归入 `MEMBER_ONLY`（`test_frontend_contract.py` 的 `MEMBER_ONLY` 集合）；缺：管理员令牌访问时由 403 变 401（`IsCommitteeMember` 对非 `User` 主体统一报 401），属可接受的语义变化。
  - B 保留 `IsMember`，视图体内加判断抛 403。优：管理员令牌仍 403；缺：与其他成员专属接口两套写法，权限扫描类测试（`test_content_permissions_scan.py` 风格）难以覆盖。
- Decision: 选 A。只改创建（`POST /claims/reimbursements`、`POST /claims/advances`）；撤回、重提、列表、详情保持 `IsMember`，使已提交过的记录仍可由原提交人处理。
- Consequences: 正向：权限一行改动即生效。负向：存量"非成员提交的申请"仍可见/可撤回，不做数据清理（REQ-FUNC-146 只约束发起）。

### ADR-082: 入口可见性以 `/me` 为单一来源，并修正 `/me` 的任期判定
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-146（前端不向非成员展示"报销/备用金"）、REQ-FUNC-157（"待办"仅成员显示，入口与接口权限一致）。Web 已有 `auth.isCommittee`（`W/stores/auth.js:11-13`，读 `me.identities.committee.position`）。基线缺陷：`B/identity/services.py:24-25` 取 `Seat.objects.filter(user, status="ACTIVE")` 的首条，不校验 `term_end >= today`，而接口权限用 `CommitteeQuery.active_seat`（`B/committee/services.py:31-35`），席位已过期但尚未被定时任务置 EXPIRED 的窗口内，入口会显示而接口返回 403。
- 约束来源与被排除方案：既有栈（Pinia store + `/me`）。被排除：新增"能力清单"接口 `/me/permissions`（只为两个布尔量多开一条契约）；前端各页各自请求 `approval/tasks` 探测 403（显示即发起错误请求，违背 REQ-FUNC-157）。
- Decision: `IdentityService.me` 的 `committee` 改用 `CommitteeQuery.active_seat`；前端沿用 `auth.isCommittee` 控制"报销/备用金""待办""备用金核销""收入表"。小程序 store 增加同名 getter。`identities.committee` 的键（`position`、`term_end`）与类型不变。
- Consequences: 正向：入口与权限同源。负向：`IdentityService.me` 行为变化需要一条回归用例（过期席位 → `committee` 为 null）。

### ADR-083: 小程序全登录方式 7 天：登录请求带 `client` 字段，服务端按配置决定会话类型
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-147、US-155。基线：`B/accounts/views.py:42-43` 的 `_session_kind` 仅在请求体 `remember_me` 为真时给 `EXTENDED`；`LoginByCodeView`（:112）、`LoginByPasswordView`（:124）、`LoginByEmailView`（:135）、`WebWechatExchangeView`（:205）都走它；小程序微信登录 `:160` 固定 `EXTENDED`；`session.miniapp_extended` 配置（`B/core/config.py:36`）全仓无读取点；`EXTENDED` 的 7 天上限由 `session.extended_seconds` 控制并在 `authenticate_token` 校验（`B/accounts/services.py:275-296`）。
- Options:
  - A 小程序前端在 `loginByCode`/`loginByPassword` 请求体加 `remember_me: true`。优：后端零改；缺：`session.miniapp_extended` 配置仍是死配置，且"小程序即 7 天"的业务规则散落在客户端。
  - B 登录请求体加可选字段 `client: "web" | "miniapp"`；服务端 `_session_kind` 在 `client == "miniapp"` 且 `SystemConfig.get("session.miniapp_extended")` 为真时给 `EXTENDED`。优：业务规则与已有配置项对上；Web 行为与管理端不变；缺：请求体多一个字段，客户端可自报（与 `remember_me` 同样可自报，无新增攻击面：7 天会话本就对任何登录用户开放勾选）。
  - C 按 User-Agent / Referer 推断小程序。缺：不可靠，且微信 UA 可伪造。
- Decision: 选 B。`client` 缺省视为 `web`；非字符串或不在 `{web, miniapp}` 中 → `400 INVALID_VALUE`。管理员登录接口不接受该字段（既有 `remember_me` 未知字段规则不变，`B/accounts/views.py:319`）。
- Consequences: 正向：启用既有配置，管理员可经配置库关掉。负向：`M/utils/api.js` 的两个登录函数请求体变化，`M/tests/api.spec.js` 中对应断言需同步（受影响用例表）。

### ADR-084: 申请/申诉新增终态 `CLOSED`，注销时在同一事务内关闭
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-155、US-164、Q-PR-04=A（状态记为"已关闭（申请人已注销）"，不再出现在待处理队列，历史列表中可见）。基线：`B/identity/services.py:105-127` 的 `cancel` 在 `transaction.atomic()` 内结束房屋关系、使席位失效、`tombstone`，不处理 `Appeal`/`ResidentApplication`；待处理唯一约束靠 `pending_slot`（`B/residency/models.py:40,58`，M-SA-001 模式：置 NULL 释放槽位）。
- Options:
  - A 新增状态值 `CLOSED`（状态列 `max_length=8`，`CLOSED` 6 字符），`pending_slot=None`，`decided_at=now`，`decided_by*` 保持空；`STATUSES` 的 choices 增一项，需手写 residency 迁移 0002（AlterField，仅 choices）。优：保留可追溯；列表/审核页按状态区分；缺：多一条迁移与前后端状态映射。
  - B 复用 `REJECTED` 并写 `reject_reason="申请人已注销"`。优：无迁移；缺：与"管理员/业主主动驳回"混在一起，统计与审计无法区分；`reject_reason` 被用户申诉页原样展示，语义错。
  - C 直接删除记录。缺：违反 Q-PR-04=A 的"保留可追溯"，且审计 `object_id` 悬空。
- Decision: 选 A。关闭逻辑放进 `PendingRequestService.close_for_cancelled_user`（IFC-277），由 `IdentityService.cancel` 在既有事务内、`tombstone` 之前调用；对每条被关闭记录各写一条审计（新增动作 `RESIDENT_APPLICATION_CLOSED`、`APPEAL_CLOSED`，须登记到 `B/core/audit.py:10` 的 `AUDIT_ACTIONS`，否则 `AuditService.record` 抛 `ValueError`）。管理员或产权业主处理已关闭记录时返回 `409 ALREADY_CLOSED`（"该申请/申诉已关闭"），区别于已处理的 `ALREADY_DECIDED`。
- Consequences: 正向：待处理队列自然清空；历史可查。负向：迁移 0002 需手写（画像 P6，禁止 makemigrations 产物），MySQL 上 AlterField 仅改 choices 不产生 SQL；账号合并时（`move_all`）待处理记录不关闭，维持现状。

### ADR-085: 金额上限复用 `SystemConfig`，新增可编辑键 `claim.amount_max`（报销/备用金/收入共用）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-161、US-170、Q-PR-01=A（共用一个上限，必须为正数，不允许清空）。基线：`B/claims/views.py:24`、`B/income/views.py:28` 各硬编码 `MAX_AMOUNT = Decimal("1000000.00")`；`B/core/config.py:37` 已有 `claim.amount_max: None` 但无读取点；`EDITABLE_KEYS` 仅含 `audit.retention_months`（`:8`）；写入端点 `PUT /admin/system-config/<key>` 已存在并写审计 `SYSTEM_CONFIG_CHANGED`（`B/core/views.py:43-66`），前端已有 `admin.updateSystemConfig`（`W/shared/api.js:168-169`）。
- Options:
  - A 复用 `SystemConfig`：把 `claim.amount_max` 默认值改为 `"1000000.00"`（字符串，JSON 友好），加入 `EDITABLE_KEYS`，在 `SystemConfigView.put` 增加该键的校验分支；claims/income 读取该键。优：零新表、零新迁移、审计已有、前端 API 已有；缺：值以 JSON 字符串存储，读取处须统一转 `Decimal`。
  - B 新建 `AmountLimit` 模型 + 迁移 + 新端点。缺：过度设计，新增迁移与端点只为一个标量。
  - C 保持硬编码，仅文档化。缺：违反用户 Q1=C。
- Decision: 选 A。校验：可转 `Decimal`；`> 0`；小数位 ≤ 2；`≤ 999999999999.99`（`DecimalField(max_digits=14, decimal_places=2)` 的列上限，`B/claims/models.py:14`）。入库统一格式化为两位小数字符串。读取走新增的 `SystemConfigService.amount_max() -> Decimal`，值缺失或损坏时回退默认 `Decimal("1000000.00")`。已提交记录不受影响（只在提交时校验）。
- Consequences: 正向：改一个键即可，审计与权限现成。负向：`GET /admin/system-config` 的返回键集合增加（既有无测试断言，`git grep system-config backend/tests` 无命中）；全局配置写入在 E2E 中属"非 e2e_ 账号数据"边界，见 ADR-096 与开放问题。

### ADR-086: 规则限制向前端暴露：新增只读 `GET /system/limits`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-161（提示当前上限）、REQ-FUNC-163（发起界面事先显示题数/选项/窗口限制，US-172 AC-172-01）、REQ-FUNC-164（导入/录入上限提示）。这些值分别来自配置 `claim.amount_max`、`poll.max_questions`、`vote.min_window_minutes`（`B/core/config.py:37-39`）和代码常量（选项 2 ~ 10：`B/polls/views.py:97-98`；导入 5000：`B/income/views.py:79`；录入 500：`:218`）。
- Options:
  - A 前端写死文案。缺：与可配置项脱节（题数、窗口、金额都可被配置改变），REQ-NFUNC-028 的"提示与行为一致"无法保证。
  - B 新增 `GET /system/limits`（IsMember）返回当前生效值。优：提示与校验同源；两端共用；缺：多一个端点。
  - C 把限制塞进各业务列表响应。缺：污染既有响应结构，违反"既有字段不变"。
- Decision: 选 B。常量收拢为 `apps/core/limits.py`（新建）中的具名常量，polls/income 视图改为引用，行为不变。
- Consequences: 正向：提示文案由数据驱动。负向：新增 IFC-272 与两端 api 函数；常量搬家需确保 polls/income 既有测试仍通过（纯重构）。

### ADR-087: 用户选择器复用 `GET /admin/users`，不新增专用搜索接口
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-151、US-159、Q-PR-09=B（候选项显示昵称、清册实名、账号、脱敏手机号、最高身份）。基线：`GET /admin/users`（`B/accounts/views.py:403-430`，IsAdmin）已支持 `q` 匹配账号、昵称、完整手机号、手机号后 4 位、实名（`directory.real_name_q`），且已返回 `identity_label`、`real_names`、脱敏 `phone`、分页（`B/accounts/serializers.py`）。
- Options:
  - A 复用 `admin/users`：前端新建 `UserPicker` 组件调用它。优：后端零改动；权限（非管理员 403，AC-159-06）、脱敏、分页现成；缺：返回字段多于选择器所需（含 `last_login_at`、`certified_units`），但仅对管理员可见，不违反 C-42。
  - B 新建 `GET /admin/users/search` 只返回 6 个字段。优：字段最小；缺：重复实现搜索条件，未来与账号页搜索口径可能分叉。
- Decision: 选 A。Q-PR-09=B 已决定实名对管理员展示，字段超集不构成新的暴露面。选中后"再次显示所选用户信息供确认"由组件持有的已选对象渲染，不再请求。
- Consequences: 正向：无后端工作量、无新契约。负向：若将来要对"业委会成员"开放选择器，需重新评估字段最小化。

### ADR-088: 列表翻页：后端保持 `page_response`，前端补翻页控件
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-152、US-160/161。基线：全部目标列表的后端已分页——`page_response`（`B/core/serializers.py:5-13`，默认 20、上限 100，返回 `{count, page, page_size, results}`），报销列表 `B/claims/views.py:199,289`、决议 `B/resolutions/views.py:65`、投票 `B/polls/views.py:36`、收入 `B/income/views.py:212,382`、报表 `B/ledger/views.py:25`、席位 `B/committee/views.py:46`、流程 `B/approval/views.py:53`、待办 `B/approval/views.py:131-150`（内存分页）；缺口全在前端（`W/admin/AdminUsers.vue:71-81` 等只取第一页）。
- 约束来源与被排除方案：既有后端契约。被排除：游标分页（现有客户端与测试依赖 `count/page/page_size`）；取消分页（数据量增长后响应过大）。
- Decision: 后端零改动。Web：新建组合函数 `usePaging`（W/shared/usePaging.js），封装 `page/pageSize/total/loading` 与"筛选条件变化回到第 1 页、翻页保持筛选"，页面用 Element Plus `el-pagination`（现有清册、审计页已在用）；小程序：新建 `M/utils/paging.js`，"加载更多"追加下一页，`has_more = loaded < count`，显示"没有更多了"与总数。`待办` 内存分页保持（量级为本人待办，小）。
- Consequences: 正向：无后端风险。负向：12 个 Web 页面 + 4 个小程序页改动面大；每个页面需要既有测试里 `http.get` mock 返回 `{results}` 形态保持兼容（组合函数对数组与分页对象都容错，沿用页面现有 `data.results || data || []` 写法）。

### ADR-089: 二次确认：Web 用 Element Plus `ElMessageBox.confirm` 封装，小程序用 `uni.showModal`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-150、US-158、US-153 AC-153-04。基线：撤销认证 `W/admin/AdminMemberships.vue:49-57`、撤销席位 `AdminSeats.vue:130-138`、删除专有部分 `AdminRegistry.vue:253-260`、删除审批流程 `AdminFlows.vue:88`、收入表作废 `W/portal/Income.vue:180`、撤回 `Claims.vue:303`、`ResolutionDetail.vue:95`、注销 `Me.vue:235` 均直接执行；内容中心已有确认先例 `AdminContentPosts.vue:63-79`。
- Options:
  - A 统一封装 `confirmDanger({ title, consequences, confirmText }): Promise<boolean>`（Web：`ElMessageBox.confirm`，`W/shared/confirm.js`；小程序：`uni.showModal`，`M/utils/confirm.js`）。优：后果文案集中、取消即不发请求、可单测；缺：小程序 `showModal` 不支持多行富文本，后果列表用换行拼接。
  - B 每个页面自行写 `ElMessageBox`。缺：9 处重复，后果文案易漂移。
  - C 自建对话框组件。缺：重复造轮子，且要适配三套风格（ui_blocks 守护）。
- Decision: 选 A。后果文案作为常量表放在 `confirm.js`（按操作键）：`revokeMembership`、`revokeSeat`、`deleteUnit`、`deleteFlow`、`voidIncome`、`withdrawResolution`、`withdrawClaim`、`withdrawIncome`、`removeResident`、`leaveUnit`、`cancelAccount`（四项后果，AC-158-04）。取消路径：返回 `false`，页面不发请求、不写审计。
- Consequences: 正向：误操作防护统一。负向：既有页面测试若直接点击"撤销/删除"并断言接口被调用，需先放行确认（MOD-086 受影响用例表）。

### ADR-090: 自定义版式模板：独立管理页 + 后端"被引用禁删" + 列表补 `id`/`usage_count`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-153、US-162、Q-PR-07=B（内置只读；被内容引用的自定义模板禁止删除并提示被引用数量）。基线：`B/content/views_admin.py:112-131` 已有 CRUD；`StyleService.delete`（`B/content/styles.py:121-127`）直接删除；内容以 `ContentPost.style_key="custom:<id>"` 引用（`B/content/models.py:12`），模板被删后 `resolve_tokens` 回落到 classic，静默改变已发布内容外观（`styles.py:52-62`）；`list_all` 只返回 `key` 无数值 `id`（`styles.py:44-49`），前端 `updateStyleTemplate(id,…)` 需要数值 id（`W/shared/api.js:177-179`）。
- Options:
  - A 新增路由页 `AdminStyleTemplates.vue`（`content/styles`），后端 `delete` 前统计引用数并 `409 STYLE_IN_USE`，列表给自定义项补 `id` 与 `usage_count`。优：边界在服务端，不依赖前端；缺：管理端路由页数量由 16 变 17，需同步 `frontend/tests/qa_unit_theme.spec.js:273` 的数量断言。
  - B 在内容编辑器内做弹窗管理。优：不加路由；缺：入口隐藏在编辑器里，不满足"提供管理页"，且编辑器文件已很大（`AdminContentEditor.vue`）。
  - C 仅前端禁用删除按钮。缺：后端不设防，直接请求即可删除，违反 AC-162-04。
- Decision: 选 A。内置模板无数值 id、路由为 `<int:template_id>`，对其的 PUT/DELETE 无法寻址（路由层 404），列表中内置项不带 `id`、`builtin: true`，页面不渲染编辑/删除入口；"直接请求被拒绝"由路由不存在保证（E2E 断言 404 且内置模板列表不变）。引用统计口径：`ContentPost` 中 `style_key == "custom:<id>"` 的全部状态（草稿、已发布、已下线）。
- Consequences: 正向：删除安全。负向：`list_all` 对自定义项新增字段（只增不改，既有字段不变）；多一次聚合查询（单条 `GROUP BY`，模板数量小）。

### ADR-091: 报表明细：小程序新增明细页；服务端对支出事由脱敏
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-159、US-168、Q-PR-06=A（与 Web 报表详情同口径）。基线事实：Web 的 `Reports.vue:25-31` 实际只渲染合计与结余；但 `GET /ledger/reports/<id>`（`B/ledger/views.py:54-62,77-78`）返回的 `detail` 数组含全部明细行，其中支出行 `summary` 直接取报销事由（`B/claims/services.py:21,41`）。已确认的既有规则 OQ-08："报表明细默认不显示支出事由，只显示类型与金额（事由可能含个人信息）"（`project_workspace/ocap/requirements/requirements_spec.md` REQ-FUNC-050），配置项 `report.show_expense_reason` 默认 False（`B/core/config.py:41`）无读取点——即 API 目前违反 OQ-08。
- Options:
  - A 小程序新页读取同一接口，客户端自己不渲染 `summary`；服务端不动。优：后端零改；缺：API 仍对任何登录用户泄露事由，新增的移动端入口放大暴露面。
  - B 服务端在 `report_detail` 中对 `direction == "EXPENSE"` 的明细行在 `report.show_expense_reason` 为假时把 `summary` 置 `null`；小程序渲染"类型、日期、金额、方向"。优：落实 OQ-08；两端同口径；缺：既有 API 响应内容变化（字段保留，值变 null）。
  - C 另开移动端专用接口。缺：两个口径，违反 Q-PR-06=A"完全同口径"。
- Decision: 选 B [ASSUMPTION：Q-PR-06 只说"同口径"，未提 `summary` 脱敏；这是对既有 OQ-08 的落实而非新需求，见开放问题 Q-B-01]。仅脱敏 `summary`；`source_type/source_id/seq` 沿用现状。Web 报表详情页同步增加明细表（日期、类型、方向、金额），使"与 Web 同口径"成立（Web 页面现状只有合计，REQ-FUNC-159 的"Web 报表详情"据此补齐 [ASSUMPTION]）。
- Consequences: 正向：封住既有泄露点。负向：若既有测试断言 `detail[*].summary` 非空，需更新（GROUP_C 须先 `git grep "\"detail\"" backend/tests`）；Web 报表页多一个明细表。

### ADR-092: 中文显示：前端集中映射表 + 统一时间格式函数
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-158、US-167。基线：`W/portal/Units.vue:175` 拼 `result.role`；`Polls.vue:15` 直出 `status/deadline`；`AdminSeats.vue:22`、`AdminUsers.vue:11,28` 显示 `ACTIVE`/`true`；后端部分接口已给中文标签（`identity_label`、`role_label` 将新增），但状态类字段（`OPEN/CLOSED/ACTIVE/PENDING…`）均为代码。`W/shared/format.js:11-14` 已有 `formatDateTime`（截到分钟）；`W/portal/StatusTag.vue` 有状态标签先例。
- Options:
  - A 前端集中映射：`W/shared/labels.js`、`M/utils/labels.js`（同一份键值，两端各一份文件）+ 既有 `formatDateTime`。优：后端零改、两端可单测；缺：映射在两个仓库目录各一份，需测试守护两份一致。
  - B 后端所有接口都返回 `*_label`。缺：改动面大、响应字段激增，违反"既有字段不变"的低风险目标。
- Decision: 选 A。时间沿用 `formatDateTime`（`YYYY-MM-DD HH:mm`，响应本身已带 `+08:00` 偏移，截取即为 Asia/Shanghai 展示，与 REQ-FUNC-139 一致）。守护测试：两份 labels 键集合一致；页面源码不再出现 `{{ …status }}` 的裸输出（以关键页面渲染断言替代源码扫描）。
- Consequences: 正向：改动局部。负向：未覆盖到的页面仍可能漏网，MOD-086 给出页面清单。

### ADR-093: Web 头像显示：带令牌取 blob，不放开附件下载权限
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-156（更换头像后显示当前头像）。基线：`/me/profile` 返回 `avatar_url = /api/v1/attachments/<uuid>/download`（`B/accounts/models.py:38-42`），该端点需 Bearer 令牌（`B/core/views.py:87-91`，`IsMemberOrAdmin`），`<img src>` 无法带 `Authorization` 头，故页面显示空白——这是"不显示当前头像"的根因（`W/portal/Me.vue:143-144` 只上传不展示）。
- Options:
  - A 前端用 `http.get(…, { responseType: 'blob' })` 取图转 `URL.createObjectURL`，封装为 `AuthImage.vue`。优：不改后端权限；缺：每次进入页面多一次请求，需在卸载时 `revokeObjectURL`。
  - B 后端给头像开放签名 URL（类似 `MediaFileView` 使用的 `verify_media_sig`，`B/content/media.py:286`、`views_member.py:52`）。缺：新增签名机制与过期策略，超出本批范围。
  - C 放开头像附件匿名下载。缺：个人信息保护倒退，违反 C-42。
- Decision: 选 A，Web 个人中心使用；小程序不在 REQ-FUNC-156 范围。头像文件类型/大小提示与选择器限制（`accept=".jpg,.jpeg,.png"`，≤ 2 MB，`B/core/attachments.py:22` 的服务端限制不变）在前端提前校验，服务端校验保持为最终防线。
- Consequences: 正向：权限模型不变。负向：Me.vue 引入新组件与 blob 生命周期管理；`W/shared/api.js` 的 `attachmentApi` 增加 `download`。

### ADR-094: 现行规则固化（REQ-FUNC-162 ~ 166）：不改行为，只导出常量并补测试
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-162（半数分母取在任人数）、163（题数 50/选项 2 ~ 10/窗口 60 分钟）、164（导入 5000 行、录入 500 条）、165（日期与数量校验、重复申请限制）、166（模板示例 6 行/4 个专有部分）。这些在代码中已按需求实现：`B/resolutions/services.py:73-76`（`agree*2 > denominator`，`result.denominator` 已记录）、`B/committee/services.py:80-90`（`ACTIVE` 模式只统计委员/副主任/主任）、`B/polls/views.py:51-53,97-98,109`、`B/income/views.py:79,218`、`B/committee/views.py:67`、`B/claims/views.py:96,124,151`、`B/residency/views.py:79,186`、`B/registry/import_spec.py:42-49`。
- 约束来源与被排除方案：REQ-NFUNC-028（现有业务不变）。被排除：把 `vote.denominator_mode` 做成不可配置/删除配置项（改动与风险无需求依据；该键不在 `EDITABLE_KEYS`，管理员无法改，`CONFIGURED_CAP` 模式仅可经直接改库触发，保留）；重写校验（零收益）。
- Decision: 后端只做两处极小改动：(1) 把导入/录入/选项数上限收拢为 `apps/core/limits.py` 常量（ADR-086）；(2) 无其它行为改动。其余以测试固化（MOD-086 的用例清单逐 AC 列出）；TC-INT-311 的期望更新为 6 行/0 失败/4 个专有部分（US-175 AC-175-03，由测试阶段执行）。
- Consequences: 正向：零行为风险。负向：规则仍分散在各视图，只有限制值集中；REQ-FUNC-162 的"发起人不回避"等既有行为依赖现有测试守护。

### ADR-095: 同住人名单与待审提示的可见范围：只对该专有部分产权业主，且不含手机号
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-143、145、C-42、REQ-NFUNC-002。基线：`to-review` 已返回申请人脱敏手机号（`B/residency/views.py:205-219`）；移除接口鉴权为 `MembershipService.is_owner_of`（`B/residency/views.py:251-258`）。
- 约束来源与被排除方案：C-42（同住人明细只对该专有部分的产权业主、申请人本人和管理员可见）。被排除：向同住人本人展示同房其他同住人名单（无需求，违反最小化）；名单中展示手机号（AC-151-01 要求不显示明文，名单同理仅给昵称与账号）。
- Decision: `GET /me/housing` 中 `residents` 仅在该用户对该房屋为 `HEAD`/`OWNER` 时填充，字段为 `user_id`、`nickname`、`account_no`、`joined_at`；`pending_application_count`、`pending_review_count` 同样仅统计本人为产权业主的专有部分。
- Consequences: 正向：不新增 PII 暴露面。负向：同住人看不到同住人名单（符合现需求）。

### ADR-096: E2E 夹具：`manage.py e2e_fixture`，只创建/清理 `e2e_` 账号及其关系数据，不触碰清册
- Status: Proposed
- Type: decision
- Context: Q-PR-05（GR-A-002 条件：夹具只新增 `e2e_` 账号相关数据，不改 `RegistryUnit`/`RegistryOwner`/`RegistryPhone`）；画像 P4-1（E2 创建并清理 `e2e_` 账号；测试代码在 `backend/tests/remote/`；短信为 console 替身）、P8。需求侧 E2E 故事（US-150 ~ 153、156、157、159、162 等）需要"已有产权业主的专有部分"。
- Options:
  - A 单一管理命令 `e2e_fixture`（`setup` / `status` / `cleanup`）：在测试机内创建 `e2e_` 前缀账号（普通用户、管理员、有席位的成员）、挑选现有"无有效房屋关系"的专有部分建立 `e2e_` 用户的 `Membership`（直接写关系行，不改清册行）、创建 `e2e_` 审批流程；`cleanup` 按"昵称/用户名前缀 + 预留手机号段"双条件删除并按 PROTECT 外键顺序先删依赖行。优：一次执行、可重复、有 `status` 校验清册行数未变；缺：需精心设计删除顺序与护栏。
  - B 全部通过 HTTP 完成（注册 → 申诉 → 管理员审核通过获得房屋关系）。优：走真实流程；缺：注册需短信验证码（console 替身，要读服务日志），步骤多且慢；席位无法通过 HTTP 在人数/任期未配置时赋予。
  - C 造 `e2e_` 前缀的专有部分。缺：违反 P4-1 与 GR-A-002 条件（需放宽边界，向用户另行申请）。
- Decision: 选 A，并保留 B 作为各 E2E 用例中"被测流程"本身（如 AC-156 的申诉提交与审核仍走 HTTP，夹具只提供前置账号与房屋）。护栏：命令需要环境变量 `OCAP_E2E_FIXTURE=1`；密码经环境变量 `OCAP_E2E_PASSWORD` 传入（不落盘、不输出）；`cleanup` 默认 dry-run，加 `--execute` 才删除；任一待删行不满足双条件时拒绝；发现 e2e 数据已产生账本分录（`LedgerEntry`）时退出码 2 并列出，不自行删除账本（见 module_design E2E 小节）。
- Consequences: 正向：满足 P4-1 与 Q-PR-05；E2 可自动化执行。负向：夹具直接写 `Membership`/`Seat` 绕过业务校验（仅限 `e2e_` 用户），且在测试期间占用 3 个真实专有部分的"户主"槽位——期间真实业主在这些房屋认证只能成为"产权业主"，清理后恢复；`Seat` 会改变测试环境"在任人数"（半数分母），故夹具默认只造 2 名委员 + 1 名业主代表，且测试结束即清理。全局配置写入（`claim.amount_max`）与 `e2e_` 账号数据边界的关系见开放问题 Q-B-02。

## 开放问题 / ASSUMPTION

| 编号 | 问题 / 假设 | 影响 | 建议 |
|---|---|---|---|
| Q-B-01 | [ASSUMPTION] ADR-091：对支出行 `summary` 脱敏属于落实既有 OQ-08，而非新增需求；Web 报表页补明细表，使"Web 报表详情含明细"成立（需求文档称 Web 已有明细，代码实为只有合计）。 | REQ-FUNC-159、US-168 AC-168-01 | 请 PM/用户确认采用 B；若选 A（仅客户端不渲染），ADR-091 与 MOD-079 回退 |
| Q-B-02 | AC-170-01 [E2E] 要求在测试环境修改全局配置 `claim.amount_max` 再恢复；画像 P4-1 允许写入"仅限测试账号自身及其产生的数据"，全局配置不属于任何 `e2e_` 账号数据。 | 部署后 HTTP E2E 的 AC-170-01 | 推荐：部署后 E2E 不修改全局配置，只验证"默认 1,000,000.00 边界"与"非管理员 403"；"500,000.00 边界"仅本地验证。若用户希望远程也验证，需用户明确授权放宽 P4-1（改后由 `finally` 恢复并由夹具 `status` 校验默认值） |
| Q-B-03 | [ASSUMPTION] 夹具直接创建 `Membership`/`Seat`（`e2e_` 用户）与 `e2e_` 审批流程；账号手机号取预留号段 `1990000xxxx`（短信为 console 替身，不会外发；真实用户手机号不会被占用的概率极低，但不能完全排除）。 | 夹具的唯一键冲突 | 夹具 `setup` 先检查号段冲突，冲突则报错退出；E2 部署前向用户确认号段 |
| Q-B-04 | [ASSUMPTION] 小程序待办（REQ-FUNC-152 含"待办"）只在首页待办卡片上做"加载更多"，不新增待办页。 | M/pages/index/index.vue | 若要独立待办页，另行评审 |
| Q-B-05 | [ASSUMPTION] `appeals/mine`、`resident-applications/mine` 保持"数组、不分页"的现状，仅在服务端限制最近 100 条，防止无限增长；REQ-FUNC-152 的翻页清单不含这两个列表。 | IFC-263 | 无需用户确认，若将来需要翻页再改 |
| Q-B-06 | 认证与申请的限流：`POST /resident-applications` 现无限流（`B/residency/views.py:169-193`，对比 `certifications` 有 `RateLimiter`）。本批不新增，沿用"同一人同一专有部分一条待审"唯一约束；入口面向全体注册用户后调用量会上升。 | 滥用面 | 建议下一批评估限流；本批不改以免超范围 |
| Q-B-07 | 基线文档编号：user_directory 与 admin_polish 的 IFC-243 ~ 246 重复（旧问题）。本批 IFC 自 261 起，引用旧接口时写 `批次/IFC`。 | 追溯 | 已在本文说明，不改前批文档（C-41） |

画像 P11：本批无新增外部 API 用法（微信/短信/邮件/内容平台/LLM 均不触碰；测试只经 `apps/integrations/fakes.py`）。
