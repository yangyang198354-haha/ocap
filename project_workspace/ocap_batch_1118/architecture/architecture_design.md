<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T00:54:23+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>requirements/user_stories.md（1.0.0）</file>
    <file>../ocap_identity_property/architecture/module_design.md（1.0.0，上一批基线）</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计（INCREMENTAL）：申诉一次提交、专有部分检索、身份页姓名、决议参与进度、卡片与导航动效、清册排序、席位授予清册业主

编号延续全仓最大值（`git grep` 数值最大：ADR-135、MOD-138、IFC-344）：本批 ADR-136~146、MOD-139~152、IFC-345~367。

## 架构概览

本批不引入新服务、新依赖、新进程。8 条用户需求落在现有 Django 单体（`backend/apps/*`）与 Vue 3 Web 前端上，小程序不改（Q-B18-01=A）。

改动在现有系统中的位置：

| 需求 | 后端落点 | 前端落点 |
|---|---|---|
| 1 申诉一次提交（REQ-FUNC-239/240） | `core/attachments.py`（新增"先校验后落盘、失败清理"）、`residency/views.py` `AppealListCreateView`（同路径增加 multipart 分支） | `portal/units/UnitsAppeal.vue`、`shared/api.js` |
| 2 专有部分检索（241） | 无 | `portal/parts/UnitCascader.vue`（一个组件覆盖三页） |
| 3 身份页姓名（242/243） | `residency/housing.py`、`residency/views.py` `MyHousingView`（`/me/housing` 增字段） | `portal/units/UnitsIdentity.vue` |
| 4 决议卡片、进度、参与人（244/245/246/254） | `resolutions/views.py`、`resolutions/services.py`、`resolutions/apps.py`（附件策略）、`core/attachments.py`（头像可读）、`committee/services.py`（分母口径文档化与守护） | `portal/Resolutions.vue`、`ResolutionDetail.vue`、`shared/voteShare.js` |
| 5 整卡可点与动效（247） | 无 | `Resolutions.vue`、`Polls.vue`、`shared/style.css` |
| 6 导航动效（248） | 无 | `layout/SideNav.vue`、`layout/SubNavBar.vue`、`shared/style.css` |
| 7 清册排序（249/250） | `registry/views.py` `AdminUnitListView`、新建 `registry/listing.py` | `admin/AdminRegistry.vue` |
| 8 席位授予清册业主（251/252/253/254） | `committee/models.py`（`Seat` 增字段，迁移 0002）、`committee/services.py`、新建 `committee/binding.py`、`committee/views.py`；`residency/models.py`（`Membership.registry_owner`，迁移 0005）、`residency/services.py`、`residency/views.py`、`residency/phone_match.py`、`residency/auto_bind.py`；`registry/views.py`、`registry/importing.py`（清册变化钩子）；`polls/views.py` 经 `CommitteeQuery` 的排除 | `admin/AdminSeats.vue`、新建 `admin/parts/SeatHolderPicker.vue`、`UnitCascader` 复用 |

关键质量属性（引 REQ-NFUNC）：

- 隐私（REQ-NFUNC-046）：真实姓名、共有产权人、参与人、候选业主的可见性全部在服务端裁剪，前端只做展示；公开决议接口移除 `votes[].voter_id/choice`（见 ADR-141）。
- 一致性与审计（REQ-NFUNC-049）：申诉失败路径无孤立文件（ADR-136）；席位"同一清册业主至多一个有效席位"由数据库唯一约束兜底（ADR-137）；通过判定与进度条共用 `CommitteeQuery.denominator_for_half_majority`（ADR-139、ADR-141）。
- 兼容与零回归（REQ-NFUNC-050）：所有后端接口变更均为"增字段/增分支/增参数"；唯一的字段删除是 `votes` 数组，其依据与影响在 ADR-141；小程序受影响接口清单见 ADR-146。
- 性能（REQ-NFUNC-048）：清册约 650 套量级，服务端排序在内存完成（ADR-142）；列表与进度不引入 N+1（ADR-141）。
- 动效可控（REQ-NFUNC-047）：新增动画只写在 `frontend/src/shared/style.css`，沿用现有全局减少动效规则（`frontend/src/theme/generated/themes.css:689-692`，由 `scripts/themes/build.mjs:156` 生成），并在 JS 驱动的高度动画处自行判断（ADR-144）。

## 部署视图

仅画像 P7 中存在的环境（测试环境，树莓派；生产不存在）。

| 组件 | 运行单元 | 环境 | 变化 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 执行 `manage.py migrate`（committee 0002、residency 0005）后重启 |
| Web 前端静态文件 | nginx 8090 站点 `ocap` 的 `web/` 目录 | 测试 | 重新构建 `npm run build -- --base=/ocap/` 并发布 |
| 定时任务 | `manage.py run_due_jobs`（既有，`apps/jobs/management/commands/run_due_jobs.py:26` 调用 `expire_due`） | 测试 | 不新增任务；`expire_due` 增加一步"清册变化失效"（ADR-139），无需改调度 |
| nginx `client_max_body_size` | `/etc/nginx/sites-available/ocap` 与 Freeark 的 `^~ /ocap/` 块（不在仓库内，参见 content_publish architecture_design.md:84） | 测试 | **须核实** ≥ 55 MB（申诉一次提交最多 5 份 ×10 MB + 表单开销，ADR-136）；核实或调整由 E1/E2 完成，不动 Freeark 其他段 |
| 小程序 | — | — | 不改、不构建；后端兼容性见 ADR-146 |

无新增 systemd 服务、环境变量、端口。

## ADR

### ADR-136: 申诉"一次提交"的传输与原子性方案
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-239/240、REQ-NFUNC-049(1)、C-76（附件类型/大小/数量沿用）。现状：`UnitsAppeal.vue:35-45` 选文件即调 `POST /attachments`（`core/views.py:16-30`）得到 TEMP 附件，`POST /appeals` 再以 `proof_ids` 关联（`residency/views.py:124-168`、`core/attachments.py:92-110`）。要求：不完整时服务端无残留附件、无半截申诉；暂存只在页面内。DRF 默认解析器含 JSON/Form/MultiPart（`config/settings.py:89-94` 未覆盖 `DEFAULT_PARSER_CLASSES`）。小程序仍走"先上传再 `proof_ids`"（`miniprogram/utils/api.js:34`），该路径必须保持可用。
- Options:
  - A. 同一路径 `POST /api/v1/appeals` 增加 multipart 分支（字段 `unit_id`、`owner_name`、多个 `files`）；服务端"全部校验通过 → 事务内创建申诉并落盘关联 → 失败则删除已落盘文件"。JSON 分支（`proof_ids`）原样保留。优：一次请求、服务端天然原子；不新增路由；小程序零影响；前端契约测试仍解析到 `POST /appeals`。缺：multipart 单请求体最大约 50 MB，须核实 nginx 限额；两条分支需同一套校验。
  - B. 前端暂存，点提交时先逐个 `POST /attachments` 再 `POST /appeals`（纯前端改动）。优：后端零改动。缺：第 3 个文件上传失败或申诉被拒（如 `APPEAL_PENDING`）时前 2 个文件留在服务器，违反 REQ-NFUNC-049(1)；只能靠定时清理 TEMP 附件补救（当前无此任务）。
  - C. 新增"申诉草稿"实体，草稿内分步上传，提交时转正。优：可断点续传。缺：新模型+迁移+清理任务，且与 Q-B18-30=A"不保留暂存"相悖，过度设计。
- Decision: 选 A。原因：唯一能在服务端保证"要么全成功、要么无残留"的方案（REQ-NFUNC-049(1)），且对现有 JSON 客户端零破坏（REQ-NFUNC-050）。
- Consequences: 正向——失败路径无孤立文件；前端暂存纯页面内状态，刷新即清空（AC-244-03）。负向——(1) 单请求体可达 50 MB，nginx/gunicorn 须核实（部署视图）；(2) 落盘在事务内、回滚不删磁盘文件，须由"失败清理"补偿（IFC-346 的 `discard`），进程在两步之间被杀会留下孤立磁盘文件（概率低，无 DB 记录，可由运维扫描 `media/appeal_proof/` 与 `Attachment.storage_path` 差集清理，记入风险）；(3) 校验逻辑须与 `AttachmentService.store` 同源，避免两套规则漂移（IFC-346 抽出共用函数）。

### ADR-137: 席位"待绑定"持有人的数据模型
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-251/252/253/254、REQ-NFUNC-049(3)(4)。现状：`Seat.user` 必填（`committee/models.py:31`），唯一约束 `uniq_seat_active_per_user`（`:39-41`）；`denominator_for_half_majority` 数所有"生效"的主任/副主任/委员席位（`committee/services.py:79-85`）；上限校验数 `status="ACTIVE"` 席位（`:107-115`，Q-OA-28=A 含未生效）。待绑定席位须占名额且计入分母（Q-B18-21=B）。
- Options:
  - A. `Seat.user` 改为可空；新增 `holder_owner`（FK→`registry.RegistryOwner`，`SET_NULL`）、快照 `holder_unit_text`/`holder_name`、`bound_at`、`bind_conflict_at`；新增唯一约束 `(holder_owner, active_slot)`。待绑定 = `status=ACTIVE 且 user IS NULL`。优：待绑定席位天然被现有"ACTIVE 计数"与"生效计数"覆盖，占名额、计入分母**无需改计数代码**；撤销/变更职位/到期/资格失效沿用同一套状态机；同一清册业主至多一个有效席位由唯一约束兜底（MySQL 唯一索引允许多个 NULL，与 M-SA-001 的槽位列做法一致）。缺：`Seat.user` 可空，所有读 `seat.user` 的地方要防空（见 MOD-140 清单）；`active_member_ids` 等返回 `user_id` 的查询须排除空值。
  - B. 新建 `PendingSeat` 表，绑定时转换为 `Seat`。优：`Seat.user` 保持非空，不改旧代码。缺：占名额与分母要在 5 处（上限、`denominator`、`config_view.over_cap`、撤销、变更职位）分别合并两张表；状态机重复；绑定时"转换"要在事务内删一建一并迁移审计关联，出错面更大。
  - C. 为未注册业主预建占位 `User` 账号。优：`Seat.user` 非空。缺：污染用户表与账号编号、手机号唯一性；注册时需"合并占位账号"，与现有账号合并机制（`register_user_reference`）纠缠；违反"系统用户即真实注册者"的现有假设。
- Decision: 选 A。理由：REQ-FUNC-254 要求待绑定与已绑定"同样视为在任席位"，A 让这一点成为模型事实而非 5 处补丁；REQ-NFUNC-049(3) 由唯一约束兜底。持有人展示字段用快照（`holder_unit_text`、`holder_name`），使清册被删后列表和审计仍可读（REQ-FUNC-253、REQ-NFUNC-049(2)）；快照仅管理员可见，不含手机号（C-79、REQ-NFUNC-046(4)）。
- Consequences: 正向——分母/上限/到期/撤销零改动即正确；迁移为单 app、可逆。负向——(1) `Seat.user` 可空是模型层语义变化，需穷举读取点（MOD-140）；(2) `polls/views.py:71` 的 `sorted(set(active_representative_ids()))` 遇到 `None` 会 `TypeError`，且业主代表投票的 `participant_count` 会被待绑定席位污染，故 `active_*_ids` 必须排除空 user（IFC-367）；(3) 快照与清册可能漂移，由 ADR-139 的"失效"规则收口。

### ADR-138: "认证核对通过的清册业主"的记录方式与绑定触发点
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-252、Q-B18-22=A（三种认证均适用）、Q-B18-23=A、Q-B18-26=A（"认证成功时记录通过核对的清册业主"，记录方式交设计）。现状三个认证入口都收敛到 `MembershipService.certify_owner`（`residency/services.py:41`）：手动认证 `CertificationView`（`residency/views.py:90-114`，核对 `owner_matches` 返回 bool，`registry/ownership.py:26-37`）、申诉通过 `AdminAppealDecisionView`（`views.py:200-237`，通过后 `append_owner_from_appeal` 返回 `AppendResult.owner_id`，`ownership.py:40-80`）、手机号匹配确认 `PhoneMatchService.confirm`（`phone_match.py:84-99`，经 `certify_one`）。
- Options:
  - A. 在 `Membership` 增加可空外键 `registry_owner`（`SET_NULL`）；三个入口各自把"本次核对通过的 `RegistryOwner.id`"传给 `certify_owner(…, verified_owner_id=…)`（申诉通过走 `record_verified_owner`，因 `append_owner_from_appeal` 在 `certify_owner` 之后执行），由其在同一事务内写入并调用 `SeatBinding.try_bind`。优：记录与认证同事务，三入口一个出口；"认证时核对的是谁"是持久事实，后续授予席位可据此直接找到已注册用户（AC-256-05）。缺：改 `Membership`（residency 迁移 0005）；`certify_owner` 签名增参（缺省 `None`，旧调用兼容，M-SA-015）。
  - B. 不存记录，绑定时按"用户已验证手机号 ↔ `RegistryPhone`"实时推导清册业主。优：无迁移。缺：申诉通过的用户可能无手机号（`ownership.py:64-65` 分支），且 Q-B18-26 明确否定 B；手机号变更后推导漂移。
  - C. 按认证时输入的姓名匹配席位。优：直观。缺：Q-B18-26 否定 C；手机号匹配确认路径没有输入姓名。
- Decision: 选 A。绑定触发点即 `certify_owner` 成功之后（含 `HEAD` 先到先得与同住人升级分支），`try_bind` 永不向外抛异常（沿用 `certify_one` 的"不得影响主流程"约定，`auto_bind.py:25-40`），冲突与失败写审计而不回滚认证。对**授予时用户已注册且已认证**的情形（AC-256-05），`SeatBinding.certified_user_of(owner)` 先查 `Membership.registry_owner`，查不到再按"产权业主 Membership 的用户已验证手机号 ∈ 该清册业主的 `RegistryPhone`"回退（与 `accounts/directory.py:42-55` 实名口径一致），以覆盖本批之前已认证、无 `registry_owner` 记录的用户（不做回填迁移，M-SA-012）。
- Consequences: 正向——三种认证方式统一、可审计；授予与绑定对称。负向——(1) 旧认证无记录，依赖手机号回退，若旧用户手机号与清册不一致则授予时按"待绑定"处理且永不自动绑定（因其已认证，无新的认证事件）——处置见开放问题 OQ-B1（管理员改用"用户 ID 授予"旧路径）；(2) `Membership.registry_owner` 因 `SET_NULL`，清册业主被删后记录丢失，但已绑定席位不依赖它；(3) 申诉通过时"核对"是管理员依据证明的人工核对，姓名取自申诉 `owner_name`，与 Q-B18-22=A 的"姓名一致"含义一致。

### ADR-139: 待绑定席位的表决口径、名额、任期、冲突与清册变化失效
- Status: Proposed
- Type: constraint-driven
- Context: Q-B18-21=B（占名额、计入分母）、Q-B18-24=A（冲突保持待绑定）、Q-B18-25=A（清册变化失效）、Q-B18-27=A（任期自授予日起算）、REQ-FUNC-252/253/254、REQ-NFUNC-049(2)(4)(5)、C-77。
- Options（被排除的替代方案及约束来源）:
  - 待绑定不计入分母（Q-B18-21=A 推荐项）——用户已明确选 B，排除。
  - 绑定时自动撤销新席位/以较高职位保留（Q-B18-24=B/C）——用户选 A，排除。
  - 清册变化后保留由管理员撤销（Q-B18-25=B）——用户选 A，排除。
  - 绑定时任期从绑定日起算（Q-B18-27=B）——用户选 A，排除。
- Decision（全部由上述用户答复与既有代码约束推出）:
  1. **分母与上限**：沿用 `CommitteeQuery.denominator_for_half_majority`（`committee/services.py:79-85`）与 `CommitteeCommands.grant` 的上限计数（`:107-115`）不改计数逻辑——ADR-137 的模型使待绑定席位（`status=ACTIVE`、`user IS NULL`）自然被计入；业主代表不在 `position__in` 内，不计入分母（AC-259-09）。判定结果的 `denominator` 沿用既有 `result` JSON（`resolutions/services.py:68-72`）。以回归用例守护，不以代码补丁实现。
  2. **表决资格**：`CommitteeQuery.is_member/active_seat/active_member_ids` 均以 `user_id` 为键，待绑定席位无 `user_id`，天然无资格；`active_member_ids`/`active_representative_ids` 显式排除空 user（IFC-367）。
  3. **绑定**：`SeatBinding.try_bind(user_id, owner_id)`（IFC-352）在事务内加锁取 `holder_owner_id=owner_id AND user IS NULL AND status=ACTIVE AND term_end>=今天` 的席位；重新核验清册业主仍存在且姓名（`normalize_owner_name`）与快照一致；用户已有 ACTIVE 席位 → 写 `bind_conflict_at` 与审计 `SEAT_BIND_CONFLICT`，席位保持待绑定（AC-257-06）；否则写 `user`、`bound_at`，审计 `SEAT_BOUND`，不改 `term_start/term_end`（AC-257-09），不发通知（Q-B18-28=A）。`(user, active_slot)` 唯一约束的 `IntegrityError` 一并按冲突处理。
  4. **冲突后的出路**：不新增"重试绑定"接口。管理员撤销该用户的原席位后，再对同一清册业主"赋予席位"，因 `Membership.registry_owner` 已记录，授予直接落到该注册用户（ADR-138）。该做法需用户知悉，列入开放问题 OQ-B2。
  5. **清册变化失效**：`CommitteeCommands.reconcile_registry_seats()`（IFC-353）把"`user IS NULL`、`ACTIVE`，且 `holder_owner` 已为空（行被删，`SET_NULL`）或其当前姓名与快照不一致"的席位置 `INVALIDATED`、`end_reason="REGISTRY_CHANGED"`、`active_slot=None`，审计 `SEAT_INVALIDATED`（原因"清册变化"）。调用点：`AdminUnitOwnersView.put`、`AdminUnitDetailView.delete`、`importing.apply_plan`（均在各自事务内，`registry/views.py:229-259`、`importing.py:575-586`）与 `expire_due` 开头（兜底）。已绑定席位不受清册变化影响（其依据是 `Membership`，由既有 `sync_after_ownership_change` 处理）。
  6. **过期**：待绑定席位到期仍由 `expire_due` 按 `term_end` 置 `EXPIRED`（`committee/services.py:222-232` 已按状态而非用户查询）；`try_bind` 对 `term_end < 今天` 的席位不绑定（AC-257-09）。
- Consequences: 正向——不用为 Q-B18-21=B 改任何计数公式，行为变化来自数据而非代码；所有决定可追溯到用户答复。负向——(1) 用户已知的副作用：待绑定越多半数同意越难通过（REQ-FUNC-254 影响说明），本设计只按 Q-B18-33 推荐 A 提供只读提示（IFC-356），不拦截，"用户待确认"；(2) `reconcile` 在清册批量导入事务内执行，需只扫描 `user IS NULL` 的少量席位，成本可忽略；(3) 清册改名使待绑定席位失效后，需管理员重新授予（与 Q-B18-25=A 一致）。

### ADR-140: 真实姓名与共有产权人的数据来源与接口位置
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-242/243、REQ-NFUNC-046(1)(2)(5)、Q-B18-04=A/05=B/06=A/07=A。现状：`/me/housing`（`MyHousingView`，`residency/views.py:34-45`）返回 `summary/units/pending_review_count`，字段集被契约测试严格相等锁定（`backend/tests/integration/test_frontend_contract.py:582-585`，M-SA-023）；实名口径函数 `accounts/directory.py:42-55 real_names` 需逐成员关系读 `unit.owners` 与 `phones`（用于管理端，会产生 N+1）。
- Options:
  - A. 扩展 `/me/housing`：顶层增加 `real_names: list[str]`，每套房屋增加 `co_owners: list[str]`；服务端只对"当前用户自己的有效成员关系所在专有部分"计算，不接受任何专有部分参数。优：一次请求；越权不可能（没有入参）；前端沿用 `useHousingStore`。缺：字段集变更须同步契约测试断言（已列清单）。
  - B. 新接口 `GET /me/identity-names`。优：不动 `/me/housing` 字段集。缺：前端要两次请求并自行按 `unit_id` 拼接；多一个需要审查的端点；用户要求"列出 /me/housing 字段变更"即倾向 A。
- Decision: 选 A（IFC-357）。`real_names`：用户为产权业主（HEAD/OWNER）的专有部分中，**与用户有对应关系**的清册业主姓名，去重保序；"对应关系" = `Membership.registry_owner_id` 命中，或清册业主的某个 `RegistryPhone.phone` 等于用户已验证手机号（Q-B18-04=A，后者为主口径，前者增强申诉通过等无手机号场景）。`co_owners`：该专有部分其余清册业主的姓名（非空、去重、排除"用户本人对应的业主行"），仅对**用户在该专有部分有有效成员关系（产权业主或同住人，Q-B18-05=B）**的行返回；不含手机号、不标注注册状态。两项各用一次"按专有部分批量取业主及电话"的查询（`prefetch`），查询数不随房屋数增长（M-SA-010）。
- Consequences: 正向——游客/未认证用户无任何成员关系，`units=[]`、`real_names=[]`，读到任意专有部分姓名的路径不存在（REQ-NFUNC-046 度量 =0）。负向——(1) 契约测试断言集合须更新：`test_frontend_contract.py:582-585`（顶层集合加 `real_names`、单元集合加 `co_owners`），新 Vue 代码中的循环变量读取须落在这些集合内（`reads()` 扫描，M-SA-023）；(2) 若用户本人在该专有部分的清册业主行无法识别（既无 `registry_owner` 也无手机号对应），其本人姓名会出现在 `co_owners` 中，属已知边界，见开放问题 OQ-B3；(3) 小程序读取 `/me/housing` 的字段不变，新增字段对其无影响。

### ADR-141: 决议公开范围、参与进度与参与人列表（含头像可读与 `votes` 数组移除）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-244/245/246/254、REQ-NFUNC-046(3)、REQ-NFUNC-049(5)、Q-B18-08=A（半数同意进行中的决议公开）、Q-B18-09/10/11/12/13/14。现状：列表 `scope=public` 只含 APPROVED/REJECTED（`resolutions/views.py:62-63`）；详情对非结束状态仅发起人与在任委员可看（`:107-110`）；附件策略同口径（`resolutions/apps.py:25-39`）；`resolution_view` 的 `votes` 含 `voter_id`、`choice`（`:35-36`），前端与小程序均不读取该数组（`git grep` 仅 `vote_counts` 被读：`Resolutions.vue:23`、`miniprogram/pages/resolutions/index.vue:17`）；他人头像下载不可行：`AVATAR` 附件为 TEMP，`AttachmentService.open` 对 TEMP 只允许属主（`core/attachments.py:121-124`）。
- Options:
  - A. 参与人用独立端点 `GET /api/v1/resolutions/{id}/participants`；列表/详情只增加聚合字段 `participation`；删除 `votes` 数组；放宽 `AVATAR` 附件为"任一已登录用户/管理员可读"。优：参与人信息的隐私评审集中在一个序列化器；列表载荷不随参与人增大；删除 `votes` 一次性满足"谁投了什么 = 0"。缺：多一个端点；`votes` 删除属字段移除。
  - B. 在详情内联 `participants`。优：少一个端点。缺：详情序列化器同时承载内容与参与人，列表/详情共用的 `resolution_view` 易误带出；每次打开详情都查昵称头像。
  - C. 保留 `votes` 但对非委员过滤。优：不删字段。缺：进行中决议向所有人公开，过滤条件难穷举，且无调用方需要。
- Decision: 选 A。细节：
  1. **公开范围**（IFC-358）：`scope=public` 为 `status∈{APPROVED,REJECTED}` 或 `status=PENDING 且 approval_mode=HALF_MAJORITY`；详情与附件策略采用同一判定函数 `is_publicly_visible(row)`，其余（指定负责人审批中、已撤回）仍仅发起人与在任委员。`scope=mine/todo` 不变。
  2. **参与进度**：半数同意决议增加 `participation: {"voted": int, "expected": int}`；`voted` = 当前 `revision` 的投票数；`expected` = 审批中取 `CommitteeQuery.denominator_for_half_majority(SystemConfig.get("vote.denominator_mode"))`（与 `judge_if_due` 同函数同口径，REQ-NFUNC-049(5)），已结束取 `result["denominator"]`；指定负责人决议该字段为 `null`。列表一次性取出本页全部决议的投票并分组、分母整页只算一次（无 N+1）。`vote_counts` 保留。
  3. **发起人**：`initiator` 增加 `display_name`（昵称，空则账号编号，REQ-FUNC-244(a)）；`labels` 为发起时身份，沿用。
  4. **参与人端点**（IFC-359）：见 module_design；只返回 `display_name`、`avatar_url`、`voted_at`，按 `voted_at,id` 升序，不返回 `user_id`、选项、手机号、真实姓名。
  5. **删除 `votes`**：`resolution_view` 不再输出 `votes`。这是对 REQ-NFUNC-050"既有字段不变"的**有意例外**：REQ-NFUNC-046(3) 的度量（接口响应中"谁投了什么"=0）在 Q-B18-08=A 之后对所有已登录用户成立，二者冲突时按需求内更具体、且有用户明确答复支撑的 046 执行；该字段无任何前端/小程序调用方，后端测试亦无断言（`git grep` 核对）。
  6. **头像可读**：`AttachmentService.open` 对 `row.purpose == "AVATAR"` 且主体为已登录成员或管理员者放行（UUID 不可枚举）。这是隐私面的有意放宽（原仅本人可读），仅限头像，不影响其他用途。
- Consequences: 正向——隐私裁剪集中；列表载荷稳定；进度与判定同源。负向——(1) 公开列表在 Web 与小程序都会出现进行中决议（后端行为），小程序无改动即显示，字段无破坏（ADR-146）；(2) 头像对所有登录用户可读，须用户知悉，列入开放问题 OQ-B4；(3) 删除 `votes` 若有未登记的外部调用方会受影响，已 `git grep` 核对仓库内无；(4) `display_name` 取账号编号时是否算"账号全称"（REQ-NFUNC-046(3)）与 REQ-FUNC-246 字面一致，按 REQ-FUNC-246 执行，OQ-B4 一并提请确认。

### ADR-142: 清册列表服务端排序的实现位置与参数白名单
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-249/250、REQ-NFUNC-048、Q-B18-17=A（全量服务端排序）、Q-B18-18=A（楼栋/单元/楼层/房号）、Q-B18-19=A（两态）。现状：`AdminUnitListView` 用 `order_by("id")` + `page_response(qs, …)`（`registry/views.py:119-139`、`core/serializers.py:4-12`，要求对象有 `count()` 与切片）；自然顺序规则只有 Python 实现（`registry/ordering.py:94-104 unit_sort_key`，含中文数字、"地下车位/商铺"层级），无法用 SQL `ORDER BY` 复现。
- Options:
  - A. 取过滤后的 `(id, building, unit_no, floor, room)`，在 Python 中用 `unit_sort_key` 排序得到 id 序列，再按页取对象并还原顺序；用一个带 `count()` 与 `__getitem__(slice)` 的轻量包装对象接入现有 `page_response`。降序仅反转主排序键，次序键仍升序（两次稳定排序）。优：与既有规则逐字一致（REQ-FUNC-249 要求沿用）；改动局部；约 650 行量级毫秒级。缺：每次请求全量取 5 列，数据量到数万行才需要优化。
  - B. 数据库侧加冗余排序列（`building_key` 等）并建索引。优：可 SQL 分页。缺：需迁移与回填、双写一致性，且数字自然规则含中文数字与保留楼栋，难以序列化为可比较的 SQL 键。
  - C. 仅前端对当前页排序。缺：Q-B18-17 明确否定。
- Decision: 选 A（IFC-361/362）。参数：`sort ∈ {building, unit_no, floor, room}`、`order ∈ {asc, desc}`；缺省 `sort` 时为默认升序（楼栋、单元、楼层、房号、id）；`order` 缺省 `asc`；`order` 单独出现、或取值不在白名单 → 400 `INVALID_QUERY`（沿用既有错误码，`views.py:68`）。过滤参数不变，排序在过滤结果内进行。
- Consequences: 正向——规则唯一来源；翻页稳定（id 为终极并列键）。负向——不适合百万级；后续规模增长需改 B，记入风险。

### ADR-143: 专有部分下拉检索的实现
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-241、REQ-NFUNC-048（≤200 ms）、Q-B18-02=A、Q-B18-03=C（前缀优先、其余包含在后）。现状 `UnitCascader.vue:4-17` 是四个 `el-select`，被三页共用；画像 P1 前端栈为 Element Plus（已装 2.14.8，`frontend/node_modules/element-plus/package.json`）。
- Options:
  - A. 四个 `el-select` 加 `filterable` 与 `filter-method`，在本地对已加载的选项做"前缀优先 + 包含"排序，`no-data-text="无匹配项"`。优：零新依赖、零新接口、选项本就一次性加载；键盘可用。缺：需自行排序（Element Plus 默认过滤不排序）。
  - B. 服务端检索接口（`/units/options?q=`）。缺：每次输入一次请求，超出 200 ms 预算风险，且要改接口与契约。
  - C. 换用 `el-autocomplete`/`el-cascader`。缺：交互与现有四级联动、`skipped` 自动跳级逻辑不兼容，改动面大。
- Decision: 选 A。检索只作用当前下拉的候选，不改变联动与已选结果（REQ-FUNC-241）。
- Consequences: 正向——一个组件覆盖三页，无后端改动。负向——`UnitCascader` 同时要服务管理端（席位授予，ADR-145），选项来源须可注入（新增 `fetcher` prop，缺省 `unitApi.options`），否则管理员令牌无法调用成员端接口。

### ADR-144: 决议/投票卡片整卡可点与导航动效的实现
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-247/248、REQ-NFUNC-047（≤400 ms、点击响应 ≤100 ms、减少动效下动画数 = 0、三主题可见）。现状：卡片仅标题是 `<router-link>`（`Resolutions.vue:15`、`Polls.vue:13-20`）；导航二级项由 `v-if` 即时显示（`SideNav.vue:25`）；全局减少动效规则已存在；`::before` 已被 terminal 主题用于 "> " 前缀（`themes.css:634`）；主题层禁止在 `.vue` 中写颜色字面量（M-SA-022，`theme.spec`）。
- Options（卡片）:
  - A. "拉伸链接"：保留标题 `<router-link>`，用 CSS `::after` 铺满卡片作为点击区；卡片内独立可点元素加 `position: relative; z-index: 1`。优：原生链接语义，键盘 Tab/Enter、中键/新标签页、读屏都成立，无需 JS；内部链接天然不触发进入正文。缺：需约束卡片内其他交互元素的层级。
  - B. 卡片 `@click` + `role="link"` + `tabindex` + `@keydown.enter`。缺：自己实现键盘/焦点语义，内部元素要逐个 `@click.stop`。
- Options（导航展开）:
  - C. Vue `<Transition>` JS 钩子测量 `scrollHeight` 做高度动画，子项 CSS 错峰淡入。优：支持 `v-if` 既有结构与 Esc/焦点逻辑不变；jsdom 中 `Transition` 被 VTU 默认 stub，既有测试不受影响。缺：钩子需自行判断减少动效（`matchMedia` 在 jsdom 缺失，缺失按"不减少"处理但不抛错，M-SA-021）。
  - D. 改为始终渲染 + CSS `grid-template-rows` 过渡。缺：改变 `v-if` 结构，破坏既有 `layout_nav`/`layout_e2e` 对 DOM 存在性的断言。
- Decision: 卡片选 A，导航选 C。选中项强调用 `::after` 竖条做 `scaleY` + 背景渐显（不用 `::before`，避免与 terminal 主题冲突），颜色全部取 `var(--accent)`/`var(--glass)` 等主题变量；卡片悬停 `translateY` + `box-shadow: var(--shadow)`、按下 `scale(.985)`；所有时长 ≤ 360 ms；新增 CSS 写在 `shared/style.css`，并放进 `@media (prefers-reduced-motion: no-preference)`，使"减少动效"下不产生任何新动画（比依赖全局覆盖更稳）。窄屏 `SubNavBar` 选中项使用同一类名与动画（Q-B18-16=a）。
- Consequences: 正向——无新依赖；可达性由原生语义保证。负向——三主题下观感需人工核对（NOT_TESTABLE 部分，列入人工验证）；`style.css` 新规则须经 `layout_css.spec`/`theme.spec` 守护，不得出现颜色字面量。

### ADR-145: 管理员选择"专有部分 + 清册业主"的接口与组件
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-251、Q-B18-20=A、REQ-NFUNC-046(4)、C-79。约束：(1) 成员端 `GET /units/options` 只接受成员令牌（`IsMember`，`registry/views.py:55-57`），管理端使用 `adminHttp`（契约测试 `test_frontend_contract.py:62-81` 禁止管理员客户端调用仅成员接口）；(2) 现有管理端清册列表返回业主**完整手机号**（`registry/serializers.py:6-17`，US-019），不能直接用作候选；(3) 候选须手机号脱敏。
- 被排除的替代方案: 复用 `GET /admin/registry/units`（泄露完整手机号，违反 046(4)）；放宽 `/units/options` 为管理员可调（违反既有契约测试的角色隔离）。
- Decision: 新增两个仅管理员接口：`GET /admin/registry/unit-options`（复用 `RegistryService.options`，IFC-351）与 `GET /admin/committee/owner-candidates`（IFC-350，返回姓名、脱敏手机号、是否已有有效席位、是否已注册）；前端 `UnitCascader` 以 `fetcher` prop 注入管理员取数函数，新增 `admin/parts/SeatHolderPicker.vue` 组合"逐级选房 + 选业主"。
- Consequences: 正向——脱敏与角色隔离靠接口形状保证。负向——多两个路由与契约条目；`AdminSeats.vue` 不再使用 `UserPicker` 的"搜索注册用户"（既有 `user_id` 授予路径后端仍保留，兼容旧客户端与既有测试）。

### ADR-146: 小程序兼容策略（本批小程序不改）
- Status: Proposed
- Type: constraint-driven
- Context: Q-B18-01=A、REQ-NFUNC-050、画像 P6（`miniprogram/utils/api.js` 仅在后端变动破坏兼容时才动）。
- 被排除的替代方案: 同步改小程序（Q-B18-01=B/C，用户未选）。
- Decision: 所有后端变更按"增字段/增分支/增参数"设计，唯一例外是 `votes` 数组移除（ADR-141，小程序不读取）。小程序读取的受影响接口及影响如下（`miniprogram/utils/api.js`）：

| 小程序调用 | 变化 | 兼容性 |
|---|---|---|
| `POST /appeals`（JSON：`unit_id`、`owner_name`、`proof_ids`；`api.js:34`）与 `POST /attachments`（`utils/http.js` upload） | 新增 multipart 分支；JSON 分支与 `/attachments` 不变 | 完全兼容；`test_owner_auth_v2_contract.py:129-134` 小程序侧断言不变 |
| `GET /me/housing`（`api.js`） | 顶层增 `real_names`，每套增 `co_owners` | 增字段，小程序按需读取，兼容；契约集合断言须同步 |
| `GET /resolutions`、`GET /resolutions/{id}`（`api.js:46` 邻近） | 公开列表新增进行中的半数同意决议；每条增 `participation`、`initiator.display_name`；`votes` 移除；详情对进行中半数同意决议 200 | 小程序仅读 `vote_counts`、`initiator.labels`（`pages/resolutions/index.vue:17`），不破坏；行为变化：小程序公开页也会出现"进行中"决议，卡片文案按其现有状态标签显示 |
| `POST /resolutions/{id}/votes` | 无变化 | 兼容 |
| 席位/身份：`/me` 的 `identities`（`IdentityService.me`） | 待绑定席位不出现；绑定后身份照常显示职位名 | 兼容 |
| `GET /polls*`（业主代表投票） | `active_representative_ids` 排除空 user，行为不变（此前无空 user） | 兼容 |
| 附件下载 `GET /attachments/{id}/download` | `AVATAR` 用途对所有已登录用户可读 | 放宽，兼容 |

- Consequences: 正向——零小程序改动与构建。负向——小程序端出现进行中决议属于行为变化，需用户知悉（OQ-B5）。

## 开放问题 / ASSUMPTION

| 编号 | 内容 | 类型 | 需谁确认 |
|---|---|---|---|
| Q-B18-33（承接需求） | 待绑定席位对半数同意的影响仅在席位页顶部提示、不拦截（推荐 A），**用户待确认** | 用户待确认 | 用户 |
| OQ-B1 | 本批之前已认证、手机号与清册不一致的用户没有 `registry_owner` 记录，也无新的认证事件；对其授予席位时回退按手机号找人，找不到则成为永不自动绑定的待绑定席位 [ASSUMPTION] | 无需求依据 | PM/用户（可接受：管理员发现后改用"用户ID授予"旧路径，后端仍保留） |
| OQ-B2 | 绑定冲突后的出路为"撤销原席位 → 对同一清册业主重新授予"（不新增重试接口）[ASSUMPTION] | 无需求依据 | 用户 |
| OQ-B3 | `/me/housing` 在无法识别用户本人对应的清册业主行时，会把用户本人姓名列入 `co_owners` [ASSUMPTION：概率低，因手动认证要求手机号+姓名匹配、申诉通过会追加业主行] | 边界 | 用户（可接受） |
| OQ-B4 | (1) 头像对所有已登录用户可读；(2) 参与人无昵称时显示账号编号，是否属 REQ-NFUNC-046(3) 所说"账号全称" | 隐私口径 | 用户 |
| OQ-B5 | 小程序公开决议页将因后端变化出现"进行中"决议；`votes` 数组移除 | 行为变化 | 用户 |
| OQ-B6 | 清册改名使待绑定席位失效后需重新授予；是否需要"改名前警告管理员"（需求未提） | [ASSUMPTION] 不做 | 用户 |
| OQ-B7 | nginx `client_max_body_size`（ocap 站点与 Freeark 反代块）是否 ≥ 55 MB，仓库内无法核实 | 运维事实 | E1/E2 只读核实 |
| OQ-B8 | 动效时长 ≤400 ms、点击响应 ≤100 ms 为需求中的 `[INFERRED]` 阈值，沿用 | 需求推断项 | 用户 |
